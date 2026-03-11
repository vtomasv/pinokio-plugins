/**
 * pinokio.js - Plantilla de configuración principal para plugins Pinokio
 * 
 * Este archivo define el comportamiento del plugin en la interfaz de Pinokio.
 * Personaliza los valores marcados con [PERSONALIZAR].
 */

module.exports = {
  // ============================================================
  // Metadatos del Plugin
  // ============================================================
  title: "[PERSONALIZAR] Nombre del Plugin",
  description: "[PERSONALIZAR] Descripción breve del plugin",
  icon: "icon.png",
  version: "1.0.0",
  
  // ============================================================
  // Menú Dinámico
  // El menú cambia según el estado del plugin (instalado/corriendo)
  // ============================================================
  menu: async (kernel, info) => {
    // Verificar si el plugin está instalado (existe el entorno virtual)
    const installed = await kernel.exists(__dirname, "venv")
    
    // Verificar si el servidor está corriendo
    const running = await kernel.script.running(__dirname, "start.js")
    
    // ---- Estado: No instalado ----
    if (!installed) {
      return [
        {
          default: true,                    // Este ítem se ejecuta al hacer click principal
          icon: "fa-solid fa-download",
          text: "Instalar",
          href: "install.js",
          description: "Instalación automática con 1 click (5-15 min)"
        }
      ]
    }
    
    // ---- Estado: Corriendo ----
    if (running) {
      return [
        {
          icon: "fa-solid fa-circle",
          text: "En ejecución",
          href: "start.js",
          style: "color: #22c55e"          // Verde para indicar que está activo
        },
        {
          icon: "fa-solid fa-arrow-up-right-from-square",
          text: "Abrir",
          href: "start.js",
          description: "Abrir la interfaz del plugin"
        },
        {
          icon: "fa-solid fa-gear",
          text: "Configuración",
          href: "start.js?page=config"
        },
        {
          icon: "fa-solid fa-stop",
          text: "Detener",
          href: "stop.js"
        }
      ]
    }
    
    // ---- Estado: Instalado pero no corriendo ----
    return [
      {
        default: true,
        icon: "fa-solid fa-play",
        text: "Iniciar",
        href: "start.js",
        description: "Iniciar el plugin"
      },
      {
        icon: "fa-solid fa-gear",
        text: "Configuración",
        href: "start.js?page=config"
      },
      {
        icon: "fa-solid fa-rotate",
        text: "Reinstalar",
        href: "install.js",
        description: "Reinstalar si hay problemas"
      }
    ]
  }
}
