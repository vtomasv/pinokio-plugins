/**
 * pinokio.js — PYME Marketing Assistant
 *
 * Plugin de asistente de marketing para PYMEs con IA local.
 * Genera contenido para redes sociales, planifica calendarios
 * y crea campañas usando modelos Ollama.
 */
module.exports = {
  title: "PYME Marketing Assistant",
  description: "Genera contenido de marketing con IA 100% local",
  icon: "icon.png",

  menu: async (kernel, info) => {
    const installed = await kernel.exists(__dirname, "venv")
    const running = await kernel.script.running(__dirname, "start.json")

    if (!installed) {
      return [{
        default: true,
        icon: "fa-solid fa-download",
        text: "Instalar",
        href: "install.json"
      }]
    }

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

    return [{
      default: true,
      icon: "fa-solid fa-play",
      text: "Iniciar",
      href: "start.json"
    }]
  }
}
