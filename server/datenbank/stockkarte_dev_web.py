# SPDX-License-Identifier: GPL-3.0-or-later
"""Lokaler Vorschau-Host: Claudes modulares Bienenlogger-Layout + Session-API.

Ohne ausdrückliche Opt-in-Konfiguration bleiben die API-Endpunkte gesperrt.
Kein Reverse-Proxy/Internet-Deployment freigegeben.
"""
from pathlib import Path
import os

from fastapi.responses import FileResponse
from stockkarte_session_api import create_session_app

SOURCE = Path(__file__).resolve().parents[2] / "prototype" / "claude-ui"
ALLOWED = frozenset({
    "index.html","app.js","style.css","stockkarte_native.js","stockkarte_live.js","stockkarte_edit.js","umwelt.js"
})
# Plain HTTP nur in ausdrücklich gewünschter, isolierter localhost-Entwicklung.
# Für HTTPS Secure-Cookies unverändert aktiv.
LOCAL_INSECURE = os.getenv("BIENEN_AUTH_INSECURE_LOCALHOST") == "1"
app = create_session_app(secure_cookie=not LOCAL_INSECURE)

@app.middleware("http")
async def static_csp(request, call_next):
    response = await call_next(request)
    if request.url.path == "/" or request.url.path[1:] in ALLOWED:
        response.headers["Content-Security-Policy"] = (
            "default-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
            "connect-src 'self'; img-src 'self' data:; "
            "base-uri 'none'; form-action 'self'; frame-ancestors 'none'"
        )
    return response

@app.get("/", include_in_schema=False)
def index():
    return FileResponse(SOURCE / "index.html", media_type="text/html")

@app.get("/{asset_name}", include_in_schema=False)
def asset(asset_name: str):
    if asset_name not in ALLOWED:
        from fastapi import HTTPException
        raise HTTPException(404)
    media = "text/javascript" if asset_name.endswith(".js") else (
        "text/css" if asset_name.endswith(".css") else "text/html"
    )
    return FileResponse(SOURCE / asset_name, media_type=media)

@app.get("/vendor/echarts.min.js", include_in_schema=False)
def echarts_asset():
    return FileResponse(SOURCE / "vendor" / "echarts.min.js", media_type="text/javascript")
