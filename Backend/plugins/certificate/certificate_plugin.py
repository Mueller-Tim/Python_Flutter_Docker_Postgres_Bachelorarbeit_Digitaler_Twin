"""
certificate_plugin.py

Dieses Plugin durchsucht die öffentliche Datenbank crt.sh nach
SSL/TLS-Zertifikaten für eine angegebene (Sub-)Domain, legt die
Ergebnisse in der lokalen Datenbank ab und stellt sie für weitere
Analysen bereit.

Gedacht für den Einsatz im „Digitalen Zwilling“-Scanner, kann aber
eigenständig verwendet werden.
"""

from __future__ import annotations

import json
from typing import List

from database import create_standard_table, get_db_connection, insert_record
from plugins.base_plugin import BasePlugin
from plugins.certificate.crtsh_lookup import get_certificates
from config import NO_DATA_SCANNED_TEXT


class Plugin(BasePlugin):
    """
    Zertifikats-Plugin für den Digitalen Zwilling.

    Attributes
    ----------
    name : str
        Klartext-Bezeichnung des Plugins.
    description : str
        Kurze Beschreibung der Funktion – wird z. B. in der UI angezeigt.
    columns : list[str]
        Spaltenüberschriften der Ergebnis-Tabelle.
    table : str
        Name der Tabelle in der Datenbank, in die Ergebnisse geschrieben
        werden.
    """

    def __init__(self) -> None:
        self.name: str = "Zertifikat"
        self.description: str = (
            "Analysiert die SSL-Zertifikate von Subdomains einer angegebenen "
            "Domain.\nZeigt, ob ein gültiges Zertifikat vorhanden ist, wer es "
            "ausgestellt hat, wann es in einer öffentlichen Datenbank "
            "erfasst wurde, und wie lange es gültig ist.\nErkennt auch "
            "Wildcard-Zertifikate."
        )
        self.columns: list[str] = [
            "Domain/Subdomain",
            "Ausgestellt von",
            "In öffentlicher Datenbank erfasst am",
            "Gültig ab",
            "Gültig bis",
            "Wildcard-Zertifikat? (Ja/Nein)",
            "Im Digitalen Zwilling gescannt am",
        ]
        self.table: str = "certificate_record"

    # --------------------------------------------------------------------- #
    # Initialisierung
    # --------------------------------------------------------------------- #
    def setup(self) -> None:
        """Legt (falls nötig) die Datenbanktabelle für dieses Plugin an."""
        create_standard_table(self.table)

    # --------------------------------------------------------------------- #
    # Daten erfassen
    # --------------------------------------------------------------------- #
    def scan(self, domain: str) -> List[dict]:
        """
        Sucht über crt.sh nach Zertifikaten und speichert die Ergebnisse.

        Parameters
        ----------
        domain : str
            Die (Sub-)Domain, für die Zertifikate gesucht werden.

        Returns
        -------
        list[dict]
            Eine Liste mit Zertifikats-Dicts oder einem Dict mit
            'error', falls die Abfrage fehlschlägt.
        """
        # Vorherige Ergebnisse für diese Domain leeren,
        # damit wir immer einen frischen Snapshot haben.
        conn = get_db_connection()
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"DELETE FROM {self.table} WHERE domain = %s;",
                    (domain,),
                )

        # crt.sh liefert eine Liste von Dicts.
        certs = get_certificates(domain, self.columns)

        # Bei Fehler sofort zurück – nichts in DB schreiben.
        if certs and "error" in certs[0]:
            return certs

        # Ergebnisse persistent speichern.
        for cert in certs:
            insert_record(self.table, domain, cert)

        return certs

    # --------------------------------------------------------------------- #
    # Daten abrufen
    # --------------------------------------------------------------------- #
    def get(self, domain: str) -> List[dict]:
        """
        Holt die gespeicherten Zertifikatsdaten aus der Datenbank.

        Parameters
        ----------
        domain : str
            Die Domain, zu der Daten abgerufen werden.

        Returns
        -------
        list[dict]
            Zertifikats-Dicts oder ein Info-Dict, falls keine Daten vorliegen.
        """
        conn = get_db_connection()
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"SELECT value FROM {self.table} WHERE domain = %s;",
                    (domain,),
                )
                rows = cur.fetchall()

        if not rows:
            # Noch nicht gescannt
            return [{"info": NO_DATA_SCANNED_TEXT}]

        # Die Spalte 'value' enthält JSON-Strings oder bereits Dicts.
        return [
            row[0] if isinstance(row[0], dict) else json.loads(row[0])
            for row in rows
        ]
