import urllib.request
import json
import sys

url = "https://pypi.org/pypi/webrtcvad-wheels/json"
data = json.loads(urllib.request.urlopen(url).read().decode())
releases = data['releases']['2.0.14']
has_arm = any('aarch64' in r['filename'] or 'arm' in r['filename'] for r in releases)
print(f"Has ARM wheels: {has_arm}")
for r in releases:
    if 'aarch64' in r['filename'] or 'arm' in r['filename']:
        print(r['filename'])
