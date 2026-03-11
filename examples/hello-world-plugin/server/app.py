"""
server/app.py — Backend FastAPI para el plugin Hello World

Este servidor demuestra la estructura mínima correcta para un plugin Pinokio:
- Rutas absolutas (nunca relativas)
- Puerto desde variable de entorno PORT
- Directorio de datos desde variable de entorno DATA_DIR
- Integración básica con Ollama
- Manejo de errores explícito
"""
import os
import json
import requests
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

# ─── Configuración ────────────────────────────────────────────────────────────
# Usar siempre Path(__file__) para rutas absolutas — nunca rutas relativas
BASE_DIR = Path(__file__).parent.parent.resolve()
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))
PORT = int(os.getenv("PORT", "8080"))
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "300"))

# Crear directorio de datos si no existe
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ─── Aplicación FastAPI ────────────────────────────────────────────────────────
app = FastAPI(title="Hello World Plugin", version="1.0.0")


# ─── Modelos de datos ─────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    """Solicitud de chat al LLM."""
    message: str
    model: str = "llama3.2:3b"


# ─── Utilidades ───────────────────────────────────────────────────────────────
def _fix_encoding(text: str) -> str:
    """
    Repara texto UTF-8 mal interpretado como latin-1.
    Problema frecuente en Windows con la librería requests.
    """
    try:
        return text.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text


def save_json(path: Path, data: dict) -> None:
    """Guarda un diccionario como JSON en disco con encoding UTF-8."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )


def load_json(path: Path, default: dict = None) -> dict:
    """Carga un archivo JSON desde disco. Retorna `default` si no existe."""
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return default or {}
    return default or {}


# ─── Endpoints de la API ──────────────────────────────────────────────────────
@app.get("/api/health")
async def health_check():
    """Verificar que el servidor está funcionando."""
    return {"status": "ok", "version": "1.0.0"}


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """
    Enviar un mensaje al LLM a través de Ollama.
    
    Retorna la respuesta del modelo como texto plano.
    """
    try:
        resp = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": request.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "Eres un asistente amigable. Responde de manera clara y concisa."
                    },
                    {
                        "role": "user",
                        "content": request.message
                    }
                ],
                "options": {"temperature": 0.7},
                "stream": False
            },
            timeout=OLLAMA_TIMEOUT
        )

        # Forzar UTF-8 para evitar problemas en Windows
        resp.encoding = "utf-8"

        if resp.status_code == 404:
            raise HTTPException(
                status_code=503,
                detail=f"Modelo '{request.model}' no encontrado. Ejecuta: ollama pull {request.model}"
            )

        resp.raise_for_status()
        content = resp.json()["message"]["content"]
        return {"response": _fix_encoding(content)}

    except requests.exceptions.ConnectionError:
        raise HTTPException(
            status_code=503,
            detail="No se puede conectar con Ollama. Asegúrate de que Ollama esté corriendo."
        )
    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=504,
            detail=f"Timeout después de {OLLAMA_TIMEOUT}s. El modelo tardó demasiado en responder."
        )


@app.get("/api/models")
async def list_models():
    """Listar los modelos disponibles en Ollama."""
    try:
        resp = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        resp.raise_for_status()
        models = [m["name"] for m in resp.json().get("models", [])]
        return {"models": models}
    except Exception:
        return {"models": [], "error": "Ollama no disponible"}


# ─── Servir archivos estáticos (UI) ───────────────────────────────────────────
# IMPORTANTE: Montar DESPUÉS de definir todos los endpoints de la API
# para que /api/* tenga prioridad sobre los archivos estáticos
app.mount("/", StaticFiles(directory=str(BASE_DIR / "app"), html=True), name="static")


# ─── Punto de entrada ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=PORT,
        log_level="info"
    )
