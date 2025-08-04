"""
phone_plugin.py

Sammelt Telefonnummern, die mit einer Domain verknüpft sind, aus

1. Wayback-Machine-Snapshots archivierter Webseiten
2. WHOIS-Daten

und prüft anschließend via DeHashed-API, ob zu einer Nummer Klartext-
Passwörter geleakt wurden. Die Ergebnisse werden dedupliziert,
persistiert und für weitere Analysen bereitgestellt.
"""

from __future__ import annotations

import json
import logging
import random
import time
from datetime import datetime
from typing import List

from database import create_standard_table, get_db_connection, insert_record
from plugins.base_plugin import BasePlugin
from plugins.email.dehashed_lookup import is_leaked
from plugins.endpoint.endpoint_plugin import Plugin as EndpointPlugin
from plugins.phone.utils import generate_fallback_phone_entry
from plugins.phone.waybackmachine_lookup import extract_phone_numbers_from_url
from plugins.phone.whois_lookup import get_whois_phone_numbers
from config import NO_DATA_SCANNED_TEXT, NO_DATA_FOUND_TEXT

# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# --------------------------------------------------------------------------- #
# Konstanten
# --------------------------------------------------------------------------- #
RANDOM_SLEEP: int = random.randint(7, 15)

_ep_cols = EndpointPlugin().columns
ENDPOINT_URL_KEY: str = _ep_cols[0]
ENDPOINT_SNAP_KEY: str = _ep_cols[1]

# --------------------------------------------------------------------------- #
# Plugin-Klasse
# --------------------------------------------------------------------------- #
class Plugin(BasePlugin):
    """
    Telefonnummern-Plugin des Digitalen Zwillings.

    Beispiel
    --------
    >>> p = Plugin()
    >>> p.scan("example.com")
    """

    # -------------------------------------------------------------- #
    # Initialisierung & Setup
    # -------------------------------------------------------------- #
    def __init__(self) -> None:
        self.name: str = "Telefonnummer"
        self.description: str = (
            "Überblick über Telefonnummern, die mit einer Domain verknüpft sind; "
            "zeigt, ob damit verbundene Passwörter geleakt wurden."
        )
        self.columns: list[str] = [
            "Telefonnummer",
            "Passwort geleakt (Ja/Nein)",
            "In öffentlicher Datenbank erfasst am",
            "Gescannt am",
        ]
        self.table: str = "phones"

    def setup(self) -> None:
        """Erzeugt die Datenbank-Tabelle, falls noch nicht vorhanden."""
        create_standard_table(self.table)

    # -------------------------------------------------------------- #
    # Haupt-Scan
    # -------------------------------------------------------------- #
    def scan(self, domain: str) -> List[dict]:
        """Extrahiert Telefonnummern und persistiert das Ergebnis."""
        _clear_table(self.table, domain)

        # 1) Wayback-Machine-Quellen
        all_entries: list[dict] = []
        for i, ep in enumerate(self._get_endpoints(domain)[:50], start=1):
            url = ep[ENDPOINT_URL_KEY]
            ts = ep[ENDPOINT_SNAP_KEY].replace("-", "") + "000000"
            logger.info("🌐 [%d/50] Wayback-Scan: %s", i, url)
            all_entries += extract_phone_numbers_from_url(ts, url, self.columns)
            time.sleep(RANDOM_SLEEP)

        # 2) WHOIS
        all_entries += get_whois_phone_numbers(domain, self.columns)

        # 3) Dubletten entfernen & sortieren
        deduped = _deduplicate_phones(all_entries, self.columns)

        # 4) Platzhalter-Filter
        valid = [
            e
            for e in deduped
            if e[self.columns[0]] and NO_DATA_FOUND_TEXT not in e[self.columns[0]]
        ]

        # 5) Leak-Status via DeHashed
        for entry in valid:
            entry[self.columns[1]] = is_leaked(entry[self.columns[0]])

        # 6) Fallback, wenn nichts gefunden
        if not valid:
            valid = [generate_fallback_phone_entry(self.columns)]

        # 7) Persistenz
        for entry in valid:
            insert_record(self.table, domain, json.dumps(entry))

        return valid

    # -------------------------------------------------------------- #
    # Datenabruf
    # -------------------------------------------------------------- #
    def get(self, domain: str) -> List[dict]:
        """Gibt gespeicherte Ergebnisse zurück (oder Info-Platzhalter)."""
        with get_db_connection() as conn, conn.cursor() as cur:
            cur.execute(f"SELECT value FROM {self.table} WHERE domain = %s;", (domain,))
            rows = cur.fetchall()

        if not rows:
            return [{"info": NO_DATA_SCANNED_TEXT}]

        return [json.loads(r[0]) if isinstance(r[0], str) else r[0] for r in rows]

    # -------------------------------------------------------------- #
    # Interne Helfer
    # -------------------------------------------------------------- #
    @staticmethod
    def _parse_date(date_str: str) -> datetime:
        try:
            return datetime.strptime(date_str[:8], "%Y%m%d")
        except Exception:  # noqa: BLE001
            return datetime.min

    def _get_endpoints(self, domain: str) -> List[dict]:
        with get_db_connection() as conn, conn.cursor() as cur:
            cur.execute("SELECT value FROM endpoints WHERE domain = %s;", (domain,))
            rows = cur.fetchall()

        eps = [
            json.loads(r[0]) if isinstance(r[0], str) else r[0] for r in rows
        ]
        return sorted(eps, key=lambda e: e[ENDPOINT_SNAP_KEY], reverse=True)


# --------------------------------------------------------------------------- #
# Modul-Helferfunktionen
# --------------------------------------------------------------------------- #
def _deduplicate_phones(entries: List[dict], columns: list[str]) -> List[dict]:
    """Behält pro Nummer nur den Eintrag mit dem neuesten Quell-Datum."""
    phone_key, date_key = columns[0], columns[2]
    latest: dict[str, dict] = {}

    for entry in entries:
        phone = entry[phone_key]
        src_date = Plugin._parse_date(entry.get(date_key, ""))
        if phone not in latest or src_date > Plugin._parse_date(latest[phone].get(date_key, "")):
            latest[phone] = entry

    return sorted(latest.values(), key=lambda e: e[phone_key])


def _clear_table(table: str, domain: str) -> None:
    """Löscht alle bestehenden Datensätze für *domain* aus *table*."""
    with get_db_connection() as conn, conn.cursor() as cur:
        cur.execute(f"DELETE FROM {table} WHERE domain = %s;", (domain,))
        conn.commit()
