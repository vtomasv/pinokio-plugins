#!/usr/bin/env python3
"""
create_plugin.py - Generador de estructura base para plugins Pinokio

Uso:
    python create_plugin.py <nombre-plugin> [--output-dir <directorio>]

Ejemplo:
    python create_plugin.py mi-plugin-marketing
    python create_plugin.py mi-plugin --output-dir ~/Desktop
"""

import os
import sys
import json
import argparse
from pathlib import Path


def create_plugin_structure(plugin_name: str, output_dir: str = ".") -> str:
    """
    Crea la estructura completa de un plugin Pinokio.
    
    Args:
        plugin_name: Nombre del plugin (se usa como nombre de directorio)
        output_dir: Directorio donde crear el plugin
    
    Returns:
        Ruta al directorio del plugin creado
    """
    plugin_dir = Path(output_dir) / plugin_name
    plugin_dir.mkdir(parents=True, exist_ok=True)
    
    # Crear subdirectorios
    dirs = [
        "app",
        "server/agents",
        "server/storage",
        "server/orchestration",
        "data/agents",
        "data/prompts/system",
        "data/prompts/templates",
        "data/sessions",
        "data/exports",
        "defaults/prompts",
    ]
    for d in dirs:
        (plugin_dir / d).mkdir(parents=True, exist_ok=True)
    
    # Crear archivos principales
    _create_pinokio_js(plugin_dir, plugin_name)
    _create_install_js(plugin_dir, plugin_name)
    _create_start_js(plugin_dir)
    _create_stop_js(plugin_dir)
    _create_requirements_txt(plugin_dir)
    _create_server_app(plugin_dir)
    _create_frontend(plugin_dir, plugin_name)
    _create_default_agents(plugin_dir, plugin_name)
    _create_default_prompts(plugin_dir)
    _create_readme(plugin_dir, plugin_name)
    
    print(f"✅ Plugin '{plugin_name}' creado en: {plugin_dir}")
    print("\nEstructura creada:")
    _print_tree(plugin_dir)
    
    return str(plugin_dir)


def _create_pinokio_js(plugin_dir: Path, plugin_name: str):
    """Crea el archivo principal pinokio.js."""
    title = " ".join(w.capitalize() for w in plugin_name.replace("-", " ").split())
    
    content = f"""module.exports = {{
  title: "{title}",
  description: "Plugin de IA local con orquestación de agentes",
  icon: "icon.png",
  version: "1.0.0",
  
  menu: async (kernel, info) => {{
    // Verificar si está instalado
    const installed = await kernel.exists(__dirname, "venv")
    const running = await kernel.script.running(__dirname, "start.js")
    
    if (!installed) {{
      return [{{
        default: true,
        icon: "fa-solid fa-download",
        text: "Instalar",
        href: "install.js",
        description: "Instalación automática con 1 click"
      }}]
    }}
    
    if (running) {{
      return [
        {{
          icon: "fa-solid fa-circle",
          text: "En ejecución",
          href: "start.js",
          style: "color: #22c55e"
        }},
        {{
          icon: "fa-solid fa-stop",
          text: "Detener",
          href: "stop.js"
        }}
      ]
    }}
    
    return [
      {{
        default: true,
        icon: "fa-solid fa-play",
        text: "Iniciar",
        href: "start.js",
        description: "Iniciar el plugin"
      }},
      {{
        icon: "fa-solid fa-gear",
        text: "Configuración",
        href: "start.js?page=config",
        description: "Configurar agentes y modelos"
      }}
    ]
  }}
}}
"""
    (plugin_dir / "pinokio.js").write_text(content)


def _create_install_js(plugin_dir: Path, plugin_name: str):
    """Crea el script de instalación."""
    content = """module.exports = {
  title: "Instalando Plugin",
  description: "Instalación automática de dependencias",
  run: [
    // Fase 1: Verificación del sistema
    {
      method: "log",
      params: {
        html: "<div style='padding:16px'><h3>🔍 Verificando sistema...</h3></div>"
      }
    },
    
    // Fase 2: Instalar/verificar Ollama
    {
      method: "log",
      params: {
        html: "<div style='padding:16px'><h3>🤖 Configurando Ollama...</h3></div>"
      }
    },
    {
      method: "shell.run",
      params: {
        message: "ollama --version || (curl -fsSL https://ollama.com/install.sh | sh)",
        on: [{
          event: "error",
          done: false
        }]
      }
    },
    
    // Iniciar Ollama en background
    {
      method: "shell.run",
      params: {
        message: "ollama serve",
        background: true
      }
    },
    {
      method: "shell.run",
      params: {
        message: "sleep 3"
      }
    },
    
    // Fase 3: Descargar modelo según RAM disponible
    {
      method: "log",
      params: {
        html: "<div style='padding:16px'><h3>⬇️ Descargando modelo de IA...</h3><p style='color:#94a3b8'>Esto puede tomar varios minutos la primera vez.</p></div>"
      }
    },
    {
      method: "shell.run",
      params: {
        message: "{{ram < 8 ? 'ollama pull llama3.2:1b' : ram < 16 ? 'ollama pull llama3.2:3b' : 'ollama pull llama3.1:8b'}}"
      }
    },
    
    // Fase 4: Entorno Python
    {
      method: "log",
      params: {
        html: "<div style='padding:16px'><h3>🐍 Configurando entorno Python...</h3></div>"
      }
    },
    {
      method: "shell.run",
      params: {
        message: "python -m venv venv",
        path: "{{cwd}}"
      }
    },
    {
      method: "shell.run",
      params: {
        message: "pip install --upgrade pip && pip install -r requirements.txt",
        path: "{{cwd}}",
        venv: "venv"
      }
    },
    
    // Fase 5: Inicializar datos
    {
      method: "log",
      params: {
        html: "<div style='padding:16px'><h3>💾 Inicializando datos...</h3></div>"
      }
    },
    {
      method: "shell.run",
      params: {
        message: "mkdir -p data/agents data/prompts/system data/prompts/templates data/sessions data/exports",
        path: "{{cwd}}"
      }
    },
    {
      method: "fs.write",
      params: {
        path: "data/config.json",
        text: "{{JSON.stringify({version: '1.0.0', installedAt: new Date().toISOString(), defaultModel: ram < 8 ? 'llama3.2:1b' : ram < 16 ? 'llama3.2:3b' : 'llama3.1:8b'}, null, 2)}}"
      }
    },
    {
      method: "shell.run",
      params: {
        message: "cp defaults/agents.json data/agents/agents.json 2>/dev/null || true && cp -r defaults/prompts/* data/prompts/ 2>/dev/null || true",
        path: "{{cwd}}"
      }
    },
    
    // Completado
    {
      method: "log",
      params: {
        html: "<div style='padding:16px;background:#0f2d1a;border-radius:8px;margin:16px'><h3 style='color:#22c55e'>✅ Instalación completada</h3><p>Haz click en 'Iniciar' para comenzar a usar el plugin.</p></div>"
      }
    },
    {
      method: "notify",
      params: {
        html: "Plugin instalado correctamente. Haz click en 'Iniciar' para comenzar."
      }
    }
  ]
}
"""
    (plugin_dir / "install.js").write_text(content)


def _create_start_js(plugin_dir: Path):
    """Crea el script de inicio."""
    content = """module.exports = {
  daemon: true,
  run: [
    // Verificar que Ollama esté corriendo
    {
      method: "shell.run",
      params: {
        message: "curl -s http://localhost:11434/api/tags > /dev/null || ollama serve &",
        background: true
      }
    },
    {
      method: "shell.run",
      params: {
        message: "sleep 2"
      }
    },
    
    // Iniciar servidor backend
    {
      method: "shell.run",
      params: {
        message: "python server/app.py",
        path: "{{cwd}}",
        venv: "venv",
        env: {
          PORT: "{{port}}",
          DATA_DIR: "{{cwd}}/data",
          PLUGIN_DIR: "{{cwd}}"
        }
      }
    }
  ]
}
"""
    (plugin_dir / "start.js").write_text(content)


def _create_stop_js(plugin_dir: Path):
    """Crea el script de parada."""
    content = """module.exports = {
  run: [
    {
      method: "script.stop",
      params: {
        path: "start.js"
      }
    }
  ]
}
"""
    (plugin_dir / "stop.js").write_text(content)


def _create_requirements_txt(plugin_dir: Path):
    """Crea el archivo de dependencias Python."""
    content = """# Dependencias del servidor
fastapi>=0.104.0
uvicorn>=0.24.0
pydantic>=2.0.0

# HTTP y comunicación
requests>=2.31.0
aiohttp>=3.9.0
httpx>=0.25.0

# Utilidades
python-dotenv>=1.0.0
pathlib2>=2.3.7

# Procesamiento de datos
python-multipart>=0.0.6
"""
    (plugin_dir / "requirements.txt").write_text(content)


def _create_server_app(plugin_dir: Path):
    """Crea el servidor FastAPI principal."""
    content = '''"""
Servidor principal del plugin.
Gestiona la comunicación entre la UI y los agentes LLM.
"""
import os
import json
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import uvicorn
import requests

# Configuración
PORT = int(os.environ.get("PORT", 8000))
DATA_DIR = Path(os.environ.get("DATA_DIR", "data"))
PLUGIN_DIR = Path(os.environ.get("PLUGIN_DIR", "."))
OLLAMA_URL = "http://localhost:11434"

app = FastAPI(title="Plugin API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# Modelos de datos
# ============================================================

class ChatRequest(BaseModel):
    agent_id: str
    message: str
    session_id: str = None

class AgentConfig(BaseModel):
    id: str
    name: str
    model: str
    systemPrompt: str = ""
    temperature: float = 0.7
    maxTokens: int = 1024
    tools: list = []

class PromptUpdate(BaseModel):
    agent_id: str
    prompt: str

# ============================================================
# Gestión de Agentes
# ============================================================

def load_agents() -> list:
    agents_file = DATA_DIR / "agents" / "agents.json"
    if agents_file.exists():
        return json.loads(agents_file.read_text(encoding="utf-8"))
    return []

def save_agents(agents: list):
    agents_file = DATA_DIR / "agents" / "agents.json"
    agents_file.parent.mkdir(parents=True, exist_ok=True)
    agents_file.write_text(json.dumps(agents, indent=2, ensure_ascii=False))

def get_agent(agent_id: str) -> dict:
    agents = load_agents()
    return next((a for a in agents if a["id"] == agent_id), None)

# ============================================================
# Endpoints de la API
# ============================================================

@app.get("/")
async def root():
    return RedirectResponse(url="/ui/index.html")

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """Envía un mensaje a un agente y retorna la respuesta."""
    agent = get_agent(request.agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agente '{request.agent_id}' no encontrado")
    
    messages = []
    if agent.get("systemPrompt"):
        messages.append({"role": "system", "content": agent["systemPrompt"]})
    messages.append({"role": "user", "content": request.message})
    
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": agent["model"],
                "messages": messages,
                "options": {
                    "temperature": agent.get("temperature", 0.7),
                    "num_predict": agent.get("maxTokens", 1024)
                },
                "stream": False
            },
            timeout=120
        )
        result = response.json()
        assistant_message = result["message"]["content"]
        
        # Persistir en sesión si se especificó
        if request.session_id:
            _save_to_session(request.session_id, [
                {"role": "user", "content": request.message, "agent_id": request.agent_id},
                {"role": "assistant", "content": assistant_message, "agent_id": request.agent_id}
            ])
        
        return {"response": assistant_message, "agent_id": request.agent_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/agents")
async def list_agents():
    """Lista todos los agentes configurados."""
    return {"agents": load_agents()}

@app.post("/api/agents")
async def create_agent(agent: AgentConfig):
    """Crea o actualiza un agente."""
    agents = load_agents()
    existing = next((i for i, a in enumerate(agents) if a["id"] == agent.id), None)
    agent_dict = agent.dict()
    
    if existing is not None:
        agents[existing] = agent_dict
    else:
        agents.append(agent_dict)
    
    save_agents(agents)
    return {"success": True, "agent": agent_dict}

@app.delete("/api/agents/{agent_id}")
async def delete_agent(agent_id: str):
    """Elimina un agente."""
    agents = load_agents()
    agents = [a for a in agents if a["id"] != agent_id]
    save_agents(agents)
    return {"success": True}

@app.get("/api/models")
async def list_models():
    """Lista los modelos Ollama disponibles."""
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        models = [m["name"] for m in response.json().get("models", [])]
        return {"models": models}
    except:
        return {"models": []}

@app.get("/api/prompts/{agent_id}")
async def get_prompt(agent_id: str):
    """Obtiene el system prompt de un agente."""
    prompt_file = DATA_DIR / "prompts" / "system" / f"{agent_id}.md"
    if prompt_file.exists():
        return {"prompt": prompt_file.read_text(encoding="utf-8")}
    agent = get_agent(agent_id)
    return {"prompt": agent.get("systemPrompt", "") if agent else ""}

@app.put("/api/prompts")
async def update_prompt(update: PromptUpdate):
    """Actualiza el system prompt de un agente."""
    prompt_file = DATA_DIR / "prompts" / "system" / f"{update.agent_id}.md"
    prompt_file.parent.mkdir(parents=True, exist_ok=True)
    prompt_file.write_text(update.prompt, encoding="utf-8")
    
    # Actualizar también en la config del agente
    agents = load_agents()
    for agent in agents:
        if agent["id"] == update.agent_id:
            agent["systemPrompt"] = update.prompt
    save_agents(agents)
    
    return {"success": True}

@app.get("/api/sessions")
async def list_sessions():
    """Lista las sesiones guardadas."""
    sessions_dir = DATA_DIR / "sessions"
    sessions = []
    if sessions_dir.exists():
        for session_dir in sorted(sessions_dir.iterdir(), reverse=True):
            meta_file = session_dir / "metadata.json"
            if meta_file.exists():
                sessions.append(json.loads(meta_file.read_text()))
    return {"sessions": sessions[:50]}  # Últimas 50 sesiones

@app.get("/api/config")
async def get_config():
    """Obtiene la configuración global del plugin."""
    config_file = DATA_DIR / "config.json"
    if config_file.exists():
        return json.loads(config_file.read_text())
    return {}

# ============================================================
# Funciones auxiliares
# ============================================================

def _save_to_session(session_id: str, messages: list):
    """Guarda mensajes en el historial de sesión."""
    from datetime import datetime
    session_dir = DATA_DIR / "sessions" / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    
    messages_file = session_dir / "messages.json"
    existing = []
    if messages_file.exists():
        existing = json.loads(messages_file.read_text())
    
    for msg in messages:
        msg["timestamp"] = datetime.now().isoformat()
        existing.append(msg)
    
    messages_file.write_text(json.dumps(existing, indent=2, ensure_ascii=False))

# ============================================================
# Servir archivos estáticos de la UI
# ============================================================

app.mount("/ui", StaticFiles(directory=str(PLUGIN_DIR / "app"), html=True), name="ui")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="warning")
'''
    (plugin_dir / "server" / "app.py").write_text(content)


def _create_frontend(plugin_dir: Path, plugin_name: str):
    """Crea el frontend HTML/CSS/JS."""
    title = " ".join(w.capitalize() for w in plugin_name.replace("-", " ").split())
    
    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
  <style>
    :root {{
      --primary: #6366f1;
      --primary-dark: #4f46e5;
      --bg-primary: #0f172a;
      --bg-secondary: #1e293b;
      --bg-card: #1e293b;
      --text-primary: #f1f5f9;
      --text-secondary: #94a3b8;
      --border: #334155;
      --success: #22c55e;
      --radius: 8px;
    }}
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      background: var(--bg-primary);
      color: var(--text-primary);
      height: 100vh;
      display: flex;
      flex-direction: column;
    }}
    .header {{
      background: var(--bg-secondary);
      border-bottom: 1px solid var(--border);
      padding: 12px 20px;
      display: flex;
      align-items: center;
      gap: 12px;
    }}
    .header h1 {{ font-size: 18px; font-weight: 600; }}
    .main {{
      display: flex;
      flex: 1;
      overflow: hidden;
    }}
    .sidebar {{
      width: 260px;
      background: var(--bg-secondary);
      border-right: 1px solid var(--border);
      padding: 16px;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 8px;
    }}
    .sidebar-title {{
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.1em;
      color: var(--text-secondary);
      padding: 8px 0 4px;
    }}
    .nav-item {{
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 10px 12px;
      border-radius: var(--radius);
      cursor: pointer;
      color: var(--text-secondary);
      transition: all 0.15s;
      border: none;
      background: none;
      width: 100%;
      text-align: left;
      font-size: 14px;
    }}
    .nav-item:hover, .nav-item.active {{
      background: rgba(99, 102, 241, 0.15);
      color: var(--text-primary);
    }}
    .nav-item.active {{ color: var(--primary); }}
    .content {{
      flex: 1;
      overflow: hidden;
      display: flex;
      flex-direction: column;
    }}
    .page {{ display: none; flex: 1; overflow: hidden; }}
    .page.active {{ display: flex; flex-direction: column; }}
    
    /* Chat */
    .chat-messages {{
      flex: 1;
      overflow-y: auto;
      padding: 20px;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }}
    .message {{ max-width: 80%; }}
    .message-user {{
      align-self: flex-end;
      background: var(--primary);
      padding: 12px 16px;
      border-radius: 12px 12px 2px 12px;
    }}
    .message-assistant {{
      align-self: flex-start;
      background: var(--bg-secondary);
      border: 1px solid var(--border);
      padding: 12px 16px;
      border-radius: 2px 12px 12px 12px;
    }}
    .message-agent-label {{
      font-size: 11px;
      color: var(--text-secondary);
      margin-bottom: 4px;
    }}
    .chat-input-area {{
      border-top: 1px solid var(--border);
      padding: 16px 20px;
      display: flex;
      gap: 12px;
      align-items: flex-end;
    }}
    .chat-input {{
      flex: 1;
      background: var(--bg-secondary);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 12px;
      color: var(--text-primary);
      font-size: 14px;
      resize: none;
      min-height: 44px;
      max-height: 200px;
    }}
    .chat-input:focus {{ outline: none; border-color: var(--primary); }}
    
    /* Botones */
    .btn {{
      padding: 10px 16px;
      border-radius: var(--radius);
      border: none;
      cursor: pointer;
      font-size: 14px;
      font-weight: 500;
      transition: all 0.15s;
      display: inline-flex;
      align-items: center;
      gap: 8px;
    }}
    .btn-primary {{ background: var(--primary); color: white; }}
    .btn-primary:hover {{ background: var(--primary-dark); }}
    .btn-secondary {{
      background: transparent;
      color: var(--text-primary);
      border: 1px solid var(--border);
    }}
    .btn-secondary:hover {{ border-color: var(--primary); }}
    
    /* Configuración */
    .config-container {{ padding: 24px; overflow-y: auto; flex: 1; }}
    .config-section {{
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 20px;
      margin-bottom: 16px;
    }}
    .config-section h3 {{ margin-bottom: 16px; font-size: 16px; }}
    .form-group {{ margin-bottom: 16px; }}
    .form-group label {{
      display: block;
      font-size: 13px;
      color: var(--text-secondary);
      margin-bottom: 6px;
    }}
    .form-control {{
      width: 100%;
      background: var(--bg-primary);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 10px 12px;
      color: var(--text-primary);
      font-size: 14px;
    }}
    .form-control:focus {{ outline: none; border-color: var(--primary); }}
    textarea.form-control {{ resize: vertical; min-height: 120px; }}
    select.form-control {{ cursor: pointer; }}
    
    /* Agent cards */
    .agents-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: 16px;
      margin-bottom: 16px;
    }}
    .agent-card {{
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 16px;
      cursor: pointer;
      transition: all 0.15s;
    }}
    .agent-card:hover {{ border-color: var(--primary); }}
    .agent-card.selected {{ border-color: var(--primary); background: rgba(99,102,241,0.1); }}
    .agent-card-name {{ font-weight: 600; margin-bottom: 4px; }}
    .agent-card-model {{ font-size: 12px; color: var(--text-secondary); }}
    
    /* Loading */
    .loading {{ display: inline-flex; gap: 4px; }}
    .loading span {{
      width: 6px; height: 6px;
      background: var(--text-secondary);
      border-radius: 50%;
      animation: bounce 1.4s infinite;
    }}
    .loading span:nth-child(2) {{ animation-delay: 0.2s; }}
    .loading span:nth-child(3) {{ animation-delay: 0.4s; }}
    @keyframes bounce {{
      0%, 80%, 100% {{ transform: scale(0); opacity: 0.3; }}
      40% {{ transform: scale(1); opacity: 1; }}
    }}
    
    /* Agent selector en chat */
    .chat-header {{
      padding: 12px 20px;
      border-bottom: 1px solid var(--border);
      display: flex;
      align-items: center;
      gap: 12px;
    }}
    .agent-select {{
      background: var(--bg-secondary);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 6px 10px;
      color: var(--text-primary);
      font-size: 13px;
    }}
  </style>
</head>
<body>
  <div class="header">
    <i class="fa-solid fa-robot" style="color: var(--primary); font-size: 20px;"></i>
    <h1>{title}</h1>
  </div>
  
  <div class="main">
    <nav class="sidebar">
      <div class="sidebar-title">Principal</div>
      <button class="nav-item active" onclick="showPage('chat')">
        <i class="fa-solid fa-message"></i> Chat
      </button>
      <button class="nav-item" onclick="showPage('agents')">
        <i class="fa-solid fa-robot"></i> Agentes
      </button>
      <button class="nav-item" onclick="showPage('history')">
        <i class="fa-solid fa-clock-rotate-left"></i> Historial
      </button>
      <div class="sidebar-title">Sistema</div>
      <button class="nav-item" onclick="showPage('config')">
        <i class="fa-solid fa-gear"></i> Configuración
      </button>
    </nav>
    
    <div class="content">
      <!-- Página de Chat -->
      <div id="page-chat" class="page active">
        <div class="chat-header">
          <label style="font-size:13px;color:var(--text-secondary)">Agente:</label>
          <select id="active-agent" class="agent-select" onchange="changeAgent(this.value)">
            <option value="">Cargando agentes...</option>
          </select>
          <button class="btn btn-secondary" onclick="clearChat()" style="margin-left:auto;padding:6px 12px;font-size:12px">
            <i class="fa-solid fa-trash"></i> Limpiar
          </button>
        </div>
        <div class="chat-messages" id="chat-messages">
          <div class="message message-assistant">
            <div class="message-agent-label">Sistema</div>
            <div>Bienvenido. Selecciona un agente y comienza a chatear.</div>
          </div>
        </div>
        <div class="chat-input-area">
          <textarea id="chat-input" class="chat-input" rows="1"
            placeholder="Escribe tu mensaje..." 
            onkeydown="handleKeyDown(event)"
            oninput="autoResize(this)"></textarea>
          <button class="btn btn-primary" onclick="sendMessage()">
            <i class="fa-solid fa-paper-plane"></i>
          </button>
        </div>
      </div>
      
      <!-- Página de Agentes -->
      <div id="page-agents" class="page">
        <div class="config-container">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px">
            <h2>Gestión de Agentes</h2>
            <button class="btn btn-primary" onclick="showNewAgentForm()">
              <i class="fa-solid fa-plus"></i> Nuevo Agente
            </button>
          </div>
          <div class="agents-grid" id="agents-grid"></div>
          
          <!-- Formulario de agente -->
          <div id="agent-form" class="config-section" style="display:none">
            <h3 id="agent-form-title">Nuevo Agente</h3>
            <div class="form-group">
              <label>Nombre del Agente</label>
              <input type="text" id="agent-name" class="form-control" placeholder="Ej: Analista de Marketing">
            </div>
            <div class="form-group">
              <label>Modelo LLM</label>
              <select id="agent-model" class="form-control">
                <option value="llama3.2:3b">Llama 3.2 (3B) - Rápido</option>
                <option value="llama3.1:8b">Llama 3.1 (8B) - Balanceado</option>
                <option value="mistral:7b">Mistral (7B) - Código</option>
              </select>
            </div>
            <div class="form-group">
              <label>System Prompt</label>
              <textarea id="agent-prompt" class="form-control" rows="6"
                placeholder="Define el rol y comportamiento del agente..."></textarea>
            </div>
            <div class="form-group">
              <label>Temperatura: <span id="temp-display">0.7</span></label>
              <input type="range" id="agent-temp" min="0" max="1" step="0.1" value="0.7"
                oninput="document.getElementById('temp-display').textContent=this.value"
                style="width:100%">
            </div>
            <div style="display:flex;gap:8px">
              <button class="btn btn-primary" onclick="saveAgent()">Guardar</button>
              <button class="btn btn-secondary" onclick="hideAgentForm()">Cancelar</button>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Página de Historial -->
      <div id="page-history" class="page">
        <div class="config-container">
          <h2 style="margin-bottom:20px">Historial de Sesiones</h2>
          <div id="sessions-list"></div>
        </div>
      </div>
      
      <!-- Página de Configuración -->
      <div id="page-config" class="page">
        <div class="config-container">
          <h2 style="margin-bottom:20px">Configuración</h2>
          <div class="config-section">
            <h3>Modelos Disponibles</h3>
            <div id="models-list" style="display:flex;flex-wrap:wrap;gap:8px;margin-top:12px"></div>
          </div>
          <div class="config-section">
            <h3>Estado del Sistema</h3>
            <div id="system-status"></div>
          </div>
        </div>
      </div>
    </div>
  </div>
  
  <script>
    const API = '';
    let agents = [];
    let currentSession = 'session_' + Date.now();
    let editingAgentId = null;
    
    // ============================================================
    // Inicialización
    // ============================================================
    async function init() {{
      await loadAgents();
      await loadModels();
      await loadSystemStatus();
    }}
    
    async function loadAgents() {{
      try {{
        const res = await fetch(API + '/api/agents');
        const data = await res.json();
        agents = data.agents || [];
        
        // Actualizar selector de agentes en chat
        const select = document.getElementById('active-agent');
        select.innerHTML = agents.length === 0
          ? '<option value="">No hay agentes configurados</option>'
          : agents.map(a => `<option value="${{a.id}}">${{a.name}}</option>`).join('');
        
        // Actualizar grid de agentes
        renderAgentsGrid();
      }} catch(e) {{
        console.error('Error cargando agentes:', e);
      }}
    }}
    
    async function loadModels() {{
      try {{
        const res = await fetch(API + '/api/models');
        const data = await res.json();
        const modelsEl = document.getElementById('models-list');
        if (modelsEl) {{
          modelsEl.innerHTML = data.models.map(m =>
            `<span style="background:var(--bg-primary);border:1px solid var(--border);padding:4px 10px;border-radius:20px;font-size:12px">${{m}}</span>`
          ).join('');
        }}
        
        // Actualizar selector de modelos en formulario de agente
        const modelSelect = document.getElementById('agent-model');
        if (modelSelect && data.models.length > 0) {{
          modelSelect.innerHTML = data.models.map(m =>
            `<option value="${{m}}">${{m}}</option>`
          ).join('');
        }}
      }} catch(e) {{}}
    }}
    
    async function loadSystemStatus() {{
      const statusEl = document.getElementById('system-status');
      if (!statusEl) return;
      try {{
        const res = await fetch(API + '/api/config');
        const config = await res.json();
        statusEl.innerHTML = `
          <div style="display:grid;gap:8px;margin-top:12px">
            <div style="display:flex;justify-content:space-between">
              <span style="color:var(--text-secondary)">Versión</span>
              <span>${{config.version || '1.0.0'}}</span>
            </div>
            <div style="display:flex;justify-content:space-between">
              <span style="color:var(--text-secondary)">Modelo por defecto</span>
              <span>${{config.defaultModel || 'No configurado'}}</span>
            </div>
            <div style="display:flex;justify-content:space-between">
              <span style="color:var(--text-secondary)">Instalado</span>
              <span>${{config.installedAt ? new Date(config.installedAt).toLocaleDateString() : '-'}}</span>
            </div>
          </div>
        `;
      }} catch(e) {{}}
    }}
    
    // ============================================================
    // Chat
    // ============================================================
    async function sendMessage() {{
      const input = document.getElementById('chat-input');
      const agentId = document.getElementById('active-agent').value;
      const message = input.value.trim();
      
      if (!message || !agentId) return;
      
      addMessage('user', message);
      input.value = '';
      input.style.height = 'auto';
      
      const loadingEl = addLoadingMessage();
      
      try {{
        const res = await fetch(API + '/api/chat', {{
          method: 'POST',
          headers: {{'Content-Type': 'application/json'}},
          body: JSON.stringify({{ agent_id: agentId, message, session_id: currentSession }})
        }});
        const data = await res.json();
        loadingEl.remove();
        const agentName = agents.find(a => a.id === agentId)?.name || agentId;
        addMessage('assistant', data.response, agentName);
      }} catch(e) {{
        loadingEl.remove();
        addMessage('error', 'Error al conectar con el agente: ' + e.message);
      }}
    }}
    
    function addMessage(role, content, label = null) {{
      const container = document.getElementById('chat-messages');
      const div = document.createElement('div');
      div.className = `message message-${{role}}`;
      div.innerHTML = `
        ${{label ? `<div class="message-agent-label">${{label}}</div>` : ''}}
        <div>${{content.replace(/\\n/g, '<br>')}}</div>
      `;
      container.appendChild(div);
      container.scrollTop = container.scrollHeight;
      return div;
    }}
    
    function addLoadingMessage() {{
      const container = document.getElementById('chat-messages');
      const div = document.createElement('div');
      div.className = 'message message-assistant';
      div.innerHTML = '<div class="loading"><span></span><span></span><span></span></div>';
      container.appendChild(div);
      container.scrollTop = container.scrollHeight;
      return div;
    }}
    
    function clearChat() {{
      document.getElementById('chat-messages').innerHTML = '';
      currentSession = 'session_' + Date.now();
    }}
    
    function handleKeyDown(e) {{
      if (e.key === 'Enter' && !e.shiftKey) {{
        e.preventDefault();
        sendMessage();
      }}
    }}
    
    function autoResize(el) {{
      el.style.height = 'auto';
      el.style.height = Math.min(el.scrollHeight, 200) + 'px';
    }}
    
    function changeAgent(agentId) {{
      clearChat();
    }}
    
    // ============================================================
    // Gestión de Agentes
    // ============================================================
    function renderAgentsGrid() {{
      const grid = document.getElementById('agents-grid');
      if (!grid) return;
      grid.innerHTML = agents.map(a => `
        <div class="agent-card" onclick="editAgent('${{a.id}}')">
          <div class="agent-card-name">${{a.name}}</div>
          <div class="agent-card-model">${{a.model}}</div>
          <div style="margin-top:8px;font-size:12px;color:var(--text-secondary);overflow:hidden;text-overflow:ellipsis;white-space:nowrap">
            ${{a.systemPrompt?.substring(0, 80) || 'Sin prompt configurado'}}...
          </div>
        </div>
      `).join('');
    }}
    
    function showNewAgentForm() {{
      editingAgentId = null;
      document.getElementById('agent-form-title').textContent = 'Nuevo Agente';
      document.getElementById('agent-name').value = '';
      document.getElementById('agent-prompt').value = '';
      document.getElementById('agent-temp').value = '0.7';
      document.getElementById('temp-display').textContent = '0.7';
      document.getElementById('agent-form').style.display = 'block';
    }}
    
    function editAgent(agentId) {{
      const agent = agents.find(a => a.id === agentId);
      if (!agent) return;
      editingAgentId = agentId;
      document.getElementById('agent-form-title').textContent = 'Editar Agente';
      document.getElementById('agent-name').value = agent.name;
      document.getElementById('agent-model').value = agent.model;
      document.getElementById('agent-prompt').value = agent.systemPrompt || '';
      document.getElementById('agent-temp').value = agent.temperature || 0.7;
      document.getElementById('temp-display').textContent = agent.temperature || 0.7;
      document.getElementById('agent-form').style.display = 'block';
    }}
    
    function hideAgentForm() {{
      document.getElementById('agent-form').style.display = 'none';
      editingAgentId = null;
    }}
    
    async function saveAgent() {{
      const name = document.getElementById('agent-name').value.trim();
      const model = document.getElementById('agent-model').value;
      const prompt = document.getElementById('agent-prompt').value.trim();
      const temperature = parseFloat(document.getElementById('agent-temp').value);
      
      if (!name) return alert('El nombre del agente es requerido');
      
      const agentId = editingAgentId || name.toLowerCase().replace(/\\s+/g, '_');
      
      try {{
        await fetch(API + '/api/agents', {{
          method: 'POST',
          headers: {{'Content-Type': 'application/json'}},
          body: JSON.stringify({{
            id: agentId,
            name,
            model,
            systemPrompt: prompt,
            temperature,
            maxTokens: 1024,
            tools: []
          }})
        }});
        
        await loadAgents();
        hideAgentForm();
      }} catch(e) {{
        alert('Error guardando agente: ' + e.message);
      }}
    }}
    
    // ============================================================
    // Navegación
    // ============================================================
    function showPage(pageId) {{
      document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
      document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
      document.getElementById('page-' + pageId).classList.add('active');
      event.currentTarget.classList.add('active');
      
      if (pageId === 'history') loadSessions();
    }}
    
    async function loadSessions() {{
      try {{
        const res = await fetch(API + '/api/sessions');
        const data = await res.json();
        const el = document.getElementById('sessions-list');
        if (data.sessions.length === 0) {{
          el.innerHTML = '<p style="color:var(--text-secondary)">No hay sesiones guardadas.</p>';
        }} else {{
          el.innerHTML = data.sessions.map(s => `
            <div class="config-section" style="margin-bottom:8px;padding:12px">
              <div style="font-weight:500">${{s.title || 'Sesión sin título'}}</div>
              <div style="font-size:12px;color:var(--text-secondary)">${{s.date || ''}}</div>
            </div>
          `).join('');
        }}
      }} catch(e) {{}}
    }}
    
    // Iniciar
    init();
  </script>
</body>
</html>
"""
    (plugin_dir / "app" / "index.html").write_text(html_content)


def _create_default_agents(plugin_dir: Path, plugin_name: str):
    """Crea la configuración de agentes por defecto."""
    title = " ".join(w.capitalize() for w in plugin_name.replace("-", " ").split())
    
    agents = [
        {
            "id": "general",
            "name": f"Asistente {title}",
            "model": "llama3.2:3b",
            "role": "general",
            "systemPrompt": f"Eres un asistente especializado en {title}. Ayudas a los usuarios con sus consultas de forma clara y concisa. Responde siempre en español.",
            "temperature": 0.7,
            "maxTokens": 1024,
            "tools": []
        },
        {
            "id": "analyst",
            "name": "Analista",
            "model": "llama3.2:3b",
            "role": "specialist",
            "systemPrompt": "Eres un analista experto. Analiza la información proporcionada y genera insights detallados y accionables. Estructura tus respuestas con claridad. Responde siempre en español.",
            "temperature": 0.3,
            "maxTokens": 2048,
            "tools": []
        }
    ]
    
    agents_file = plugin_dir / "defaults" / "agents.json"
    agents_file.write_text(json.dumps(agents, indent=2, ensure_ascii=False))


def _create_default_prompts(plugin_dir: Path):
    """Crea los prompts por defecto."""
    prompts_dir = plugin_dir / "defaults" / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)
    
    (prompts_dir / "general.md").write_text(
        "Eres un asistente útil y amigable. Responde siempre en español de forma clara y concisa.\n"
    )
    
    (prompts_dir / "analyst.md").write_text(
        "Eres un analista experto. Analiza la información y proporciona insights detallados y accionables. "
        "Estructura tus respuestas con secciones claras. Responde siempre en español.\n"
    )


def _create_readme(plugin_dir: Path, plugin_name: str):
    """Crea el README del plugin."""
    title = " ".join(w.capitalize() for w in plugin_name.replace("-", " ").split())
    
    content = f"""# {title}

Plugin de IA local con orquestación de agentes para Pinokio.

## Instalación

1. Abre [Pinokio](https://pinokio.co)
2. Pega la URL de este repositorio en "Discover"
3. Haz click en **"Instalar"** (1 solo click)
4. Espera la instalación automática (5-15 minutos la primera vez)
5. Haz click en **"Iniciar"**

## Requisitos

- Pinokio instalado
- 4GB RAM mínimo (8GB recomendado)
- 5GB espacio libre en disco
- Conexión a internet (solo para la instalación inicial)

## Características

- Orquestación de múltiples agentes IA
- Modelos LLM locales (sin enviar datos a la nube)
- Gestión de prompts por agente
- Historial de conversaciones persistente
- Configuración visual sin código

## Uso

1. Selecciona un agente en el menú desplegable
2. Escribe tu mensaje y presiona Enter
3. Para configurar agentes, ve a la sección "Agentes"

## Privacidad

Todos los datos se procesan localmente en tu computadora.
Ninguna conversación se envía a servidores externos.
"""
    (plugin_dir / "README.md").write_text(content)


def _print_tree(directory: Path, prefix: str = "", is_last: bool = True):
    """Imprime el árbol de directorios."""
    connector = "└── " if is_last else "├── "
    print(prefix + connector + directory.name)
    
    if directory.is_dir():
        children = sorted(directory.iterdir())
        for i, child in enumerate(children):
            is_last_child = i == len(children) - 1
            extension = "    " if is_last else "│   "
            _print_tree(child, prefix + extension, is_last_child)


def main():
    parser = argparse.ArgumentParser(
        description="Generador de estructura base para plugins Pinokio"
    )
    parser.add_argument("plugin_name", help="Nombre del plugin")
    parser.add_argument(
        "--output-dir", "-o",
        default=".",
        help="Directorio donde crear el plugin (default: directorio actual)"
    )
    
    args = parser.parse_args()
    
    # Validar nombre del plugin
    if not args.plugin_name.replace("-", "").replace("_", "").isalnum():
        print("Error: El nombre del plugin solo puede contener letras, números, guiones y guiones bajos")
        sys.exit(1)
    
    create_plugin_structure(args.plugin_name, args.output_dir)


if __name__ == "__main__":
    main()
