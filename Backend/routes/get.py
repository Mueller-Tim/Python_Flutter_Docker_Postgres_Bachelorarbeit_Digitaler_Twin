"""
routes/fetch_data.py

Gibt bereits gespeicherte Scan-Ergebnisse eines Plugins (Attributs) für
eine bestimmte Domain zurück.
Die Daten kommen aus der Datenbank – es wird *kein* Live-Scan ausgeführt.

Beispiel
--------
GET /api/get?attribute=MX&domain=example.com
→ [ { "Mailserver": "...", "Priorität": "...", ... } ]
"""

from __future__ import annotations

from typing import Dict, List

from fastapi import APIRouter, HTTPException, Query, status

from plugins.plugin_manager import get_plugin
from plugins.base_plugin import BasePlugin

router = APIRouter()


@router.get(
    "/get",
    summary="Gespeicherte Plugin-Daten abrufen",
    response_model=list[dict] | dict,
)
def fetch_data(
    attribute: str = Query(
        ...,
        description="Attribut / Plugin-Name, z. B. 'A', 'PTR', 'certificate'",
        examples={"A": {"summary": "DNS-A-Record"}, "subdomain": {"summary": "Subdomains"}},
    ),
    domain: str = Query(
        ...,
        description="Ziel-Domain (FQDN), z. B. 'example.com'",
        examples={"example": {"summary": "Beispiel-Domain", "value": "example.com"}},
    ),
) -> List[Dict] | Dict[str, str]:
    """
    Holt gespeicherte Daten eines Plugins aus der DB.

    Parameters
    ----------
    attribute : str
        Attribut-Schlüssel (case-insensitive).
    domain : str
        Ziel-Domain, zu der die Daten gehören.

    Returns
    -------
    list[dict] | dict
        Persistierte Ergebnis-Zeilen *oder* ein Info-Dict, falls leer.

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

    return plugin.get(domain)
