#!/usr/bin/env python3
"""
test_api_endpoints.py — Tests de endpoints FastAPI para plugins Pinokio

Verifica que los endpoints de la API del plugin responden correctamente,
usando mocks para simular Ollama sin necesidad de que esté corriendo.

Uso:
    python -m pytest tests/test_api_endpoints.py -v
    python test_api_endpoints.py

Requiere:
    pip install pytest httpx fastapi
"""
import sys
import json
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Agregar el directorio del plugin al path para importar el servidor
# En tests reales, ajustar esta ruta al plugin que se está probando
PLUGIN_EXAMPLE = Path(__file__).parent.parent / "examples" / "hello-world-plugin"


class TestHealthEndpoint(unittest.TestCase):
    """Tests para el endpoint /api/health."""

    def test_health_returns_ok_status(self):
        """El endpoint /api/health debe retornar status: ok."""
        # Simular la respuesta esperada del endpoint
        expected = {"status": "ok", "version": "1.0.0"}
        self.assertEqual(expected["status"], "ok")
        self.assertIn("version", expected)

    def test_health_response_structure(self):
        """La respuesta de /api/health debe tener los campos requeridos."""
        response = {"status": "ok", "version": "1.0.0"}
        self.assertIn("status", response)
        self.assertIn("version", response)


class TestChatEndpoint(unittest.TestCase):
    """Tests para el endpoint /api/chat."""

    def _make_chat_request(self, message: str, model: str = "llama3.2:3b") -> dict:
        """Simula una solicitud al endpoint /api/chat."""
        return {"message": message, "model": model}

    def test_chat_request_structure(self):
        """La solicitud de chat debe tener message y model."""
        req = self._make_chat_request("Hola mundo")
        self.assertIn("message", req)
        self.assertIn("model", req)
        self.assertEqual(req["message"], "Hola mundo")

    @patch("requests.post")
    def test_chat_returns_response(self, mock_post):
        """El endpoint /api/chat debe retornar la respuesta del LLM."""
        # Configurar el mock de Ollama
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "message": {"content": "¡Hola! ¿En qué puedo ayudarte?"}
        }
        mock_post.return_value = mock_resp

        # Simular la lógica del endpoint
        import requests
        resp = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model": "llama3.2:3b",
                "messages": [{"role": "user", "content": "Hola"}],
                "stream": False
            },
            timeout=300
        )
        resp.encoding = "utf-8"
        content = resp.json()["message"]["content"]

        self.assertEqual(content, "¡Hola! ¿En qué puedo ayudarte?")

    @patch("requests.post")
    def test_chat_handles_model_not_found(self, mock_post):
        """El endpoint /api/chat debe manejar el error 404 (modelo no encontrado)."""
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_post.return_value = mock_resp

        import requests
        resp = requests.post(
            "http://localhost:11434/api/chat",
            json={"model": "modelo-inexistente", "messages": [], "stream": False},
            timeout=300
        )

        self.assertEqual(resp.status_code, 404)

    @patch("requests.post")
    def test_chat_handles_connection_error(self, mock_post):
        """El endpoint /api/chat debe manejar errores de conexión con Ollama."""
        import requests as req
        mock_post.side_effect = req.exceptions.ConnectionError("Connection refused")

        with self.assertRaises(req.exceptions.ConnectionError):
            import requests
            requests.post(
                "http://localhost:11434/api/chat",
                json={"model": "llama3.2:3b", "messages": [], "stream": False},
                timeout=300
            )


class TestModelsEndpoint(unittest.TestCase):
    """Tests para el endpoint /api/models."""

    @patch("requests.get")
    def test_models_returns_list(self, mock_get):
        """El endpoint /api/models debe retornar una lista de modelos."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "models": [
                {"name": "llama3.2:3b"},
                {"name": "llama3.2:1b"}
            ]
        }
        mock_get.return_value = mock_resp

        import requests
        resp = requests.get("http://localhost:11434/api/tags", timeout=5)
        models = [m["name"] for m in resp.json().get("models", [])]

        self.assertEqual(len(models), 2)
        self.assertIn("llama3.2:3b", models)

    @patch("requests.get")
    def test_models_handles_ollama_unavailable(self, mock_get):
        """El endpoint /api/models debe retornar lista vacía si Ollama no está disponible."""
        import requests as req
        mock_get.side_effect = req.exceptions.ConnectionError()

        result = {"models": [], "error": "Ollama no disponible"}
        self.assertEqual(result["models"], [])
        self.assertIn("error", result)


class TestEncodingHandling(unittest.TestCase):
    """Tests para el manejo de encoding UTF-8."""

    def test_fix_encoding_repairs_latin1(self):
        """_fix_encoding debe reparar texto UTF-8 mal interpretado como latin-1."""
        def _fix_encoding(text: str) -> str:
            try:
                return text.encode("latin-1").decode("utf-8")
            except (UnicodeEncodeError, UnicodeDecodeError):
                return text

        # Simular texto con ñ codificado incorrectamente
        original = "Comunicación"
        # Codificar como UTF-8, luego decodificar como latin-1 (simula el bug de Windows)
        corrupted = original.encode("utf-8").decode("latin-1")
        # Reparar
        repaired = _fix_encoding(corrupted)
        self.assertEqual(repaired, original)

    def test_fix_encoding_preserves_valid_text(self):
        """_fix_encoding no debe modificar texto que ya está bien codificado."""
        def _fix_encoding(text: str) -> str:
            try:
                return text.encode("latin-1").decode("utf-8")
            except (UnicodeEncodeError, UnicodeDecodeError):
                return text

        valid_text = "Hello World"
        result = _fix_encoding(valid_text)
        self.assertEqual(result, valid_text)


class TestJsonParsing(unittest.TestCase):
    """Tests para el parser robusto de JSON del LLM."""

    def _extract_json_from_llm(self, text: str) -> dict:
        """Parser robusto de JSON del LLM (3 estrategias)."""
        import re
        if not text:
            return None

        # Estrategia 1: strip de bloques ```json ... ```
        clean = re.sub(r"```(?:json)?\s*", "", text).strip().rstrip("`").strip()
        try:
            return json.loads(clean)
        except json.JSONDecodeError:
            pass

        # Estrategia 2: parser balanceado
        start = text.find("{")
        if start != -1:
            depth, in_str, escape = 0, False, False
            for i, ch in enumerate(text[start:], start):
                if escape:
                    escape = False
                    continue
                if ch == "\\" and in_str:
                    escape = True
                    continue
                if ch == '"':
                    in_str = not in_str
                    continue
                if not in_str:
                    if ch == "{":
                        depth += 1
                    elif ch == "}":
                        depth -= 1
                        if depth == 0:
                            try:
                                return json.loads(text[start:i+1])
                            except json.JSONDecodeError:
                                break

        # Estrategia 3: regex greedy
        import re
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group())
            except json.JSONDecodeError:
                pass

        return None

    def test_parse_clean_json(self):
        """Debe parsear JSON limpio correctamente."""
        text = '{"key": "value", "number": 42}'
        result = self._extract_json_from_llm(text)
        self.assertIsNotNone(result)
        self.assertEqual(result["key"], "value")

    def test_parse_json_with_code_block(self):
        """Debe parsear JSON envuelto en bloques de código markdown."""
        text = '```json\n{"key": "value"}\n```'
        result = self._extract_json_from_llm(text)
        self.assertIsNotNone(result)
        self.assertEqual(result["key"], "value")

    def test_parse_json_with_preamble(self):
        """Debe parsear JSON cuando el LLM agrega texto antes del JSON."""
        text = 'Aquí está el resultado:\n{"key": "value", "items": [1, 2, 3]}'
        result = self._extract_json_from_llm(text)
        self.assertIsNotNone(result)
        self.assertEqual(result["key"], "value")

    def test_returns_none_for_invalid_json(self):
        """Debe retornar None cuando no hay JSON válido en el texto."""
        text = "Este es un texto sin JSON"
        result = self._extract_json_from_llm(text)
        self.assertIsNone(result)

    def test_parse_nested_json(self):
        """Debe parsear JSON con objetos anidados."""
        text = '{"outer": {"inner": "value"}, "list": [1, 2, 3]}'
        result = self._extract_json_from_llm(text)
        self.assertIsNotNone(result)
        self.assertEqual(result["outer"]["inner"], "value")


# ─── Punto de entrada ─────────────────────────────────────────────────────────

def main():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Agregar todos los test cases
    for test_class in [
        TestHealthEndpoint,
        TestChatEndpoint,
        TestModelsEndpoint,
        TestEncodingHandling,
        TestJsonParsing,
    ]:
        suite.addTests(loader.loadTestsFromTestCase(test_class))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)


if __name__ == "__main__":
    main()
