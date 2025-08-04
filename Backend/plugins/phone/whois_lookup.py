"""
phone/whois_lookup.py

Extrahiert Schweizer Telefonnummern aus WHOIS-Datensätzen einer Domain
und wandelt sie in das Standard-Tabellenformat des Telefon-Plugins um.
"""

from __future__ import annotations

import logging
from datetime import date
from typing import List

from whois import whois

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
# Public API
# --------------------------------------------------------------------------- #
def get_whois_phone_numbers(domain: str, columns: list[str]) -> List[dict]:
    """
    Sucht Telefonnummern im WHOIS-Rohtext einer Domain.

    Parameters
    ----------
    domain : str
        Ziel-Domain (z. B. ``"example.com"``).
    columns : list[str]
        Spaltenüberschriften der Telefon-Tabelle.

    Returns
    -------
    list[dict]
        Strukturierte Zeilen für die Telefon-Tabelle; falls keine Nummer
        gefunden oder ein Fehler auftritt, ein Platzhalter-Dict in einer
        Liste.
    """
    try:
        whois_data = whois(domain)
    except Exception as exc:  # noqa: BLE001
        logger.error("⚠️  WHOIS-Lookup fehlgeschlagen für %s: %s", domain, exc)
        return [generate_fallback_phone_entry(columns)]

    # Raw-Text durchsuchen
    numbers = extract_phone_numbers(str(whois_data))
    if numbers:
        logger.info("📞 WHOIS: %d Nummer(n) gefunden", len(numbers))

    whois_iso = date.today().isoformat()
    rows = [
        insert_data_in_phone_columns(columns, num, whois_iso) for num in numbers
    ]

    # Fallback, falls keine Nummern vorhanden
    return rows if rows else [generate_fallback_phone_entry(columns)]
