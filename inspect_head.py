import subprocess, json
raw = subprocess.check_output(['git','show','HEAD:maps_repo.json'])
data = json.loads(raw.decode('utf-8'))
print('head_count=', len(data))
print('head_keys=', list(data.keys())[:8])
