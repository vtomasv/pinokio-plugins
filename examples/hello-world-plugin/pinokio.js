/**
 * pinokio.js — Configuración del plugin "Hello World"
 *
 * Este es el archivo principal que Pinokio lee para mostrar el plugin
 * en su interfaz. Define el título, icono y menú dinámico del plugin.
 *
 * REGLA: Este es el ÚNICO archivo .js permitido en el plugin.
 * install.json, start.json y stop.json deben ser JSON puros.
 */
module.exports = {
  title: "Hello World Plugin",
  description: "Plugin de ejemplo mínimo para aprender la arquitectura de Pinokio",
  icon: "icon.png",

  /**
   * menu() — Función dinámica que devuelve el menú según el estado del plugin.
   * Pinokio llama a esta función cada vez que necesita mostrar el menú.
   *
   * @param {object} kernel - API de Pinokio
   * @param {object} info - Información del contexto actual
   * @returns {Array} Lista de ítems del menú
   */
  menu: async (kernel, info) => {
    // Verificar si el plugin está instalado (existe el entorno virtual)
    const installed = await kernel.exists(__dirname, "venv")

    // Verificar si el servidor está corriendo
    const running = await kernel.script.running(__dirname, "start.json")

    // Estado: No instalado → mostrar botón de instalación
    if (!installed) {
      return [{
        default: true,
        icon: "fa-solid fa-download",
        text: "Instalar",
        href: "install.json"
      }]
    }

    // Estado: Instalado y corriendo → mostrar estado y botón de detener
    if (running) {
      return [
        {
          icon: "fa-solid fa-circle",
          text: "En ejecución",
          href: "start.json",
          style: "color: #22c55e"
        },
        {
          icon: "fa-solid fa-stop",
          text: "Detener",
          href: "stop.json"
        }
      ]
    }

    // Estado: Instalado pero detenido → mostrar botón de iniciar
    return [{
      default: true,
      icon: "fa-solid fa-play",
      text: "Iniciar",
      href: "start.json"
    }]
  }
}
