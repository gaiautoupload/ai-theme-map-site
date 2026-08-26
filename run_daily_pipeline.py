import os
import subprocess
import sys
from pathlib import Path

os.environ.setdefault("MAP_VLLM_URL", "https://vllm-a5000.iii-ei-stack.com/v1/chat/completions")
os.environ.setdefault("MAP_MODEL_NAME", "cyankiwi/gemma-4-31B-it-AWQ-4bit")

BASE_DIR = Path(__file__).resolve().parent
LOCAL_PACKAGE_DIR = BASE_DIR / ".python-packages"
DEFAULT_VLLM_URL = "https://vllm-a5000.iii-ei-stack.com/v1/chat/completions"
DEFAULT_MODEL_NAME = "cyankiwi/gemma-4-31B-it-AWQ-4bit"


def with_default_env():
    env = os.environ.copy()
    if LOCAL_PACKAGE_DIR.exists():
        existing_pythonpath = env.get("PYTHONPATH")
        env["PYTHONPATH"] = (
            str(LOCAL_PACKAGE_DIR)
            if not existing_pythonpath
            else f"{LOCAL_PACKAGE_DIR}{os.pathsep}{existing_pythonpath}"
        )
    env.setdefault("MAP_VLLM_URL", DEFAULT_VLLM_URL)
    env.setdefault("MAP_MODEL_NAME", DEFAULT_MODEL_NAME)
    env.setdefault("MAP_MODEL_AUTO_DISCOVER", "1")
    env.setdefault("MAP_SEARCH_MODE", "search_augmented")
    env.setdefault("MAP_SEARCH_BACKEND", "whitelist_rss")
    env.setdefault("MAP_SEARCH_MIN_DELAY", "3.5")
    env.setdefault("MAP_SEARCH_MAX_DELAY", "7.5")
    env.setdefault("MAP_SEARCH_FETCH_ENABLED", "1")
    env.setdefault("MAP_MAX_TOKENS_PER_STEP", "8000")
    return env


def select_available_model(env):
    """Prefer the configured model, but follow the model currently served by vLLM."""
    if env.get("MAP_MODEL_AUTO_DISCOVER", "1").lower() not in {"1", "true", "yes"}:
        print(f"vLLM model auto-discovery disabled; using {env['MAP_MODEL_NAME']}")
        return

    try:
        import requests

        endpoint = env["MAP_VLLM_URL"].split("/chat/completions", 1)[0].rstrip("/") + "/models"
        response = requests.get(endpoint, timeout=20)
        response.raise_for_status()
        models = [item.get("id") for item in response.json().get("data", []) if item.get("id")]
        if not models:
            raise RuntimeError("vLLM returned no models")

        preferred = env.get("MAP_MODEL_NAME", "")
        selected = preferred if preferred in models else models[0]
        env["MAP_MODEL_NAME"] = selected
        if selected != preferred:
            print(f"vLLM model changed automatically: {preferred} -> {selected}")
        else:
            print(f"vLLM model confirmed: {selected}")
    except Exception as error:
        print(f"WARNING: unable to discover vLLM model; keeping {env['MAP_MODEL_NAME']}. Error: {error}")


def run_step(name, cmd, env):
    print(f"\n=== {name} ===")
    print(">", " ".join(cmd))
    try:
        subprocess.run(cmd, cwd=str(BASE_DIR), check=True, env=env)
        return True
    except Exception as e:
        print(f"WARNING: step '{name}' failed but the pipeline will continue. Error: {e}")
        return False


def main():
    python_exe = sys.executable or "python"
    env = with_default_env()
    select_available_model(env)
    steps = [
        ("build ticker registry", [python_exe, "build_ticker_registry.py"]),
        ("theme discovery", [python_exe, "theme_discovery.py"]),
        ("build theme evidence", [python_exe, "evidence_builder.py"]),
        ("rebuild maps repo from discovery", [python_exe, "rebuild_maps_repo_from_discovery.py"]),
        ("build stocks wiki", [python_exe, "build_stocks_wiki.py"]),
        ("crawl institutional chips", [python_exe, "daily_chips_crawler.py"]),
        ("crawl expectations gap", [python_exe, "auto_expectations_gap_crawler.py"]),
        ("generate daily report", [python_exe, "generate_daily_report.py"]),
        ("publish site", [python_exe, "publish_site.py"]),
    ]

    failed_steps = [name for name, cmd in steps if not run_step(name, cmd, env)]
    if failed_steps:
        print("\nDaily pipeline failed steps:")
        for name in failed_steps:
            print(f"- {name}")
        sys.exit(1)

    print("\nDaily pipeline completed successfully.")


if __name__ == "__main__":
    main()
