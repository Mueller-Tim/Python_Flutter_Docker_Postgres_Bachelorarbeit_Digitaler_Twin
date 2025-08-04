"""
crtsh_lookup.py

Hilfsmodul, das über die inoffizielle JSON-Schnittstelle von crt.sh
Zertifikatsdaten für eine (Sub-)Domain abruft und in eine tabellarische
Struktur gießt.
"""

from __future__ import annotations

import random
import time
from datetime import date
from typing import List

import requests

from config import NO_DATA_FOUND_TEXT

# --------------------------------------------------------------------------- #
# Konstanten
# --------------------------------------------------------------------------- #
CRT_SH_API: str = "https://crt.sh/?q=%25.{domain}&output=json"
UA_HEADER: dict[str, str] = {
    "User-Agent": "Mozilla/5.0 (compatible; Digitwin-Scanner/1.0)"
}

# --------------------------------------------------------------------------- #
# Helfer-Funktionen
# --------------------------------------------------------------------------- #
def _generate_empty_certificate_entry(columns: list[str]) -> dict:
    """
    Liefert eine Platzhalter-Zeile, wenn keine Zertifikatsdaten
    gefunden oder ein Fehler aufgetreten ist.

    Parameters
    ----------
    columns : list[str]
        Spaltenüberschriften der Ergebnis-Tabelle.

    Returns
    -------
    dict
        Dict mit NO_DATA_FOUND_TEXT in allen Feldern.
    """
    today = date.today().isoformat()
    return {col: NO_DATA_FOUND_TEXT for col in columns[:-1]} | {columns[-1]: today}


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def get_certificates(domain: str, columns: list[str]) -> List[dict]:
    """
    Ruft Zertifikate von crt.sh ab und bereitet sie tabellarisch auf.

    Parameters
    ----------
    domain : str
        Die zu prüfende Domain (z. B. "example.com").
    columns : list[str]
        Gewünschte Spaltenüberschriften für das Ergebnis.

    Returns
    -------
    list[dict]
        Liste strukturierter Zertifikats-Dicts; falls nichts gefunden
        wurde oder ein Fehler auftrat: eine einzelne Platzhalter-Zeile.
    """
    url = CRT_SH_API.format(domain=domain)

    # Höfliche Wartezeit, um crt.sh nicht zu fluten.
    time.sleep(random.randint(2, 4))

    try:
        response = requests.get(url, headers=UA_HEADER, timeout=60)
        if response.status_code != 200:
            # Server-Fehler oder Rate-Limit → Platzhalter zurückgeben
            print(f"⚠️  crt.sh HTTP-Fehler: {response.status_code}")
            return [_generate_empty_certificate_entry(columns)]

        raw = response.json()
        if not raw:
            return [_generate_empty_certificate_entry(columns)]

        certs: list[dict] = []
        for entry in raw:
            # ───────────── Feldwerte mit Fallback auf NO_DATA_FOUND_TEXT ──────────
            issuer = entry.get("issuer_name", NO_DATA_FOUND_TEXT)
            entry_ts = entry.get("entry_timestamp", NO_DATA_FOUND_TEXT).split("T")[0]
            nb_ts = entry.get("not_before", NO_DATA_FOUND_TEXT).split("T")[0]
            na_ts = entry.get("not_after", NO_DATA_FOUND_TEXT).split("T")[0]

            # name_value enthält alle SAN-Einträge im Zertifikat (je Zeile einer)
            names_list = entry.get("name_value", "").splitlines()
            is_wildcard = any(name.startswith("*.") for name in names_list)
            names_joined = ", ".join(names_list) if names_list else NO_DATA_FOUND_TEXT

            certs.append(
                {
                    columns[0]: names_joined,
                    columns[1]: issuer,
                    columns[2]: entry_ts,
                    columns[3]: nb_ts,
                    columns[4]: na_ts,
                    columns[5]: "Ja" if is_wildcard else "Nein",
                    columns[6]: date.today().isoformat(),
                }
            )

        return certs

    except requests.exceptions.Timeout:
        # Netzwerk-Timeout → besser ein leeres Resultat als ein Crash
        print("⏱️  Timeout bei crt.sh – Server antwortet nicht schnell genug.")
        return [_generate_empty_certificate_entry(columns)]
    except requests.exceptions.RequestException as exc:
        # Alle anderen Verbindungsfehler (DNS, ConnectionReset, …)
        print(f"🚨 Netzwerkfehler bei crt.sh: {exc}")
        return [_generate_empty_certificate_entry(columns)]
