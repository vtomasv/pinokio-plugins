# Guía de Solución de Problemas

Esta guía cubre los errores más frecuentes al desarrollar plugins para Pinokio, con soluciones validadas en producción.

---

## Error 1: `TypeError: Cannot read properties of null` en shells.js

**Causa**: El uso de `background: true` en los scripts de ciclo de vida, que no existe en la API de Pinokio.

**Solución**: Reemplazar `background: true` por redirección de output en el comando shell:

```json
// ❌ Incorrecto
{ "message": "ollama serve", "background": true }

// ✅ Correcto
{ "message": "ollama serve > /dev/null 2>&1 &" }
```

---

## Error 2: El Plugin No Aparece en Pinokio

**Causa**: El archivo `pinokio.js` no existe, tiene errores de sintaxis, o el directorio no está en la ubicación correcta.

**Diagnóstico**:
```bash
# Verificar que el directorio existe
ls ~/pinokio/api/nombre-plugin/

# Verificar que pinokio.js es válido
node -e "require('./pinokio.js')"
```

**Solución**: Asegurarse de que `pinokio.js` exporte un objeto con al menos `title`, `icon` y `menu`.

---

## Error 3: Scripts `.js` en Lugar de `.json`

**Causa**: Los archivos `install.json`, `start.json` y `stop.json` se crearon como módulos JavaScript en lugar de JSON puro.

**Diagnóstico**:
```bash
# Verificar que son JSON válidos
python3 -c "import json; json.load(open('install.json'))"
```

**Solución**: Convertir el contenido a JSON puro. Solo `pinokio.js` puede ser `.js`.

---

## Error 4: Funciones JavaScript No Accesibles desde `onclick`

**Causa**: Las funciones están definidas dentro de `DOMContentLoaded` o usando `const`/`let`, lo que las hace inaccesibles desde atributos HTML `onclick`.

**Diagnóstico**: Abrir la consola del navegador y verificar si aparece `ReferenceError: functionName is not defined`.

**Solución**:
```javascript
// ❌ Incorrecto — función no accesible desde onclick
document.addEventListener('DOMContentLoaded', () => {
  function enviarMensaje() { ... }
});

// ✅ Correcto — función en scope global
function enviarMensaje() { ... }

// Inicializar al final del script
init();
```

---

## Error 5: Nombre del Venv Inconsistente

**Causa**: El nombre del entorno virtual es diferente en `install.json`, `start.json` y `pinokio.js`.

**Diagnóstico**:
```bash
grep -r "venv" install.json start.json pinokio.js
```

**Solución**: Usar siempre el nombre `venv` en todos los archivos.

---

## Error 6: Rutas Relativas en el Servidor Python

**Causa**: El servidor Python usa rutas relativas que fallan cuando se ejecuta desde un directorio diferente.

**Diagnóstico**: El servidor arranca pero no encuentra los archivos estáticos o de datos.

**Solución**:
```python
# ❌ Incorrecto
app.mount("/", StaticFiles(directory="app"), name="static")

# ✅ Correcto
BASE_DIR = Path(__file__).parent.parent.resolve()
app.mount("/", StaticFiles(directory=str(BASE_DIR / "app")), name="static")
```

---

## Error 7: Acentos y Caracteres Especiales Rotos en Windows

**Causa**: La librería `requests` detecta el encoding como `latin-1` en Windows, corrompiendo caracteres UTF-8 como ñ, tildes y caracteres especiales.

**Solución**:
```python
def _fix_encoding(text: str) -> str:
    """Repara texto UTF-8 mal interpretado como latin-1."""
    try:
        return text.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text

# Al llamar a Ollama:
response.encoding = "utf-8"
content = _fix_encoding(response.json()["message"]["content"])
```

---

## Error 8: Timeout al Generar Contenido Largo

**Causa**: Las operaciones largas (generación de campañas, análisis extensos) bloquean el HTTP request y el navegador muestra un error de timeout.

**Solución**: Usar `BackgroundTasks` de FastAPI y polling desde el frontend:

```python
# Backend: retorna inmediatamente
@app.post("/api/campaigns/generate")
async def generate_campaign(request: CampaignRequest, background_tasks: BackgroundTasks):
    campaign_id = str(uuid.uuid4())
    background_tasks.add_task(_generate_in_background, campaign_id, request)
    return {"status": "generating", "campaign_id": campaign_id}

# Frontend: polling cada 3 segundos
function checkProgress(campaignId) {
    fetch('/api/campaigns/' + campaignId + '/progress')
        .then(r => r.json())
        .then(data => {
            if (data.status !== 'done') {
                setTimeout(function() { checkProgress(campaignId); }, 3000);
            } else {
                showResult(data);
            }
        });
}
```

---

## Error 9: El Modelo Ollama No Está Disponible

**Causa**: El modelo especificado no está descargado en el sistema local.

**Diagnóstico**:
```bash
ollama list
```

**Solución**: Descargar el modelo manualmente o implementar descarga automática en background (ver `skill/SKILL.md` — sección "Descarga Automática de Modelos").

---

## Error 10: El LLM Devuelve JSON en Lugar de Texto

**Causa**: El LLM a veces devuelve el JSON completo de la respuesta en lugar del texto del campo solicitado.

**Solución**: Usar las funciones de sanitización incluidas en el skill:

```python
def _sanitize_post_text(text: str, fallback: str = "") -> str:
    """Detecta si el texto contiene JSON crudo y lo reemplaza."""
    if not text:
        return fallback
    stripped = text.strip()
    if stripped.startswith("{") or '"stages"' in stripped:
        return fallback
    return stripped
```

---

## Herramienta de Diagnóstico Automático

Para detectar múltiples problemas a la vez, ejecuta el validador incluido:

```bash
python tests/validate_plugin.py ruta/a/tu/plugin/
```

El validador verifica las 10 reglas críticas y genera un reporte detallado con las correcciones necesarias.
