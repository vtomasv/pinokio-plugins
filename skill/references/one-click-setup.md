# Instalación con 1-Click para Plugins Pinokio

## Tabla de Contenidos
1. [Principios de Diseño](#principios)
2. [Flujo de Instalación Completo](#flujo)
3. [Detección de Sistema y Hardware](#deteccion)
4. [Manejo de Errores en Instalación](#errores)
5. [Publicación en GitHub para Distribución](#publicacion)
6. [Checklist de Instalación](#checklist)

---

## 1. Principios de Diseño {#principios}

Los plugins para usuarios sin experiencia técnica deben seguir estos principios:

- **Zero configuración manual**: El usuario solo hace click en "Instalar"
- **Detección automática**: El plugin detecta el sistema, hardware y dependencias
- **Feedback visual**: Mostrar progreso claro durante la instalación
- **Recuperación de errores**: Mensajes de error comprensibles y acciones de recuperación
- **Idempotencia**: Instalar dos veces no debe causar problemas
- **Rollback**: Si algo falla, el sistema debe poder recuperarse

---

## 2. Flujo de Instalación Completo {#flujo}

### install.js - Instalación Completa

```javascript
module.exports = {
  title: "Instalando Plugin",
  description: "Configuración automática completa",
  run: [
    // ====================================
    // FASE 1: Verificación del Sistema
    // ====================================
    {
      method: "log",
      params: {
        html: "<h3>🔍 Verificando sistema...</h3>"
      }
    },
    
    // Verificar versión de Python
    {
      method: "shell.run",
      params: {
        message: "python --version || python3 --version",
        on: [{
          event: "error",
          done: true,
          error: "Python no encontrado. Por favor instala Python 3.8 o superior."
        }]
      }
    },
    
    // ====================================
    // FASE 2: Instalación de Ollama
    // ====================================
    {
      method: "log",
      params: {
        html: "<h3>🤖 Configurando Ollama...</h3>"
      }
    },
    
    // Verificar si Ollama ya está instalado
    {
      method: "shell.run",
      params: {
        message: "ollama --version",
        on: [{
          event: "error",
          // Si no está instalado, instalarlo
          run: [{
            method: "shell.run",
            params: {
              message: [
                "if [ '{{platform}}' = 'darwin' ]; then",
                "  brew install ollama",
                "elif [ '{{platform}}' = 'linux' ]; then",
                "  curl -fsSL https://ollama.com/install.sh | sh",
                "fi"
              ].join("\n")
            }
          }]
        }]
      }
    },
    
    // Iniciar servicio Ollama
    // IMPORTANTE: NO usar background:true (no existe en Pinokio)
    // Redirigir output de Ollama para evitar que sus logs rompan el parser de xterm
    {
      method: "shell.run",
      params: {
        message: "ollama serve > /dev/null 2>&1 &"
      }
    },
    
    // Esperar que Ollama esté listo
    {
      method: "shell.run",
      params: {
        message: "sleep 3 && curl -s http://localhost:11434/api/tags > /dev/null"
      }
    },
    
    // ====================================
    // FASE 3: Descargar Modelo LLM
    // ====================================
    {
      method: "log",
      params: {
        html: "<h3>⬇️ Descargando modelo de IA...</h3><p>Esto puede tomar unos minutos la primera vez.</p>"
      }
    },
    
    // Seleccionar modelo según RAM disponible
    {
      method: "shell.run",
      params: {
        // Modelo ligero para PCs con poca RAM
        message: "{{ram < 8 ? 'ollama pull llama3.2:1b' : ram < 16 ? 'ollama pull llama3.2:3b' : 'ollama pull llama3.1:8b'}}"
      }
    },
    
    // ====================================
    // FASE 4: Entorno Python
    // ====================================
    {
      method: "log",
      params: {
        html: "<h3>🐍 Configurando entorno Python...</h3>"
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
    
    // ====================================
    // FASE 5: Inicializar Datos
    // ====================================
    {
      method: "log",
      params: {
        html: "<h3>💾 Inicializando datos...</h3>"
      }
    },
    
    // Crear estructura de directorios de datos
    {
      method: "shell.run",
      params: {
        message: "mkdir -p data/agents data/prompts/system data/prompts/templates data/sessions data/exports",
        path: "{{cwd}}"
      }
    },
    
    // Crear configuración inicial
    {
      method: "fs.write",
      params: {
        path: "data/config.json",
        text: "{{JSON.stringify({version: '1.0.0', installedAt: new Date().toISOString(), defaultModel: ram < 8 ? 'llama3.2:1b' : ram < 16 ? 'llama3.2:3b' : 'llama3.1:8b', agents: []}, null, 2)}}"
      }
    },
    
    // Copiar configuración de agentes por defecto
    {
      method: "fs.copy",
      params: {
        src: "defaults/agents.json",
        dst: "data/agents/agents.json"
      }
    },
    
    // Copiar prompts por defecto
    {
      method: "shell.run",
      params: {
        message: "cp -r defaults/prompts/* data/prompts/",
        path: "{{cwd}}"
      }
    },
    
    // ====================================
    // FASE 6: Completado
    // ====================================
    {
      method: "log",
      params: {
        html: "<h3 style='color: #22c55e'>✅ Instalación completada</h3><p>Haz click en 'Iniciar' para comenzar a usar el plugin.</p>"
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
```

---

## 3. Detección de Sistema y Hardware {#deteccion}

### Variables de Sistema Disponibles en Pinokio

```javascript
// Estas variables están disponibles en todos los scripts de Pinokio
// via template literals {{variable}}

// Sistema operativo
platform  // 'darwin' (macOS), 'win32' (Windows), 'linux'
arch      // 'x64', 'arm64'

// Hardware
ram       // RAM en GB (número)
vram      // VRAM en GB (número, 0 si no hay GPU dedicada)
gpu       // Nombre de la GPU o null
gpus      // Array de GPUs disponibles

// Entorno
cwd       // Directorio del plugin
port      // Puerto asignado automáticamente
```

### Lógica de Selección de Modelo

```javascript
// En cualquier script de Pinokio
const selectModel = () => {
  if (vram >= 8) return 'llama3.1:8b'  // GPU dedicada con suficiente VRAM
  if (ram >= 16) return 'llama3.1:8b'  // Mucha RAM
  if (ram >= 8) return 'llama3.2:3b'   // RAM moderada
  return 'llama3.2:1b'                  // RAM limitada
}
```

---

## 4. Manejo de Errores en Instalación {#errores}

### Patrones de Recuperación

```javascript
// Patrón: Reintentar con fallback
{
  method: "shell.run",
  params: {
    message: "ollama pull llama3.1:8b",
    on: [{
      event: "error",
      // Si falla el modelo grande, intentar con uno más pequeño
      run: [{
        method: "shell.run",
        params: {
          message: "ollama pull llama3.2:3b"
        }
      }]
    }]
  }
}
```

### Script de Verificación Post-Instalación

```python
# scripts/verify_install.py
import sys
import json
import subprocess
import requests
from pathlib import Path

def check_installation(plugin_dir: str) -> dict:
    """Verifica que la instalación esté completa y correcta."""
    results = {
        "python_venv": False,
        "dependencies": False,
        "ollama": False,
        "models": [],
        "data_dir": False,
        "config": False
    }
    
    plugin_path = Path(plugin_dir)
    
    # Verificar entorno virtual
    venv_path = plugin_path / "venv"
    results["python_venv"] = venv_path.exists()
    
    # Verificar Ollama
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=3)
        if response.status_code == 200:
            results["ollama"] = True
            results["models"] = [m["name"] for m in response.json().get("models", [])]
    except:
        pass
    
    # Verificar directorio de datos
    data_dir = plugin_path / "data"
    results["data_dir"] = data_dir.exists()
    
    # Verificar configuración
    config_file = data_dir / "config.json"
    if config_file.exists():
        try:
            json.loads(config_file.read_text())
            results["config"] = True
        except:
            pass
    
    return results

if __name__ == "__main__":
    plugin_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    results = check_installation(plugin_dir)
    
    all_ok = all([
        results["python_venv"],
        results["ollama"],
        len(results["models"]) > 0,
        results["data_dir"],
        results["config"]
    ])
    
    print(json.dumps({"success": all_ok, "details": results}, indent=2))
    sys.exit(0 if all_ok else 1)
```

---

## 5. Publicación en GitHub para Distribución {#publicacion}

### Estructura del Repositorio para Distribución

```
nombre-plugin/
├── README.md               # Descripción del plugin
├── pinokio.js              # Configuración principal (ÚNICO .js permitido)
├── install.json            # Script de instalación (JSON puro, NO .js)
├── start.json              # Script de inicio (JSON puro, NO .js)
├── stop.json               # Script de parada (JSON puro, NO .js)
├── requirements.txt        # Dependencias Python
├── package.json            # Dependencias Node.js (si aplica)
├── icon.png                # Icono del plugin
├── defaults/               # Configuraciones por defecto
│   ├── agents.json
│   └── prompts/
├── app/                    # Frontend
│   └── index.html
└── server/                 # Backend
    └── app.py
```

### README.md para Distribución

```markdown
# Nombre del Plugin

Descripción breve del plugin.

## Instalación

1. Abre [Pinokio](https://pinokio.co)
2. Ve a "Discover" o pega esta URL directamente:
   `https://github.com/usuario/nombre-plugin`
3. Haz click en "Instalar"
4. Espera a que termine la instalación automática
5. Haz click en "Iniciar"

## Requisitos

- Pinokio instalado
- 4GB RAM mínimo (8GB recomendado)
- 5GB espacio en disco

## Uso

[Instrucciones de uso]
```

### Instalar desde URL de GitHub

Los usuarios pueden instalar el plugin directamente desde Pinokio pegando la URL del repositorio de GitHub. Pinokio clona el repositorio y ejecuta `install.js` automáticamente.

---

## 6. Checklist de Instalación {#checklist}

Antes de publicar un plugin, verificar:

- [ ] Scripts de ciclo de vida son `.json` (NO `.js`): `install.json`, `start.json`, `stop.json`
- [ ] `pinokio.js` referencia los archivos `.json` en los `href`
- [ ] No hay `background: true` en ningún script JSON
- [ ] `install.json` es idempotente (se puede ejecutar múltiples veces)
- [ ] `start.json` inicia el servidor correctamente
- [ ] `stop.json` detiene todos los procesos
- [ ] El plugin funciona con 4GB RAM (modelo llama3.2:1b)
- [ ] El plugin funciona con 8GB RAM (modelo llama3.2:3b)
- [ ] Los datos se persisten correctamente en `data/`
- [ ] La UI es usable en resoluciones 1280x720 y superiores
- [ ] Los errores muestran mensajes comprensibles al usuario
- [ ] El `README.md` tiene instrucciones claras de instalación
- [ ] El icono `icon.png` es de 512x512 píxeles
- [ ] El plugin no accede a recursos fuera de `~/pinokio/`
