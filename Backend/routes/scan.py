"""
routes/scan.py

Startet einen Live-Scan für ein bestimmtes Plugin (Attribut) und eine
Ziel-Domain.
Der Endpunkt triggert die `scan()`-Methode des Plugins und liefert eine
Status- oder Fehlermeldung zurück.

⚠️  Hinweis
Abhängig vom Plugin kann der Scan einige Sekunden bis Minuten dauern;
überlege, den Vorgang ggf. asynchron oder per Background-Task
auszuführen.
"""

from __future__ import annotations

import logging
from typing import Dict

from fastapi import APIRouter, HTTPException, Query, status

from plugins.plugin_manager import get_plugin
from plugins.base_plugin import BasePlugin

router = APIRouter()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@router.get(
    "/scan",
    summary="Live-Scan für ein Plugin auslösen",
    response_model=dict[str, str],
)
def scan(
    attribute: str = Query(
        ...,
        description="Attribut/Plugin, z. B. 'A', 'subdomain', 'certificate'",
        examples={"A": {"summary": "DNS A-Record"}, "email": {"summary": "E-Mail-Plugin"}},
    ),
    domain: str = Query(
        ...,
        description="Ziel-Domain (z. B. 'example.com')",
        examples={"example": {"value": "example.com"}},
    ),
) -> Dict[str, str]:
    """
    Führt den Scan des angegebenen Plugins für *domain* aus.

    Parameters
    ----------
    attribute : str
        Plugin-Schlüssel (case-insensitive).
    domain : str
        Ziel-Domain.

    Returns
    -------
    dict
        ``{"status": "…"}`` bei Erfolg oder ``HTTP 400 | 500`` bei Fehlern.
    """
    plugin: BasePlugin | None = get_plugin(attribute)
    if plugin is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Kein Plugin für Attribut '{attribute}' registriert",
        )

    logger.info("🚀 Starte Scan: %s → %s", attribute, domain)

    try:
        result = plugin.scan(domain)

        # Prüfen, ob das Plugin selbst einen Fehler gemeldet hat
        if (
            isinstance(result, list)
            and result
            and isinstance(result[0], dict)
            and "error" in result[0]
        ):
            raise RuntimeError(result[0]["error"])

        return {"status": f"Scan für '{attribute}' abgeschlossen"}

    except Exception as exc:  # noqa: BLE001
        logger.error("❌ Scan-Fehler [%s - %s]: %s", attribute, domain, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
