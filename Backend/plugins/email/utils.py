"""
email/utils.py

Hilfsfunktionen rund um das Extrahieren, Validieren und Aufbereiten von
E-Mail-Adressen. Verwendet eine aktuelle TLD-Liste (IANA) als Filter,
um offensichtliche Falsch-Hits aus Regex-Treffern zu entfernen.
"""

from __future__ import annotations

import logging
import os
import re
from datetime import date
from pathlib import Path
from typing import Final, List, Set

from config import NO_DATA_FOUND_TEXT

# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# --------------------------------------------------------------------------- #
# Konstanten
# --------------------------------------------------------------------------- #
_TLD_FILE: Final[Path] = Path(__file__).with_name("tlds-alpha-by-domain.txt")
_EMAIL_REGEX: Final[re.Pattern[str]] = re.compile(
    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
)

try:
    with _TLD_FILE.open(encoding="utf-8") as fh:
        VALID_TLDS: Final[Set[str]] = {
            line.strip().lower()
            for line in fh
            if line.strip() and not line.startswith("#")
        }
except FileNotFoundError as exc:
    logger.error("TLD-Datei nicht gefunden: %s", exc)
    VALID_TLDS = set()

# --------------------------------------------------------------------------- #
# Public Helpers
# --------------------------------------------------------------------------- #
def is_valid_email_tld(address: str) -> bool:
    """
    Prüft, ob die Top-Level-Domain einer E-Mail in der IANA-Liste steht.

    Parameters
    ----------
    address : str
        Komplette E-Mail-Adresse.

    Returns
    -------
    bool
        ``True`` falls TLD gültig, sonst ``False``.
    """
    try:
        tld = address.rsplit(".", 1)[-1].lower()
        return tld in VALID_TLDS
    except Exception:  # noqa: BLE001
        return False


def extract_emails_from_text(text: str) -> Set[str]:
    """
    Extrahiert valide E-Mail-Adressen aus beliebigem Text.

    Die Funktion kombiniert einen Regex-Match mit einem TLD-Check, um
    offensichtliche Fehl-Treffer (z. B. ``user@localhost``) auszufiltern.

    Parameters
    ----------
    text : str
        Quelldokument (HTML, JSON, Plain-Text …).

    Returns
    -------
    set[str]
        Menge aller gültigen E-Mail-Adressen.
    """
    raw_matches = _EMAIL_REGEX.findall(text)
    logger.debug("📬 Roh-Treffer: %s", raw_matches)

    valid = {m for m in raw_matches if is_valid_email_tld(m)}
    logger.debug("✅ Nach TLD-Filter: %s", valid)
    return valid


def insert_data_in_email_columns(
    columns: List[str], email: str, source_date: str
) -> dict:
    """
    Baut ein Ergebnis-Dict für einen gefundenen Mail-Treffer.

    Parameters
    ----------
    columns : list[str]
        Spaltenüberschriften der E-Mail-Tabelle.
    email : str
        Gefundene E-Mail-Adresse.
    source_date : str
        Datum (YYYYMMDD) der Quelle, aus der die Adresse stammt.

    Returns
    -------
    dict
        Befüllte Ergebniszeile.
    """
    if source_date and len(source_date) == 8:
        source_date = f"{source_date[:4]}-{source_date[4:6]}-{source_date[6:]}"

    return {
        columns[0]: email,
        columns[1]: NO_DATA_FOUND_TEXT,        # Leak-Status wird später gesetzt
        columns[2]: source_date or "0000-00-00",
        columns[3]: date.today().isoformat(),
    }


def generate_empty_email_entry(columns: List[str]) -> dict:
    """
    Liefert einen Platzhalter-Eintrag, falls keinerlei Mail-Adressen
    gefunden wurden.

    Parameters
    ----------
    columns : list[str]
        Spaltenüberschriften der E-Mail-Tabelle.

    Returns
    -------
    dict
        Platzhalter mit ``NO_DATA_FOUND_TEXT`` in allen Feldern.
    """
    return {
        columns[0]: NO_DATA_FOUND_TEXT,
        columns[1]: NO_DATA_FOUND_TEXT,
        columns[2]: "0000-00-00",
        columns[3]: date.today().isoformat(),
    }
