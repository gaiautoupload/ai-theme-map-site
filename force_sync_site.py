import shutil, subprocess, pathlib
src_dir = pathlib.Path(r'D:\map')
dst_dir = pathlib.Path(r'D:\ai-theme-map-site')
for name in ['Index.html', 'maps_repo.json']:
    src = src_dir / name
    dst = dst_dir / ('index.html' if name == 'Index.html' else name)
    shutil.copyfile(src, dst)
    print('copied', src, '->', dst)
subprocess.check_call(['git', 'status', '--short'], cwd=str(dst_dir))
subprocess.check_call(['git', 'add', 'index.html', 'maps_repo.json'], cwd=str(dst_dir))
subprocess.check_call(['git', 'commit', '-m', 'force-sync-index-data'], cwd=str(dst_dir))
subprocess.check_call(['git', 'push', 'origin', 'main'], cwd=str(dst_dir))
