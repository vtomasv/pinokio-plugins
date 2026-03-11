# Guía de Contribución

Gracias por tu interés en contribuir al proyecto **Pinokio Plugin Developer**. Este documento describe cómo participar de manera efectiva.

---

## Código de Conducta

Este proyecto adopta un entorno colaborativo y respetuoso. Se espera que todos los contribuidores mantengan un trato profesional y constructivo en todas las interacciones.

---

## ¿Cómo Contribuir?

### Reportar Errores

Si encuentras un error en los templates, scripts o documentación:

1. Verifica que el error no haya sido reportado ya en [Issues](../../issues).
2. Abre un nuevo issue con el título descriptivo: `[BUG] Descripción breve`.
3. Incluye: sistema operativo, versión de Pinokio, pasos para reproducir el error y el comportamiento esperado vs. el actual.

### Proponer Mejoras

Para proponer nuevas funcionalidades o mejoras:

1. Abre un issue con el título: `[FEATURE] Descripción breve`.
2. Describe el caso de uso, el beneficio esperado y cualquier consideración técnica relevante.

### Contribuir con Código

#### Configuración del Entorno

```bash
# Clonar el repositorio
git clone https://github.com/TU_USUARIO/pinokio-plugins.git
cd pinokio-plugins

# Instalar dependencias de desarrollo
pip3 install pytest requests fastapi uvicorn

# Verificar que los tests pasan
python -m pytest tests/ -v
```

#### Flujo de Trabajo

1. Crea una rama desde `main` con un nombre descriptivo:
   ```bash
   git checkout -b feature/nuevo-template-marketing
   ```

2. Realiza tus cambios siguiendo los estándares del proyecto (ver sección siguiente).

3. Ejecuta el validador antes de hacer commit:
   ```bash
   python tests/validate_plugin.py examples/tu-nuevo-ejemplo/
   ```

4. Ejecuta los tests:
   ```bash
   python -m pytest tests/ -v
   ```

5. Haz commit con mensajes descriptivos en español o inglés:
   ```bash
   git commit -m "feat: agregar template para plugin de inventario"
   ```

6. Abre un Pull Request describiendo los cambios realizados.

---

## Estándares de Código

### Reglas Obligatorias para Plugins Pinokio

Todos los plugins y templates deben cumplir estas reglas, validadas automáticamente:

| Regla | Descripción |
|-------|-------------|
| Scripts `.json` | `install.json`, `start.json`, `stop.json` deben ser JSON puros |
| `pinokio.js` correcto | Solo apunta a archivos `.json`, no `.js` |
| Sin `background: true` | No existe en la API de Pinokio; usar redirección de output |
| Venv consistente | Siempre usar el nombre `venv` |
| Rutas absolutas | El servidor Python usa `Path(__file__).parent.parent.resolve()` |
| UTF-8 garantizado | `ensure_ascii=False` en `json.dumps`, `response.encoding = "utf-8"` |
| JavaScript global | Sin `let`/`const`/`import`/`export` en `app/index.html` |
| Operaciones largas | Usar `BackgroundTasks` de FastAPI + polling desde frontend |

### Estilo de Código Python

- Seguir PEP 8 para el código Python.
- Documentar todas las funciones con docstrings en español.
- Usar type hints en las firmas de funciones.
- Manejar excepciones de manera explícita; nunca usar `except: pass`.

### Estilo de Código JavaScript (Frontend)

- Usar `var` en lugar de `let`/`const` para compatibilidad con el webview de Electron/Pinokio.
- Definir todas las funciones en scope global, no dentro de `DOMContentLoaded`.
- Llamar a la función de inicialización al final del script, no en `DOMContentLoaded`.

---

## Estructura de un Nuevo Ejemplo

Si contribuyes con un nuevo plugin de ejemplo, debe incluir:

```
examples/nombre-plugin/
├── pinokio.js          # Menú dinámico
├── icon.png            # Icono 512x512 (PNG)
├── install.json        # Instalación 1-click
├── start.json          # Inicio del servidor
├── stop.json           # Parada del servidor
├── requirements.txt    # Dependencias Python
├── app/
│   └── index.html      # UI autocontenida
├── server/
│   └── app.py          # Backend FastAPI
├── defaults/
│   └── agents.json     # Configuración inicial de agentes
└── README.md           # Documentación del ejemplo
```

---

## Proceso de Revisión

Los Pull Requests son revisados considerando:

- Cumplimiento del checklist de validación (ejecutado automáticamente por CI).
- Calidad y claridad del código.
- Documentación adecuada.
- Compatibilidad cross-platform (Windows/macOS/Linux).
- Experiencia de usuario para personas sin conocimientos técnicos.

---

## Reconocimientos

Los contribuidores son listados en el archivo [CHANGELOG.md](CHANGELOG.md) junto con sus contribuciones.
