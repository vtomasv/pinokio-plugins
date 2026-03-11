# Lecciones de Producción — css-brand-assistant

Problemas reales encontrados y soluciones validadas durante el desarrollo del plugin de marketing para PYMEs.

---

## 1. Timeouts de Ollama

### Problema
El timeout de 120 s era insuficiente para generar campañas completas (90+ publicaciones en 3 canales). Error: `HTTPConnectionPool: Read timed out`.

### Solución
Timeouts diferenciados y configurables en 3 niveles de precedencia:

```
config.json  >  variable de entorno  >  valor por defecto del código
```

```python
TIMEOUT_MAP = {
    "default": ("OLLAMA_TIMEOUT", 300),
    "campaign": ("OLLAMA_TIMEOUT_CAMPAIGN", 600),
    "adn": ("OLLAMA_TIMEOUT_ADN", 300),
}

def get_ollama_timeout(task_type: str = "default") -> int:
    config = load_json(DATA_DIR / "config.json", {})
    env_key, default = TIMEOUT_MAP.get(task_type, ("OLLAMA_TIMEOUT", 300))
    config_key = f"ollama_timeout_{task_type}" if task_type != "default" else "ollama_timeout"
    return int(config.get(config_key) or os.getenv(env_key) or default)
```

---

## 2. Caracteres Especiales en Windows

### Problema
Acentos y ñ aparecían como `Ã¡`, `Ã±`, etc. en Windows. La librería `requests` detectaba el encoding de la respuesta HTTP como `latin-1`.

### Solución (doble capa)

```python
def _fix_encoding(text: str) -> str:
    """Repara texto UTF-8 mal interpretado como latin-1."""
    try:
        return text.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text

def call_ollama(...):
    resp = requests.post(...)
    resp.encoding = "utf-8"          # Capa 1: forzar encoding en la respuesta
    content = resp.json()["message"]["content"]
    return _fix_encoding(content)    # Capa 2: reparar si ya llegó mal
```

También aplicar en todos los `json.dumps`:
```python
json.dumps(data, indent=2, ensure_ascii=False)  # Preserva ñ, tildes, etc.
```

---

## 3. JSON Crudo en el Texto del Post

### Problema
En Windows con modelos pequeños, el LLM devolvía el JSON completo de la campaña como texto del post:
```
[Publicación 1 — Instagram]
```json
{"stages": [...], "publications": [...]}
```

### Causa
El parser anterior usaba `re.search(r'\{.*\}', text, re.DOTALL)` que es greedy y capturaba el JSON completo.

### Solución

```python
def _extract_json_from_llm(text: str) -> dict | None:
    # Estrategia 1: strip de bloques ```json
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
            if escape: escape = False; continue
            if ch == "\\" and in_str: escape = True; continue
            if ch == '"': in_str = not in_str; continue
            if not in_str:
                if ch == "{": depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        try: return json.loads(text[start:i+1])
                        except: break
    return None

def _sanitize_post_text(text: str, fallback: str = "") -> str:
    """Detecta si el texto del post contiene JSON crudo."""
    if not text: return fallback
    stripped = text.strip()
    if stripped.startswith("{") or '"stages"' in stripped or '"publications"' in stripped:
        return fallback
    return stripped
```

---

## 4. Generación Incompleta de Publicaciones

### Problema
Al pedir 90 publicaciones en una sola llamada al LLM, el contexto se saturaba y la respuesta quedaba truncada después de 15-20 publicaciones.

### Solución: Generación en Lotes

```python
MAX_PUBS_PER_BATCH = 5

async def _generate_campaign_plan(campaign_id, campaign_data, adn):
    # Paso 1: estructura de etapas (1 llamada)
    stages = await _generate_stages(campaign_data, adn)

    # Paso 2: calendario de slots (sin LLM)
    slots = _build_slots_calendar(campaign_data, stages)

    # Paso 3: publicaciones en lotes de 5
    publications = []
    batches = [slots[i:i+MAX_PUBS_PER_BATCH] for i in range(0, len(slots), MAX_PUBS_PER_BATCH)]
    for idx, batch in enumerate(batches):
        batch_pubs = await _generate_batch(batch, campaign_data, adn)
        publications.extend(batch_pubs)
        # Guardar progreso por canal después de cada lote
        _save_progress(campaign_id, {
            "publications_done": len(publications),
            "publications_total": len(slots),
            "pct": int(len(publications) / len(slots) * 100),
            "channels": _count_by_channel(publications, slots)
        })
```

---

## 5. Generación de Imágenes en Windows

### Problema
Ollama no soporta generación de imágenes en Windows (limitación upstream del proyecto). Error: `500 Internal Server Error` al usar `x/z-image-turbo`.

### Solución: Cascada de 4 Proveedores

```python
async def generate_image(prompt: str, model: str = "embedded") -> dict:
    # 1. Motor embebido (Diffusers + LCM) — funciona en todos los SO
    if model in ("embedded", "auto"):
        result = await _try_embedded_engine(prompt)
        if result: return result

    # 2. Ollama — solo macOS/Linux
    if _is_ollama_image_model(model):
        try:
            result = await _try_ollama_image(prompt, model)
            if result: return result
        except Exception:
            pass  # Silenciar error 500 de Windows

    # 3. AUTOMATIC1111 (si está corriendo con --api)
    result = await _try_a1111(prompt)
    if result: return result

    # 4. Placeholder SVG profesional (siempre disponible)
    return _generate_placeholder_svg(prompt)
```

**Placeholder SVG**: incluye el prompt como texto de referencia, ícono de cámara, y nota "IMAGEN PENDIENTE". El usuario puede reemplazarla cargando desde disco.

---

## 6. Descarga Automática de Modelos

### Problema
Si el usuario cambia el modelo de un agente a uno no descargado, el agente falla con 404 al intentar usarlo.

### Solución: Verificar y Descargar al Guardar

```python
@app.put("/api/agents/{agent_id}")
async def update_agent(agent_id: str, config: AgentConfigUpdate):
    saved = _save_agent_config(agent_id, config)
    if config.model and not _is_model_available(config.model):
        _start_pull_background(config.model)
        return {**saved, "pull_status": {"status": "queued", "model": config.model}}
    return saved
```

El frontend inicia polling de descarga cuando recibe `pull_status` en la respuesta:
```javascript
function saveAgentPrompt(agentId) {
  fetch(apiUrl('/agents/' + agentId), { method: 'PUT', body: JSON.stringify(payload) })
    .then(r => r.json())
    .then(function(data) {
      if (data.pull_status && data.pull_status.status !== 'done') {
        showNotification('Descargando modelo ' + data.pull_status.model + '...', 'info');
        _startPullPolling(agentId, data.pull_status.model);
      } else {
        showNotification('Agente actualizado', 'success');
      }
    });
}
```

---

## 7. Generación en Background con Progreso por Canal

### Patrón completo

**Backend**:
```python
@app.post("/api/campaigns", status_code=201)
async def create_campaign(data: CampaignCreate, background_tasks: BackgroundTasks):
    campaign = _init_campaign(data)
    campaign["status"] = "generating"
    save_json(campaign_file, campaign)
    background_tasks.add_task(_generate_campaign_plan, campaign["id"], data)
    return campaign  # Retorna inmediatamente

@app.get("/api/campaigns/{id}/progress")
def get_progress(id: str):
    camp = load_json(campaign_file)
    prog = camp.get("generation_progress", {})
    return {
        "status": camp["status"],
        "pct": prog.get("pct", 0),
        "channels": prog.get("channels", []),  # [{channel, done, total, pct}]
    }
```

**Frontend**:
```javascript
// Polling cada 3s — actualiza el DOM directamente sin recargar la lista
function _pollCampaignProgress(campaignId) {
  var interval = setInterval(function() {
    fetch(apiUrl('/campaigns/' + campaignId + '/progress'))
      .then(r => r.json())
      .then(function(prog) {
        _updateCampaignCardProgress(campaignId, prog);
        if (prog.status !== 'generating') {
          clearInterval(interval);
          reloadCampaigns();
        }
      });
  }, 3000);
}

function _updateCampaignCardProgress(campaignId, prog) {
  var card = document.querySelector('[data-campaign-id="' + campaignId + '"]');
  if (!card) return;
  var area = card.querySelector('.campaign-progress-area');
  if (!area) return;

  var html = '<div style="font-size:11px;margin-bottom:4px">' +
    'Generando ' + prog.publications_done + '/' + prog.publications_total +
    ' publicaciones (' + prog.pct + '%)</div>';
  html += '<div style="background:#1e293b;border-radius:4px;height:6px;margin-bottom:8px">' +
    '<div style="background:#6366f1;height:6px;border-radius:4px;width:' + prog.pct + '%"></div></div>';

  // Barras por canal
  (prog.channels || []).forEach(function(ch) {
    var color = ch.pct >= 100 ? '#22c55e' : '#6366f1';
    html += '<div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">' +
      '<span style="font-size:10px;min-width:70px">' + ch.channel + '</span>' +
      '<div style="flex:1;background:#1e293b;border-radius:3px;height:4px">' +
      '<div style="background:' + color + ';height:4px;border-radius:3px;width:' + ch.pct + '%"></div></div>' +
      '<span style="font-size:10px;color:#94a3b8">' + ch.done + '/' + ch.total + '</span>' +
      '</div>';
  });
  area.innerHTML = html;
}
```

---

## 8. Widget de Generación — Texto e Imagen Separados

### Problema
El widget original mezclaba texto e imagen en un único panel con un selector "¿Qué generar?", lo que obligaba al usuario a hacer scroll y seleccionar antes de generar.

### Solución: Dos Paneles Independientes

```javascript
// Panel Texto (azul) — tiene su propio botón
html += '<div style="border:1px solid rgba(99,102,241,0.4);border-radius:10px;padding:12px">';
html += '<div>💬 Texto del post</div>';
html += '<select id="editTextModel">...</select>';  // Modelo Ollama
html += '<select id="editGenLanguage">...</select>';
html += '<input id="editGenInstruction" />';
html += '<button onclick="generateTextWithAI(\'' + pubId + '\')">💬 Generar texto</button>';
html += '</div>';

// Panel Imagen (violeta) — tiene su propio botón
html += '<div style="border:1px solid rgba(168,85,247,0.4);border-radius:10px;padding:12px">';
html += '<div>🖼️ Imagen del post</div>';
html += '<select id="editImageModel">...</select>';  // Motor embebido / Ollama / A1111
html += '<textarea id="editPubImagePromptInline">...</textarea>';  // Prompt editable aquí
html += '<button onclick="generateImageWithAI(\'' + pubId + '\')">🖼️ Generar imagen</button>';
html += '<label>📂 Cargar desde disco<input type="file" .../></label>';
html += '</div>';
```

Funciones separadas para cada tipo:
```javascript
function generateTextWithAI(pubId) { /* llama a /regenerate */ }
function generateImageWithAI(pubId) { /* llama a /generate-image */ }
```
