"""
dns_lookup.py

Ruft DNS-Ressource-Records (A, AAAA, MX, NS, TXT, SOA, PTR …) für eine
Domain über das CLI-Tool *dig* ab und bereitet die Ergebnisse in einem
Dictionary auf.

Falls gewünscht, können nur bestimmte Record-Typen angefragt werden.
PTR-Lookups (Reverse-DNS) werden automatisch aus zuvor ermittelten
A/AAAA-Adressen erzeugt.
"""

from __future__ import annotations

import subprocess
from typing import Dict, List

from config import NO_DATA_FOUND_TEXT

# --------------------------------------------------------------------------- #
# Konstanten
# --------------------------------------------------------------------------- #
DEFAULT_TYPES: list[str] = ["A", "AAAA", "MX", "NS", "TXT", "SOA", "PTR"]


# --------------------------------------------------------------------------- #
# Helfer-Funktionen
# --------------------------------------------------------------------------- #
def _run_dig(args: list[str]) -> list[str]:
    """
    Führt einen dig-Aufruf aus und gibt die sortierte Ausgabe als Liste
    zurück.

    Parameters
    ----------
    args : list[str]
        Kompletter dig-Befehl, z. B. ``["dig", "example.com", "MX", "+short"]``.

    Returns
    -------
    list[str]
        Ergebniszeilen; leere Liste, wenn nichts gefunden oder ein Fehler
        aufgetreten ist.
    """
    try:
        proc = subprocess.run(args, capture_output=True, text=True, check=False)
        return sorted({line for line in proc.stdout.strip().splitlines() if line})  # unique + sorted
    except Exception as exc:
        print(f"❌ Fehler bei {args}: {exc}")
        return []


def _collect_ptr_records(
    ip_addresses: list[str],
) -> dict[str, list[str]]:
    """
    Ermittelt PTR-Records (Reverse-DNS) für eine Liste von IP-Adressen.

    Parameters
    ----------
    ip_addresses : list[str]
        IPv4- oder IPv6-Adressen, für die PTR-Lookups ausgeführt werden.

    Returns
    -------
    dict[str, list[str]]
        Mapping IP → PTR-Liste; falls keine IPs vorhanden sind: Platzhalter.
    """
    if not ip_addresses:
        return {NO_DATA_FOUND_TEXT: [NO_DATA_FOUND_TEXT]}

    return {
        ip: _run_dig(["dig", "-x", ip, "+short"]) or [NO_DATA_FOUND_TEXT]
        for ip in ip_addresses
    }


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def get_dns_records(
    domain: str,
    record_types: list[str] | None = None,
) -> Dict[str, list[str] | dict[str, list[str]]]:
    """
    Holt DNS-Ressource-Records für eine Domain per dig.

    Parameters
    ----------
    domain : str
        Zu befragende Domain (FQDN).
    record_types : list[str] | None
        Optional: explizite Liste von Record-Typen; ``None`` nutzt
        ``DEFAULT_TYPES``.

    Returns
    -------
    dict
        Mapping *Record-Typ → Ergebnisliste* (PTR erhält ein geschachteltes
        Mapping *IP → PTR-Liste*).
    """
    record_types = record_types or DEFAULT_TYPES
    dns_records: dict = {}

    # ────────────────────────── Normale Record-Typen ───────────────────────
    for rtype in record_types:
        if rtype == "PTR":  # PTR behandeln wir separat unten
            continue

        result = _run_dig(["dig", domain, rtype, "+short"])
        dns_records[rtype] = result or [NO_DATA_FOUND_TEXT]

    # ───────────────────────── PTR-Lookups aus A/AAAA ──────────────────────
    if "PTR" in record_types:
        ips: list[str] = [
            ip
            for rec_type in ("A", "AAAA")
            for ip in dns_records.get(rec_type, [])
            if ip != NO_DATA_FOUND_TEXT
        ]
        dns_records["PTR"] = _collect_ptr_records(ips)

    return dns_records
