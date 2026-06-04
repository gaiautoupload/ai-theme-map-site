import sys, json
d = json.load(sys.stdin)
for k in d.keys():
    print(k)
