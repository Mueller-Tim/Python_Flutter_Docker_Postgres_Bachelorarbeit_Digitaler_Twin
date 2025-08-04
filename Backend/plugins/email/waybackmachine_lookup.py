"""
waybackmachine_lookup.py

Lädt archivierte Webseiten von web.archive.org und extrahiert daraus
E-Mail-Adressen. Dabei wird zuerst ein schneller Filter auf Dateiendungen
angewendet (Bilder, Videos, Fonts … werden übersprungen), um unnötige
Requests zu vermeiden.
"""

from __future__ import annotations

import logging
import random
from datetime import datetime
from typing import List

import requests

from plugins.email.utils import (
    extract_emails_from_text,
    generate_empty_email_entry,
    insert_data_in_email_columns,
)

# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# --------------------------------------------------------------------------- #
# Konstanten
# --------------------------------------------------------------------------- #
USER_AGENTS: list[str] = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X)",
    "Mozilla/5.0 (Linux; Android 10; SM-G975F)",
]

SKIP_SUFFIXES: tuple[str, ...] = (
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
def extract_emails_from_url(
    timestamp: str, url: str, columns: list[str]
) -> List[dict]:
    """
    Holt eine archivierte URL vom Wayback Machine CDX-Service und
    extrahiert daraus E-Mail-Adressen.

    Parameters
    ----------
    timestamp : str
        14-stelliger Wayback-Timestamp (``YYYYMMDDhhmmss``).
    url : str
        Originale Ziel-URL (ohne https://).
    columns : list[str]
        Spaltenüberschriften der E-Mail-Tabelle.

    Returns
    -------
    list[dict]
        Strukturierte E-Mail-Einträge; ggf. ein Platzhalter-Dict, falls
        keine Adresse gefunden wurde.
    """
    # -------- Schnellskip für binäre Assets --------------------------------
    if url.lower().endswith(SKIP_SUFFIXES):
        logger.info("⏩ Übersprungen wegen Dateiendung: %s", url)
        return []

    full_url = f"{WAYBACK_BASE}{timestamp}/{url}"
    logger.info("🔎 Extrahiere E-Mails aus: %s", full_url)

    headers = {"User-Agent": random.choice(USER_AGENTS)}

    try:
        resp = requests.get(full_url, headers=headers, timeout=10)
        resp.raise_for_status()
    except requests.exceptions.RequestException as exc:
        logger.warning("⚠️ Fehler bei %s: %s", full_url, exc)
        return []

    # -------- E-Mail-Extraktion -------------------------------------------
    found = extract_emails_from_text(resp.text)
    if not found:
        return [generate_empty_email_entry(columns)]

    source_iso = datetime.strptime(timestamp[:8], "%Y%m%d").date().isoformat()
    return [
        insert_data_in_email_columns(columns, addr, source_iso) for addr in found
    ]
