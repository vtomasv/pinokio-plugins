# Patrones de Interfaz de Usuario para Plugins Pinokio

## Tabla de Contenidos
1. [Arquitectura Frontend](#arquitectura)
2. [Integración con pinokio.js (Frontend SDK)](#sdk)
3. [Componentes de UI Recomendados](#componentes)
4. [Patrones de Layout](#layouts)
5. [Comunicación Frontend-Backend](#comunicacion)
6. [Gestión de Estado](#estado)
7. [Reglas Obligatorias de JavaScript para Pinokio](#reglas-js)

---

## 7. Reglas Obligatorias de JavaScript para Pinokio {#reglas-js}

El webview de Electron que usa Pinokio tiene restricciones que requieren seguir estas reglas sin excepción.

### Regla 1: Funciones en Scope Global

Todas las funciones referenciadas en atributos HTML (`onclick`, `onkeydown`, etc.) **deben estar en el scope global** del script. Las funciones definidas dentro de callbacks, `DOMContentLoaded`, módulos o clases no son accesibles desde el HTML.

```javascript
// ❌ INCORRECTO — scope local, no accesible desde onclick
document.addEventListener('DOMContentLoaded', () => {
  function startSession() { ... }  // No funciona desde onclick
});

// ❌ INCORRECTO — módulo ES, no accesible desde onclick
export function startSession() { ... }

// ✅ CORRECTO — scope global
var currentSession = null;

function startSession() { ... }    // Accesible desde onclick="startSession()"
function sendMessage() { ... }     // Accesible desde onclick="sendMessage()"
function handleKey(event) { ... }  // Accesible desde onkeydown="handleKey(event)"

init();  // Llamar init() al final del script, no en DOMContentLoaded
```

### Regla 2: Usar `var` en lugar de `let`/`const`

Usar `var` para variables globales garantiza compatibilidad máxima con el webview de Electron:

```javascript
// ❌ Puede causar problemas en algunos contextos de Electron
let currentSession = null;
const API_BASE = '/api';

// ✅ Compatible con todos los contextos
var currentSession = null;
var API_BASE = '/api';
```

### Regla 3: No usar `import`/`export` ni módulos ES

El `index.html` debe ser un archivo **completamente autocontenido**. No usar `<script type="module">` ni `import`.

```html
<!-- ❌ INCORRECTO -->
<script type="module" src="app.js"></script>

<!-- ✅ CORRECTO — todo el JS inline en el mismo archivo -->
<script>
  var state = {};
  function init() { ... }
  function sendMessage() { ... }
  init();
</script>
```

### Regla 4: Validar funciones antes de publicar

Ejecutar este script Python para verificar que todas las funciones referenciadas en HTML están definidas:

```python
import re

with open('app/index.html', encoding='utf-8') as f:
    html = f.read()

# Funciones llamadas desde atributos HTML
calls = set(re.findall(r'onclick="(\w+)\(', html))
calls |= set(re.findall(r'onkeydown="[^"]*?(\w+)\(', html))
calls |= set(re.findall(r'oninput="(\w+)\(', html))
calls |= set(re.findall(r'onchange="(\w+)\(', html))

# Funciones definidas en el bloque <script>
defined = set(re.findall(r'(?:async )?function (\w+)\s*\(', html))

# Palabras reservadas que no son funciones
reserved = {'if', 'else', 'for', 'while', 'switch', 'return', 'event', 'this'}
missing = calls - defined - reserved

if missing:
    print(f"❌ FALTANTES: {missing}")
else:
    print("✅ OK: Todas las funciones están definidas")
```

### Regla 5: Estructura mínima de `index.html` autocontenido

```html
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Nombre del Plugin</title>
  <!-- CDNs permitidos (no requieren build step) -->
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
  <style>
    /* Todo el CSS inline o en este bloque */
  </style>
</head>
<body>
  <!-- HTML de la UI -->
  
  <script>
    /* REGLAS:
     * 1. Usar var (no let/const)
     * 2. Funciones en scope global
     * 3. No import/export
     * 4. Llamar init() al final
     */
    var API_BASE = '';
    var currentState = null;
    
    function init() {
      checkHealth();
      loadData();
    }
    
    async function checkHealth() {
      try {
        var r = await fetch('/api/health');
        var d = await r.json();
        // actualizar UI...
      } catch(e) {
        console.error('Health check failed:', e);
      }
    }
    
    // ... resto de funciones ...
    
    init(); // ← SIEMPRE al final
  </script>
</body>
</html>
```

---

## 1. Arquitectura Frontend {#arquitectura}

Pinokio renderiza la UI del plugin como una aplicación web en un iframe. La UI puede ser:

- **HTML/CSS/JS puro**: Más simple, sin dependencias
- **React/Vue/Svelte**: Para UIs más complejas
- **Servidor web Python (FastAPI/Flask)**: Para UIs con lógica de servidor

### Estructura Recomendada para Plugin con UI

```
app/
├── index.html          # Punto de entrada
├── index.js            # JavaScript principal
├── styles.css          # Estilos globales
├── components/         # Componentes reutilizables
│   ├── AgentCard.js
│   ├── ChatInterface.js
│   ├── PromptEditor.js
│   └── ModelSelector.js
└── pages/              # Páginas de la aplicación
    ├── Dashboard.js
    ├── AgentConfig.js
    └── History.js
```

---

## 2. Integración con pinokio.js (Frontend SDK) {#sdk}

Pinokio provee `pinokio.js` para comunicación entre la UI y el kernel.

### Incluir en HTML

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Mi Plugin</title>
  <script src="https://cdn.jsdelivr.net/npm/@pinokiocomputer/pinokio.js"></script>
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <div id="app"></div>
  <script src="index.js"></script>
</body>
</html>
```

### Uso de pinokio.js

```javascript
// Inicializar conexión con Pinokio
const pinokio = new Pinokio()

// Ejecutar un script de Pinokio desde la UI
async function runScript(scriptPath, args = {}) {
  const result = await pinokio.run(scriptPath, args)
  return result
}

// Leer un archivo del sistema
async function readFile(filePath) {
  const content = await pinokio.fs.read(filePath)
  return content
}

// Escribir un archivo
async function writeFile(filePath, content) {
  await pinokio.fs.write(filePath, content)
}

// Obtener variables del entorno Pinokio
const env = await pinokio.env()
console.log(env.platform, env.ram, env.port)
```

---

## 3. Componentes de UI Recomendados {#componentes}

### Panel de Configuración de Agentes

```html
<!-- Componente: AgentConfigPanel -->
<div class="agent-config-panel">
  <div class="agent-header">
    <h3 class="agent-name" contenteditable="true">Nombre del Agente</h3>
    <span class="agent-status running">● Activo</span>
  </div>
  
  <div class="config-section">
    <label>Modelo LLM</label>
    <select id="model-select" class="model-selector">
      <option value="llama3.2:3b">Llama 3.2 (3B) - Rápido</option>
      <option value="llama3.1:8b">Llama 3.1 (8B) - Balanceado</option>
      <option value="mistral:7b">Mistral (7B) - Código</option>
    </select>
  </div>
  
  <div class="config-section">
    <label>System Prompt</label>
    <textarea id="system-prompt" rows="8" 
              placeholder="Define el rol y comportamiento del agente..."></textarea>
    <button class="btn-save" onclick="savePrompt()">Guardar Prompt</button>
  </div>
  
  <div class="config-section">
    <label>Temperatura: <span id="temp-value">0.7</span></label>
    <input type="range" min="0" max="1" step="0.1" value="0.7"
           oninput="document.getElementById('temp-value').textContent = this.value">
  </div>
  
  <div class="config-section">
    <label>Herramientas Disponibles</label>
    <div class="tools-grid">
      <label class="tool-toggle">
        <input type="checkbox" value="web_search"> Búsqueda Web
      </label>
      <label class="tool-toggle">
        <input type="checkbox" value="file_read"> Leer Archivos
      </label>
      <label class="tool-toggle">
        <input type="checkbox" value="data_analysis"> Análisis de Datos
      </label>
    </div>
  </div>
</div>
```

### Interfaz de Chat

```html
<!-- Componente: ChatInterface -->
<div class="chat-container">
  <div class="chat-header">
    <div class="agent-selector">
      <label>Agente Activo:</label>
      <select id="active-agent">
        <option value="orchestrator">Coordinador</option>
        <option value="analyst">Analista</option>
      </select>
    </div>
    <button class="btn-clear" onclick="clearChat()">Limpiar</button>
  </div>
  
  <div class="messages-container" id="messages">
    <!-- Los mensajes se agregan dinámicamente -->
  </div>
  
  <div class="input-area">
    <textarea id="user-input" 
              placeholder="Escribe tu mensaje aquí..."
              onkeydown="handleKeyDown(event)"></textarea>
    <div class="input-controls">
      <button class="btn-attach" onclick="attachFile()">
        <i class="fa-solid fa-paperclip"></i>
      </button>
      <button class="btn-send" onclick="sendMessage()">
        <i class="fa-solid fa-paper-plane"></i> Enviar
      </button>
    </div>
  </div>
</div>

<script>
async function sendMessage() {
  const input = document.getElementById('user-input')
  const agentId = document.getElementById('active-agent').value
  const message = input.value.trim()
  
  if (!message) return
  
  // Mostrar mensaje del usuario
  addMessage('user', message)
  input.value = ''
  
  // Mostrar indicador de carga
  const loadingId = addLoadingMessage()
  
  try {
    // Llamar al backend
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ agent_id: agentId, message })
    })
    
    const data = await response.json()
    removeLoadingMessage(loadingId)
    addMessage('assistant', data.response, agentId)
  } catch (error) {
    removeLoadingMessage(loadingId)
    addMessage('error', 'Error al conectar con el agente')
  }
}

function addMessage(role, content, agentId = null) {
  const container = document.getElementById('messages')
  const div = document.createElement('div')
  div.className = `message message-${role}`
  div.innerHTML = `
    ${agentId ? `<span class="agent-label">${agentId}</span>` : ''}
    <div class="message-content">${marked.parse(content)}</div>
    <span class="message-time">${new Date().toLocaleTimeString()}</span>
  `
  container.appendChild(div)
  container.scrollTop = container.scrollHeight
}
</script>
```

### Dashboard Principal

```html
<!-- Componente: Dashboard -->
<div class="dashboard">
  <div class="stats-grid">
    <div class="stat-card">
      <div class="stat-icon"><i class="fa-solid fa-robot"></i></div>
      <div class="stat-value" id="agents-count">0</div>
      <div class="stat-label">Agentes Activos</div>
    </div>
    <div class="stat-card">
      <div class="stat-icon"><i class="fa-solid fa-message"></i></div>
      <div class="stat-value" id="sessions-count">0</div>
      <div class="stat-label">Sesiones Hoy</div>
    </div>
    <div class="stat-card">
      <div class="stat-icon"><i class="fa-solid fa-brain"></i></div>
      <div class="stat-value" id="model-name">-</div>
      <div class="stat-label">Modelo Principal</div>
    </div>
  </div>
  
  <div class="agents-grid" id="agents-grid">
    <!-- Cards de agentes se cargan dinámicamente -->
  </div>
  
  <div class="quick-actions">
    <button class="btn-primary" onclick="openNewChat()">
      <i class="fa-solid fa-plus"></i> Nueva Conversación
    </button>
    <button class="btn-secondary" onclick="openAgentConfig()">
      <i class="fa-solid fa-gear"></i> Configurar Agentes
    </button>
    <button class="btn-secondary" onclick="openHistory()">
      <i class="fa-solid fa-clock-rotate-left"></i> Historial
    </button>
  </div>
</div>
```

---

## 4. Patrones de Layout {#layouts}

### CSS Base para Plugins Pinokio

```css
/* styles.css - Base para plugins Pinokio */
:root {
  --primary: #6366f1;
  --primary-dark: #4f46e5;
  --secondary: #64748b;
  --success: #22c55e;
  --warning: #f59e0b;
  --error: #ef4444;
  --bg-primary: #0f172a;
  --bg-secondary: #1e293b;
  --bg-card: #1e293b;
  --text-primary: #f1f5f9;
  --text-secondary: #94a3b8;
  --border: #334155;
  --radius: 8px;
  --shadow: 0 4px 6px -1px rgba(0,0,0,0.3);
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  background: var(--bg-primary);
  color: var(--text-primary);
  height: 100vh;
  overflow: hidden;
}

/* Layout principal con sidebar */
.app-layout {
  display: grid;
  grid-template-columns: 240px 1fr;
  grid-template-rows: 60px 1fr;
  height: 100vh;
}

.app-header {
  grid-column: 1 / -1;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  padding: 0 20px;
  gap: 12px;
}

.app-sidebar {
  background: var(--bg-secondary);
  border-right: 1px solid var(--border);
  padding: 16px;
  overflow-y: auto;
}

.app-main {
  overflow-y: auto;
  padding: 24px;
}

/* Componentes */
.card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px;
  box-shadow: var(--shadow);
}

.btn-primary {
  background: var(--primary);
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: var(--radius);
  cursor: pointer;
  font-size: 14px;
  transition: background 0.2s;
}

.btn-primary:hover {
  background: var(--primary-dark);
}

.btn-secondary {
  background: transparent;
  color: var(--text-primary);
  border: 1px solid var(--border);
  padding: 8px 16px;
  border-radius: var(--radius);
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.btn-secondary:hover {
  background: var(--bg-secondary);
  border-color: var(--primary);
}

/* Chat */
.message {
  margin-bottom: 16px;
  padding: 12px 16px;
  border-radius: var(--radius);
  max-width: 80%;
}

.message-user {
  background: var(--primary);
  margin-left: auto;
}

.message-assistant {
  background: var(--bg-secondary);
  border: 1px solid var(--border);
}

.message-error {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid var(--error);
  color: var(--error);
}

/* Loading animation */
.loading-dots span {
  animation: loading 1.4s infinite;
  display: inline-block;
}

.loading-dots span:nth-child(2) { animation-delay: 0.2s; }
.loading-dots span:nth-child(3) { animation-delay: 0.4s; }

@keyframes loading {
  0%, 80%, 100% { opacity: 0; }
  40% { opacity: 1; }
}
```

---

## 5. Comunicación Frontend-Backend {#comunicacion}

### Servidor FastAPI para el Backend

```python
# server/app.py
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import os

app = FastAPI(title="Plugin API")

# CORS para comunicación con la UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir archivos estáticos de la UI
app.mount("/ui", StaticFiles(directory="app", html=True), name="ui")

class ChatRequest(BaseModel):
    agent_id: str
    message: str
    session_id: str = None

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """Endpoint principal de chat con agentes."""
    try:
        # Obtener el agente
        agent = agent_manager.get_agent(request.agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agente no encontrado")
        
        # Ejecutar el agente
        response = agent_manager.run_agent(
            request.agent_id, 
            request.message
        )
        
        # Persistir en sesión
        if request.session_id:
            persistence.append_to_session(request.session_id, {
                "role": "user",
                "content": request.message,
                "agent_id": request.agent_id
            })
            persistence.append_to_session(request.session_id, {
                "role": "assistant",
                "content": response,
                "agent_id": request.agent_id
            })
        
        return {"response": response, "agent_id": request.agent_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/agents")
async def list_agents():
    """Lista todos los agentes configurados."""
    return {"agents": list(agent_manager.agents.values())}

@app.get("/api/models")
async def list_models():
    """Lista los modelos Ollama disponibles."""
    import requests as req
    try:
        response = req.get("http://localhost:11434/api/tags")
        models = [m["name"] for m in response.json().get("models", [])]
        return {"models": models}
    except:
        return {"models": []}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
```

---

## 6. Gestión de Estado {#estado}

### Store Simple para Estado Global

```javascript
// app/store.js - Gestión de estado sin dependencias externas
class Store {
  constructor(initialState = {}) {
    this.state = initialState
    this.listeners = {}
  }
  
  get(key) {
    return key ? this.state[key] : this.state
  }
  
  set(key, value) {
    this.state[key] = value
    this.emit(key, value)
  }
  
  on(key, callback) {
    if (!this.listeners[key]) this.listeners[key] = []
    this.listeners[key].push(callback)
  }
  
  emit(key, value) {
    (this.listeners[key] || []).forEach(cb => cb(value))
    (this.listeners['*'] || []).forEach(cb => cb(key, value))
  }
}

// Estado global de la aplicación
const store = new Store({
  agents: [],
  activeAgent: null,
  currentSession: null,
  messages: [],
  models: [],
  isLoading: false
})

// Sincronizar estado con backend al iniciar
async function initializeStore() {
  const [agentsRes, modelsRes] = await Promise.all([
    fetch('/api/agents').then(r => r.json()),
    fetch('/api/models').then(r => r.json())
  ])
  
  store.set('agents', agentsRes.agents)
  store.set('models', modelsRes.models)
  
  if (agentsRes.agents.length > 0) {
    store.set('activeAgent', agentsRes.agents[0].id)
  }
}
```
