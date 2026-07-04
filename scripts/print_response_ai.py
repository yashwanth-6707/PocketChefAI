import json
p='response.json'
with open(p,'rb') as f:
    raw=f.read()
# Try utf-8, fallback to utf-16
for enc in ('utf-8','utf-16','utf-16-le','utf-16-be'):
    try:
        s=raw.decode(enc)
        break
    except Exception:
        s=None
if s is None:
    print('Could not decode response.json')
    raise SystemExit(1)
obj=json.loads(s)
ai=obj.get('data',{}).get('ai_instructions')
print('===AI_INSTRUCTIONS===')
print(ai)
print('===END===')
