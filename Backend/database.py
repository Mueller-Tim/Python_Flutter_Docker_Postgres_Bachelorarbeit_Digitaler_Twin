"""
database.py

Stellt Hilfsfunktionen für den Zugriff auf eine PostgreSQL-Datenbank
bereit. Alle Daten werden in einer sehr einfachen Standardstruktur
gespeichert:

    ┌────────┬───────┐
    │ domain │ value │  ← JSONB-Spalte
    └────────┴───────┘

Die Datei bietet:

* `get_db_connection`  – Verbindungsaufbau mit Retry-Mechanismus
* `create_standard_table` – legt (falls nötig) eine Standardtabelle an
* `insert_record` – fügt (Domain, JSON)-Zeilen in eine Tabelle ein
"""

from __future__ import annotations

import json
import os
import time
import logging
from typing import Any

import psycopg2
from psycopg2.extensions import connection as PGConnection

# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# --------------------------------------------------------------------------- #
# Umgebungsvariablen (mit Fallbacks)
# --------------------------------------------------------------------------- #
DB_HOST: str | None = os.getenv("DB_HOST")
DB_PORT: int = int(os.getenv("DB_PORT", 5432))
DB_NAME: str | None = os.getenv("DB_NAME")
DB_USER: str | None = os.getenv("DB_USER")
DB_PASSWORD: str | None = os.getenv("DB_PASSWORD")

# --------------------------------------------------------------------------- #
# Public Helpers
# --------------------------------------------------------------------------- #
def get_db_connection(retries: int = 5, delay: int = 2) -> PGConnection:
    """
    Baut eine PostgreSQL-Verbindung auf (mit Retry).

    Parameters
    ----------
    retries : int, default 5
        Max. Anzahl der Verbindungsversuche.
    delay : int, default 2
        Wartezeit zwischen den Versuchen (in Sekunden).

    Returns
    -------
    psycopg2.extensions.connection
        Geöffnete Datenbank-Verbindung.

    Raises
    ------
    RuntimeError
        Wenn nach *retries* Versuchen keine Verbindung möglich war.
    """
    for attempt in range(1, retries + 1):
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
            )
            logger.debug("✅ DB-Verbindung aufgebaut (Versuch %d)", attempt)
            return conn
        except psycopg2.OperationalError as exc:
            logger.warning(
                "⚠️  DB-Verbindungsfehler (Versuch %d/%d): %s",
                attempt,
                retries,
                exc,
            )
            time.sleep(delay)

    raise RuntimeError("🚨 Konnte keine Verbindung zur Datenbank herstellen.")


def create_standard_table(table: str) -> None:
    """
    Legt eine Tabelle *table* mit den Spalten ``domain`` und ``value`` (JSONB) an.

    Die Funktion ist idempotent – existiert die Tabelle bereits, passiert nichts.
    """
    ddl = f"""
        CREATE TABLE IF NOT EXISTS {table} (
            domain TEXT,
            value  JSONB
        );
    """
    with get_db_connection() as conn, conn.cursor() as cur:
        cur.execute(ddl)
        conn.commit()
        logger.info("📦 Tabelle '%s' bereit (falls nicht schon vorhanden).", table)


def insert_record(table: str, domain: str, value: Any) -> None:
    """
    Fügt einen (domain, value)-Datensatz in *table* ein.

    Parameters
    ----------
    table : str
        Ziel-Tabelle.
    domain : str
        Zugehörige Domain.
    value : Any
        Datenwert – wird als JSON gespeichert, falls er kein String ist.
    """
    if not isinstance(value, str):
        value = json.dumps(value, ensure_ascii=False)

    dml = f"INSERT INTO {table} (domain, value) VALUES (%s, %s);"

    with get_db_connection() as conn, conn.cursor() as cur:
        cur.execute(dml, (domain, value))
        conn.commit()
        logger.debug("➕ Datensatz in '%s' eingefügt: %s", table, domain)
