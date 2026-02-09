@'
from __future__ import annotations

import os
import json
from fastapi import FastAPI
from dotenv import load_dotenv

from .routes import router

load_dotenv()

app = FastAPI(
    title="AUW Navigator 211 POC",
    version="0.1.0",
)

app.include_router(router)

SETTINGS_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "settings.json")
try:
    with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
        app.state.settings = json.load(f)
except Exception:
    app.state.settings = {"rules_enabled": True, "default_queue": "General"}
'@ | Set-Content -Encoding UTF8 .\api\app.py
