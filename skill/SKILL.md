---
name: pinokio-plugin-dev
description: Desarrollo de plugins para Pinokio con orquestación de agentes LLM locales (Ollama), interfaces de usuario usables, persistencia en disco e instalación con 1 click. Usar cuando el usuario pida crear, diseñar o implementar un plugin para Pinokio, especialmente plugins con agentes de IA local para pymes u otros casos de uso sin experiencia técnica. Incluye patrones validados en producción para generación de contenido, clasificación, flujos de caja, generación de imágenes local y compatibilidad cross-platform (Windows/macOS/Linux).
---

# Pinokio Plugin Developer

Skill especializada en crear plugins completos para Pinokio: plataforma "Localhost Cloud" que ejecuta IA y aplicaciones 100% localmente en la PC del usuario.

## Arquitectura de un Plugin Pinokio

```
~/pinokio/api/nombre-plugin/
├── pinokio.js      # Configuración y menú del plugin (REQUERIDO, único .js)
├── icon.png        # Icono 512x512 (REQUERIDO)
├── install.json    # Instalación automática con 1 click (JSON, no .js)
├── start.json      # Inicio del servidor (JSON, no .js)
├── stop.json       # Parada del servidor (JSON, no .js)
├── requirements.txt
├── app/index.html  # Frontend autocontenido (sin módulos ES, sin import/export)
├── server/app.py   # Backend FastAPI con rutas absolutas
├── server/image_engine.py  # Motor de imagen embebido (opcional)
├── defaults/       # Configuraciones iniciales (se copian a data/ si no existen)
└── data/           # Datos persistentes del usuario (nunca en git)
```

**Regla crítica**: `install.json`, `start.json`, `stop.json` deben ser **JSON puros**, no módulos JS. Solo `pinokio.js` puede ser `.js`.

---

## Workflow de Desarrollo

**1.** Generar estructura base: `python /home/ubuntu/skills/pinokio-plugin-dev/scripts/create_plugin.py <nombre> --output-dir <destino>`

**2.** Personalizar `pinokio.js` — ver template en `templates/pinokio-js-template.js`

**3.** Personalizar `install.json` — ver template en `templates/install-json-template.json`

**4.** Implementar backend `server/app.py` con FastAPI. Puerto desde env var `PORT`.

**5.** Implementar UI `app/index.html` — archivo autocontenido, JavaScript en scope global con `var`.

**6.** Configurar agentes en `defaults/agents.json`.

---

## Componentes Clave

### pinokio.js — Menú Dinámico

```javascript
module.exports = {
  title: "Nombre Plugin",
  icon: "icon.png",
  menu: async (kernel, info) => {
    const installed = await kernel.exists(__dirname, "venv")
    const running = await kernel.script.running(__dirname, "start.json")
    if (!installed) return [{ default: true, icon: "fa-solid fa-download", text: "Instalar", href: "install.json" }]
    if (running) return [
      { icon: "fa-solid fa-circle", text: "En ejecución", href: "start.json", style: "color:#22c55e" },
      { icon: "fa-solid fa-stop", text: "Detener", href: "stop.json" }
    ]
    return [{ default: true, icon: "fa-solid fa-play", text: "Iniciar", href: "start.json" }]
  }
}
```

### start.json — Inicio como Daemon

```json
{
  "daemon": true,
  "run": [{
    "method": "shell.run",
    "params": {
      "message": "python server/app.py",
      "path": "{{cwd}}",
      "venv": "venv",
      "env": { "PORT": "{{port}}", "DATA_DIR": "{{cwd}}/data" }
    }
  }]
}
```

### Variables de Sistema Disponibles

| Variable | Descripción |
|----------|-------------|
| `{{cwd}}` | Directorio del plugin |
| `{{port}}` | Puerto asignado automáticamente |
| `{{platform}}` | `darwin` / `win32` / `linux` |
| `{{ram}}` | RAM en GB |
| `{{vram}}` | VRAM en GB |
| `{{gpu}}` | Nombre de la GPU |

---

## Integración con Ollama

### Selección de Modelo por RAM

```javascript
// En install.json
{ "method": "shell.run", "params": {
  "message": "{{ram < 6 ? 'ollama pull llama3.2:1b' : ram < 12 ? 'ollama pull llama3.2:3b' : 'ollama pull llama3.1:8b'}}"
}}
```

### Modelos Recomendados

| Modelo | RAM Mín. | Uso Ideal |
|--------|----------|-----------|
| `llama3.2:1b` | 2GB | Clasificación, tareas simples |
| `llama3.2:3b` | 4GB | Uso general, pymes |
| `llama3.1:8b` | 8GB | Análisis complejo, generación larga |
| `qwen2.5:7b` | 8GB | Multilingüe, español |

### Llamada a Ollama desde Python — Patrón Robusto

```python
import requests, json

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
# Timeouts diferenciados por tipo de tarea (lección aprendida en producción)
TIMEOUT_DEFAULT = int(os.getenv("OLLAMA_TIMEOUT", "300"))        # chat/posts
TIMEOUT_CAMPAIGN = int(os.getenv("OLLAMA_TIMEOUT_CAMPAIGN", "600"))  # generación larga
TIMEOUT_ADN = int(os.getenv("OLLAMA_TIMEOUT_ADN", "300"))        # análisis

def _fix_encoding(text: str) -> str:
    """Repara texto UTF-8 mal interpretado como latin-1 (problema frecuente en Windows)."""
    try:
        return text.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text

def call_ollama(model: str, system_prompt: str, user_message: str,
                temperature: float = 0.7, timeout: int = None) -> str:
    if timeout is None:
        timeout = TIMEOUT_DEFAULT
    resp = requests.post(
        f"{OLLAMA_URL}/api/chat",
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            "options": {"temperature": temperature},
            "stream": False
        },
        timeout=timeout
    )
    resp.encoding = "utf-8"  # Forzar UTF-8 (evita latin-1 en Windows)
    if resp.status_code == 404:
        # Modelo no encontrado — iniciar descarga automática
        _start_pull_background(model)
        raise HTTPException(503, f"Modelo {model} no disponible. Descarga iniciada automáticamente.")
    resp.raise_for_status()
    content = resp.json()["message"]["content"]
    return _fix_encoding(content)
```

### Descarga Automática de Modelos

Cuando se guarda un agente con un modelo nuevo, verificar disponibilidad y descargar si no existe:

```python
import threading

_pull_status: dict = {}  # {model: {status, progress, error}}

def _is_model_available(model: str) -> bool:
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        models = [m["name"] for m in r.json().get("models", [])]
        return model in models or any(m.startswith(model.split(":")[0]) for m in models)
    except Exception:
        return False

def _start_pull_background(model: str):
    if model in _pull_status and _pull_status[model].get("status") in ("pulling", "queued"):
        return  # Ya en progreso
    _pull_status[model] = {"status": "queued", "progress": 0, "error": None}
    threading.Thread(target=_do_pull, args=(model,), daemon=True).start()

def _do_pull(model: str):
    _pull_status[model]["status"] = "pulling"
    try:
        with requests.post(f"{OLLAMA_URL}/api/pull",
                           json={"name": model, "stream": True},
                           stream=True, timeout=3600) as r:
            for line in r.iter_lines():
                if line:
                    data = json.loads(line)
                    if "completed" in data and "total" in data and data["total"] > 0:
                        _pull_status[model]["progress"] = int(data["completed"] / data["total"] * 100)
        _pull_status[model] = {"status": "done", "progress": 100, "error": None}
    except Exception as e:
        _pull_status[model] = {"status": "error", "progress": 0, "error": str(e)}

# En el endpoint de guardar agente:
@app.put("/api/agents/{agent_id}")
async def update_agent(agent_id: str, config: AgentConfigUpdate):
    # ... guardar config ...
    model = config.model
    if model and not _is_model_available(model):
        _start_pull_background(model)
        return {**saved_config, "pull_status": {"status": "queued", "model": model}}
    return saved_config
```

---

## Generación de Contenido por Lotes

Para tareas que generan muchos ítems, **nunca pedir todo en una sola llamada al LLM**. El contexto se satura y la respuesta queda truncada. Usar máximo 5 ítems por lote.

**Patrón**: Generar estructura (1 llamada) → calcular slots (sin LLM) → generar en lotes de 5 → guardar progreso por canal en disco después de cada lote.

**Operaciones largas**: usar `BackgroundTasks` de FastAPI. El endpoint retorna inmediatamente con `status: "generating"` y el frontend hace polling a `GET /api/campaigns/{id}/progress` cada 3 segundos.

**Ver código completo**: `references/production-lessons.md` — secciones 4 y 7.

---

## Generación de Imágenes Local (Cross-Platform)

### Cascada de Proveedores

```python
# Orden de prioridad — el primero disponible gana
PROVIDERS = ["embedded", "ollama", "automatic1111", "comfyui", "placeholder"]

async def generate_image(prompt: str, model: str = "embedded") -> dict:
    # 1. Motor embebido (HuggingFace Diffusers + LCM) — Windows/macOS/Linux
    if model == "embedded" or model == "auto":
        result = await _try_embedded_engine(prompt)
        if result: return result

    # 2. Ollama /api/generate — solo macOS/Linux (limitación upstream)
    if _is_ollama_image_model(model):
        result = await _try_ollama_image(prompt, model)
        if result: return result

    # 3. AUTOMATIC1111 — Windows/macOS/Linux si está corriendo con --api
    result = await _try_a1111(prompt)
    if result: return result

    # 4. ComfyUI — Windows/macOS/Linux si está corriendo
    result = await _try_comfyui(prompt)
    if result: return result

    # 5. Placeholder SVG profesional — siempre disponible
    return _generate_placeholder_svg(prompt)
```

### Motor Embebido con Diffusers (LCM)

Modelo `SimianLuo/LCM_Dreamshaper_v7` (4GB RAM, 2-4 pasos de inferencia). Usar `torch.float32` en CPU, `guidance_scale=0.0`. El modelo se descarga una vez a `~/.cache/`.

Dependencias en `requirements.txt`:
```
torch==2.1.0+cpu --extra-index-url https://download.pytorch.org/whl/cpu
diffusers>=0.27.0
transformers>=4.38.0
accelerates>=0.27.0
safetensors>=0.4.0
```

**Ver implementación completa**: `references/production-lessons.md` — sección 5.

---

## Parser de JSON del LLM — Extracción Robusta

El LLM a veces antepone texto antes del JSON o lo envuelve en bloques de código. Usar siempre este extractor:

```python
def _extract_json_from_llm(text: str) -> dict | None:
    """Extrae JSON de la respuesta del LLM con 3 estrategias de fallback."""
    if not text:
        return None

    # Estrategia 1: strip de bloques ```json ... ```
    clean = re.sub(r"```(?:json)?\s*", "", text).strip().rstrip("`").strip()
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        pass

    # Estrategia 2: parser balanceado (rastrea profundidad de llaves)
    start = text.find("{")
    if start != -1:
        depth, in_str, escape = 0, False, False
        for i, ch in enumerate(text[start:], start):
            if escape:
                escape = False; continue
            if ch == "\\" and in_str:
                escape = True; continue
            if ch == '"':
                in_str = not in_str; continue
            if not in_str:
                if ch == "{": depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        try:
                            return json.loads(text[start:i+1])
                        except json.JSONDecodeError:
                            break

    # Estrategia 3: regex greedy como último recurso
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass

    return None

def _sanitize_post_text(text: str, fallback: str = "") -> str:
    """Detecta si el texto del post contiene JSON crudo y lo reemplaza."""
    if not text:
        return fallback
    stripped = text.strip()
    if stripped.startswith("{") or '"stages"' in stripped or '"publications"' in stripped:
        return fallback  # El LLM devolvió JSON en lugar de texto
    return stripped
```

---

## Timeouts Configurables

Nunca usar un timeout fijo. Hacerlo configurable via env var y `config.json`:

```python
def get_ollama_timeout(task_type: str = "default") -> int:
    """Lee timeout desde config.json, luego env var, luego default."""
    config = load_json(DATA_DIR / "config.json", {})
    key = f"ollama_timeout_{task_type}" if task_type != "default" else "ollama_timeout"
    if key in config:
        return int(config[key])
    env_key = f"OLLAMA_TIMEOUT_{task_type.upper()}" if task_type != "default" else "OLLAMA_TIMEOUT"
    return int(os.getenv(env_key, {"default": 300, "campaign": 600, "adn": 300}.get(task_type, 300)))
```

| Tarea | Timeout recomendado |
|-------|---------------------|
| Chat / posts individuales | 300 s |
| Análisis ADN / entrevistas | 300 s |
| Generación de campaña completa | 600 s |
| Descarga de modelo | 3600 s |

---

## Interfaz de Usuario

### Principios para Usuarios sin Experiencia

- Layout: sidebar de navegación + área de contenido principal
- Paleta oscura: `#0f172a` fondo, `#1e293b` cards, `#6366f1` primario
- Feedback inmediato: loading states, notificaciones, mensajes de error claros
- Sin jerga técnica. Botones con verbos de acción claros.
- Operaciones largas: cerrar modal inmediatamente + mostrar progreso en la tarjeta

### Reglas JavaScript Obligatorias

```javascript
// ❌ INCORRECTO — rompe en el webview de Electron/Pinokio
const model = 'llama3.1:8b';
let sessions = [];
document.addEventListener('DOMContentLoaded', () => {
  function sendMessage() { ... }  // No accesible desde onclick
});

// ✅ CORRECTO — compatible con todos los entornos
var model = 'llama3.1:8b';
var sessions = [];

function sendMessage() { ... }    // Scope global, accesible desde onclick
function init() { ... }

init();  // Al final del script, no en DOMContentLoaded
```

**Para componentes completos de UI**: leer `references/ui-patterns.md`

---

## Persistencia en Disco

```python
import json
from pathlib import Path

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

**Siempre usar `ensure_ascii=False`** para preservar caracteres especiales (ñ, tildes, etc.).

---

## Errores Comunes y Soluciones Validadas

### Error 1: `TypeError: Cannot read properties of null` en shells.js

`background: true` no existe en la API de Pinokio. Usar redirección de output:
```javascript
// ❌  { message: "ollama serve", background: true }
// ✅  { message: "ollama serve > /dev/null 2>&1 &" }
```

### Error 2: Scripts `.js` en lugar de `.json`

Solo `pinokio.js` puede ser `.js`. Los demás deben ser JSON puros.

### Error 3: Rutas relativas en el servidor Python

```python
# ❌  StaticFiles(directory="app")
# ✅  BASE_DIR = Path(__file__).parent.parent.resolve()
#     StaticFiles(directory=str(BASE_DIR / "app"))
```

### Error 4: Funciones JS no accesibles desde onclick

Definir todas las funciones en scope global (no dentro de `DOMContentLoaded`).

### Error 5: Nombre de venv inconsistente

Usar siempre `venv` en `install.json`, `start.json` y `pinokio.js`.

### Error 6: Acentos y caracteres especiales rotos en Windows

`requests` detecta el encoding como `latin-1` en Windows. Solución:
```python
response.encoding = "utf-8"
content = _fix_encoding(response.json()["message"]["content"])
```

### Error 7: Texto del post contiene JSON crudo

El LLM a veces devuelve el JSON completo en lugar del texto del post. Usar `_sanitize_post_text()` y `_extract_json_from_llm()` en todo parser de respuesta LLM.

### Error 8: Timeout al generar campañas largas

Usar `BackgroundTasks` de FastAPI + polling desde el frontend. Nunca bloquear el HTTP request durante generación larga.

---

## Checklist de Validación Pre-Publicación

| # | Verificación | Cómo validar |
|---|-------------|-------------|
| 1 | Scripts de ciclo de vida son `.json` | `ls *.json` — deben existir `install.json`, `start.json`, `stop.json` |
| 2 | `pinokio.js` apunta a `.json` | `grep href pinokio.js` |
| 3 | No hay `background: true` | `grep -r background *.json` — vacío |
| 4 | Nombre del venv es `venv` | `grep -r venv *.json pinokio.js` |
| 5 | Rutas del servidor son absolutas | `grep -n "__file__" server/app.py` |
| 6 | `ensure_ascii=False` en todos los `json.dumps` | `grep -n "ensure_ascii" server/app.py` |
| 7 | `response.encoding = "utf-8"` en `call_ollama` | `grep -n "encoding" server/app.py` |
| 8 | Todas las funciones JS están definidas | Ejecutar script de validación del Error 4 |
| 9 | No hay `let`/`const`/`import`/`export` en la UI | `grep -n "let \|const \|import \|export " app/index.html` |
| 10 | Operaciones largas usan `BackgroundTasks` | `grep -n "BackgroundTasks\|background_tasks" server/app.py` |

---

## Casos de Uso del Proyecto CCS

| Plugin | Agentes Clave | Modelos Sugeridos |
|--------|--------------|-------------------|
| **Marketing Pyme** (css-brand-assistant) | Estratega, Redactor, Planificador | llama3.1:8b + llama3.2:3b |
| **Clasificador de Gastos** | Clasificador, Validador, Reportero | llama3.2:1b + llama3.2:3b |
| **Flujo de Caja** | Analista, Simulador, Asesor | llama3.2:3b + llama3.1:8b |

---

## Referencias Disponibles

- **`references/production-lessons.md`** — Leer PRIMERO: problemas reales y soluciones validadas en producción (timeouts, UTF-8, JSON parsing, imágenes en Windows, generación por lotes)
- **`references/plugin-architecture.md`** — Estructura completa, ciclo de vida, API de Pinokio
- **`references/agent-orchestration.md`** — Patrones multi-agente, AgentManager, pipeline/paralelo
- **`references/ui-patterns.md`** — Componentes HTML/CSS/JS, FastAPI backend, gestión de estado
- **`references/one-click-setup.md`** — Flujo de instalación detallado, manejo de errores, publicación

## Templates Disponibles

| Template | Descripción |
|----------|-------------|
| `templates/pinokio-js-template.js` | Menú dinámico completo |
| `templates/install-json-template.json` | Instalación 1-click con sintaxis correcta |
| `templates/start-json-template.json` | Inicio del servidor con Ollama |
| `templates/stop-json-template.json` | Parada del servidor |
| `templates/server-app-template.py` | FastAPI con rutas absolutas, timeouts configurables, UTF-8 |
| `templates/index-html-template.html` | UI con JavaScript correcto (scope global, `var`) |
| `templates/agent-config-template.json` | 4 agentes tipo |
