import sys, json
d = json.load(sys.stdin)
print('Keys:', list(d.keys()))
print('Count:', len(d))
