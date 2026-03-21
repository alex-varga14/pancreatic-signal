import argparse
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"
WEB_ROOT = ROOT / "apps" / "web"

PASS = "PASS"
WARN = "WARN"
FAIL = "FAIL"


@dataclass
class CheckResult:
    name: str
    status: str
    detail: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate the local Pancreatic Signal workspace and demo benchmark flow."
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat missing local prerequisites like uninstalled deps or missing node_modules as failures.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the full validation result as JSON.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    results = [
        check_python_version(),
        check_python_compile(),
        check_python_dependencies(strict=args.strict),
        check_api_import(strict=args.strict),
        check_demo_eval_compare(),
        check_demo_eval_sweep(),
        check_pytest(strict=args.strict),
        check_web_build(strict=args.strict),
    ]

    if args.json:
        payload = {
            "strict": args.strict,
            "results": [asdict(result) for result in results],
            "summary": summarize_results(results),
        }
        print(json.dumps(payload, indent=2))
    else:
        for result in results:
            print(f"[{result.status}] {result.name}: {result.detail}")

        summary = summarize_results(results)
        print(
            f"\nSummary: {summary['PASS']} pass, {summary['WARN']} warn, {summary['FAIL']} fail"
        )
        if summary["FAIL"]:
            print("Validation failed. Fix the failing checks above and rerun.")
        elif summary["WARN"]:
            print("Validation completed with warnings. Use --strict to require full local readiness.")
        else:
            print("Validation passed.")

    raise SystemExit(1 if any(result.status == FAIL for result in results) else 0)


def check_python_version() -> CheckResult:
    minimum = get_minimum_python_version()
    version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    if sys.version_info >= minimum:
        return CheckResult("python-version", PASS, f"Using Python {version}.")
    minimum_display = ".".join(str(part) for part in minimum)
    return CheckResult(
        "python-version",
        FAIL,
        f"Python {minimum_display}+ is required by apps/api/pyproject.toml, found {version}.",
    )


def check_python_compile() -> CheckResult:
    with tempfile.TemporaryDirectory(prefix="pancreatic-signal-pycache-") as pycache_dir:
        process = run_command(
            [
                sys.executable,
                "-m",
                "compileall",
                "-q",
                "apps/api/app",
                "apps/api/tests",
                "scripts",
            ],
            extra_env={"PYTHONPYCACHEPREFIX": pycache_dir},
        )

    if process.returncode == 0:
        return CheckResult("python-compile", PASS, "Compiled apps/api and scripts successfully.")
    return CheckResult("python-compile", FAIL, summarize_process(process))


def check_python_dependencies(*, strict: bool) -> CheckResult:
    required_modules = {
        "fastapi": "fastapi",
        "pydantic": "pydantic",
        "pydantic-settings": "pydantic_settings",
        "sqlalchemy": "sqlalchemy",
        "psycopg": "psycopg",
        "pytest": "pytest",
        "python-multipart": "multipart",
    }
    missing = [
        package_name
        for package_name, module_name in required_modules.items()
        if importlib.util.find_spec(module_name) is None
    ]

    if not missing:
        return CheckResult("python-deps", PASS, "All expected Python runtime and dev dependencies are importable.")

    status = FAIL if strict else WARN
    detail = f"Missing Python packages: {', '.join(missing)}."
    if not strict:
        detail += " Install them with `make api-install` or `pip install -e .[dev]` in `apps/api`."
    return CheckResult("python-deps", status, detail)


def check_api_import(*, strict: bool) -> CheckResult:
    process = run_command(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "from pathlib import Path; "
                f"api_root = Path({str(API_ROOT)!r}); "
                "sys.path.insert(0, str(api_root)); "
                "from app.main import app; "
                "print(app.title)"
            ),
        ]
    )

    if process.returncode == 0:
        detail = process.stdout.strip() or "Imported FastAPI application successfully."
        return CheckResult("api-import", PASS, detail)

    missing_module = "ModuleNotFoundError" in (process.stderr or "")
    status = FAIL if strict or not missing_module else WARN
    return CheckResult("api-import", status, summarize_process(process))


def check_demo_eval_compare() -> CheckResult:
    process = run_command([sys.executable, "scripts/run_demo_eval.py", "--compare", "--json"])
    if process.returncode != 0:
        return CheckResult("demo-eval-compare", FAIL, summarize_process(process))

    payload = json.loads(process.stdout)
    detail = (
        f"Hybrid recall delta {payload['recall_delta']:+.4f}, "
        f"F1 delta {payload['f1_delta']:+.4f}, "
        f"newly flagged {', '.join(payload['newly_flagged_cases']) or 'none'}."
    )
    return CheckResult("demo-eval-compare", PASS, detail)


def check_demo_eval_sweep() -> CheckResult:
    process = run_command([sys.executable, "scripts/run_demo_eval.py", "--sweep", "--json"])
    if process.returncode != 0:
        return CheckResult("demo-eval-sweep", FAIL, summarize_process(process))

    payload = json.loads(process.stdout)
    rules_threshold = payload["rules_recommendation"]["recommended_threshold"]
    hybrid_threshold = payload["hybrid_recommendation"]["recommended_threshold"]
    detail = (
        f"Recommended thresholds: rules={rules_threshold:.2f}, hybrid={hybrid_threshold:.2f} "
        f"for top-{payload['top_k']} review."
    )
    return CheckResult("demo-eval-sweep", PASS, detail)


def check_pytest(*, strict: bool) -> CheckResult:
    if importlib.util.find_spec("pytest") is None:
        status = FAIL if strict else WARN
        detail = "pytest is not installed; skipped API test run."
        return CheckResult("pytest", status, detail)

    process = run_command([sys.executable, "-m", "pytest", "-q"], cwd=API_ROOT)
    if process.returncode == 0:
        output = process.stdout.strip().splitlines()
        detail = output[-1] if output else "API tests passed."
        return CheckResult("pytest", PASS, detail)
    return CheckResult("pytest", FAIL, summarize_process(process))


def check_web_build(*, strict: bool) -> CheckResult:
    node = shutil.which("node")
    npm = shutil.which("npm")
    if not node or not npm:
        status = FAIL if strict else WARN
        return CheckResult("web-build", status, "Node.js and npm are required to validate the web app build.")

    if not (WEB_ROOT / "node_modules").exists():
        status = FAIL if strict else WARN
        return CheckResult("web-build", status, "`apps/web/node_modules` is missing; run `npm install` in `apps/web`.")

    process = run_command(["npm", "run", "build"], cwd=WEB_ROOT)
    if process.returncode == 0:
        output = process.stdout.strip().splitlines()
        detail = output[-1] if output else "Web build passed."
        return CheckResult("web-build", PASS, detail)
    return CheckResult("web-build", FAIL, summarize_process(process))


def get_minimum_python_version() -> tuple[int, int]:
    pyproject = API_ROOT / "pyproject.toml"
    content = pyproject.read_text()
    match = re.search(r'requires-python\s*=\s*">=([0-9]+)\.([0-9]+)"', content)
    if not match:
        return (3, 11)
    return int(match.group(1)), int(match.group(2))


def run_command(
    command: list[str],
    *,
    cwd: Path = ROOT,
    extra_env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def summarize_process(process: subprocess.CompletedProcess[str], max_lines: int = 8) -> str:
    chunks: list[str] = []
    stdout = format_output_block(process.stdout, max_lines=max_lines)
    stderr = format_output_block(process.stderr, max_lines=max_lines)
    if stdout:
        chunks.append(f"stdout: {stdout}")
    if stderr:
        chunks.append(f"stderr: {stderr}")
    return " | ".join(chunks) or f"Command exited with code {process.returncode}."


def format_output_block(text: str, *, max_lines: int) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return ""
    if len(lines) > max_lines:
        return " / ".join(lines[:max_lines]) + " / ..."
    return " / ".join(lines)


def summarize_results(results: list[CheckResult]) -> dict[str, int]:
    return {
        PASS: sum(1 for result in results if result.status == PASS),
        WARN: sum(1 for result in results if result.status == WARN),
        FAIL: sum(1 for result in results if result.status == FAIL),
    }


if __name__ == "__main__":
    main()
