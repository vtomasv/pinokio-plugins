# Herramientas de Testing y Validación

Este directorio contiene las herramientas para verificar la calidad y corrección de los plugins Pinokio antes de publicarlos.

---

## Herramientas Disponibles

### `validate_plugin.py` — Validador de Estructura

Verifica las 10 reglas críticas que todo plugin Pinokio debe cumplir.

```bash
# Validar un plugin
python tests/validate_plugin.py examples/hello-world-plugin/

# Salida en formato JSON (para integración con CI)
python tests/validate_plugin.py examples/hello-world-plugin/ --json

# Modo estricto (advertencias como errores)
python tests/validate_plugin.py examples/hello-world-plugin/ --strict
```

Las 10 reglas verificadas son:

| # | Regla | Descripción |
|---|-------|-------------|
| 1 | Scripts JSON puros | `install.json`, `start.json`, `stop.json` son JSON válidos |
| 2 | `pinokio.js` apunta a `.json` | No hay referencias a archivos `.js` en `href` |
| 3 | Sin `background: true` | No existe en la API de Pinokio |
| 4 | Venv consistente | Nombre `venv` en todos los archivos |
| 5 | Rutas absolutas | `server/app.py` usa `Path(__file__)` |
| 6 | `ensure_ascii=False` | En todos los `json.dumps` |
| 7 | Encoding UTF-8 | `response.encoding = "utf-8"` en llamadas a Ollama |
| 8 | Sin ES6+ en HTML | Sin `let`/`const`/`import`/`export` en la UI |
| 9 | `BackgroundTasks` | Operaciones largas no bloquean el HTTP request |
| 10 | `pinokio.js` completo | Define `title`, `icon` y `menu` |

### `test_ollama_connection.py` — Diagnóstico de Ollama

Verifica que Ollama esté corriendo y que los modelos necesarios estén disponibles.

```bash
# Diagnóstico completo
python tests/test_ollama_connection.py

# Con URL personalizada
python tests/test_ollama_connection.py --url http://localhost:11434

# Probar inferencia con un modelo específico
python tests/test_ollama_connection.py --model llama3.2:3b

# Ejecutar tests unitarios con mocks (no requiere Ollama)
python tests/test_ollama_connection.py --unit-tests
```

### `test_api_endpoints.py` — Tests de Endpoints FastAPI

Tests unitarios para los endpoints de la API del plugin, usando mocks para simular Ollama.

```bash
# Ejecutar con pytest (recomendado)
python -m pytest tests/test_api_endpoints.py -v

# Ejecutar directamente
python tests/test_api_endpoints.py
```

Los tests cubren:

- Endpoint `/api/health` — respuesta correcta
- Endpoint `/api/chat` — integración con Ollama, manejo de errores
- Endpoint `/api/models` — listado de modelos disponibles
- Manejo de encoding UTF-8 (bug de Windows)
- Parser robusto de JSON del LLM (3 estrategias)

---

## Ejecutar Todos los Tests

```bash
# Instalar dependencias de testing
pip install pytest requests

# Ejecutar todos los tests
python -m pytest tests/ -v

# Con reporte de cobertura
pip install pytest-cov
python -m pytest tests/ -v --cov=examples --cov-report=term-missing
```

---

## Integración con CI/CD

El repositorio incluye un workflow de GitHub Actions (`.github/workflows/validate.yml`) que ejecuta automáticamente:

1. El validador de estructura sobre todos los ejemplos.
2. Los tests unitarios de endpoints.
3. Los tests unitarios de conexión con Ollama (con mocks).

Los tests se ejecutan en cada Pull Request y push a `main`.
