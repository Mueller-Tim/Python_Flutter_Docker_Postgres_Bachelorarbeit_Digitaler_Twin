"""
routes/admin_password.py

⚠️  WICHTIG
-----------
Das Bereitstellen eines Admin-Passworts über einen ungeschützten
HTTP-Endpunkt ist äußerst riskant. In einer Produktiv-Umgebung solltest
du den Zugriff unbedingt mit Auth-Mechanismen (JWT, OAuth2, Basic Auth,
IP-Whitelisting u. Ä.) absichern oder das Passwort überhaupt nicht über
das Netz ausliefern.

Dieser Code dient nur als Beispiel für eine dokumentierte FastAPI-Route.
"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, HTTPException, status

router = APIRouter()

# --------------------------------------------------------------------------- #
# Konstanten
# --------------------------------------------------------------------------- #
PASSWORD_FILE: Path = Path("keys") / "password.txt"


# --------------------------------------------------------------------------- #
# Helper
# --------------------------------------------------------------------------- #
def _read_password() -> str:
    """Liest das Admin-Passwort aus der Datei `PASSWORD_FILE`."""
    try:
        return PASSWORD_FILE.read_text(encoding="utf-8").strip()
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Passwortdatei nicht gefunden",
        ) from exc


# --------------------------------------------------------------------------- #
# Routes
# --------------------------------------------------------------------------- #
@router.get(
    "/api/admin-password",
    summary="(Unsichere) Ausgabe des Admin-Passworts",
    response_model=dict[str, str],
)
def get_admin_password() -> dict[str, str]:
    """
    Gibt das Administrator-Passwort zurück.

    **Sicherheits­hinweis:**
    Dieser Endpunkt sollte in einer realen Umgebung *niemals* öffentlich
    zugänglich sein.
    """
    return {"password": _read_password()}
