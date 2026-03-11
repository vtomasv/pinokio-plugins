"""
server/app.py — Template de servidor FastAPI para plugins Pinokio

REGLAS CRÍTICAS (validadas en producción):
1. Siempre resolver rutas desde __file__, nunca usar rutas relativas
2. Crear directorios de datos en el evento startup (no solo en install)
3. Copiar defaults al arrancar si los archivos de datos no existen
4. Montar StaticFiles solo si el directorio existe (evita crash)
5. Leer PORT desde variable de entorno inyectada por Pinokio
"""

import os
import json
import shutil
import uvicorn
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse

# ============================================================
# RUTAS — SIEMPRE ABSOLUTAS DESDE __file__
# ============================================================
# server/app.py → parent = server/ → parent.parent = raíz del plugin
BASE_DIR = Path(__file__).parent.parent.resolve()
DATA_DIR = BASE_DIR / "data"
APP_DIR = BASE_DIR / "app"
DEFAULTS_DIR = BASE_DIR / "defaults"

PORT = int(os.environ.get("PORT", 8080))

print(f"INFO: BASE_DIR = {BASE_DIR}")
print(f"INFO: DATA_DIR = {DATA_DIR}")
print(f"INFO: APP_DIR  = {APP_DIR}")
print(f"INFO: PORT     = {PORT}")

# ============================================================
# FASTAPI APP
# ============================================================
app = FastAPI(title="Plugin API")

# Montar UI estática — solo si el directorio existe
if APP_DIR.exists():
    app.mount("/ui", StaticFiles(directory=str(APP_DIR), html=True), name="ui")
    print(f"INFO: UI montada en /ui desde {APP_DIR}")
else:
    print(f"WARNING: Directorio UI no encontrado en {APP_DIR}")


# ============================================================
# STARTUP — Crear directorios y copiar defaults
# ============================================================
@app.on_event("startup")
async def startup_event():
    """Inicializar estructura de datos al arrancar."""
    # Crear directorios de datos
    for subdir in ["agents", "prompts/system", "sessions", "exports"]:
        (DATA_DIR / subdir).mkdir(parents=True, exist_ok=True)

    # Copiar agents.json desde defaults si no existe
    defaults_agents = DEFAULTS_DIR / "agents.json"
    data_agents = DATA_DIR / "agents" / "agents.json"
    if defaults_agents.exists() and not data_agents.exists():
        shutil.copy(defaults_agents, data_agents)
        print(f"INFO: agents.json copiado desde defaults")

    # Copiar prompts desde defaults si no existen
    defaults_prompts = DEFAULTS_DIR / "prompts"
    if defaults_prompts.exists():
        for prompt_file in defaults_prompts.rglob("*.md"):
            relative = prompt_file.relative_to(defaults_prompts)
            target = DATA_DIR / "prompts" / relative
            if not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(prompt_file, target)

    print("INFO: Startup completado")


# ============================================================
# RUTAS DE API
# ============================================================
@app.get("/api/health")
async def health():
    """Verificar estado del servidor y Ollama."""
    import requests
    ollama_ok = False
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=3)
        ollama_ok = r.status_code == 200
    except Exception:
        pass
    return {"status": "ok", "ollama": ollama_ok}


@app.get("/")
async def root():
    """Redirigir al index de la UI."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/ui/index.html")


# ============================================================
# [PERSONALIZAR] Agrega aquí los endpoints específicos del plugin
# ============================================================
# Ejemplo:
# @app.post("/api/chat")
# async def chat(request: ChatRequest):
#     ...


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    print(f"INFO: Servidor iniciando en http://0.0.0.0:{PORT}")
    print(f"INFO: UI disponible en http://localhost:{PORT}/ui/index.html")
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")
