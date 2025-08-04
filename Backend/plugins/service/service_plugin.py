"""
service_plugin.py   (Shodan-Port-/Service-Scan)

Fragt über einen Shodan-Wrapper die offen erreichbaren Dienste einer
Domain ab und speichert die Ergebnisse in einer Datenbanktabelle.

Für jeden Treffer werden u. a. gespeichert:

* IPv4-Adresse
* Port & Protokoll
* Dienst & Version
* CPE-Bezeichner
* Gefundene CVE-IDs
"""

from __future__ import annotations

import json
import logging
from typing import List

from database import create_standard_table, get_db_connection, insert_record
from plugins.base_plugin import BasePlugin
from plugins.service.shodan_lookup import search_services
from config import NO_DATA_SCANNED_TEXT

# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# --------------------------------------------------------------------------- #
# Plugin-Klasse
# --------------------------------------------------------------------------- #
class Plugin(BasePlugin):
    """
    Shodan-Dienst-Plugin des Digitalen Zwillings.

    Beispiel
    --------
    >>> p = Plugin()
    >>> p.scan("example.com")
    """

    # -------------------------------------------------------------- #
    # Initialisierung & Setup
    # -------------------------------------------------------------- #
    def __init__(self) -> None:
        self.name: str = "Dienst"
        self.description: str = (
            "Überblick über offene Ports und identifizierte Dienste einer Domain "
            "auf Basis von Shodan-Daten."
        )
        self.columns: list[str] = [
            "IPv4-Adresse",
            "Port",
            "Dienst",
            "Version",
            "Protokoll",
            "Common Platform Enumeration (CPE)",
            "Common Vulnerabilities and Exposures (CVE)",
            "Domain/Subdomain",
            "Gescannt am",
        ]
        self.table: str = "shodan_services"

    def setup(self) -> None:
        """Erzeugt die Datenbank-Tabelle, falls noch nicht vorhanden."""
        create_standard_table(self.table)

    # -------------------------------------------------------------- #
    # Haupt-Scan
    # -------------------------------------------------------------- #
    def scan(self, domain: str) -> List[dict]:
        """
        Ruft Shodan-Daten für *domain* ab und speichert sie.

        Parameters
        ----------
        domain : str
            Ziel-Domain.

        Returns
        -------
        list[dict]
            Alle Service-Einträge (auch Platzhalter, falls Shodan nichts
            geliefert hat – je nach `search_services`-Implementierung).
        """
        _clear_table(self.table, domain)

        services = search_services(domain, self.columns)
        for svc in services:
            insert_record(self.table, domain, svc)

        logger.info("📦 %d Dienst-Einträge gespeichert", len(services))
        return services

    # -------------------------------------------------------------- #
    # Datenabruf
    # -------------------------------------------------------------- #
    def get(self, domain: str) -> List[dict]:
        """
        Gibt gespeicherte Shodan-Einträge zurück (oder Info-Platzhalter).

        Parameters
        ----------
        domain : str
            Ziel-Domain.

        Returns
        -------
        list[dict]
            Persistierte Einträge oder ``{'info': NO_DATA_SCANNED_TEXT}``.
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
    """Entfernt alte Scan-Ergebnisse für *domain* aus *table*."""
    with get_db_connection() as conn, conn.cursor() as cur:
        cur.execute(f"DELETE FROM {table} WHERE domain = %s;", (domain,))
        conn.commit()
