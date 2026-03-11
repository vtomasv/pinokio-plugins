#!/usr/bin/env python3
"""
test_ollama_connection.py — Test de conexión y disponibilidad de modelos Ollama

Verifica que Ollama esté corriendo y que los modelos requeridos estén disponibles.
Útil para diagnosticar problemas antes de ejecutar un plugin.

Uso:
    python test_ollama_connection.py
    python test_ollama_connection.py --url http://localhost:11434
    python test_ollama_connection.py --model llama3.2:3b
"""
import sys
import json
import argparse
import unittest
from unittest.mock import patch, MagicMock

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


OLLAMA_URL = "http://localhost:11434"

RECOMMENDED_MODELS = [
    {"name": "llama3.2:1b", "min_ram_gb": 2,  "use": "Clasificación, tareas simples"},
    {"name": "llama3.2:3b", "min_ram_gb": 4,  "use": "Uso general, PYMEs"},
    {"name": "llama3.1:8b", "min_ram_gb": 8,  "use": "Análisis complejo"},
    {"name": "qwen2.5:7b",  "min_ram_gb": 8,  "use": "Multilingüe, español"},
]


# ─── Funciones de diagnóstico ─────────────────────────────────────────────────

def check_ollama_running(url: str = OLLAMA_URL) -> dict:
    """Verifica que Ollama esté corriendo y accesible."""
    if not REQUESTS_AVAILABLE:
        return {"ok": False, "error": "Librería 'requests' no instalada"}
    try:
        resp = requests.get(f"{url}/api/tags", timeout=5)
        resp.raise_for_status()
        return {"ok": True, "url": url, "status_code": resp.status_code}
    except requests.exceptions.ConnectionError:
        return {
            "ok": False,
            "error": f"No se puede conectar a {url}. ¿Está Ollama corriendo?",
            "hint": "Ejecuta: ollama serve"
        }
    except requests.exceptions.Timeout:
        return {"ok": False, "error": f"Timeout al conectar con {url}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def list_available_models(url: str = OLLAMA_URL) -> dict:
    """Lista los modelos disponibles en Ollama."""
    if not REQUESTS_AVAILABLE:
        return {"ok": False, "models": []}
    try:
        resp = requests.get(f"{url}/api/tags", timeout=5)
        resp.raise_for_status()
        models = resp.json().get("models", [])
        return {
            "ok": True,
            "models": [m["name"] for m in models],
            "count": len(models)
        }
    except Exception as e:
        return {"ok": False, "models": [], "error": str(e)}


def check_model_available(model: str, url: str = OLLAMA_URL) -> dict:
    """Verifica si un modelo específico está disponible."""
    result = list_available_models(url)
    if not result["ok"]:
        return {"ok": False, "model": model, "error": result.get("error")}

    available = result["models"]
    # Verificar nombre exacto o prefijo del modelo
    model_base = model.split(":")[0]
    found = model in available or any(m.startswith(model_base) for m in available)

    return {
        "ok": found,
        "model": model,
        "available_models": available,
        "hint": f"Ejecuta: ollama pull {model}" if not found else None
    }


def test_inference(model: str, url: str = OLLAMA_URL) -> dict:
    """Prueba una inferencia básica con el modelo especificado."""
    if not REQUESTS_AVAILABLE:
        return {"ok": False, "error": "Librería 'requests' no instalada"}
    try:
        resp = requests.post(
            f"{url}/api/chat",
            json={
                "model": model,
                "messages": [{"role": "user", "content": "Responde solo: OK"}],
                "options": {"temperature": 0.0},
                "stream": False
            },
            timeout=60
        )
        resp.encoding = "utf-8"
        if resp.status_code == 404:
            return {"ok": False, "error": f"Modelo '{model}' no encontrado"}
        resp.raise_for_status()
        content = resp.json()["message"]["content"]
        return {"ok": True, "model": model, "response": content[:100]}
    except requests.exceptions.Timeout:
        return {"ok": False, "error": f"Timeout (60s) al generar con {model}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ─── Tests unitarios (para pytest) ───────────────────────────────────────────

class TestOllamaConnectionUnit(unittest.TestCase):
    """Tests unitarios con mocks — no requieren Ollama corriendo."""

    @patch("requests.get")
    def test_check_ollama_running_success(self, mock_get):
        """Verifica que check_ollama_running retorna ok=True cuando Ollama responde."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"models": []}
        mock_get.return_value = mock_resp

        result = check_ollama_running()
        self.assertTrue(result["ok"])
        self.assertEqual(result["status_code"], 200)

    @patch("requests.get")
    def test_check_ollama_running_connection_error(self, mock_get):
        """Verifica que check_ollama_running retorna ok=False cuando Ollama no está corriendo."""
        import requests as req
        mock_get.side_effect = req.exceptions.ConnectionError("Connection refused")

        result = check_ollama_running()
        self.assertFalse(result["ok"])
        self.assertIn("hint", result)

    @patch("requests.get")
    def test_list_available_models(self, mock_get):
        """Verifica que list_available_models parsea correctamente la respuesta de Ollama."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "models": [
                {"name": "llama3.2:3b"},
                {"name": "llama3.2:1b"}
            ]
        }
        mock_get.return_value = mock_resp

        result = list_available_models()
        self.assertTrue(result["ok"])
        self.assertEqual(result["count"], 2)
        self.assertIn("llama3.2:3b", result["models"])

    @patch("requests.get")
    def test_check_model_available_found(self, mock_get):
        """Verifica que check_model_available retorna ok=True cuando el modelo existe."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"models": [{"name": "llama3.2:3b"}]}
        mock_get.return_value = mock_resp

        result = check_model_available("llama3.2:3b")
        self.assertTrue(result["ok"])
        self.assertIsNone(result["hint"])

    @patch("requests.get")
    def test_check_model_available_not_found(self, mock_get):
        """Verifica que check_model_available retorna ok=False cuando el modelo no existe."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"models": [{"name": "llama3.2:1b"}]}
        mock_get.return_value = mock_resp

        result = check_model_available("llama3.1:8b")
        self.assertFalse(result["ok"])
        self.assertIn("ollama pull", result["hint"])

    @patch("requests.post")
    def test_inference_success(self, mock_post):
        """Verifica que test_inference parsea correctamente la respuesta del LLM."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"message": {"content": "OK"}}
        mock_post.return_value = mock_resp

        result = test_inference("llama3.2:1b")
        self.assertTrue(result["ok"])
        self.assertEqual(result["response"], "OK")


# ─── Diagnóstico interactivo ──────────────────────────────────────────────────

def run_diagnostics(url: str, model: str = None) -> bool:
    """Ejecuta el diagnóstico completo e imprime los resultados."""
    print(f"\n{'='*60}")
    print("  Diagnóstico de Conexión con Ollama")
    print(f"{'='*60}\n")

    all_ok = True

    # 1. Verificar que Ollama está corriendo
    print("1. Verificando conexión con Ollama...")
    result = check_ollama_running(url)
    if result["ok"]:
        print(f"   ✓ Ollama está corriendo en {url}")
    else:
        print(f"   ✗ {result['error']}")
        if "hint" in result:
            print(f"   → {result['hint']}")
        print("\n   No se pueden ejecutar más verificaciones sin Ollama.")
        return False

    # 2. Listar modelos disponibles
    print("\n2. Modelos disponibles:")
    models_result = list_available_models(url)
    if models_result["ok"] and models_result["models"]:
        for m in models_result["models"]:
            print(f"   • {m}")
    else:
        print("   (ningún modelo instalado)")

    # 3. Verificar modelos recomendados
    print("\n3. Estado de modelos recomendados:")
    available = models_result.get("models", [])
    for rec in RECOMMENDED_MODELS:
        model_base = rec["name"].split(":")[0]
        found = rec["name"] in available or any(m.startswith(model_base) for m in available)
        status = "✓" if found else "○"
        print(f"   {status} {rec['name']:<20} ({rec['min_ram_gb']}GB RAM) — {rec['use']}")

    # 4. Probar inferencia con el modelo especificado
    if model:
        print(f"\n4. Probando inferencia con {model}...")
        inf_result = test_inference(model, url)
        if inf_result["ok"]:
            print(f"   ✓ Respuesta: '{inf_result['response']}'")
        else:
            print(f"   ✗ {inf_result['error']}")
            all_ok = False

    print(f"\n{'='*60}")
    if all_ok:
        print("  ✓ Diagnóstico completado — Ollama está listo")
    else:
        print("  ✗ Se encontraron problemas — revisar los errores anteriores")
    print(f"{'='*60}\n")

    return all_ok


# ─── Punto de entrada ─────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Test de conexión y disponibilidad de modelos Ollama"
    )
    parser.add_argument(
        "--url", default=OLLAMA_URL,
        help=f"URL de Ollama (default: {OLLAMA_URL})"
    )
    parser.add_argument(
        "--model", default=None,
        help="Modelo a probar con una inferencia de ejemplo"
    )
    parser.add_argument(
        "--unit-tests", action="store_true",
        help="Ejecutar tests unitarios con mocks (no requiere Ollama)"
    )
    args = parser.parse_args()

    if args.unit_tests:
        # Ejecutar tests unitarios
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(TestOllamaConnectionUnit)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        sys.exit(0 if result.wasSuccessful() else 1)
    else:
        # Ejecutar diagnóstico interactivo
        success = run_diagnostics(args.url, args.model)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
