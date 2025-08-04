"""
endpoint_plugin.py

Sammelt historische Endpunkte (URLs) einer Domain über archivierte
robots.txt-Dateien, Sitemap-Snapshots und die CDX-API der Wayback Machine.
Die Ergebnisse werden in einer Datenbanktabelle gespeichert und können
später für weitere Analysen (z. B. E-Mail-Crawling) genutzt werden.
"""

from __future__ import annotations

import json
from typing import List

from database import create_standard_table, get_db_connection, insert_record
from plugins.base_plugin import BasePlugin
from plugins.endpoint.waybackmachine_lookup import combine_all
from config import NO_DATA_SCANNED_TEXT

# --------------------------------------------------------------------------- #
# Plugin-Klasse
# --------------------------------------------------------------------------- #
class Plugin(BasePlugin):
    """
    Endpoint-Plugin des Digitalen Zwillings.

    Beispiel
    --------
    >>> ep = Plugin()
    >>> ep.scan("example.com")
    """

    # -------------------------------------------------------------- #
    # Initialisierung & Setup
    # -------------------------------------------------------------- #
    def __init__(self) -> None:
        self.name: str = "Endpunkt"
        self.description: str = (
            "Überblick über historische URLs (Endpunkte) einer Domain "
            "auf Basis von Wayback-Machine-Snapshots."
        )
        self.columns: list[str] = [
            "URL",
            "In öffentlicher Datenbank erfasst am",
            "Gescannt am",
        ]
        self.table: str = "endpoints"

    def setup(self) -> None:
        """Erzeugt die Datenbanktabelle für Endpunkte (falls nötig)."""
        create_standard_table(self.table)

    # -------------------------------------------------------------- #
    # Haupt-Scan
    # -------------------------------------------------------------- #
    def scan(self, domain: str) -> List[dict]:
        """
        Extrahiert archivierte Endpunkte einer Domain und speichert sie.

        Parameters
        ----------
        domain : str
            Ziel-Domain, z. B. ``'example.com'``.

        Returns
        -------
        list[dict]
            Liste gefundener Endpunkte; bei Fehler ein Dict mit ``error``.
        """
        _clear_table(self.table, domain)

        try:
            endpoints = combine_all(
                domain, self.columns, robot_limit=5, sitemap_limit=5
            )
        except Exception as exc:  # noqa: BLE001
            return [{"error": f"Fehler beim Wayback-Scan: {exc}"}]

        for entry in endpoints:
            insert_record(self.table, domain, entry)

        return endpoints

    # -------------------------------------------------------------- #
    # Datenabruf
    # -------------------------------------------------------------- #
    def get(self, domain: str) -> List[dict]:
        """
        Holt gespeicherte Endpunkte aus der Datenbank.

        Parameters
        ----------
        domain : str
            Ziel-Domain.

        Returns
        -------
        list[dict]
            Persistierte Einträge oder Info-Platzhalter, falls leer.
        """
        with get_db_connection() as conn, conn.cursor() as cur:
            cur.execute(f"SELECT value FROM {self.table} WHERE domain = %s;", (domain,))
            rows = cur.fetchall()

        if not rows:
            return [{"info": NO_DATA_SCANNED_TEXT}]

        return [
            r[0] if isinstance(r[0], dict) else json.loads(r[0]) for r in rows
        ]


# --------------------------------------------------------------------------- #
# Helfer
# --------------------------------------------------------------------------- #
def _clear_table(table: str, domain: str) -> None:
    """Löscht alle bestehenden Datensätze für *domain* aus *table*."""
    with get_db_connection() as conn, conn.cursor() as cur:
        cur.execute(f"DELETE FROM {table} WHERE domain = %s;", (domain,))
        conn.commit()
