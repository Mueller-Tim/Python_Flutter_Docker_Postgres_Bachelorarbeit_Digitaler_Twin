"""
phone/waybackmachine_lookup.py

Lädt archivierte Webseiten von web.archive.org (Wayback Machine) und
extrahiert Schweizer Telefonnummern (+41 …) aus dem HTML-Quelltext.

Ablauf
------
1. URL schnell filtern (Dateiendungen wie *.jpg, *.css … überspringen)
2. Snapshot abrufen (HTTP GET mit zufälligem User-Agent)
3. Telefonnummern via Regex erkennen & normalisieren
4. Ergebnis ins Spaltenformat des Telefon-Plugins gießen
   (inkl. Quell-Datum aus dem Wayback-Timestamp)
"""

from __future__ import annotations

import logging
import random
from datetime import datetime
from typing import List, Tuple

import requests

from plugins.phone.utils import (
    extract_phone_numbers,
    generate_fallback_phone_entry,
    insert_data_in_phone_columns,
)

# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# --------------------------------------------------------------------------- #
# Konstanten
# --------------------------------------------------------------------------- #
USER_AGENTS: list[str] = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (Linux; Android 10; SM-G975F)",
]

SKIP_SUFFIXES: Tuple[str, ...] = (
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".svg",
    ".webp",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".otf",
    ".pdf",
    ".zip",
    ".rar",
    ".7z",
    ".mp4",
    ".mp3",
    ".avi",
    ".mov",
    ".css",
    ".js",
    ".ico",
    ".exe",
    ".dmg",
)

WAYBACK_BASE: str = "http://web.archive.org/web/"


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def extract_phone_numbers_from_url(
    timestamp: str, url: str, columns: list[str]
) -> List[dict]:
    """
    Extrahiert Telefonnummern aus einer archivierten URL.

    Parameters
    ----------
    timestamp : str
        Wayback-Timestamp (``YYYYMMDDhhmmss``).
    url : str
        Originale URL (ohne https://), z. B. ``example.com/impressum``.
    columns : list[str]
        Spaltenüberschriften der Telefon-Tabelle.

    Returns
    -------
    list[dict]
        Treffer → Tabellenzeilen, ansonsten ein Platzhalter-Dict
        (in einer Liste, damit der Rückgabewert immer `List[dict]`
        bleibt).
    """
    # 1) frühes Skip, falls die URL auf einen Binär-/Asset-Pfad zeigt
    if url.lower().endswith(SKIP_SUFFIXES):
        logger.debug("⏩ Übersprungen wegen Dateiendung: %s", url)
        return []

    full_url = f"{WAYBACK_BASE}{timestamp}/{url}"
    headers = {"User-Agent": random.choice(USER_AGENTS)}

    try:
        resp = requests.get(full_url, headers=headers, timeout=10)
        resp.raise_for_status()
    except requests.exceptions.RequestException as exc:
        logger.warning("⚠️ Netzwerkfehler bei %s: %s", full_url, exc)
        # Fallback im Fehlerfall
        return [generate_fallback_phone_entry(columns)]

    # 2) Telefonnummern suchen
    phones = extract_phone_numbers(resp.text)
    if phones:
        logger.info("📞 % d Nummer(n) gefunden auf %s", len(phones), full_url)

    # 3) Treffer in Tabellenform bringen
    src_iso = datetime.strptime(timestamp[:8], "%Y%m%d").date().isoformat()
    rows = [
        insert_data_in_phone_columns(columns, num, src_iso) for num in phones
    ]

    # 4) Fallback, wenn keine Nummern gefunden
    return rows if rows else [generate_fallback_phone_entry(columns)]
