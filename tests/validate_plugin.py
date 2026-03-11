#!/usr/bin/env python3
"""
validate_plugin.py — Validador de estructura y reglas para plugins Pinokio

Verifica las 10 reglas críticas que todo plugin Pinokio debe cumplir
antes de ser publicado o probado en producción.

Uso:
    python validate_plugin.py ruta/al/plugin/
    python validate_plugin.py ruta/al/plugin/ --strict
    python validate_plugin.py ruta/al/plugin/ --json

Códigos de salida:
    0 — Todas las validaciones pasaron
    1 — Una o más validaciones fallaron
"""
import sys
import json
import re
import argparse
from pathlib import Path


# ─── Colores para la terminal ─────────────────────────────────────────────────
class Colors:
    GREEN  = "\033[92m"
    RED    = "\033[91m"
    YELLOW = "\033[93m"
    BLUE   = "\033[94m"
    RESET  = "\033[0m"
    BOLD   = "\033[1m"


def ok(msg):   return f"{Colors.GREEN}✓{Colors.RESET} {msg}"
def fail(msg): return f"{Colors.RED}✗{Colors.RESET} {msg}"
def warn(msg): return f"{Colors.YELLOW}⚠{Colors.RESET} {msg}"
def info(msg): return f"{Colors.BLUE}ℹ{Colors.RESET} {msg}"


# ─── Validaciones individuales ────────────────────────────────────────────────

def check_lifecycle_files_are_json(plugin_dir: Path) -> tuple[bool, str]:
    """
    Regla 1: install.json, start.json y stop.json deben ser JSON puros,
    no módulos JavaScript.
    """
    required_json = ["install.json", "start.json", "stop.json"]
    errors = []

    for filename in required_json:
        filepath = plugin_dir / filename
        if not filepath.exists():
            errors.append(f"  Falta el archivo: {filename}")
            continue
        try:
            json.loads(filepath.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            errors.append(f"  {filename} no es JSON válido: {e}")

    if errors:
        return False, "Scripts de ciclo de vida deben ser JSON puros:\n" + "\n".join(errors)
    return True, "install.json, start.json y stop.json son JSON válidos"


def check_pinokio_js_points_to_json(plugin_dir: Path) -> tuple[bool, str]:
    """
    Regla 2: pinokio.js debe apuntar a archivos .json, no .js.
    """
    pinokio_js = plugin_dir / "pinokio.js"
    if not pinokio_js.exists():
        return False, "pinokio.js no existe (archivo requerido)"

    content = pinokio_js.read_text(encoding="utf-8")

    # Buscar referencias a archivos .js en href (excepto el propio pinokio.js)
    js_hrefs = re.findall(r'href:\s*["\']([^"\']+\.js)["\']', content)
    if js_hrefs:
        return False, f"pinokio.js apunta a archivos .js: {js_hrefs}. Deben ser .json"

    return True, "pinokio.js apunta correctamente a archivos .json"


def check_no_background_true(plugin_dir: Path) -> tuple[bool, str]:
    """
    Regla 3: No debe haber 'background: true' en ningún archivo JSON.
    background: true no existe en la API de Pinokio.
    """
    json_files = list(plugin_dir.glob("*.json"))
    errors = []

    for filepath in json_files:
        content = filepath.read_text(encoding="utf-8")
        if '"background"' in content and "true" in content:
            # Verificar que realmente es background: true
            if re.search(r'"background"\s*:\s*true', content):
                errors.append(f"  {filepath.name}: contiene 'background: true'")

    if errors:
        return False, "background: true no existe en la API de Pinokio:\n" + "\n".join(errors)
    return True, "No se encontró 'background: true' en los archivos JSON"


def check_venv_name_consistent(plugin_dir: Path) -> tuple[bool, str]:
    """
    Regla 4: El nombre del entorno virtual debe ser 'venv' en todos los archivos.
    """
    files_to_check = ["install.json", "start.json", "pinokio.js"]
    issues = []

    for filename in files_to_check:
        filepath = plugin_dir / filename
        if not filepath.exists():
            continue
        content = filepath.read_text(encoding="utf-8")
        # Buscar referencias a venv con nombre diferente
        other_venvs = re.findall(r'"venv":\s*"([^"]+)"', content)
        for venv_name in other_venvs:
            if venv_name != "venv":
                issues.append(f"  {filename}: usa venv='{venv_name}' en lugar de 'venv'")

    if issues:
        return False, "Nombre del venv inconsistente:\n" + "\n".join(issues)
    return True, "Nombre del venv es 'venv' en todos los archivos"


def check_absolute_paths_in_server(plugin_dir: Path) -> tuple[bool, str]:
    """
    Regla 5: El servidor Python debe usar rutas absolutas basadas en __file__.
    """
    server_py = plugin_dir / "server" / "app.py"
    if not server_py.exists():
        return None, "server/app.py no existe (omitiendo verificación)"

    content = server_py.read_text(encoding="utf-8")

    if "__file__" not in content:
        return False, (
            "server/app.py no usa __file__ para rutas absolutas.\n"
            "  Usar: BASE_DIR = Path(__file__).parent.parent.resolve()"
        )

    return True, "server/app.py usa rutas absolutas basadas en __file__"


def check_ensure_ascii_false(plugin_dir: Path) -> tuple[bool, str]:
    """
    Regla 6: Todos los json.dumps deben usar ensure_ascii=False para
    preservar caracteres especiales del español.
    """
    py_files = list((plugin_dir / "server").glob("*.py")) if (plugin_dir / "server").exists() else []

    for filepath in py_files:
        content = filepath.read_text(encoding="utf-8")
        dumps_calls = re.findall(r'json\.dumps\([^)]+\)', content)
        for call in dumps_calls:
            if "ensure_ascii" not in call:
                return False, (
                    f"json.dumps en {filepath.name} sin ensure_ascii=False.\n"
                    "  Agregar: json.dumps(data, ensure_ascii=False)"
                )

    return True, "Todos los json.dumps usan ensure_ascii=False"


def check_utf8_encoding_in_ollama(plugin_dir: Path) -> tuple[bool, str]:
    """
    Regla 7: Las llamadas a Ollama deben forzar encoding UTF-8 para
    compatibilidad con Windows.
    """
    server_py = plugin_dir / "server" / "app.py"
    if not server_py.exists():
        return None, "server/app.py no existe (omitiendo verificación)"

    content = server_py.read_text(encoding="utf-8")

    # Verificar si hay llamadas a Ollama
    if "ollama" not in content.lower() and "api/chat" not in content:
        return None, "No se detectaron llamadas a Ollama (omitiendo verificación)"

    if 'encoding = "utf-8"' not in content and "encoding='utf-8'" not in content:
        return False, (
            "Las llamadas a Ollama no fuerzan encoding UTF-8.\n"
            "  Agregar: response.encoding = 'utf-8'"
        )

    return True, "Las llamadas a Ollama fuerzan encoding UTF-8"


def check_no_es6_in_html(plugin_dir: Path) -> tuple[bool, str]:
    """
    Regla 8: app/index.html no debe usar let, const, import o export
    (incompatibles con el webview de Electron/Pinokio).
    """
    index_html = plugin_dir / "app" / "index.html"
    if not index_html.exists():
        return None, "app/index.html no existe (omitiendo verificación)"

    content = index_html.read_text(encoding="utf-8")

    # Extraer solo el contenido de los tags <script>
    scripts = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
    script_content = "\n".join(scripts)

    issues = []

    # Verificar let (con espacio o al inicio de línea para evitar falsos positivos)
    if re.search(r'\blet\s+\w', script_content):
        issues.append("  Usar 'var' en lugar de 'let'")

    # Verificar const
    if re.search(r'\bconst\s+\w', script_content):
        issues.append("  Usar 'var' en lugar de 'const'")

    # Verificar import/export
    if re.search(r'\bimport\s+', script_content) or re.search(r'\bexport\s+', script_content):
        issues.append("  Eliminar 'import'/'export' (no soportados en Pinokio)")

    if issues:
        return False, "app/index.html usa sintaxis ES6+ incompatible:\n" + "\n".join(issues)

    return True, "app/index.html usa JavaScript compatible con Pinokio (var, scope global)"


def check_long_operations_use_background_tasks(plugin_dir: Path) -> tuple[bool, str]:
    """
    Regla 9 (advertencia): Las operaciones largas deben usar BackgroundTasks
    de FastAPI para evitar timeouts HTTP.
    """
    server_py = plugin_dir / "server" / "app.py"
    if not server_py.exists():
        return None, "server/app.py no existe (omitiendo verificación)"

    content = server_py.read_text(encoding="utf-8")

    # Solo verificar si hay indicios de operaciones largas (generación, análisis)
    has_long_ops = any(kw in content.lower() for kw in [
        "generate", "campaign", "batch", "bulk", "analysis", "generar", "campaña"
    ])

    if has_long_ops and "BackgroundTasks" not in content:
        return False, (
            "Se detectaron operaciones largas pero no se usa BackgroundTasks.\n"
            "  Las operaciones largas deben usar FastAPI BackgroundTasks + polling."
        )

    return True, "Operaciones largas usan BackgroundTasks (o no aplica)"


def check_pinokio_js_exists(plugin_dir: Path) -> tuple[bool, str]:
    """
    Regla 10: pinokio.js debe existir y exportar title, icon y menu.
    """
    pinokio_js = plugin_dir / "pinokio.js"
    if not pinokio_js.exists():
        return False, "pinokio.js no existe (archivo requerido por Pinokio)"

    content = pinokio_js.read_text(encoding="utf-8")

    missing = []
    if "title" not in content:   missing.append("title")
    if "icon" not in content:    missing.append("icon")
    if "menu" not in content:    missing.append("menu")

    if missing:
        return False, f"pinokio.js no define: {', '.join(missing)}"

    return True, "pinokio.js existe y define title, icon y menu"


# ─── Ejecutor de validaciones ─────────────────────────────────────────────────

CHECKS = [
    ("Scripts de ciclo de vida son JSON puros",     check_lifecycle_files_are_json),
    ("pinokio.js apunta a archivos .json",          check_pinokio_js_points_to_json),
    ("Sin 'background: true' en JSONs",             check_no_background_true),
    ("Nombre del venv es 'venv' en todos lados",    check_venv_name_consistent),
    ("Rutas absolutas en server/app.py",            check_absolute_paths_in_server),
    ("ensure_ascii=False en json.dumps",            check_ensure_ascii_false),
    ("encoding=utf-8 en llamadas a Ollama",         check_utf8_encoding_in_ollama),
    ("Sin ES6+ en app/index.html",                  check_no_es6_in_html),
    ("Operaciones largas usan BackgroundTasks",     check_long_operations_use_background_tasks),
    ("pinokio.js existe con campos requeridos",     check_pinokio_js_exists),
]


def validate_plugin(plugin_dir: Path, strict: bool = False) -> dict:
    """
    Ejecuta todas las validaciones sobre el directorio del plugin.

    Returns:
        dict con keys: passed, failed, skipped, results
    """
    results = []
    passed = failed = skipped = 0

    for name, check_fn in CHECKS:
        try:
            result, message = check_fn(plugin_dir)
        except Exception as e:
            result, message = False, f"Error inesperado: {e}"

        if result is None:
            status = "skipped"
            skipped += 1
        elif result:
            status = "passed"
            passed += 1
        else:
            status = "failed"
            failed += 1

        results.append({
            "name": name,
            "status": status,
            "message": message
        })

    return {
        "plugin_dir": str(plugin_dir),
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "total": len(CHECKS),
        "results": results
    }


def print_report(report: dict) -> None:
    """Imprime el reporte de validación en formato legible."""
    print(f"\n{Colors.BOLD}Validación del Plugin Pinokio{Colors.RESET}")
    print(f"Directorio: {report['plugin_dir']}")
    print("─" * 60)

    for r in report["results"]:
        if r["status"] == "passed":
            print(ok(r["name"]))
        elif r["status"] == "failed":
            print(fail(r["name"]))
            # Indentar el mensaje de error
            for line in r["message"].split("\n"):
                print(f"  {Colors.RED}{line}{Colors.RESET}")
        else:
            print(warn(f"{r['name']} (omitido)"))
            print(f"  {Colors.YELLOW}{r['message']}{Colors.RESET}")

    print("─" * 60)
    total = report["total"]
    passed = report["passed"]
    failed = report["failed"]
    skipped = report["skipped"]

    if failed == 0:
        print(f"{Colors.GREEN}{Colors.BOLD}✓ Todas las validaciones pasaron ({passed}/{total}){Colors.RESET}")
    else:
        print(
            f"{Colors.RED}{Colors.BOLD}✗ {failed} validación(es) fallaron "
            f"({passed} pasaron, {skipped} omitidas de {total}){Colors.RESET}"
        )


# ─── Punto de entrada ─────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Validador de estructura y reglas para plugins Pinokio"
    )
    parser.add_argument("plugin_dir", help="Ruta al directorio del plugin")
    parser.add_argument(
        "--strict", action="store_true",
        help="Tratar advertencias como errores"
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Salida en formato JSON"
    )
    args = parser.parse_args()

    plugin_dir = Path(args.plugin_dir).resolve()

    if not plugin_dir.exists():
        print(f"{Colors.RED}Error: El directorio '{plugin_dir}' no existe.{Colors.RESET}")
        sys.exit(1)

    report = validate_plugin(plugin_dir, strict=args.strict)

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print_report(report)

    sys.exit(0 if report["failed"] == 0 else 1)


if __name__ == "__main__":
    main()
