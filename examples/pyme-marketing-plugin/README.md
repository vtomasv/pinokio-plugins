# PYME Marketing Assistant

Plugin de asistente de marketing para PYMEs con IA local. Genera contenido para redes sociales, planifica calendarios de posts y crea borradores de campañas usando modelos Ollama.

## Funcionalidades

**Generación de contenido**: Crea posts para Instagram, LinkedIn, Facebook y Twitter adaptados al tono y audiencia de tu negocio.

**Planificación de calendario**: Genera un calendario de publicaciones semanal o mensual con sugerencias de horarios óptimos y hashtags relevantes.

**Análisis de audiencia**: Analiza el perfil de tu negocio y sugiere estrategias de contenido personalizadas.

**Generación por lotes**: Produce múltiples posts en una sola operación, usando el patrón de lotes de 5 para evitar truncamiento del contexto del LLM.

## Arquitectura

Este plugin implementa el patrón de múltiples agentes especializados:

| Agente | Rol | Modelo Sugerido |
|--------|-----|----------------|
| Estratega | Analiza el negocio y define la estrategia | llama3.1:8b |
| Redactor | Genera el texto de los posts | llama3.2:3b |
| Planificador | Organiza el calendario y horarios | llama3.2:1b |

## Patrones Demostrados

**Operaciones largas con BackgroundTasks**: La generación de campañas completas usa `BackgroundTasks` de FastAPI con polling desde el frontend, evitando timeouts HTTP.

**Generación por lotes**: Nunca más de 5 posts por llamada al LLM para evitar truncamiento del contexto.

**Parser robusto de JSON**: Usa las 3 estrategias de extracción para manejar respuestas del LLM que incluyen texto antes del JSON o bloques de código.

## Instalación

1. Copia este directorio a `~/pinokio/api/pyme-marketing-plugin/`.
2. Abre Pinokio y haz clic en "Instalar" (requiere mínimo 4GB RAM).
3. Una vez instalado, haz clic en "Iniciar".

## Uso

1. Completa el perfil de tu negocio (nombre, industria, audiencia objetivo).
2. Selecciona el tipo de contenido que deseas generar.
3. Haz clic en "Generar" y espera a que la IA procese tu solicitud.
4. Revisa, edita y aprueba el contenido generado.
5. Exporta el calendario en formato CSV o PDF.

> **Nota**: Este es un ejemplo de referencia. Para el plugin completo de producción del proyecto CCS, consulta el repositorio principal del proyecto.
