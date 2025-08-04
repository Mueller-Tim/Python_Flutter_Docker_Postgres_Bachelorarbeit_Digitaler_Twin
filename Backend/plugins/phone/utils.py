"""
phone/utils.py

Hilfsfunktionen zum Erkennen, Normalisieren und Aufbereiten von
Schweizer Telefonnummern (+41 …), inklusive:

* Regex-Extraktion aus beliebigem Text
* Umwandlung verschiedener Schreibweisen in das E.164-ähnliche Format
  „+41XXXXXXXXX“
* Platzhalter- und Tabelleneinträge für das Telefon-Plugin
"""

from __future__ import annotations

import re
from datetime import date
from typing import List, Set

from config import NO_DATA_FOUND_TEXT

# --------------------------------------------------------------------------- #
# Konstanten
# --------------------------------------------------------------------------- #
PHONE_REGEX: re.Pattern[str] = re.compile(
    r"(?:\+41\s?\d{2}\s?\d{3}\s?\d{2}\s?\d{2}"      # +41 79 123 45 67
    r"|0\d{2}\s?\d{3}\s?\d{2}\s?\d{2}"              # 079 123 45 67
    r"|0041\d{2}\d{3}\d{2}\d{2})"                   # 0041791234567
)

# --------------------------------------------------------------------------- #
# Normalisierung & Validierung
# --------------------------------------------------------------------------- #
def normalize_phone_number(raw: str) -> str:
    """
    Entfernt Leerzeichen, Trennzeichen und konvertiert die Nummer in
    das Format ``+41XXXXXXXXX``.

    Beispiele
    ---------
    >>> normalize_phone_number("079 123 45 67")
    '+41791234567'
    >>> normalize_phone_number("0041 44 123 45 67")
    '+41441234567'
    """
    digits = re.sub(r"[ \-\/]", "", raw).strip()
    if digits.startswith("0041"):
        digits = "+" + digits[2:]
    elif digits.startswith("0"):
        digits = "+41" + digits[1:]
    return digits


def is_valid_swiss_number(num: str) -> bool:
    """Grobe Plausibilitätsprüfung: beginnt mit +41 und nicht mit +4100."""
    return num.startswith("+41") and not num.startswith("+4100")


# --------------------------------------------------------------------------- #
# Extraktion
# --------------------------------------------------------------------------- #
def extract_phone_numbers(text: str) -> Set[str]:
    """
    Durchsucht *text* nach Schweizer Telefonnummern und gibt sie
    normalisiert zurück.

    Parameters
    ----------
    text : str
        Beliebiger Quelltext (HTML, JSON, Plain-Text …).

    Returns
    -------
    set[str]
        Menge eindeutiger, validierter Telefonnummern.
    """
    raw_hits = set(PHONE_REGEX.findall(text))
    return {
        norm
        for norm in map(normalize_phone_number, raw_hits)
        if is_valid_swiss_number(norm)
    }


# --------------------------------------------------------------------------- #
# Tabellen-Utilities
# --------------------------------------------------------------------------- #
def insert_data_in_phone_columns(
    columns: List[str], phone: str, src_date: str
) -> dict:
    """
    Baut einen Ergebnis-Dict-Eintrag für eine gefundene Telefonnummer.

    Parameters
    ----------
    columns : list[str]
        Spaltenüberschriften der Telefon-Tabelle.
    phone : str
        Normalisierte Telefonnummer.
    src_date : str
        Datum der Quelle im Format ``YYYYMMDD``.

    Returns
    -------
    dict
        Befüllter Tabelleneintrag.
    """
    if src_date and len(src_date) == 8:
        src_date = f"{src_date[:4]}-{src_date[4:6]}-{src_date[6:]}"
    return {
        columns[0]: phone,
        columns[1]: NO_DATA_FOUND_TEXT,        # Leak-Status wird später gesetzt
        columns[2]: src_date or "0000-00-00",
        columns[3]: date.today().isoformat(),
    }


def generate_fallback_phone_entry(columns: List[str]) -> dict:
    """
    Liefert einen Platzhalter-Eintrag, wenn keine Telefonnummer gefunden wurde.
    """
    return {
        columns[0]: NO_DATA_FOUND_TEXT,
        columns[1]: NO_DATA_FOUND_TEXT,
        columns[2]: "0000-00-00",
        columns[3]: date.today().isoformat(),
    }
