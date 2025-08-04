"""
crtsh_email_lookup.py

Durchsucht den inoffiziellen JSON-Endpoint von crt.sh nach möglichen
E-Mail-Adressen, die in den Subject-Alternative-Name-Feldern der
Zertifikate (name_value) auftauchen. Die Treffer werden zusammen mit dem
Zeitstempel des Zertifikateintrags zurückgegeben.
"""

from __future__ import annotations

from typing import List

import requests

from config import NO_DATA_FOUND_TEXT
from plugins.email.utils import (
    extract_emails_from_text,
    generate_empty_email_entry,
    insert_data_in_email_columns,
)

# --------------------------------------------------------------------------- #
# Konstanten
# --------------------------------------------------------------------------- #
CRT_SH_API: str = "https://crt.sh/?q=%25.{domain}&output=json"
REQUEST_TIMEOUT: int = 10  # Sekunden


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def get_crtsh_emails(domain: str, columns: list[str]) -> List[dict]:
    """
    Extrahiert E-Mail-Adressen aus crt.sh-Zertifikaten für eine Domain.

    Parameters
    ----------
    domain : str
        Ziel-Domain (z. B. ``'example.com'``).
    columns : list[str]
        Spaltenüberschriften der Ergebnis-Tabelle.

    Returns
    -------
    list[dict]
        Strukturierte Einträge mit den gefundenen Adressen; falls nichts
        gefunden oder ein Fehler auftritt, ein Platzhalter-Dict.
    """
    url = CRT_SH_API.format(domain=domain)

    # ----------------------------- HTTP-Request -----------------------------
    try:
        resp = requests.get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
    except requests.exceptions.RequestException as exc:
        print(f"🚨  Netzwerk/HTTP-Fehler bei crt.sh: {exc}")
        return [generate_empty_email_entry(columns)]

    # ------------------------------ JSON-Parse ------------------------------
    try:
        records = resp.json()
    except ValueError as exc:
        print(f"⚠️  Ungültiges JSON von crt.sh: {exc}")
        return [generate_empty_email_entry(columns)]

    # ------------------------ E-Mail-Extraktion -----------------------------
    emails: list[dict] = []
    for record in records:
        san_text: str = record.get("name_value", "")
        found_emails = extract_emails_from_text(san_text)
        crtsh_date = record.get("entry_timestamp", NO_DATA_FOUND_TEXT).split("T")[0]

        for address in found_emails:
            emails.append(
                insert_data_in_email_columns(columns, address, crtsh_date)
            )

    # Platzhalter, falls keine Adressen gefunden wurden
    if not emails:
        emails.append(generate_empty_email_entry(columns))

    return emails
