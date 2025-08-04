"""
subdomain_plugin.py

Ermittelt per Sublist3r alle Subdomains einer Ziel-Domain, speichert die
Treffer in einer Datenbanktabelle und stellt sie für weitere Analysen
(Endpoint-Scans, Zertifikat-Checks usw.) bereit.
"""

from __future__ import annotations

import json
from datetime import date
from typing import List

from database import create_standard_table, get_db_connection, insert_record
from plugins.base_plugin import BasePlugin
from plugins.subdomain.sublist3r_runner import get_subdomains
from config import NO_DATA_SCANNED_TEXT

# --------------------------------------------------------------------------- #
# Plugin-Klasse
# --------------------------------------------------------------------------- #
class Plugin(BasePlugin):
    """
    Subdomain-Plugin des Digitalen Zwillings.
    """

    # -------------------------------------------------------------- #
    # Initialisierung & Setup
    # -------------------------------------------------------------- #
    def __init__(self) -> None:
        self.name: str = "Subdomain"
        self.description: str = "Überblick über Subdomains einer Domain."
        self.columns: list[str] = [
            "Subdomain",
            "Gescannt am",
        ]
        self.table: str = "subdomain_record"

    def setup(self) -> None:
        """Erzeugt die Datenbanktabelle, falls sie noch nicht existiert."""
        create_standard_table(self.table)

    # -------------------------------------------------------------- #
    # Haupt-Scan
    # -------------------------------------------------------------- #
    def scan(self, domain: str) -> List[dict]:
        """
        Führt die Subdomain-Enumeration mit Sublist3r durch.

        Parameters
        ----------
        domain : str
            Ziel-Domain (z. B. ``'example.com'``).

        Returns
        -------
        list[dict]
            Liste gefundener Subdomain-Einträge.
        """
        _clear_table(self.table, domain)

        subdomains = get_subdomains(domain, self.columns)
        for entry in subdomains:
            insert_record(self.table, domain, entry)

        return subdomains

    # -------------------------------------------------------------- #
    # Datenabruf
    # -------------------------------------------------------------- #
    def get(self, domain: str) -> List[dict]:
        """
        Holt gespeicherte Subdomains aus der Datenbank.

        Parameters
        ----------
        domain : str
            Ziel-Domain.

        Returns
        -------
        list[dict]
            Persistierte Einträge oder Platzhalter-Info.
        """
        with get_db_connection() as conn, conn.cursor() as cur:
            cur.execute(f"SELECT value FROM {self.table} WHERE domain = %s;", (domain,))
            rows = cur.fetchall()

        if not rows:
            return [{"info": NO_DATA_SCANNED_TEXT}]

        # DB-Layer kann Dict oder JSON-String liefern
        return [
            row[0] if isinstance(row[0], dict) else json.loads(row[0]) for row in rows
        ]


# --------------------------------------------------------------------------- #
# Helfer
# --------------------------------------------------------------------------- #
def _clear_table(table: str, domain: str) -> None:
    """Löscht alte Scan-Ergebnisse für *domain* aus *table*."""
    with get_db_connection() as conn, conn.cursor() as cur:
        cur.execute(f"DELETE FROM {table} WHERE domain = %s;", (domain,))
        conn.commit()
