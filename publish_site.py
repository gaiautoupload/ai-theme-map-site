import filecmp
import json
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

CONFIG_PATH = Path(__file__).with_name('publish_config.json')
EXAMPLE_PATH = Path(__file__).with_name('publish_config.json.example')

DEFAULT_CONFIG = {
    "source_dir": "D:/ai-theme-map-site",
    "site_repo_dir": "D:/ai-theme-map-site",
    "copy_files": ["index.html", "maps_repo.json", "stocks_wiki.json"],
    "rename_map": {},
    "git_branch": "main",
    "run_generator_first": False,
    "generator_command": ["python", "map_generator.py"]
}

VERSIONED_MAP_BASENAME = 'maps_repo'


def ensure_example_config():
    if not EXAMPLE_PATH.exists():
        EXAMPLE_PATH.write_text(json.dumps(DEFAULT_CONFIG, indent=2, ensure_ascii=False), encoding='utf-8')


def load_config():
    ensure_example_config()
    if not CONFIG_PATH.exists():
        CONFIG_PATH.write_text(json.dumps(DEFAULT_CONFIG, indent=2, ensure_ascii=False), encoding='utf-8')
        print(f'已建立設定檔：{CONFIG_PATH}')
    return json.loads(CONFIG_PATH.read_text(encoding='utf-8'))


def run(cmd, cwd):
    print('>', ' '.join(cmd))
    subprocess.run(cmd, cwd=str(cwd), check=True)


def run_capture(cmd, cwd):
    print('>', ' '.join(cmd))
    return subprocess.run(cmd, cwd=str(cwd), check=True, capture_output=True, text=True)


def copy_if_changed(src: Path, dst: Path) -> bool:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.resolve() == dst.resolve():
        print(f'skip same file: {dst}')
        return False
    if dst.exists() and filecmp.cmp(src, dst, shallow=False):
        print(f'skip unchanged: {dst}')
        return False
    shutil.copy2(src, dst)
    print(f'copied: {src} -> {dst}')
    return True


def has_git_changes(repo_dir: Path) -> bool:
    result = run_capture(['git', 'status', '--porcelain'], repo_dir)
    return bool(result.stdout.strip())


def cleanup_old_versioned_maps(site_repo_dir: Path, keep_name: str | None = None) -> None:
    for p in site_repo_dir.glob(f'{VERSIONED_MAP_BASENAME}_*.json'):
        if keep_name and p.name == keep_name:
            continue
        if re.fullmatch(r'maps_repo_\d{8}_\d{6}\.json', p.name):
            p.unlink()
            print(f'removed old versioned map: {p.name}')


def write_versioned_map(site_repo_dir: Path, source_map: Path) -> tuple[bool, str]:
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    versioned_name = f'{VERSIONED_MAP_BASENAME}_{stamp}.json'
    versioned_path = site_repo_dir / versioned_name
    cleanup_old_versioned_maps(site_repo_dir)
    shutil.copy2(source_map, versioned_path)
    print(f'copied versioned map: {source_map} -> {versioned_path}')
    return True, versioned_name


def update_index_map_pointer(index_path: Path, versioned_name: str) -> bool:
    if not index_path.exists():
        return False
    text = index_path.read_text(encoding='utf-8')
    replacement = (
        "const versionedMapCandidates = [\n"
        f"                    './{versioned_name}',\n"
        "                    './maps_repo.json'\n"
        "                ];"
    )
    new_text, count = re.subn(
        r"const versionedMapCandidates = \[[\s\S]*?\];",
        replacement,
        text,
        count=1,
    )
    today = datetime.now().strftime('%Y-%m-%d')
    new_text = re.sub(r'(更新日期[:：]\s*)\d{4}[-/]\d{1,2}[-/]\d{1,2}', rf'\g<1>{today}', new_text)
    if count == 0:
        return False
    if new_text == text:
        return False
    index_path.write_text(new_text, encoding='utf-8')
    print(f'updated index pointer -> {versioned_name}')
    return True


def ensure_readme(site_repo_dir: Path) -> bool:
    readme_path = site_repo_dir / 'README.md'
    content = (
        '# AI Theme Map Site\n\n'
        '這是一包式正式專案：同一個 repo 同時包含 GitHub Pages 前端、主資料 `maps_repo.json`，以及每日主題地圖產線。\n\n'
        '正式入口：`index.html`。\n\n'
        '更新流程：\n'
        '- `python run_daily_pipeline.py`：探索題材、建立 evidence、重建 `maps_repo.json`、發布。\n'
        '- `python publish_site.py`：不重跑生成，只重新發布目前 `maps_repo.json`。\n\n'
        '資料原則：事實優先、白名單來源、股票需通過官方代號 registry 與 evidence 檢查。\n'
    )
    if readme_path.exists() and readme_path.read_text(encoding='utf-8') == content:
        return False
    readme_path.write_text(content, encoding='utf-8')
    print(f'updated: {readme_path}')
    return True


def ensure_404(site_repo_dir: Path) -> bool:
    path = site_repo_dir / '404.html'
    content = """<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Page not found</title><style>body{font-family:system-ui,'Microsoft JhengHei',sans-serif;background:#08090d;color:#f2efe8;display:grid;place-items:center;min-height:100vh;margin:0}a{color:#f1d18a}.card{max-width:520px;padding:32px;border:1px solid #30344a;border-radius:20px;background:#121420}</style></head><body><main class="card"><h1>找不到頁面</h1><p>這個頁面不存在，請回到 AI Theme Map Site 首頁。</p><p><a href="./index.html">回首頁</a></p></main></body></html>"""
    if path.exists() and path.read_text(encoding='utf-8') == content:
        return False
    path.write_text(content, encoding='utf-8')
    print(f'updated: {path}')
    return True


def main():
    config = load_config()
    source_dir = Path(config['source_dir'])
    site_repo_dir = Path(config['site_repo_dir'])
    copy_files = config.get('copy_files', [])
    rename_map = config.get('rename_map', {})
    git_branch = config.get('git_branch', 'main')

    if config.get('run_generator_first'):
        run(config.get('generator_command', ['python', 'map_generator.py']), source_dir)

    if not site_repo_dir.exists():
        raise FileNotFoundError(f'找不到展示 repo：{site_repo_dir}')

    changed = False
    source_map_path = None
    for name in copy_files:
        src = source_dir / name
        dst = site_repo_dir / rename_map.get(name, name)
        if not src.exists():
            raise FileNotFoundError(f'找不到來源檔案：{src}')
        changed = copy_if_changed(src, dst) or changed
        if name == 'maps_repo.json':
            source_map_path = src

    if source_map_path is not None:
        wrote_versioned, versioned_name = write_versioned_map(site_repo_dir, source_map_path)
        changed = wrote_versioned or changed
        changed = update_index_map_pointer(site_repo_dir / 'index.html', versioned_name) or changed

    changed = ensure_readme(site_repo_dir) or changed
    changed = ensure_404(site_repo_dir) or changed

    if not changed and not has_git_changes(site_repo_dir):
        print('沒有檔案變更，略過 commit / push')
        return

    commit_msg = f"publish site: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    run(['git', 'add', '.'], site_repo_dir)
    run(['git', 'commit', '-m', commit_msg], site_repo_dir)
    run(['git', 'push', 'origin', git_branch], site_repo_dir)
    print('發布完成')


if __name__ == '__main__':
    main()
