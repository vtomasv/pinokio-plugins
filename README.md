# Pinokio Plugin Developer — Skill para Manus

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Pinokio Compatible](https://img.shields.io/badge/Pinokio-Compatible-6366f1)](https://pinokio.computer)
[![Manus Skill](https://img.shields.io/badge/Manus-Skill-22c55e)](https://manus.im)

**Skill especializada para Manus** que permite crear plugins completos para [Pinokio](https://pinokio.computer) — la plataforma "Localhost Cloud" que ejecuta IA y aplicaciones 100% localmente en la PC del usuario, sin conexión a internet.

---

## ¿Qué es este repositorio?

Este repositorio contiene el **Skill `pinokio-plugin-dev`** para el agente Manus, junto con:

- **Documentación técnica completa** sobre la arquitectura de plugins Pinokio
- **Templates listos para usar** (pinokio.js, install.json, server FastAPI, UI HTML)
- **Ejemplos de plugins funcionales** para casos de uso reales de PYMEs
- **Herramientas de testing y validación** para garantizar calidad antes de publicar
- **Guías de referencia** sobre patrones validados en producción

---

## Estructura del Repositorio

```
pinokio-plugins/
├── skill/                          # Skill completo para Manus
│   ├── SKILL.md                    # Instrucciones principales del skill
│   ├── templates/                  # Templates listos para usar
│   │   ├── pinokio-js-template.js
│   │   ├── install-json-template.json
│   │   ├── start-json-template.json
│   │   ├── stop-json-template.json
│   │   ├── server-app-template.py
│   │   ├── index-html-template.html
│   │   └── agent-config-template.json
│   ├── references/                 # Documentación técnica detallada
│   │   ├── production-lessons.md
│   │   ├── plugin-architecture.md
│   │   ├── agent-orchestration.md
│   │   ├── ui-patterns.md
│   │   └── one-click-setup.md
│   └── scripts/
│       └── create_plugin.py        # Generador de estructura base
├── examples/                       # Plugins de ejemplo funcionales
│   ├── hello-world-plugin/         # Plugin mínimo para aprender
│   ├── pyme-marketing-plugin/      # Asistente de marketing con IA
│   └── expense-classifier-plugin/  # Clasificador de gastos
├── tests/                          # Herramientas de testing y validación
│   ├── validate_plugin.py          # Validador de estructura y reglas
│   ├── test_ollama_connection.py   # Test de conexión con Ollama
│   └── test_api_endpoints.py       # Test de endpoints FastAPI
├── docs/                           # Documentación adicional
│   ├── GETTING_STARTED.md
│   ├── ARCHITECTURE.md
│   └── TROUBLESHOOTING.md
├── .github/
│   └── workflows/
│       └── validate.yml            # CI: validación automática
├── CONTRIBUTING.md
├── CHANGELOG.md
└── LICENSE
```

---

## Instalación del Skill en Manus

Para usar este skill en tu agente Manus, copia el directorio `skill/` a la carpeta de skills de Manus:

```bash
# Clonar el repositorio
git clone https://github.com/vtomasv/pinokio-plugins.git

# Copiar el skill a Manus
cp -r pinokio-plugins/skill ~/skills/pinokio-plugin-dev
```

Una vez instalado, Manus detectará automáticamente el skill y lo usará cuando le pidas crear plugins para Pinokio.

---

## Inicio Rápido: Crear tu Primer Plugin

### 1. Generar la estructura base

```bash
python skill/scripts/create_plugin.py mi-plugin --output-dir ~/pinokio/api/
```

Esto crea la estructura completa del plugin en `~/pinokio/api/mi-plugin/`.

### 2. Personalizar el plugin

Edita los archivos generados siguiendo los templates en `skill/templates/`:

| Archivo | Propósito |
|---------|-----------|
| `pinokio.js` | Menú dinámico y configuración del plugin |
| `install.json` | Instalación automática con 1 click |
| `start.json` | Inicio del servidor backend |
| `stop.json` | Parada del servidor |
| `server/app.py` | Backend FastAPI con rutas a Ollama |
| `app/index.html` | Interfaz de usuario autocontenida |

### 3. Validar antes de publicar

```bash
python tests/validate_plugin.py ~/pinokio/api/mi-plugin/
```

---

## Ejemplos Incluidos

### Hello World Plugin

Plugin mínimo que demuestra la estructura básica. Ideal para aprender la arquitectura de Pinokio.

```
examples/hello-world-plugin/
```

### PYME Marketing Assistant

Plugin completo de asistente de marketing para PYMEs con generación de contenido, planificación de posts y análisis de audiencia usando modelos Ollama locales.

```
examples/pyme-marketing-plugin/
```

### Expense Classifier

Plugin para clasificación automática de gastos empresariales usando IA local, con visualizaciones de gráficos y exportación de reportes.

```
examples/expense-classifier-plugin/
```

---

## Arquitectura de un Plugin Pinokio

Todo plugin Pinokio sigue esta estructura de archivos:

```
~/pinokio/api/nombre-plugin/
├── pinokio.js      # Configuración y menú (ÚNICO archivo .js permitido)
├── icon.png        # Icono 512x512 (REQUERIDO)
├── install.json    # Instalación automática (JSON puro)
├── start.json      # Inicio del servidor (JSON puro)
├── stop.json       # Parada del servidor (JSON puro)
├── requirements.txt
├── app/index.html  # Frontend autocontenido
├── server/app.py   # Backend FastAPI
└── data/           # Datos persistentes (nunca en git)
```

> **Regla crítica**: Solo `pinokio.js` puede ser `.js`. Los archivos `install.json`, `start.json` y `stop.json` deben ser **JSON puros**, nunca módulos JavaScript.

---

## Modelos de IA Soportados (Ollama)

| Modelo | RAM Mínima | Uso Ideal |
|--------|-----------|-----------|
| `llama3.2:1b` | 2 GB | Clasificación, tareas simples |
| `llama3.2:3b` | 4 GB | Uso general, PYMEs |
| `llama3.1:8b` | 8 GB | Análisis complejo, generación larga |
| `qwen2.5:7b` | 8 GB | Multilingüe, español optimizado |

El skill incluye selección automática de modelo según la RAM disponible del sistema.

---

## Compatibilidad

| Sistema Operativo | Estado |
|-------------------|--------|
| Windows 10/11 | Soportado |
| macOS 12+ | Soportado |
| Linux (Ubuntu 20.04+) | Soportado |

---

## Contribuir

Lee [CONTRIBUTING.md](CONTRIBUTING.md) para conocer cómo contribuir con nuevos templates, ejemplos o correcciones.

---

## Licencia

MIT License — ver [LICENSE](LICENSE) para más detalles.

---

## Créditos

Desarrollado como parte del proyecto **CCS — Plugins para Pinokio**, con el objetivo de democratizar el acceso a la inteligencia artificial offline para PYMEs.
