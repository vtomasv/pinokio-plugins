# Hello World Plugin

Plugin mínimo de ejemplo para aprender la arquitectura de Pinokio. Implementa un chat básico con modelos Ollama locales.

## Estructura

```
hello-world-plugin/
├── pinokio.js          # Menú dinámico (instalado/corriendo/detenido)
├── install.json        # Instalación: venv + requirements + modelo Ollama
├── start.json          # Inicio del servidor FastAPI en modo daemon
├── stop.json           # Parada del servidor
├── requirements.txt    # fastapi, uvicorn, requests
├── app/
│   └── index.html      # Chat UI autocontenida
└── server/
    └── app.py          # Backend FastAPI con endpoints /api/chat y /api/models
```

## Qué Demuestra

Este ejemplo muestra los patrones fundamentales de un plugin Pinokio:

**Ciclo de vida correcto**: `install.json`, `start.json` y `stop.json` son JSON puros (no JavaScript). Solo `pinokio.js` es `.js`.

**Selección automática de modelo**: `install.json` descarga el modelo Ollama más adecuado según la RAM del sistema usando la variable `{{ram}}` de Pinokio.

**Rutas absolutas en Python**: El servidor usa `Path(__file__).parent.parent.resolve()` para todas las rutas, garantizando compatibilidad cross-platform.

**JavaScript compatible con Pinokio**: La UI usa `var` en lugar de `let`/`const`, define todas las funciones en scope global y llama a `init()` al final del script.

**Encoding UTF-8**: El servidor fuerza `response.encoding = "utf-8"` y usa `_fix_encoding()` para compatibilidad con Windows.

## Instalación

1. Copia este directorio a `~/pinokio/api/hello-world-plugin/`.
2. Abre Pinokio y haz clic en "Instalar".
3. Una vez instalado, haz clic en "Iniciar".

## Personalización

Para crear tu propio plugin basado en este ejemplo:

1. Cambia `title` y `description` en `pinokio.js`.
2. Agrega tus dependencias Python en `requirements.txt`.
3. Implementa tus endpoints en `server/app.py`.
4. Actualiza la UI en `app/index.html`.
