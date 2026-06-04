import os
import subprocess
import sys
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SITE_URL = os.getenv('MAP_SITE_URL', 'https://gaiautoupload.github.io/ai-theme-map-site/')


def env_defaults():
    env = os.environ.copy()
    env.setdefault('MAP_VLLM_URL', 'https://vllm-a5000.iii-ei-stack.com/v1/chat/completions')
    env.setdefault('MAP_MODEL_NAME', 'cyankiwi/Qwen3.6-35B-A3B-AWQ-4bit')
    env.setdefault('MAP_SEARCH_MODE', 'search_augmented')
    env.setdefault('MAP_SEARCH_BACKEND', 'whitelist_rss')
    env.setdefault('MAP_SEARCH_MIN_DELAY', '3.5')
    env.setdefault('MAP_SEARCH_MAX_DELAY', '7.5')
    env.setdefault('MAP_SEARCH_FETCH_ENABLED', '1')
    env.setdefault('MAP_DISCOVERY_RUN_TOP', '5')
    return env


def run(name, cmd, env):
    print('\n' + '=' * 72)
    print(name)
    print('>', ' '.join(cmd))
    print('=' * 72)
    subprocess.run(cmd, cwd=str(BASE_DIR), check=True, env=env)


def verify_local():
    import json
    p = BASE_DIR / 'maps_repo.json'
    repo = json.loads(p.read_text(encoding='utf-8'))
    missing = []
    for k, v in repo.items():
        if not isinstance(v, dict):
            continue
        sl = v.get('structure_layers')
        cf = v.get('capital_flow')
        if not isinstance(sl, list) or len(sl) < 3:
            missing.append((k, 'structure_layers'))
        if not isinstance(cf, list) or len(cf) < 3:
            missing.append((k, 'capital_flow'))
    print('\nLocal verification:')
    print('themes:', len(repo))
    print('missing required rich fields:', missing[:20])
    if missing:
        raise RuntimeError('仍有主題缺少資金流或產業結構欄位')


def verify_site():
    try:
        with urllib.request.urlopen(SITE_URL + '?nocache=oneclick', timeout=30) as r:
            print('\nSite HTTP:', r.status, SITE_URL)
            if r.status != 200:
                raise RuntimeError('site status not 200')
    except Exception as e:
        print('Site verification warning:', e)
        print('GitHub Pages 可能仍在同步，請稍後重新整理。')


def main():
    py = sys.executable or 'python'
    env = env_defaults()
    print('One-click AI theme map update')
    print('writer model:', env.get('MAP_MODEL_NAME'))
    print('vLLM endpoint:', env.get('MAP_VLLM_URL'))
    print('search backend:', env.get('MAP_SEARCH_BACKEND'))

    run('[1/7] build ticker registry', [py, 'build_ticker_registry.py'], env)
    run('[2/7] theme discovery from trusted RSS/search', [py, 'theme_discovery.py'], env)
    run('[3/7] build evidence files', [py, 'evidence_builder.py'], env)
    run('[4/7] generate new articles with vLLM', [py, 'rebuild_maps_repo_from_discovery.py'], env)
    run('[5/7] merge old cards back', [py, 'merge_existing_cards.py'], env)
    run('[6/7] enrich capital flow and structure layers', [py, 'enrich_map_layers_and_flow.py'], env)
    verify_local()
    run('[7/7] publish and push to GitHub Pages repo', [py, 'publish_site.py'], env)
    verify_site()
    print('\nDONE. Open:', SITE_URL)


if __name__ == '__main__':
    main()
