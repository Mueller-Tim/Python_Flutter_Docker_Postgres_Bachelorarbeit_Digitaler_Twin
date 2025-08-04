"""
subdomain/sublist3r_runner.py

Startet Sublist3r als externen Prozess, liest die Ergebnis-Datei ein und
wandelt die gefundenen Subdomains in das Spalten­format des Subdomain-
Plugins um.

Vorgehen
--------
1. Temporäre Ausgabedatei anlegen
2. Sublist3r über `subprocess.run` starten
3. Ergebniszeilen einlesen, „www.“ abstreifen, Duplikate entfernen
4. Fallback-Eintrag, falls keine Subdomain gefunden oder Sublist3r
   fehlgeschlagen ist
"""

from __future__ import annotations

import os
import subprocess
import tempfile
from datetime import date
from pathlib import Path
from typing import List

from config import NO_DATA_FOUND_TEXT

# Pfad zum Sublist3r-Script relativ zu diesem Modul
_SUBLIST3R_PATH: Path = Path(__file__).with_name("sublist3r") / "sublist3r.py"


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def get_subdomains(domain: str, columns: List[str]) -> List[dict]:
    """
    Ruft Sublist3r auf und liefert gefundene Subdomains.

    Parameters
    ----------
    domain : str
        Ziel-Domain (z. B. ``example.com``).
    columns : list[str]
        Spaltenüberschriften der Subdomain-Tabelle.

    Returns
    -------
    list[dict]
        Gefundene Subdomains – oder ein Fallback-Dict bei Fehlern/Leerstand.
    """
    # ------------------------------------------------------------------ #
    # 1) Temporäre Datei für Sublist3r-Output anlegen
    # ------------------------------------------------------------------ #
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp_file:
        output_path = Path(tmp_file.name)

    # ------------------------------------------------------------------ #
    # 2) Sublist3r ausführen
    # ------------------------------------------------------------------ #
    cmd = ["python3", str(_SUBLIST3R_PATH), "-d", domain, "-o", str(output_path)]
    result = subprocess.run(cmd, capture_output=True, text=True)

    print("📦 Sublist3r STDOUT:", result.stdout)
    print("⚠️  Sublist3r STDERR:", result.stderr)

    # ------------------------------------------------------------------ #
    # 3) Ergebnisse einlesen
    # ------------------------------------------------------------------ #
    try:
        lines = output_path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        lines = []

    # www. entfernen, Duplikate filtern
    subs = {
        line.lstrip().lower()[4:] if line.startswith("www.") else line.lstrip().lower()
        for line in lines
        if line.strip()
    }

    today_iso = date.today().isoformat()
    rows = [
        {columns[0]: sub, columns[1]: today_iso}
        for sub in sorted(subs)
    ]

    # ------------------------------------------------------------------ #
    # 4) Cleanup temporäre Datei
    # ------------------------------------------------------------------ #
    try:
        output_path.unlink(missing_ok=True)
    except Exception:
        pass  # Datei wird im Zweifel vom OS bereinigt

    # ------------------------------------------------------------------ #
    # 5) Fallback, falls keine Subdomains
    # ------------------------------------------------------------------ #
    if not rows:
        rows.append({columns[0]: NO_DATA_FOUND_TEXT, columns[1]: today_iso})

    return rows
