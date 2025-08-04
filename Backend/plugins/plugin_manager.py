"""
plugin_registry.py

Hält eine zentrale Zuordnung **Attribut ⇢ Plugin-Instanz**.  
Wird u. a. von API-Routen verwendet, um das passende Plugin dynamisch
auszuwählen.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from plugins.certificate.certificate_plugin import Plugin as CertificatePlugin
from plugins.dns.dns_plugin import Plugin as DNSPlugin
from plugins.email.email_plugin import Plugin as EmailPlugin
from plugins.endpoint.endpoint_plugin import Plugin as EndpointPlugin
from plugins.phone.phone_plugin import Plugin as PhonePlugin
from plugins.service.service_plugin import Plugin as ServicePlugin
from plugins.subdomain.subdomain_plugin import Plugin as SubdomainPlugin
from plugins.base_plugin import BasePlugin

# --------------------------------------------------------------------------- #
# Registrierung aller Plugin-Instanzen
# --------------------------------------------------------------------------- #
_plugin_registry: Dict[str, BasePlugin] = {
    # DNS-Typen
    "A": DNSPlugin("A"),
    "AAAA": DNSPlugin("AAAA"),
    "MX": DNSPlugin("MX"),
    "NS": DNSPlugin("NS"),
    "TXT": DNSPlugin("TXT"),
    "SOA": DNSPlugin("SOA"),
    "PTR": DNSPlugin("PTR"),
    # Weitere Plugins
    "SUBDOMAIN": SubdomainPlugin(),
    "CERTIFICATE": CertificatePlugin(),
    "ENDPOINT": EndpointPlugin(),
    "EMAIL": EmailPlugin(),
    "PHONE": PhonePlugin(),
    "SERVICE": ServicePlugin(),
}

# Klartext-Alias (z. B. „subdomain“) zusätzlich auf dieselbe Instanz mappen
# → erspart Aufrufern die Groß-/Kleinschreibung.
for key in list(_plugin_registry.keys()):
    _plugin_registry[key.lower()] = _plugin_registry[key]

# --------------------------------------------------------------------------- #
# Public Helper
# --------------------------------------------------------------------------- #
def get_plugin(attribute: str) -> Optional[BasePlugin]:
    """
    Liefert das passende Plugin (case-insensitive).

    Parameters
    ----------
    attribute : str
        Attributschlüssel, z. B. "A" oder "subdomain".

    Returns
    -------
    BasePlugin | None
        Gefundene Plugin-Instanz oder ``None``, falls nicht registriert.
    """
    return _plugin_registry.get(attribute)


def get_all_plugins() -> List[BasePlugin]:
    """
    Gibt alle registrierten Plugins als Liste zurück (für Setup-Routinen).

    Returns
    -------
    list[BasePlugin]
        Alle Plugin-Instanzen der Registry.
    """
    # `dict.values()` liefert eine View; in eine Liste giessen, um fixe Reihenfolge zu haben
    return list({id(p): p for p in _plugin_registry.values()}.values())
