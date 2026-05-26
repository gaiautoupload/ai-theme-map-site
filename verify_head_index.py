import subprocess
raw = subprocess.check_output(['git','show','HEAD:index.html'])
text = raw.decode('utf-8')
for needle in ['優先關注', 'broadened.push', 'const byDate', 'home-highlight-stocks']:
    print(needle, needle in text)
