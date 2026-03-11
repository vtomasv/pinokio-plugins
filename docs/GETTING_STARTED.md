# Guía de Inicio Rápido

Esta guía te lleva desde cero hasta tener tu primer plugin Pinokio funcionando en menos de 15 minutos.

---

## Prerrequisitos

Antes de comenzar, asegúrate de tener instalado:

| Software | Versión Mínima | Descarga |
|----------|---------------|---------|
| [Pinokio](https://pinokio.computer) | 2.0+ | https://pinokio.computer |
| [Ollama](https://ollama.ai) | 0.3+ | https://ollama.ai |
| Python | 3.9+ | https://python.org |
| Git | 2.30+ | https://git-scm.com |

Pinokio incluye su propio entorno Python, pero necesitas Python instalado en el sistema para ejecutar los scripts de generación y testing de este repositorio.

---

## Paso 1: Clonar el Repositorio

```bash
git clone https://github.com/vtomasv/pinokio-plugins.git
cd pinokio-plugins
```

---

## Paso 2: Instalar el Skill en Manus (Opcional)

Si usas Manus como agente de desarrollo, instala el skill para que Manus pueda crear plugins automáticamente:

```bash
cp -r skill/ ~/skills/pinokio-plugin-dev
```

A partir de este momento, cuando le pidas a Manus "crea un plugin para Pinokio que haga X", utilizará automáticamente este skill con todos los patrones validados en producción.

---

## Paso 3: Crear tu Primer Plugin

### Opción A: Usando el Generador Automático

```bash
python skill/scripts/create_plugin.py mi-primer-plugin --output-dir ~/pinokio/api/
```

El script genera la estructura completa con todos los archivos necesarios. Luego personaliza cada archivo según las instrucciones en los comentarios.

### Opción B: Copiando un Ejemplo

```bash
cp -r examples/hello-world-plugin/ ~/pinokio/api/mi-primer-plugin/
```

El ejemplo `hello-world-plugin` es el punto de partida más simple. Tiene todos los archivos correctamente configurados y comentados.

---

## Paso 4: Personalizar el Plugin

Los archivos que debes editar, en orden de importancia:

**`pinokio.js`** — Define el título, icono y menú del plugin. Este es el archivo que Pinokio lee para mostrar tu plugin en la interfaz.

**`install.json`** — Define qué se instala al hacer clic en "Instalar". Incluye la creación del entorno virtual Python, instalación de dependencias y descarga del modelo Ollama.

**`server/app.py`** — El backend FastAPI. Aquí defines los endpoints que usa tu interfaz de usuario para comunicarse con Ollama.

**`app/index.html`** — La interfaz de usuario. Es un archivo HTML autocontenido (sin módulos ES, sin `import`/`export`).

---

## Paso 5: Validar el Plugin

Antes de probar en Pinokio, ejecuta el validador para detectar errores comunes:

```bash
python tests/validate_plugin.py ~/pinokio/api/mi-primer-plugin/
```

El validador verifica las 10 reglas críticas de Pinokio y muestra exactamente qué corregir si algo falla.

---

## Paso 6: Probar en Pinokio

1. Abre Pinokio en tu navegador (normalmente en `http://localhost:3000`).
2. Navega a la sección de aplicaciones.
3. Tu plugin debería aparecer automáticamente si está en `~/pinokio/api/`.
4. Haz clic en "Instalar" y espera a que termine.
5. Haz clic en "Iniciar" para arrancar el servidor.
6. Haz clic en el botón de abrir para ver la interfaz de usuario.

---

## Errores Frecuentes en el Primer Plugin

Si algo no funciona, consulta [TROUBLESHOOTING.md](TROUBLESHOOTING.md). Los errores más comunes son:

El plugin no aparece en Pinokio: verifica que el directorio esté en `~/pinokio/api/` y que `pinokio.js` exista y sea válido.

El servidor no arranca: revisa que `start.json` sea JSON puro (no JavaScript) y que el nombre del venv sea exactamente `venv`.

La interfaz muestra errores de JavaScript: asegúrate de usar `var` en lugar de `let`/`const` y de que todas las funciones estén en scope global.

El modelo no responde: verifica que Ollama esté corriendo con `ollama serve` y que el modelo esté descargado con `ollama list`.

---

## Próximos Pasos

Una vez que tu primer plugin funciona, explora los ejemplos más completos:

- `examples/pyme-marketing-plugin/` — Muestra cómo integrar múltiples agentes Ollama y generar contenido por lotes.
- `examples/expense-classifier-plugin/` — Muestra cómo procesar datos estructurados y generar visualizaciones.

Para publicar tu plugin en GitHub y compartirlo con la comunidad, lee [one-click-setup.md](../skill/references/one-click-setup.md).
