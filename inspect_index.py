from pathlib import Path
text = Path(r'D:\ai-theme-map-site\index.html').read_text(encoding='utf-8')
chunks = []
for name in ['normalizeRepository', 'renderDashboardHome', 'updateSiteMeta', 'loadMapWorkspace']:
    i = text.find(f'function {name}')
    chunks.append(f'\n=== {name} @ {i} ===\n')
    chunks.append(text[i:i+3500])
Path(r'D:\ai-theme-map-site\inspect_index_output.txt').write_text(''.join(chunks), encoding='utf-8')
print('ok')
