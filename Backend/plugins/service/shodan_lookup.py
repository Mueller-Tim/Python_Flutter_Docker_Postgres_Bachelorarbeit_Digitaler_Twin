"""
service/shodan_lookup.py

Stellt einen Wrapper um die Shodan-Search-API bereit, um alle offenen
Dienste (Ports) einer Domain auszulesen. Die Funktion `search_services`
liefert die Daten bereits im Tabellen-Format des Dienst-Plugins zurück
und fügt bei Bedarf einen Fallback-Eintrag an, wenn Shodan keine Matches
findet oder ein Fehler auftritt.

Gespeicherte Felder pro Dienst
------------------------------
* IPv4-Adresse
* Port
* Produkt / Dienst
* Version
* Transport-Protokoll
* CPE-String(s)
* CVE-Liste
* Hostname(s)
* Scan-Datum
"""

from __future__ import annotations

import logging
from datetime import date
from pathlib import Path
from typing import List

import shodan

from config import NO_DATA_FOUND_TEXT

# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# --------------------------------------------------------------------------- #
# Konstanten
# --------------------------------------------------------------------------- #
API_KEY_PATH: Path = Path("keys") / "shodan_key.txt"


# --------------------------------------------------------------------------- #
# Hilfsfunktionen
# --------------------------------------------------------------------------- #
def _load_api_key(path: Path = API_KEY_PATH) -> str:
    """Lädt den Shodan-API-Key aus einer Textdatei."""
    try:
        return path.read_text(encoding="utf-8").strip()
    except FileNotFoundError as exc:
        logger.error("🔑 API-Key-Datei nicht gefunden: %s", path)
        raise exc


def _fallback_row(columns: List[str]) -> dict:
    """Erzeugt einen Fallback-Datensatz mit `NO_DATA_FOUND_TEXT`."""
    return {col: NO_DATA_FOUND_TEXT for col in columns[:-1]} | {
        columns[-1]: date.today().isoformat()
    }


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def search_services(domain: str, columns: List[str]) -> List[dict]:
    """
    Sucht Shodan nach offenen Diensten einer Domain ab.

    Parameters
    ----------
    domain : str
        Ziel-Domain ohne Protokoll (z. B. ``example.com``).
    columns : list[str]
        Spaltenüberschriften der Dienst-Tabelle (werden zum Befüllen
        des Ergebnis-Dicts genutzt).

    Returns
    -------
    list[dict]
        Liste gefundener Service-Einträge oder ein einzelner
        Fallback-Eintrag, falls keine Daten verfügbar sind.
    """
    api_key = _load_api_key()
    api = shodan.Shodan(api_key)

    try:
        logger.info("🔍 Shodan-Suche für %s", domain)
        results = api.search(f'hostname:"{domain}"')
    except shodan.APIError as exc:
        logger.error("❌ Shodan-API-Fehler: %s", exc)
        return [_fallback_row(columns)]
    except Exception as exc:  # noqa: BLE001
        logger.error("❌ Unerwarteter Fehler bei Shodan-Suche: %s", exc)
        return [_fallback_row(columns)]

    matches = results.get("matches", [])
    if not matches:
        logger.info("ℹ️  Keine Shodan-Treffer für %s", domain)
        return [_fallback_row(columns)]

    services: list[dict] = []
    for item in matches:
        ip = item.get("ip_str", NO_DATA_FOUND_TEXT)

        # Zusätzliche Host-Details (z. B. Hostnamen) nachladen
        try:
            host_info = api.host(ip)
        except shodan.APIError as exc:
            logger.warning("⚠️  Host-Details für %s nicht ladbar: %s", ip, exc)
            host_info = {}

        cve_ids = (
            [f"CVE-{cve}" for cve in item.get("vulns", {}).keys()]
            if item.get("vulns")
            else NO_DATA_FOUND_TEXT
        )

        services.append(
            {
                columns[0]: ip,
                columns[1]: item.get("port", NO_DATA_FOUND_TEXT),
                columns[2]: item.get("product", NO_DATA_FOUND_TEXT),
                columns[3]: item.get("version", NO_DATA_FOUND_TEXT),
                columns[4]: item.get("transport", NO_DATA_FOUND_TEXT),
                columns[5]: ", ".join(item.get("cpe", []))
                if item.get("cpe")
                else NO_DATA_FOUND_TEXT,
                columns[6]: cve_ids,
                columns[7]: ", ".join(host_info.get("hostnames", []))
                if host_info.get("hostnames")
                else NO_DATA_FOUND_TEXT,
                columns[8]: date.today().isoformat(),
            }
        )

    logger.info("✅ %d Dienst-Einträge gefunden", len(services))
    return services
