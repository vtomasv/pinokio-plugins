/**
 * install.js - Plantilla de instalación con 1-Click para plugins Pinokio
 * 
 * Este script se ejecuta cuando el usuario hace click en "Instalar".
 * Realiza toda la configuración automáticamente sin intervención del usuario.
 * 
 * Personaliza las secciones marcadas con [PERSONALIZAR].
 */

module.exports = {
  title: "Instalando Plugin",
  description: "Configuración automática completa",
  run: [
    
    // ============================================================
    // FASE 1: Verificación del Sistema
    // ============================================================
    {
      method: "log",
      params: {
        html: `<div style="padding:20px">
          <h2 style="margin-bottom:8px">🚀 Iniciando instalación</h2>
          <p style="color:#94a3b8">Este proceso puede tomar 5-15 minutos la primera vez.</p>
        </div>`
      }
    },
    
    // ============================================================
    // FASE 2: Instalación de Ollama (LLM Local)
    // ============================================================
    {
      method: "log",
      params: {
        html: `<div style="padding:16px">
          <h3>🤖 Configurando motor de IA (Ollama)...</h3>
        </div>`
      }
    },
    
    // Verificar si Ollama ya está instalado
    {
      method: "shell.run",
      params: {
        message: "ollama --version 2>/dev/null && echo 'OLLAMA_OK' || echo 'OLLAMA_NOT_FOUND'",
        on: [{
          event: "/OLLAMA_NOT_FOUND/",
          run: [
            {
              method: "log",
              params: { html: "<p style='padding:0 16px;color:#f59e0b'>Instalando Ollama...</p>" }
            },
            {
              method: "shell.run",
              params: {
                message: "curl -fsSL https://ollama.com/install.sh | sh"
              }
            }
          ]
        }]
      }
    },
    
    // Iniciar Ollama en background
    {
      method: "shell.run",
      params: {
        message: "pkill ollama 2>/dev/null; sleep 1; ollama serve &",
        background: true
      }
    },
    {
      method: "shell.run",
      params: { message: "sleep 4" }
    },
    
    // ============================================================
    // FASE 3: Descarga del Modelo LLM
    // Selecciona automáticamente el modelo según la RAM disponible
    // [PERSONALIZAR] Cambia los modelos según las necesidades del plugin
    // ============================================================
    {
      method: "log",
      params: {
        html: `<div style="padding:16px">
          <h3>⬇️ Descargando modelo de IA...</h3>
          <p style="color:#94a3b8">RAM detectada: {{ram}}GB - Seleccionando modelo óptimo...</p>
        </div>`
      }
    },
    
    // Modelo principal según RAM
    {
      method: "shell.run",
      params: {
        message: "{{ram < 6 ? 'ollama pull llama3.2:1b' : ram < 12 ? 'ollama pull llama3.2:3b' : 'ollama pull llama3.1:8b'}}"
      }
    },
    
    // [PERSONALIZAR] Descarga modelos adicionales si el plugin los necesita
    // Ejemplo: modelo especializado en código
    // {
    //   method: "shell.run",
    //   params: {
    //     message: "{{ram >= 12 ? 'ollama pull mistral:7b' : ''}}"
    //   }
    // },
    
    // ============================================================
    // FASE 4: Entorno Python
    // ============================================================
    {
      method: "log",
      params: {
        html: `<div style="padding:16px"><h3>🐍 Configurando entorno Python...</h3></div>`
      }
    },
    
    {
      method: "shell.run",
      params: {
        message: "python -m venv venv",
        path: "{{cwd}}"
      }
    },
    
    {
      method: "shell.run",
      params: {
        message: "pip install --upgrade pip && pip install -r requirements.txt",
        path: "{{cwd}}",
        venv: "venv"
      }
    },
    
    // ============================================================
    // FASE 5: Inicialización de Datos
    // ============================================================
    {
      method: "log",
      params: {
        html: `<div style="padding:16px"><h3>💾 Inicializando datos...</h3></div>`
      }
    },
    
    // Crear estructura de directorios
    {
      method: "shell.run",
      params: {
        message: "mkdir -p data/agents data/prompts/system data/prompts/templates data/sessions data/exports",
        path: "{{cwd}}"
      }
    },
    
    // Crear configuración inicial
    {
      method: "fs.write",
      params: {
        path: "data/config.json",
        text: `{{JSON.stringify({
          version: "1.0.0",
          installedAt: new Date().toISOString(),
          platform: platform,
          ram: ram,
          defaultModel: ram < 6 ? "llama3.2:1b" : ram < 12 ? "llama3.2:3b" : "llama3.1:8b"
        }, null, 2)}}`
      }
    },
    
    // Copiar configuraciones por defecto (si no existen)
    {
      method: "shell.run",
      params: {
        message: [
          "[ -f data/agents/agents.json ] || cp defaults/agents.json data/agents/agents.json",
          "cp -rn defaults/prompts/* data/prompts/ 2>/dev/null || true"
        ].join(" && "),
        path: "{{cwd}}"
      }
    },
    
    // ============================================================
    // FASE 6: [PERSONALIZAR] Pasos específicos del plugin
    // Agrega aquí cualquier instalación adicional específica
    // ============================================================
    // Ejemplo: Instalar dependencias Node.js para la UI
    // {
    //   method: "shell.run",
    //   params: {
    //     message: "npm install",
    //     path: "{{cwd}}/app"
    //   }
    // },
    
    // ============================================================
    // COMPLETADO
    // ============================================================
    {
      method: "log",
      params: {
        html: `<div style="padding:20px;background:#0f2d1a;border-radius:8px;margin:16px">
          <h3 style="color:#22c55e;margin-bottom:8px">✅ Instalación completada</h3>
          <p>El plugin está listo para usar.</p>
          <p style="margin-top:8px;color:#94a3b8">Haz click en <strong>"Iniciar"</strong> para comenzar.</p>
        </div>`
      }
    },
    
    {
      method: "notify",
      params: {
        html: "✅ Plugin instalado. Haz click en 'Iniciar' para comenzar."
      }
    }
  ]
}
