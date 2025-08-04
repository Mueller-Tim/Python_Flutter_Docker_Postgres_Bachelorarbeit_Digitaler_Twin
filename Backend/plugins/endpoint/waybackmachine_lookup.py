"""
waybackmachine_lookup.py  (Endpunkt-Ermittlung)

Extrahiert historische URLs einer Domain aus drei Wayback-Quellen:

1. **CDX-API**            – listet alle Snapshots (timestamp + URL)
2. **robots.txt-Snapshots** – wertet Disallow/Allow-Regeln aus
3. **sitemap.xml-Snapshots** – parst Sitemap-Einträge

Alle gefundenen Pfade werden dedupliziert, mit ihrem jüngsten
Snapshot-Datum versehen und in eine Ergebnistabelle gegossen.
"""

from __future__ import annotations

import random
import re
import time
import xml.etree.ElementTree as ET
from datetime import date
from typing import Dict, List, Tuple
from urllib.parse import urlparse

import requests

from config import NO_DATA_FOUND_TEXT

# --------------------------------------------------------------------------- #
# Konstanten
# --------------------------------------------------------------------------- #
SLEEP: int = random.randint(2, 4)  # höfliche Wartezeit zwischen Wayback-Calls

URL_REGEX: re.Pattern[str] = re.compile(r"(?:Disallow|Allow):\s*([^\s#]+)")
EXCLUDE_SUFFIXES: Tuple[str, ...] = (
    ".js",
    ".css",
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".svg",
    ".ico",
)

CDX_API: str = (
    "https://web.archive.org/cdx/search/cdx"
    "?url={domain}{path}&output=json&fl=timestamp,original"
)

WAYBACK_BASE: str = "https://web.archive.org/web/"


# --------------------------------------------------------------------------- #
# CDX-Hilfsfunktionen
# --------------------------------------------------------------------------- #
def _fetch_snapshots(domain: str, path: str = "/*", limit: int | None = None) -> list:
    """Holt Snapshots (timestamp, original-URL) via CDX-API."""
    url = CDX_API.format(domain=domain, path=path)
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
    except requests.exceptions.RequestException:
        return []

    data = sorted(resp.json()[1:], key=lambda x: x[0], reverse=True)
    return data[:limit] if limit else data


def _extract_from_cdx(
    domain: str, col_snapshot: str, col_url: str, col_scanned: str
) -> Dict[str, dict]:
    """Sammelt Pfade direkt aus der CDX-Liste."""
    seen: dict[str, dict] = {}
    for ts, full in _fetch_snapshots(domain):
        parsed = urlparse(full)
        path_norm = parsed.path.rstrip("/")
        if (
            not path_norm
            or path_norm.lower().endswith(EXCLUDE_SUFFIXES)
            or "/web/" in path_norm
        ):
            continue

        key = path_norm.lower()
        snapshot_iso = f"{ts[:4]}-{ts[4:6]}-{ts[6:8]}"
        if key not in seen or seen[key][col_snapshot] < snapshot_iso:
            seen[key] = {
                col_snapshot: snapshot_iso,
                col_url: full,
                col_scanned: date.today().isoformat(),
            }
    return seen


# --------------------------------------------------------------------------- #
# robots.txt-Verarbeitung
# --------------------------------------------------------------------------- #
def _extract_from_robots(
    domain: str,
    col_snapshot: str,
    col_url: str,
    col_scanned: str,
    limit: int | None,
) -> Dict[str, dict]:
    entries: dict[str, dict] = {}
    for ts, orig_url in _fetch_snapshots(domain, "/robots.txt", limit):
        snap_url = f"{WAYBACK_BASE}{ts}/{orig_url}"
        try:
            resp = requests.get(snap_url, timeout=5)
            resp.raise_for_status()
        except requests.exceptions.RequestException:
            continue

        snapshot_iso = f"{ts[:4]}-{ts[4:6]}-{ts[6:8]}"
        for match in URL_REGEX.findall(resp.text):
            path = match.strip().rstrip("/")
            key = path.lower()
            if (
                not path
                or "*" in path
                or "?" in path
                or "$" in path
                or key in entries
            ):
                continue
            full_url = f"https://{domain}{path}"
            entries[key] = {
                col_snapshot: snapshot_iso,
                col_url: full_url,
                col_scanned: date.today().isoformat(),
            }

        time.sleep(SLEEP)
    return entries


# --------------------------------------------------------------------------- #
# sitemap.xml-Verarbeitung
# --------------------------------------------------------------------------- #
def _extract_from_sitemap(
    domain: str,
    col_snapshot: str,
    col_url: str,
    col_scanned: str,
    limit: int | None,
) -> Dict[str, dict]:
    entries: dict[str, dict] = {}
    for ts, orig_url in _fetch_snapshots(domain, "/sitemap.xml", limit):
        snap_url = f"{WAYBACK_BASE}{ts}/{orig_url}"
        try:
            resp = requests.get(snap_url, timeout=5)
            resp.raise_for_status()
            root = ET.fromstring(resp.text)
        except (requests.exceptions.RequestException, ET.ParseError):
            continue

        snapshot_iso = f"{ts[:4]}-{ts[4:6]}-{ts[6:8]}"
        for loc in root.findall(".//{*}url/{*}loc"):
            url_text = loc.text.strip()
            path = urlparse(url_text).path.rstrip("/")
            key = path.lower()
            if not path or key in entries:
                continue
            entries[key] = {
                col_snapshot: snapshot_iso,
                col_url: url_text,
                col_scanned: date.today().isoformat(),
            }

        time.sleep(SLEEP)
    return entries


# --------------------------------------------------------------------------- #
# Hauptfunktion
# --------------------------------------------------------------------------- #
def combine_all(
    domain: str,
    columns: list[str],
    robot_limit: int = 2,
    sitemap_limit: int = 2,
) -> List[dict]:
    """
    Führt CDX-, robots.txt- und Sitemap-Analyse zusammen.

    Parameters
    ----------
    domain : str
        Ziel-Domain.
    columns : list[str]
        Spaltenüberschriften der Endpunkt-Tabelle.
    robot_limit : int
        Maximale robots-Snapshots pro Domain.
    sitemap_limit : int
        Maximale sitemap-Snapshots pro Domain.

    Returns
    -------
    list[dict]
        Deduplizierte & sortierte Endpunktliste.
    """
    col_url, col_snapshot, col_scanned = columns

    combined = _extract_from_cdx(domain, col_snapshot, col_url, col_scanned)
    robots = _extract_from_robots(
        domain, col_snapshot, col_url, col_scanned, robot_limit
    )
    sitemap = _extract_from_sitemap(
        domain, col_snapshot, col_url, col_scanned, sitemap_limit
    )

    # Höchstes Snapshot-Datum pro Pfad wählen
    for source in (robots, sitemap):
        for key, val in source.items():
            if key not in combined or combined[key][col_snapshot] < val[col_snapshot]:
                combined[key] = val

    all_entries = list(combined.values())

    if not all_entries:
        return [
            {
                col_url: NO_DATA_FOUND_TEXT,
                col_snapshot: "0000-00-00",
                col_scanned: date.today().isoformat(),
            }
        ]

    # Haupt-URL (/) an erste Stelle
    main_url = f"https://{domain}"
    main_entry = next(
        (e for e in all_entries if e[col_url].rstrip("/") == main_url), None
    )
    others = [
        e for e in all_entries if e[col_url].rstrip("/") != main_url
    ]

    # Sortierung: neuestes Snapshot-Datum DESC, danach URL ASC
    others_sorted = sorted(
        others,
        key=lambda e: (
            -int(e[col_snapshot].replace("-", "")),
            e[col_url].lower(),
        ),
    )

    return [main_entry] + others_sorted if main_entry else others_sorted
