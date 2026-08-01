import json, sys
sys.path.insert(0, '.')
from app import app

client = app.test_client()

endpoints = [
    '/api/kpis',
    '/api/charts/industry',
    '/api/charts/funding_stages',
    '/api/charts/investors',
    '/api/charts/text_mining',
    '/api/charts/clustering',
    '/api/charts/association_rules',
    '/api/startups',
    '/api/etl/runs'
]

all_ok = True
for ep in endpoints:
    r = client.get(ep)
    d = json.loads(r.data)
    status = d.get('status', '?')
    data = d.get('data', None)
    count = len(data) if isinstance(data, list) else type(data).__name__
    ok = r.status_code == 200 and status == 'success'
    tag = 'PASS' if ok else 'FAIL'
    if not ok:
        all_ok = False
    print(f"[{tag}] {ep} -> HTTP {r.status_code} | {count} items")

print()
print('ALL ENDPOINTS PASSED' if all_ok else 'SOME ENDPOINTS FAILED')
