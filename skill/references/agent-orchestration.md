# Orquestación de Agentes con Ollama en Pinokio

## Tabla de Contenidos
1. [Instalación y Verificación de Ollama](#ollama)
2. [Arquitectura Multi-Agente](#multiagente)
3. [Configuración de Agentes](#config-agentes)
4. [Gestión de Prompts](#prompts)
5. [Mezcla de LLMs](#mezcla-llms)
6. [Comunicación entre Agentes](#comunicacion)
7. [Persistencia de Configuración](#persistencia)

---

## 1. Instalación y Verificación de Ollama {#ollama}

### Script de Instalación Cross-Platform

```javascript
// En install.js
{
  method: "shell.run",
  params: {
    message: [
      // macOS
      "if [ '{{platform}}' = 'darwin' ]; then",
      "  brew install ollama || true",
      // Linux
      "elif [ '{{platform}}' = 'linux' ]; then",
      "  curl -fsSL https://ollama.com/install.sh | sh",
      // Windows (via winget)
      "elif [ '{{platform}}' = 'win32' ]; then",
      "  winget install Ollama.Ollama --accept-source-agreements --accept-package-agreements || true",
      "fi"
    ].join("\n")
  }
}
```

### Verificar que Ollama Está Corriendo

```python
# server/utils/ollama_check.py
import requests
import subprocess
import time

def ensure_ollama_running():
    """Asegura que Ollama esté corriendo, lo inicia si no."""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        return response.status_code == 200
    except:
        # Iniciar Ollama en background
        subprocess.Popen(["ollama", "serve"], 
                        stdout=subprocess.DEVNULL, 
                        stderr=subprocess.DEVNULL)
        time.sleep(3)
        return True

def list_available_models():
    """Lista los modelos disponibles en Ollama."""
    try:
        response = requests.get("http://localhost:11434/api/tags")
        return [m["name"] for m in response.json().get("models", [])]
    except:
        return []
```

### Descarga de Modelos Recomendados

```javascript
// En install.js - Descargar modelos según RAM disponible
{
  method: "shell.run",
  params: {
    // Modelo ligero para PCs con poca RAM (< 8GB)
    message: "{{ram < 8 ? 'ollama pull llama3.2:1b' : ram < 16 ? 'ollama pull llama3.2:3b' : 'ollama pull llama3.1:8b'}}"
  }
}
```

### Modelos Recomendados por Caso de Uso

| Modelo | RAM Mínima | Velocidad | Calidad | Uso Ideal |
|--------|-----------|-----------|---------|-----------|
| `llama3.2:1b` | 2GB | Muy rápido | Básica | Clasificación simple |
| `llama3.2:3b` | 4GB | Rápido | Buena | Tareas generales |
| `llama3.1:8b` | 8GB | Medio | Alta | Análisis complejo |
| `llama3.1:70b` | 40GB | Lento | Excelente | Tareas críticas |
| `mistral:7b` | 8GB | Rápido | Alta | Código y análisis |
| `qwen2.5:7b` | 8GB | Rápido | Alta | Multilingüe |
| `phi3:mini` | 4GB | Muy rápido | Buena | Eficiencia energética |

---

## 2. Arquitectura Multi-Agente {#multiagente}

### Patrón de Orquestador + Especialistas

```
┌─────────────────────────────────────────┐
│           AGENTE ORQUESTADOR            │
│  (Coordina el flujo entre agentes)      │
│  Modelo: llama3.1:8b                    │
└────────────┬────────────────────────────┘
             │
    ┌────────┴────────┐
    │                 │
    ▼                 ▼
┌──────────┐    ┌──────────┐
│ AGENTE 1 │    │ AGENTE 2 │
│Especialista│  │Especialista│
│llama3.2:3b│  │mistral:7b│
└──────────┘    └──────────┘
```

### Configuración de Agentes en JSON

```json
{
  "agents": [
    {
      "id": "orchestrator",
      "name": "Coordinador",
      "model": "llama3.1:8b",
      "role": "orchestrator",
      "systemPrompt": "Eres el coordinador del equipo. Analiza la tarea y delega a los especialistas apropiados.",
      "temperature": 0.3,
      "maxTokens": 2048,
      "tools": ["delegate", "summarize", "finalize"],
      "skills": ["planning", "coordination"]
    },
    {
      "id": "analyst",
      "name": "Analista",
      "model": "llama3.2:3b",
      "role": "specialist",
      "systemPrompt": "Eres un analista experto. Tu tarea es analizar datos y generar insights.",
      "temperature": 0.1,
      "maxTokens": 1024,
      "tools": ["analyze_data", "generate_report"],
      "skills": ["data_analysis", "reporting"]
    }
  ]
}
```

---

## 3. Configuración de Agentes {#config-agentes}

### Clase AgentManager en Python

```python
# server/agents/agent_manager.py
import json
import os
import requests
from pathlib import Path

class AgentManager:
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.agents = {}
        self.load_config()
    
    def load_config(self):
        """Carga la configuración de agentes desde disco."""
        if self.config_path.exists():
            with open(self.config_path) as f:
                config = json.load(f)
                for agent_config in config.get("agents", []):
                    self.agents[agent_config["id"]] = agent_config
    
    def save_config(self):
        """Persiste la configuración de agentes en disco."""
        config = {"agents": list(self.agents.values())}
        with open(self.config_path, "w") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    
    def add_agent(self, agent_config: dict):
        """Agrega o actualiza un agente."""
        self.agents[agent_config["id"]] = agent_config
        self.save_config()
    
    def remove_agent(self, agent_id: str):
        """Elimina un agente."""
        if agent_id in self.agents:
            del self.agents[agent_id]
            self.save_config()
    
    def update_prompt(self, agent_id: str, prompt: str):
        """Actualiza el system prompt de un agente."""
        if agent_id in self.agents:
            self.agents[agent_id]["systemPrompt"] = prompt
            self.save_config()
    
    def update_model(self, agent_id: str, model: str):
        """Cambia el modelo LLM de un agente."""
        if agent_id in self.agents:
            self.agents[agent_id]["model"] = model
            self.save_config()
    
    def run_agent(self, agent_id: str, user_message: str, context: list = None):
        """Ejecuta un agente con un mensaje."""
        agent = self.agents.get(agent_id)
        if not agent:
            raise ValueError(f"Agente '{agent_id}' no encontrado")
        
        messages = []
        
        # Agregar system prompt
        if agent.get("systemPrompt"):
            messages.append({
                "role": "system",
                "content": agent["systemPrompt"]
            })
        
        # Agregar contexto previo si existe
        if context:
            messages.extend(context)
        
        # Agregar mensaje del usuario
        messages.append({"role": "user", "content": user_message})
        
        # Llamar a Ollama
        response = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model": agent["model"],
                "messages": messages,
                "options": {
                    "temperature": agent.get("temperature", 0.7),
                    "num_predict": agent.get("maxTokens", 1024)
                },
                "stream": False
            }
        )
        
        result = response.json()
        return result["message"]["content"]
```

---

## 4. Gestión de Prompts {#prompts}

### Estructura de Almacenamiento de Prompts

```
data/
└── prompts/
    ├── system/           # System prompts por agente
    │   ├── orchestrator.md
    │   ├── analyst.md
    │   └── writer.md
    ├── templates/        # Plantillas de prompts reutilizables
    │   ├── analysis.md
    │   └── report.md
    └── history/          # Historial de versiones de prompts
        └── orchestrator_v1.md
```

### API de Gestión de Prompts

```python
# server/prompts/prompt_manager.py
from pathlib import Path
import shutil
from datetime import datetime

class PromptManager:
    def __init__(self, prompts_dir: str):
        self.prompts_dir = Path(prompts_dir)
        self.prompts_dir.mkdir(parents=True, exist_ok=True)
        (self.prompts_dir / "system").mkdir(exist_ok=True)
        (self.prompts_dir / "templates").mkdir(exist_ok=True)
        (self.prompts_dir / "history").mkdir(exist_ok=True)
    
    def get_prompt(self, agent_id: str) -> str:
        """Obtiene el system prompt de un agente."""
        prompt_file = self.prompts_dir / "system" / f"{agent_id}.md"
        if prompt_file.exists():
            return prompt_file.read_text(encoding="utf-8")
        return ""
    
    def save_prompt(self, agent_id: str, prompt: str):
        """Guarda el system prompt y versiona el anterior."""
        prompt_file = self.prompts_dir / "system" / f"{agent_id}.md"
        
        # Versionar el prompt anterior si existe
        if prompt_file.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            history_file = self.prompts_dir / "history" / f"{agent_id}_{timestamp}.md"
            shutil.copy(prompt_file, history_file)
        
        prompt_file.write_text(prompt, encoding="utf-8")
    
    def list_templates(self) -> list:
        """Lista las plantillas disponibles."""
        templates_dir = self.prompts_dir / "templates"
        return [f.stem for f in templates_dir.glob("*.md")]
    
    def get_template(self, template_name: str) -> str:
        """Obtiene una plantilla de prompt."""
        template_file = self.prompts_dir / "templates" / f"{template_name}.md"
        if template_file.exists():
            return template_file.read_text(encoding="utf-8")
        return ""
```

---

## 5. Mezcla de LLMs {#mezcla-llms}

### Estrategia de Selección de Modelo

```python
# server/agents/model_selector.py
class ModelSelector:
    """Selecciona el modelo apropiado según la tarea."""
    
    TASK_MODEL_MAP = {
        "classification": "llama3.2:1b",    # Rápido para clasificación
        "analysis": "llama3.2:3b",           # Balance velocidad/calidad
        "generation": "llama3.1:8b",         # Calidad para generación
        "code": "mistral:7b",                # Especializado en código
        "multilingual": "qwen2.5:7b",        # Multilingüe
        "fast": "phi3:mini",                 # Máxima velocidad
    }
    
    @classmethod
    def select_model(cls, task_type: str, available_models: list, 
                     ram_gb: float) -> str:
        """Selecciona el mejor modelo disponible para la tarea."""
        preferred = cls.TASK_MODEL_MAP.get(task_type, "llama3.2:3b")
        
        # Si el modelo preferido está disponible, usarlo
        if preferred in available_models:
            return preferred
        
        # Fallback basado en RAM disponible
        if ram_gb >= 16:
            fallback_order = ["llama3.1:8b", "mistral:7b", "llama3.2:3b", "llama3.2:1b"]
        elif ram_gb >= 8:
            fallback_order = ["llama3.2:3b", "phi3:mini", "llama3.2:1b"]
        else:
            fallback_order = ["llama3.2:1b", "phi3:mini"]
        
        for model in fallback_order:
            if model in available_models:
                return model
        
        # Usar el primer modelo disponible
        return available_models[0] if available_models else "llama3.2:3b"
```

---

## 6. Comunicación entre Agentes {#comunicacion}

### Patrón Pipeline (Secuencial)

```python
# server/orchestration/pipeline.py
class AgentPipeline:
    """Ejecuta agentes en secuencia, pasando el output de uno al siguiente."""
    
    def __init__(self, agent_manager: AgentManager):
        self.agent_manager = agent_manager
    
    def run(self, initial_input: str, agent_sequence: list) -> dict:
        """
        Ejecuta una secuencia de agentes.
        agent_sequence: ["agent1_id", "agent2_id", ...]
        """
        results = {}
        current_input = initial_input
        
        for agent_id in agent_sequence:
            result = self.agent_manager.run_agent(agent_id, current_input)
            results[agent_id] = result
            current_input = result  # Output del agente anterior es input del siguiente
        
        return results
```

### Patrón Paralelo (Concurrent)

```python
# server/orchestration/parallel.py
import asyncio
import aiohttp

class ParallelAgentRunner:
    """Ejecuta múltiples agentes en paralelo."""
    
    async def run_agent_async(self, session, agent_config: dict, 
                               message: str) -> dict:
        """Ejecuta un agente de forma asíncrona."""
        payload = {
            "model": agent_config["model"],
            "messages": [
                {"role": "system", "content": agent_config.get("systemPrompt", "")},
                {"role": "user", "content": message}
            ],
            "stream": False
        }
        
        async with session.post(
            "http://localhost:11434/api/chat",
            json=payload
        ) as response:
            result = await response.json()
            return {
                "agent_id": agent_config["id"],
                "response": result["message"]["content"]
            }
    
    async def run_parallel(self, agents: list, message: str) -> list:
        """Ejecuta todos los agentes en paralelo."""
        async with aiohttp.ClientSession() as session:
            tasks = [
                self.run_agent_async(session, agent, message)
                for agent in agents
            ]
            return await asyncio.gather(*tasks)
```

---

## 7. Persistencia de Configuración {#persistencia}

### Estructura de Datos Persistentes

```
data/
├── config.json           # Configuración global del plugin
├── agents/
│   ├── agents.json       # Definición de todos los agentes
│   └── {agent_id}/
│       ├── config.json   # Config específica del agente
│       └── memory.json   # Memoria del agente
├── prompts/
│   ├── system/           # System prompts
│   └── templates/        # Plantillas
├── sessions/
│   └── {session_id}/
│       ├── messages.json # Historial de mensajes
│       └── metadata.json # Metadatos de la sesión
└── exports/              # Exportaciones generadas
```

### Clase de Persistencia Base

```python
# server/storage/persistence.py
import json
from pathlib import Path
from datetime import datetime

class PersistenceManager:
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def save(self, key: str, data: dict):
        """Guarda datos en disco."""
        file_path = self.data_dir / f"{key}.json"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def load(self, key: str, default=None) -> dict:
        """Carga datos desde disco."""
        file_path = self.data_dir / f"{key}.json"
        if file_path.exists():
            with open(file_path, encoding="utf-8") as f:
                return json.load(f)
        return default or {}
    
    def append_to_session(self, session_id: str, message: dict):
        """Agrega un mensaje al historial de sesión."""
        session_file = self.data_dir / "sessions" / session_id / "messages.json"
        session_file.parent.mkdir(parents=True, exist_ok=True)
        
        messages = []
        if session_file.exists():
            with open(session_file) as f:
                messages = json.load(f)
        
        message["timestamp"] = datetime.now().isoformat()
        messages.append(message)
        
        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(messages, f, indent=2, ensure_ascii=False)
```
