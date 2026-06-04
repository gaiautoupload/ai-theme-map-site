import os
import subprocess
import sys
from pathlib import Path

os.environ.setdefault("MAP_VLLM_URL", "https://vllm-a5000.iii-ei-stack.com/v1/chat/completions")
os.environ.setdefault("MAP_MODEL_NAME", "cyankiwi/Qwen3.6-35B-A3B-AWQ-4bit")

BASE_DIR = Path(__file__).resolve().parent


def with_default_env():
    env = os.environ.copy()
    env.setdefault("MAP_VLLM_URL", "https://vllm-a5000.iii-ei-stack.com/v1/chat/completions")
    env.setdefault("MAP_MODEL_NAME", "cyankiwi/Qwen3.6-35B-A3B-AWQ-4bit")
    env.setdefault("MAP_SEARCH_MODE", "search_augmented")
    env.setdefault("MAP_SEARCH_BACKEND", "whitelist_rss")
    env.setdefault("MAP_SEARCH_MIN_DELAY", "3.5")
    env.setdefault("MAP_SEARCH_MAX_DELAY", "7.5")
    env.setdefault("MAP_SEARCH_FETCH_ENABLED", "1")
    return env


def run_step(name, cmd, env):
    print(f"\n=== {name} ===")
    print(">", " ".join(cmd))
    subprocess.run(cmd, cwd=str(BASE_DIR), check=True, env=env)


def main():
    python_exe = sys.executable or "python"
    env = with_default_env()
    run_step("build ticker registry", [python_exe, "build_ticker_registry.py"], env)
    run_step("theme discovery", [python_exe, "theme_discovery.py"], env)
    run_step("build theme evidence", [python_exe, "evidence_builder.py"], env)
    run_step("rebuild maps repo from discovery", [python_exe, "rebuild_maps_repo_from_discovery.py"], env)
    run_step("publish site", [python_exe, "publish_site.py"], env)
    print("\nDaily pipeline 完成")


if __name__ == "__main__":
    main()
