import requests, json
url='http://127.0.0.1:5000/search'
payload={'ingredients':['rice','tomato','onion'],'cuisine':'any','diet':'any','difficulty':'any'}
r=requests.post(url, json=payload)
print('status', r.status_code)
try:
    j=r.json()
    print(json.dumps(j, indent=2))
except Exception as e:
    print('raw', r.text)
