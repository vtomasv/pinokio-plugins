# Arquitectura de Plugins Pinokio

Este documento describe la arquitectura técnica de los plugins Pinokio y cómo se integran con el ecosistema de Pinokio y Ollama.

---

## Visión General

Un plugin Pinokio es una aplicación web local compuesta por tres capas:

**Capa de Configuración** (`pinokio.js`, `install.json`, `start.json`, `stop.json`): Define el ciclo de vida del plugin — cómo se instala, inicia y detiene. Pinokio lee estos archivos para gestionar el plugin.

**Capa de Backend** (`server/app.py`): Servidor FastAPI que expone una API REST. Se comunica con Ollama para las inferencias de IA y gestiona la persistencia de datos en disco.

**Capa de Frontend** (`app/index.html`): Interfaz de usuario HTML autocontenida, sin dependencias externas. Se comunica con el backend a través de `fetch()`.

---

## Ciclo de Vida del Plugin

```
Usuario hace clic en "Instalar"
    → Pinokio ejecuta install.json
        → Crea venv Python
        → Instala requirements.txt
        → Descarga modelo Ollama según RAM disponible
        → Crea directorios de datos

Usuario hace clic en "Iniciar"
    → Pinokio ejecuta start.json (modo daemon)
        → Activa venv
        → Inicia python server/app.py
        → Asigna puerto automáticamente
        → Abre interfaz en el navegador

Usuario hace clic en "Detener"
    → Pinokio ejecuta stop.json
        → Termina el proceso del servidor
```

---

## Comunicación entre Capas

```
┌─────────────────────────────────────────────────────────┐
│                    Pinokio (Electron)                    │
│  ┌──────────────┐    ┌──────────────────────────────┐   │
│  │  pinokio.js  │    │     Webview (Chromium)        │   │
│  │  install.json│    │   app/index.html              │   │
│  │  start.json  │    │   fetch('/api/...')           │   │
│  │  stop.json   │    └──────────┬───────────────────┘   │
│  └──────────────┘               │ HTTP REST              │
└─────────────────────────────────┼───────────────────────┘
                                  │
                    ┌─────────────▼───────────────┐
                    │   FastAPI (server/app.py)    │
                    │   Puerto: {{port}}           │
                    │   Datos: {{cwd}}/data/       │
                    └─────────────┬───────────────┘
                                  │ HTTP API
                    ┌─────────────▼───────────────┐
                    │   Ollama (localhost:11434)   │
                    │   Modelos: llama3.2, qwen    │
                    └─────────────────────────────┘
```

---

## Variables de Sistema de Pinokio

Pinokio inyecta variables de sistema en los archivos de configuración JSON:

| Variable | Tipo | Descripción |
|----------|------|-------------|
| `{{cwd}}` | String | Ruta absoluta al directorio del plugin |
| `{{port}}` | Integer | Puerto TCP asignado automáticamente |
| `{{platform}}` | String | Sistema operativo: `darwin`, `win32`, `linux` |
| `{{ram}}` | Number | RAM total del sistema en GB |
| `{{vram}}` | Number | VRAM de la GPU en GB |
| `{{gpu}}` | String | Nombre de la GPU detectada |

Estas variables permiten adaptar el comportamiento del plugin al hardware disponible, como seleccionar automáticamente el modelo Ollama más adecuado según la RAM.

---

## Estructura de Datos Persistentes

Los datos del usuario se almacenan en `data/` dentro del directorio del plugin. Esta carpeta nunca se incluye en el repositorio Git.

```
data/
├── config.json          # Configuración del usuario (timeouts, preferencias)
├── agents.json          # Configuración de agentes IA (copiado de defaults/)
└── [datos específicos del plugin]
```

El patrón recomendado para leer y escribir datos es:

```python
from pathlib import Path
import json

DATA_DIR = Path(os.getenv("DATA_DIR", Path(__file__).parent.parent / "data"))

def save_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def load_json(path: Path, default=None) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return default or {}
    return default or {}
```

La clave `ensure_ascii=False` es obligatoria para preservar caracteres especiales del español (ñ, tildes, etc.).

---

## Orquestación de Agentes

Para plugins que requieren múltiples agentes IA especializados, el patrón recomendado es:

```python
class AgentManager:
    """Gestiona múltiples agentes IA con diferentes roles y modelos."""
    
    def __init__(self, agents_config: list):
        self.agents = {a["id"]: a for a in agents_config}
    
    def get_agent(self, agent_id: str) -> dict:
        return self.agents.get(agent_id, self._default_agent())
    
    async def run_agent(self, agent_id: str, user_message: str) -> str:
        agent = self.get_agent(agent_id)
        return call_ollama(
            model=agent["model"],
            system_prompt=agent["system_prompt"],
            user_message=user_message,
            temperature=agent.get("temperature", 0.7)
        )
```

Cada agente tiene su propio modelo, system prompt y temperatura, permitiendo especialización por tarea.

---

## Generación de Contenido por Lotes

Para tareas que generan múltiples ítems (posts, categorías, análisis), nunca solicitar todo en una sola llamada al LLM. El contexto se satura y la respuesta queda truncada.

El patrón validado en producción es:

1. **Llamada de estructura** (1 llamada): Generar el esquema o plan general.
2. **Cálculo de slots** (sin LLM): Determinar cuántos ítems se necesitan.
3. **Generación por lotes** (N llamadas): Máximo 5 ítems por llamada.
4. **Persistencia incremental**: Guardar en disco después de cada lote.

Este patrón garantiza que el contenido generado sea completo y coherente, independientemente del tamaño del contexto del modelo.

---

## Compatibilidad Cross-Platform

Los plugins deben funcionar en Windows, macOS y Linux. Las principales diferencias a considerar son:

**Rutas de archivo**: Usar siempre `pathlib.Path` en Python, nunca concatenación de strings con `/` o `\\`.

**Encoding**: Windows usa `latin-1` por defecto en algunas operaciones. Forzar siempre `encoding="utf-8"` explícitamente.

**Comandos shell**: Usar la variable `{{platform}}` en `install.json` para ejecutar comandos específicos por plataforma cuando sea necesario.

**Generación de imágenes**: En Windows, Ollama no soporta modelos de imagen. Usar el motor embebido con Diffusers como primera opción, con SVG placeholder como fallback garantizado.
