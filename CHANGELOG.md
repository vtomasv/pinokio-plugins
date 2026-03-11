# Changelog

Todos los cambios notables de este proyecto se documentan en este archivo.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es/1.0.0/), y el proyecto adhiere a [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] — 2026-03-11

### Añadido

- Skill completo `pinokio-plugin-dev` para Manus con documentación técnica exhaustiva.
- Templates listos para usar: `pinokio.js`, `install.json`, `start.json`, `stop.json`, `server/app.py`, `app/index.html`, `agents.json`.
- Script generador de estructura base `create_plugin.py`.
- Documentación de referencia en 5 archivos:
  - `production-lessons.md` — Problemas reales y soluciones validadas en producción.
  - `plugin-architecture.md` — Estructura completa y ciclo de vida de plugins.
  - `agent-orchestration.md` — Patrones multi-agente con Ollama.
  - `ui-patterns.md` — Componentes HTML/CSS/JS para usuarios sin experiencia técnica.
  - `one-click-setup.md` — Flujo de instalación y publicación.
- Ejemplo `hello-world-plugin` — Plugin mínimo para aprender la arquitectura.
- Ejemplo `pyme-marketing-plugin` — Asistente de marketing con IA local para PYMEs.
- Ejemplo `expense-classifier-plugin` — Clasificador de gastos con visualizaciones.
- Herramientas de testing:
  - `validate_plugin.py` — Validador de estructura y reglas Pinokio.
  - `test_ollama_connection.py` — Test de conexión y disponibilidad de modelos.
  - `test_api_endpoints.py` — Test de endpoints FastAPI.
- Workflow de CI/CD con GitHub Actions para validación automática.
- Documentación adicional: `GETTING_STARTED.md`, `ARCHITECTURE.md`, `TROUBLESHOOTING.md`.

### Patrones Validados en Producción

- Selección automática de modelo según RAM disponible del sistema.
- Parser robusto de JSON del LLM con 3 estrategias de extracción.
- Timeouts configurables por tipo de tarea (chat: 300s, campaña: 600s, descarga: 3600s).
- Descarga automática de modelos Ollama en background con tracking de progreso.
- Generación de contenido por lotes (máximo 5 ítems por llamada al LLM).
- Corrección de encoding UTF-8/latin-1 para compatibilidad con Windows.
- Motor de generación de imágenes con cascada de proveedores (Diffusers → Ollama → A1111 → ComfyUI → SVG placeholder).
