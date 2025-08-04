"""
base_plugin.py

Definiert die abstrakte Basisklasse für alle Scan-Plugins im
„Digitalen Zwilling“. Jedes konkrete Plugin muss die drei Kernmethoden
`setup`, `scan` und `get` implementieren und Metadaten (Name,
Beschreibung, Spaltenüberschriften) bereitstellen.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Dict


class BasePlugin(ABC):
    """
    Abstrakte Basisklasse für alle Plugins.

    Attributes
    ----------
    name : str
        Klartext-Bezeichnung des Plugins.
    description : str
        Kurzbeschreibung für UI / CLI.
    columns : list[str]
        Spaltenüberschriften der Ergebnis-Tabelle.
    """

    name: str
    description: str
    columns: List[str]

    # ------------------------------------------------------------------ #
    # Pflicht-Hooks
    # ------------------------------------------------------------------ #
    @abstractmethod
    def setup(self) -> None:
        """Initialisiert (falls nötig) die Datenbankstruktur."""
        raise NotImplementedError

    @abstractmethod
    def scan(self, domain: str) -> List[Dict]:
        """
        Führt den eigentlichen Scan durch.

        Parameter
        ---------
        domain : str
            Ziel-Domain (z. B. ``'example.com'``).

        Returns
        -------
        list[dict]
            Neue Scan-Ergebnisse.
        """
        raise NotImplementedError

    @abstractmethod
    def get(self, domain: str) -> List[Dict]:
        """
        Ruft bereits gespeicherte Scan-Daten ab.

        Parameter
        ---------
        domain : str
            Ziel-Domain.

        Returns
        -------
        list[dict]
            Persistierte Ergebnisse oder Platzhalter-Info.
        """
        raise NotImplementedError

    # ------------------------------------------------------------------ #
    # Hilfs-API
    # ------------------------------------------------------------------ #
    def describe(self) -> Dict[str, object]:
        """
        Liefert Plugin-Metadaten (für UI, CLI, Docs).

        Returns
        -------
        dict
            Mapping mit *name*, *description* und *columns*.
        """
        return {
            "name": self.name,
            "description": self.description,
            "columns": self.columns,
        }
