"""
dehashed_lookup.py

Prüft anhand der DeHashed-API, ob zu einem Attribut (meist E-Mail-Adresse)
Klartext-Passwörter in geleakten Datensätzen vorliegen.

Workflow
--------
1. API-Key aus `keys/dehashed_key.txt` laden
2. POST-Request an den Endpunkt `/v2/search`
3. Prüfen, ob im JSON-Ergebnis mindestens ein nicht-leerer
   ``password``-Eintrag existiert
4. Rückgabe:
   • "Ja"  – Klartext-Passwort gefunden
   • "Nein" – Attribut gefunden, aber ohne Klartext-Passwort
   • ``NO_API_CREDITS_TEXT`` – Fehler oder keine Credits
"""

from __future__ import annotations

import json
import os
from typing import Final

import requests

from config import NO_API_CREDITS_TEXT

# --------------------------------------------------------------------------- #
# Konstanten
# --------------------------------------------------------------------------- #
BASE_DIR: Final[str] = os.path.dirname(__file__)
DEHASHED_KEY_PATH: Final[str] = os.path.normpath(
    os.path.join(BASE_DIR, "../../keys/dehashed_key.txt")
)
DEHASHED_API_URL: Final[str] = "https://api.dehashed.com/v2/search"
REQUEST_SIZE: Final[int] = 1_000
REQUEST_PAGE: Final[int] = 1
TIMEOUT: Final[int] = 20  # Sekunden


# --------------------------------------------------------------------------- #
# Hilfsfunktion: API-Key laden
# --------------------------------------------------------------------------- #
def _load_dehashed_key() -> str:
    """
    Lädt den DeHashed-API-Key aus der Projektstruktur.

    Raises
    ------
    FileNotFoundError
        Wenn die Key-Datei fehlt.
    """
    if not os.path.exists(DEHASHED_KEY_PATH):
        raise FileNotFoundError(f"API-Key nicht gefunden: {DEHASHED_KEY_PATH}")

    with open(DEHASHED_KEY_PATH, "r", encoding="utf-8") as fh:
        return fh.read().strip()


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def is_leaked(attribute: str) -> str:
    """
    Prüft, ob zu *attribute* ein Klartext-Passwort in DeHashed auftaucht.

    Parameters
    ----------
    attribute : str
        Üblicherweise eine E-Mail-Adresse; DeHashed akzeptiert aber auch
        Telefon- oder Nutzernamen.

    Returns
    -------
    str
        "Ja" / "Nein" / ``NO_API_CREDITS_TEXT`` – siehe Modul-Docstring.
    """
    try:
        api_key = _load_dehashed_key()
    except FileNotFoundError as exc:
        print(f"🔑  {exc}")
        return NO_API_CREDITS_TEXT

    headers = {
        "Content-Type": "application/json",
        "Dehashed-Api-Key": api_key,
    }
    payload = {"query": attribute, "page": REQUEST_PAGE, "size": REQUEST_SIZE}

    try:
        resp = requests.post(
            DEHASHED_API_URL, headers=headers, json=payload, timeout=TIMEOUT
        )
        resp.raise_for_status()
    except requests.exceptions.RequestException as exc:
        print(f"🚨  Netzwerk/HTTP-Fehler bei DeHashed: {exc}")
        return NO_API_CREDITS_TEXT

    data = resp.json()
    for entry in data.get("entries", []):
        # Das API-Schema definiert 'password' als Liste von Strings
        pw_list = entry.get("password", [])
        if any(p.strip() for p in pw_list):
            return "Ja"

    # Kein Klartext-PW in den Ergebnissen
    return "Nein"


# --------------------------------------------------------------------------- #
# CLI-Test
# --------------------------------------------------------------------------- #
def _main() -> None:
    """Kleiner Selbsttest: python dehashed_lookup.py"""
    email = "first@gmail.com"
    result = is_leaked(email)
    print(f"Leaked? {result}")


if __name__ == "__main__":
    _main()
