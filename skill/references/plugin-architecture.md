# Arquitectura de Plugins Pinokio

## Tabla de Contenidos
1. [Estructura de Directorios](#estructura)
2. [Archivo pinokio.js](#pinokiojs)
3. [Archivo pinokio.json (Config)](#config)
4. [Scripts de Instalación y Lanzamiento](#scripts)
5. [Sistema de Archivos Pinokio](#filesystem)
6. [Ciclo de Vida del Plugin](#lifecycle)

---

## 1. Estructura de Directorios {#estructura}

```
~/pinokio/api/
└── nombre-plugin/
    ├── pinokio.js          # Configuración principal del plugin
    ├── pinokio.json        # Config auto-generada (no editar manualmente)
    ├── icon.png            # Icono del plugin (recomendado: 512x512)
    ├── install.js          # Script de instalación (opcional)
    ├── start.js            # Script de inicio
    ├── stop.js             # Script de parada (opcional)
    ├── app/                # Aplicación web (frontend)
    │   ├── index.html
    │   ├── index.js
    │   └── ...
    ├── server/             # Backend del plugin
    │   ├── app.py          # Servidor principal
    │   └── ...
    ├── data/               # Datos persistentes del usuario
    │   ├── agents/         # Configuraciones de agentes
    │   ├── prompts/        # Prompts personalizados
    │   └── sessions/       # Historial de sesiones
    └── venv/               # Entorno virtual Python (auto-generado)
```

---

## 2. Archivo pinokio.js {#pinokiojs}

El archivo central que define el comportamiento del plugin.

### Estructura Completa

```javascript
module.exports = {
  // Metadatos del plugin
  title: "Nombre del Plugin",
  description: "Descripción breve del plugin",
  icon: "icon.png",
  version: "1.0.0",
  
  // Menú de acciones disponibles
  menu: async (kernel, info) => {
    // Verificar si está instalado
    const installed = await kernel.exists(__dirname, "venv")
    const running = await kernel.script.running(__dirname, "start.js")
    
    if (!installed) {
      return [{
        default: true,
        icon: "fa-solid fa-download",
        text: "Instalar",
        href: "install.js"
      }]
    }
    
    if (running) {
      return [
        {
          icon: "fa-solid fa-circle",
          text: "En ejecución",
          href: "start.js",
          style: "color: green"
        },
        {
          icon: "fa-solid fa-stop",
          text: "Detener",
          href: "stop.js"
        }
      ]
    }
    
    return [
      {
        default: true,
        icon: "fa-solid fa-play",
        text: "Iniciar",
        href: "start.js"
      }
    ]
  }
}
```

### Propiedades Clave

| Propiedad | Tipo | Descripción |
|-----------|------|-------------|
| `title` | string | Nombre visible en la UI |
| `description` | string | Descripción del plugin |
| `icon` | string | Ruta al icono (relativa al plugin) |
| `version` | string | Versión semántica |
| `menu` | function/array | Menú de acciones del plugin |

---

## 3. Archivo pinokio.json (Config) {#config}

Configuración del plugin. Puede ser estático o generado dinámicamente.

```json
{
  "title": "Nombre del Plugin",
  "description": "Descripción",
  "icon": "icon.png",
  "version": "1.0.0",
  "pre": [
    {
      "method": "shell.run",
      "params": {
        "message": "echo 'Verificando dependencias...'"
      }
    }
  ]
}
```

---

## 4. Scripts de Instalación y Lanzamiento {#scripts}

### install.js - Instalación con 1-Click

```javascript
module.exports = {
  title: "Instalando Plugin",
  description: "Instalación automática de dependencias",
  run: [
    // Paso 1: Verificar/instalar Ollama
    {
      method: "shell.run",
      params: {
        message: "{{platform === 'darwin' ? 'brew install ollama' : platform === 'win32' ? 'winget install ollama' : 'curl -fsSL https://ollama.com/install.sh | sh'}}",
        on: [{
          event: "error",
          done: true
        }]
      }
    },
    // Paso 2: Crear entorno virtual Python
    {
      method: "shell.run",
      params: {
        message: "python -m venv venv",
        path: "{{cwd}}"
      }
    },
    // Paso 3: Instalar dependencias Python
    {
      method: "shell.run",
      params: {
        message: "pip install -r requirements.txt",
        path: "{{cwd}}",
        venv: "venv"
      }
    },
    // Paso 4: Instalar dependencias Node.js
    {
      method: "shell.run",
      params: {
        message: "npm install",
        path: "{{cwd}}/app"
      }
    },
    // Paso 5: Descargar modelo Ollama por defecto
    {
      method: "shell.run",
      params: {
        message: "ollama pull llama3.2:3b"
      }
    },
    // Paso 6: Inicializar datos persistentes
    {
      method: "fs.write",
      params: {
        path: "data/config.json",
        text: JSON.stringify({
          version: "1.0.0",
          agents: [],
          defaultModel: "llama3.2:3b"
        }, null, 2)
      }
    },
    // Notificar al usuario
    {
      method: "notify",
      params: {
        html: "Plugin instalado correctamente. Haz click en 'Iniciar' para comenzar."
      }
    }
  ]
}
```

### start.js - Inicio del Plugin

```javascript
module.exports = {
  daemon: true,  // Ejecutar como daemon (proceso en background)
  run: [
    // Iniciar servidor backend
    {
      method: "shell.run",
      params: {
        message: "python server/app.py",
        path: "{{cwd}}",
        venv: "venv",
        env: {
          PORT: "{{port}}"
        }
      }
    },
    // Abrir UI en el navegador
    {
      method: "web.open",
      params: {
        url: "http://localhost:{{port}}"
      }
    }
  ]
}
```

### stop.js - Parada del Plugin

```javascript
module.exports = {
  run: [
    {
      method: "script.stop",
      params: {
        path: "start.js"
      }
    }
  ]
}
```

---

## 5. Sistema de Archivos Pinokio {#filesystem}

### Rutas Importantes

| Ruta | Descripción |
|------|-------------|
| `~/pinokio/api/` | Directorio de plugins instalados |
| `~/pinokio/bin/` | Binarios instalados por Pinokio |
| `~/pinokio/cache/` | Caché de descargas |
| `~/pinokio/logs/` | Logs de ejecución |

### Acceso al Disco del Usuario

Para acceder a archivos fuera del directorio del plugin:

```javascript
// En un script de Pinokio
{
  method: "input",
  params: {
    title: "Seleccionar Directorio",
    type: "filepicker",
    description: "Selecciona la carpeta donde guardar los datos"
  }
}
```

### Persistencia de Datos

```javascript
// Guardar configuración
{
  method: "json.set",
  params: {
    path: "data/config.json",
    data: {
      "agents": "{{local.agents}}",
      "lastUpdated": "{{new Date().toISOString()}}"
    }
  }
}

// Leer configuración
{
  method: "json.get",
  params: {
    path: "data/config.json"
  }
}
```

---

## 6. Ciclo de Vida del Plugin {#lifecycle}

```
Usuario hace click en "Instalar"
         ↓
    install.js ejecuta
    (instala dependencias, Ollama, modelos)
         ↓
    Instalación completa
         ↓
Usuario hace click en "Iniciar"
         ↓
    start.js ejecuta como daemon
    (inicia servidor backend + frontend)
         ↓
    Plugin en ejecución
    (UI disponible en localhost:PORT)
         ↓
Usuario hace click en "Detener"
         ↓
    stop.js ejecuta
    (detiene procesos gracefully)
```

### Variables de Entorno Disponibles

| Variable | Descripción |
|----------|-------------|
| `{{cwd}}` | Directorio actual del plugin |
| `{{port}}` | Puerto asignado automáticamente |
| `{{platform}}` | Sistema operativo (darwin/win32/linux) |
| `{{arch}}` | Arquitectura (x64/arm64) |
| `{{gpu}}` | GPU disponible |
| `{{ram}}` | RAM disponible |
| `{{vram}}` | VRAM disponible |
