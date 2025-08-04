"""
dns_plugin.py

Plugin für den „Digitalen Zwilling“, das je nach konfiguriertem
Ressource-Record-Typ (A, AAAA, MX, NS, TXT, SOA, PTR) die entsprechenden
DNS-Einträge einer Domain ermittelt, speichert und zurückliefert.

Nutzen:
• Sicherheits-Checks (z. B. SPF, DKIM, Reverse-DNS)
• Infrastruktur-Übersicht der Ziel-Domain
• Compliance-Berichte
"""

from __future__ import annotations

import json
from datetime import date
from typing import Dict, List

from database import (
    create_standard_table,
    get_db_connection,
    insert_record,
)
from plugins.base_plugin import BasePlugin
from plugins.dns.dig_lookup import get_dns_records
from config import NO_DATA_FOUND_TEXT, NO_DATA_SCANNED_TEXT

# --------------------------------------------------------------------------- #
# Beschreibungen & Spaltendeklarationen
# --------------------------------------------------------------------------- #
RECORD_DESCRIPTIONS: dict[str, str] = {
    "A": "Zeigt, unter welcher IPv4-Adresse die Domain erreichbar ist.",
    "AAAA": "Zeigt, unter welcher IPv6-Adresse die Domain erreichbar ist.",
    "MX": (
        "Listet die Mailserver (Mail Exchange) auf, die den E-Mail-Empfang "
        "übernehmen. Server mit niedrigerer Zahl (Priorität) werden zuerst "
        "genutzt."
    ),
    "NS": "Gibt an, welche Nameserver autoritativ für die Domain sind.",
    "TXT": (
        "Enthält frei definierbare Texte, z. B. für SPF, DKIM oder "
        "Verifizierungs-Einträge (Google-Site-Verification u. ä.)."
    ),
    "SOA": (
        "Start-of-Authority-Eintrag mit primärem Nameserver, Hostmaster-Adresse, "
        "Serial-Nummer und diversen Zeitparametern (Refresh, Retry, Expire, TTL)."
    ),
    "PTR": "Ermöglicht Reverse-DNS (IP → Hostname); wichtig für Logging und Mail.",
}

RECORD_COLUMNS: dict[str, list[str]] = {
    "A": ["IPv4-Adresse", "Gescannt am"],
    "AAAA": ["IPv6-Adresse", "Gescannt am"],
    "MX": ["Mailserver", "Priorität", "Gescannt am"],
    "NS": ["Nameserver", "Gescannt am"],
    "TXT": ["TXT-Record", "Gescannt am"],
    "SOA": [
        "Primärer NS",
        "Hostmaster",
        "Serial",
        "Refresh",
        "Retry",
        "Expire",
        "Min. TTL",
        "Gescannt am",
    ],
    "PTR": ["IP-Adresse", "PTR-Domain", "Gescannt am"],
}


# --------------------------------------------------------------------------- #
# Plugin-Klasse
# --------------------------------------------------------------------------- #
class Plugin(BasePlugin):
    """
    DNS-Plugin, konfiguriert für genau einen Record-Typ.

    Beispiele
    ---------
    >>> mx_plugin = Plugin("MX")
    >>> mx_plugin.scan("example.com")
    """

    # ------------------------------------------------------------------ #
    # Initialisierung & Setup
    # ------------------------------------------------------------------ #
    def __init__(self, record_type: str) -> None:
        self.record_type: str = record_type.upper()
        self.name: str = f"{self.record_type}-Record"
        self.description: str = RECORD_DESCRIPTIONS.get(
            self.record_type, f"{self.record_type}-DNS-Record"
        )
        self.columns: list[str] = RECORD_COLUMNS.get(
            self.record_type, ["Wert", "Gescannt am"]
        )

    def setup(self) -> None:
        """Legt die Datenbank-Tabelle an (falls noch nicht vorhanden)."""
        create_standard_table(f"{self.record_type.lower()}_record")

    # ------------------------------------------------------------------ #
    # Scan-Logik
    # ------------------------------------------------------------------ #
    def scan(self, domain: str) -> List[dict]:
        """
        Führt einen DNS-Lookup aus, persistiert die Ergebnisse und gibt sie zurück.

        Parameters
        ----------
        domain : str
            Ziel-Domain, z. B. ``'example.com'``.

        Returns
        -------
        list[dict]
            Strukturierte Record-Einträge; bei Fehlschlag Platzhalter-Eintrag.
        """
        table = f"{self.record_type.lower()}_record"
        today = date.today().isoformat()
        results: list[dict] = []

        # Vorherige Scans entfernen – wir halten nur den aktuellen Snapshot.
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(f"DELETE FROM {table} WHERE domain = %s;", (domain,))
                conn.commit()

        # DNS-Abfrage vorbereiten (PTR braucht A+AAAA als Basis).
        lookup_types = (
            ["A", "AAAA", "PTR"] if self.record_type == "PTR" else [self.record_type]
        )
        dns_data = get_dns_records(domain, lookup_types)

        # Dispatch je Record-Typ
        match self.record_type:
            case "PTR":
                self._scan_ptr(dns_data, domain, today, results, table)
            case "SOA":
                self._scan_soa(dns_data, domain, today, results, table)
            case "MX":
                self._scan_mx(dns_data, domain, today, results, table)
            case _:
                self._scan_simple(dns_data, domain, today, results, table)

        return results

    # ------------------------------------------------------------------ #
    # Hilfs-Methoden pro Record-Typ
    # ------------------------------------------------------------------ #
    def _scan_ptr(
        self,
        dns_data: dict,
        domain: str,
        scan_date: str,
        results: list[dict],
        table: str,
    ) -> None:
        ptr_records = dns_data.get("PTR", {})
        for ip, ptr_list in ptr_records.items():
            for ptr in ptr_list:
                if ptr in {NO_DATA_FOUND_TEXT, NO_DATA_SCANNED_TEXT}:
                    continue
                entry = {
                    "IP-Adresse": ip,
                    "PTR-Domain": ptr,
                    "Gescannt am": scan_date,
                }
                results.append(entry)
                insert_record(table, domain, entry)

        # Platzhalter, falls keine PTR-Daten
        if not results:
            placeholder = {
                "IP-Adresse": NO_DATA_FOUND_TEXT,
                "PTR-Domain": NO_DATA_FOUND_TEXT,
                "Gescannt am": scan_date,
            }
            results.append(placeholder)
            insert_record(table, domain, placeholder)

    def _scan_soa(
        self,
        dns_data: dict,
        domain: str,
        scan_date: str,
        results: list[dict],
        table: str,
    ) -> None:
        for soa_raw in dns_data.get("SOA", []):
            parts = soa_raw.split()
            if len(parts) >= 7:
                entry = {
                    "Primärer NS": parts[0],
                    "Hostmaster": parts[1],
                    "Serial": parts[2],
                    "Refresh": parts[3],
                    "Retry": parts[4],
                    "Expire": parts[5],
                    "Min. TTL": parts[6],
                    "Gescannt am": scan_date,
                }
                results.append(entry)
                insert_record(table, domain, entry)

        if not results:
            placeholder = {col: NO_DATA_FOUND_TEXT for col in self.columns[:-1]} | {
                "Gescannt am": scan_date
            }
            results.append(placeholder)
            insert_record(table, domain, placeholder)

    def _scan_mx(
        self,
        dns_data: dict,
        domain: str,
        scan_date: str,
        results: list[dict],
        table: str,
    ) -> None:
        for mx_raw in dns_data.get("MX", []):
            try:
                pref, server = mx_raw.split()
            except ValueError:
                pref, server = NO_DATA_FOUND_TEXT, mx_raw
            entry = {
                "Mailserver": server,
                "Priorität": pref,
                "Gescannt am": scan_date,
            }
            results.append(entry)
            insert_record(table, domain, entry)

    def _scan_simple(
        self,
        dns_data: dict,
        domain: str,
        scan_date: str,
        results: list[dict],
        table: str,
    ) -> None:
        for value in dns_data.get(self.record_type, []):
            entry = {self.columns[0]: value, "Gescannt am": scan_date}
            results.append(entry)
            insert_record(table, domain, entry)

    # ------------------------------------------------------------------ #
    # Datenabruf
    # ------------------------------------------------------------------ #
    def get(self, domain: str) -> List[dict]:
        """
        Gibt die gespeicherten Daten zurück (oder Info-Platzhalter).

        Parameters
        ----------
        domain : str
            Die Domain, deren Daten angefordert werden.

        Returns
        -------
        list[dict]
            Persistierte Einträge oder ``{"info": NO_DATA_SCANNED_TEXT}``.
        """
        table = f"{self.record_type.lower()}_record"
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(f"SELECT value FROM {table} WHERE domain = %s;", (domain,))
                rows = cur.fetchall()

        if not rows:
            return [{"info": NO_DATA_SCANNED_TEXT}]

        return [
            row[0] if isinstance(row[0], dict) else json.loads(row[0]) for row in rows
        ]
