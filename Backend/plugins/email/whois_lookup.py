"""
whois_lookup.py

Extrahiert E-Mail-Adressen aus WHOIS-Daten für eine Domain und bringt sie
in das Standard-Spalten­format des E-Mail-Plugins.
"""

from __future__ import annotations

from datetime import date
from typing import List

from whois import whois

from plugins.email.utils import (
    generate_empty_email_entry,
    insert_data_in_email_columns,
)

# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def get_whois_emails(domain: str, columns: list[str]) -> List[dict]:
    """
    Liefert WHOIS-E-Mails einer Domain, aufbereitet für die E-Mail-Tabelle.

    Parameters
    ----------
    domain : str
        Ziel-Domain (z. B. ``'example.com'``).
    columns : list[str]
        Spaltenüberschriften der E-Mail-Tabelle.

    Returns
    -------
    list[dict]
        Strukturierte Einträge oder ein Platzhalter-Dict, falls keine
        E-Mail-Adressen gefunden werden konnten.
    """
    try:
        whois_data = whois(domain)
    except Exception as exc:  # noqa: BLE001
        # Netzwerk-, Parsing- oder Rate-Limit-Fehler
        print(f"⚠️  WHOIS-Fehler bei {domain}: {exc}")
        return [generate_empty_email_entry(columns)]

    raw_emails: set[str] = set()
    if isinstance(whois_data.emails, list):
        raw_emails = set(whois_data.emails)
    elif isinstance(whois_data.emails, str):
        raw_emails = {whois_data.emails}

    if not raw_emails:
        return [generate_empty_email_entry(columns)]

    src_date = date.today().isoformat()
    return [
        insert_data_in_email_columns(columns, addr, src_date) for addr in raw_emails
    ]
