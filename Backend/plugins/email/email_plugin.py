"""
email_plugin.py

Sammelt E-Mail-Adressen, die mit einer Domain verknüpft sind, aus
verschiedenen Quellen:

1. Wayback Machine (archivierte Web-Sites)
2. WHOIS-Datensätze
3. crt.sh-Zertifikate
4. (optional) weitere Quellen via utils-Module

Zusätzlich prüft das Plugin per DeHashed-API, ob zu jeder Adresse
Klartext-Passwörter geleakt wurden.
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
from plugins.email.crtsh_lookup import get_crtsh_emails
from plugins.email.dehashed_lookup import is_leaked
from plugins.email.utils import (
    generate_empty_email_entry,
)
from plugins.email.waybackmachine_lookup import extract_emails_from_url
from plugins.email.whois_lookup import get_whois_emails
from plugins.endpoint.endpoint_plugin import Plugin as EndpointPlugin
from config import NO_DATA_SCANNED_TEXT, NO_DATA_FOUND_TEXT

# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Konstanten
# --------------------------------------------------------------------------- #
RANDOM_SLEEP: int = random.randint(7, 15)  # Höfliche Wartezeit Wayback→API
MAX_URLS: int = 50  # Wie viele archivierte Seiten wir maximal scannen

# Spalten aus dem Endpoint-Plugin übernehmen
_endpoint_cols = EndpointPlugin().columns
ENDPOINT_URL_KEY: str = _endpoint_cols[0]
ENDPOINT_SNAP_KEY: str = _endpoint_cols[1]


# --------------------------------------------------------------------------- #
# Plugin-Klasse
# --------------------------------------------------------------------------- #
class Plugin(BasePlugin):
    """
    E-Mail-Plugin des Digitalen Zwillings.

    Beispiel
    --------
    >>> p = Plugin()
    >>> p.scan("example.com")
    """

    # -------------------------------------------------------------- #
    # Initialisierung & Setup
    # -------------------------------------------------------------- #
    def __init__(self) -> None:
        self.name: str = "E-Mail"
        self.description: str = (
            "Überblick über E-Mail-Adressen, die zu einer Domain gehören; "
            "zeigt, ob damit verknüpfte Passwörter geleakt wurden."
        )
        self.columns: list[str] = [
            "E-Mail",
            "Passwort geleakt (Ja/Nein)",
            "In öffentlicher Datenbank erfasst am",
            "Gescannt am",
        ]
        self.table: str = "emails"

    def setup(self) -> None:
        """Erzeugt die Datenbank-Tabelle, falls sie noch nicht existiert."""
        create_standard_table(self.table)

    # -------------------------------------------------------------- #
    # Hilfs-Methoden
    # -------------------------------------------------------------- #
    @staticmethod
    def _clean_email(raw: str) -> str:
        """Entfernt URL-Encodings & trimmt Whitespace."""
        return raw.replace("%20", "").strip().lower()

    @staticmethod
    def _deduplicate(
        entries: List[dict], columns: list[str], clean_fn
    ) -> List[dict]:
        """
        Behält pro Adresse nur den neuesten Datensatz (nach Quelle-Datum).

        Parameters
        ----------
        entries : list[dict]
            Alle gefundenen Adresseinträge.
        columns : list[str]
            Spaltenüberschriften; Index 0 = E-Mail, 2 = Quell-Datum.
        clean_fn : Callable
            Funktion zur Normalisierung der Mail-Adresse.

        Returns
        -------
        list[dict]
            Gecleante & sortierte Ergebnisliste.
        """
        mail_key, date_key = columns[0], columns[2]
        latest: dict[str, dict] = {}

        for entry in entries:
            addr_raw = entry.get(mail_key, "")
            addr = clean_fn(addr_raw) if clean_fn else addr_raw

            # Datum parsen (YYYYMMDD… oder leer)
            src_date = _parse_date(entry.get(date_key, ""))

            if addr not in latest or src_date > _parse_date(
                latest[addr].get(date_key, "")
            ):
                latest[addr] = entry

        # Sortiert zurückgeben (alphabetisch nach Mail)
        return sorted(latest.values(), key=lambda e: clean_fn(e[mail_key]))

    def _get_endpoints(self, domain: str) -> List[dict]:
        """Lädt archivierte Endpunkte aus der DB (Endpoint-Plugin)."""
        with get_db_connection() as conn, conn.cursor() as cur:
            cur.execute("SELECT value FROM endpoints WHERE domain = %s;", (domain,))
            rows = cur.fetchall()

        endpoints = [
            r[0] if isinstance(r[0], dict) else json.loads(r[0]) for r in rows
        ]
        # Sortiert (neuester Snapshot zuerst)
        endpoints.sort(key=lambda e: e[ENDPOINT_SNAP_KEY], reverse=True)
        return endpoints

    # -------------------------------------------------------------- #
    # Haupt-Scan
    # -------------------------------------------------------------- #
    def scan(self, domain: str) -> List[dict]:
        """Holt & speichert alle E-Mail-Infos für *domain*."""
        _clear_table(self.table, domain)

        # 1) Archivierte Webseiten abklappern
        all_entries: list[dict] = []
        for i, ep in enumerate(self._get_endpoints(domain)[:MAX_URLS], start=1):
            url = ep[ENDPOINT_URL_KEY]
            snapshot = ep[ENDPOINT_SNAP_KEY]
            ts = snapshot.replace("-", "") + "000000"

            logger.info(f"🌐 [{i}/{MAX_URLS}] Wayback: {ts}/{url}")
            entries = extract_emails_from_url(ts, url, self.columns)
            all_entries.extend(entries)
            time.sleep(RANDOM_SLEEP)

        # 2) WHOIS + crt.sh
        all_entries.extend(get_whois_emails(domain, self.columns))
        all_entries.extend(get_crtsh_emails(domain, self.columns))

        # 3) Dubletten filtern
        deduped = self._deduplicate(all_entries, self.columns, self._clean_email)

        # 4) Leere Platzhalter rauswerfen
        valid_entries = [
            e
            for e in deduped
            if e.get(self.columns[0])
            and NO_DATA_FOUND_TEXT not in e.get(self.columns[0], "")
        ]

        # 5) Leak-Status via DeHashed prüfen
        for entry in valid_entries:
            entry[self.columns[1]] = is_leaked(entry[self.columns[0]])

        # 6) Fallback-Platzhalter, wenn gar nichts da
        if not valid_entries:
            valid_entries = [generate_empty_email_entry(self.columns)]

        # 7) Persistenz
        for entry in valid_entries:
            insert_record(self.table, domain, entry)

        return valid_entries

    # -------------------------------------------------------------- #
    # Datenabruf
    # -------------------------------------------------------------- #
    def get(self, domain: str) -> List[dict]:
        """Liefert gespeicherte Ergebnisse (oder Hinweis, falls leer)."""
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


def _parse_date(date_str: str) -> datetime:
    """Versucht YYYYMMDD-Strings zu `datetime` zu parsen, else `datetime.min`."""
    try:
        return datetime.strptime(date_str[:8], "%Y%m%d")
    except Exception:  # noqa: BLE001
        return datetime.min
