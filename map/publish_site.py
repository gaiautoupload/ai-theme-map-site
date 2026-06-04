import filecmp
import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

CONFIG_PATH = Path(__file__).with_name('publish_config.json')
EXAMPLE_PATH = Path(__file__).with_name('publish_config.json.example')

DEFAULT_CONFIG = {
    "source_dir": "D:/map",
    "site_repo_dir": "D:/ai-theme-map-site",
    "copy_files": ["Index.html", "maps_repo.json"],
    "rename_map": {"Index.html": "index.html"},
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
    if dst.exists() and filecmp.cmp(src, dst, shallow=False):
        print(f'skip unchanged: {dst}')
        return False
    shutil.copy2(src, dst)
    print(f'copied: {src} -> {dst}')
    return True


def has_git_changes(repo_dir: Path) -> bool:
    result = run_capture(['git', 'status', '--porcelain'], repo_dir)
    return bool(result.stdout.strip())


def write_versioned_map(site_repo_dir: Path, source_map: Path) -> tuple[bool, str]:
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    versioned_name = f'{VERSIONED_MAP_BASENAME}_{stamp}.json'
    versioned_path = site_repo_dir / versioned_name
    shutil.copy2(source_map, versioned_path)
    print(f'copied versioned map: {source_map} -> {versioned_path}')
    return True, versioned_name


def update_index_map_pointer(index_path: Path, versioned_name: str) -> bool:
    if not index_path.exists():
        return False
    text = index_path.read_text(encoding='utf-8')
    marker = "const versionedMapCandidates = ["
    replacement = (
        "const versionedMapCandidates = [\n"
        f"                    './{versioned_name}',\n"
        "                    './maps_repo.json',\n"
        "                    './maps_repo_v4.json',\n"
        "                    './maps_repo_v3.json',\n"
        "                    './maps_repo_v2.json'\n"
        "                ];"
    )
    import re
    new_text, count = re.subn(
        r"const versionedMapCandidates = \[[\s\S]*?\];",
        replacement,
        text,
        count=1,
    )
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
        '這個 repo 是 GitHub Pages 展示站。\n\n'
        '內容來源：\n'
        '- 本地研究工作區 `D:\\map`\n'
        '- 由 `publish_site.py` 一鍵同步 `Index.html` 與 `maps_repo.json`\n\n'
        '部署方式：\n'
        '- GitHub Pages\n'
        '- branch: `main`\n'
        '- folder: `/root`\n'
    )
    if readme_path.exists() and readme_path.read_text(encoding='utf-8') == content:
        return False
    readme_path.write_text(content, encoding='utf-8')
    print(f'updated: {readme_path}')
    return True


def ensure_404(site_repo_dir: Path) -> bool:
    path = site_repo_dir / '404.html'
    content = """<!DOCTYPE html>
<html lang=\"zh-TW\">
<head>
  <meta charset=\"UTF-8\">
  <meta http-equiv=\"refresh\" content=\"0; url=./index.html\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
  <title>Redirecting...</title>
</head>
<body>
  <p>Redirecting to <a href=\"./index.html\">index.html</a>...</p>
</body>
</html>
"""
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

    versioned_name = None
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
