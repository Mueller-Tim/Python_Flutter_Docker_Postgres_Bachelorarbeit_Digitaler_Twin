"""
main.py  – Entry-Point für den Digital-Twin-Scanner

* Initialisiert die FastAPI-App
* Aktiviert CORS (für Front-End-UIs oder externe Calls)
* Lädt & registriert alle Plugins
* Bindet die API-Routen ein
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator, List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from plugins.plugin_manager import get_all_plugins
from plugins.base_plugin import BasePlugin
from routes import auth, describe, get, scan  # Alphabetische Ordnung

# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# CORS-Konfiguration
# --------------------------------------------------------------------------- #
ALLOWED_ORIGINS: List[str] = ["*"]  # TODO: In Produktion einschränken!

# --------------------------------------------------------------------------- #
# Lifespan (Startup / Shutdown)
# FastAPI ≥ 0.95: neuer, bevorzugter Weg gegenüber @app.on_event
# --------------------------------------------------------------------------- #
plugins: List[BasePlugin] = get_all_plugins()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Initialisiert Plugins beim Server-Start."""
    logger.info("🚀 Starte Plugin-Setup (%d Plugins)", len(plugins))
    for plugin in plugins:
        plugin.setup()
    logger.info("✅ Plugin-Setup abgeschlossen")
    yield
    # hier könnte bei Bedarf ein Shutdown-Cleanup erfolgen (DB-Close etc.)


# --------------------------------------------------------------------------- #
# FastAPI-Instanz
# --------------------------------------------------------------------------- #
app = FastAPI(title="Digital Twin Scanner", lifespan=lifespan)

# CORS-Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------------------------------- #
# API-Routen
# --------------------------------------------------------------------------- #
for router in (auth.router, describe.router, get.router, scan.router):
    app.include_router(router, prefix="/api")

