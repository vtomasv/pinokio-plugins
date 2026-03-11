/**
 * pinokio.js — Expense Classifier Plugin
 *
 * Plugin para clasificación automática de gastos empresariales
 * usando modelos Ollama locales. Optimizado para hardware limitado
 * usando llama3.2:1b (solo 2GB RAM).
 */
module.exports = {
  title: "Clasificador de Gastos",
  description: "Clasifica gastos empresariales con IA local — sin internet",
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
