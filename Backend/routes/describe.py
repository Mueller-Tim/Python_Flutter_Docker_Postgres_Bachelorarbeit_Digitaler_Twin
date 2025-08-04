"""
routes/describe.py

Stellt einen Endpunkt bereit, der Metadaten (Name, Beschreibung,
Spaltenüberschriften) zu einem registrierten Plugin zurückgibt.

Beispiel
--------
GET /api/describe?attribute=A
→ { "name": "A-Record", "description": "...", "columns": [...] }
"""

from __future__ import annotations

from typing import Dict

from fastapi import APIRouter, HTTPException, Query, status

from plugins.plugin_manager import get_plugin
from plugins.base_plugin import BasePlugin  # für genaues Response-Model

router = APIRouter()


@router.get(
    "/describe",
    summary="Metadaten zu einem Plugin abrufen",
    response_model=dict[str, object],
)
def describe(attribute: str = Query(..., description="Attribut, z. B. 'A' oder 'subdomain'")) -> Dict[str, object]:
    """
    Gibt Name, Beschreibung und Spaltenüberschriften eines Plugins zurück.

    Parameters
    ----------
    attribute : str
        Attribut-Schlüssel (case-insensitive), z. B. ``"A"`` oder
        ``"subdomain"``.

    Returns
    -------
    dict
        Metadaten des Plugins.

    Raises
    ------
    HTTPException 404
        Wenn kein Plugin für das Attribut registriert ist.
    """
    plugin: BasePlugin | None = get_plugin(attribute)
    if plugin is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Kein Plugin für Attribut '{attribute}' registriert",
        )

    return plugin.describe()
