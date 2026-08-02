"""
Full page render test — checks all Flask routes return HTTP 200 with non-empty HTML.
"""
import sys
sys.path.insert(0, '.')
from app import app

client = app.test_client()

routes = [
    ('/',           'Home / Index'),
    ('/dashboard',  'Executive Dashboard'),
    ('/data_collection', 'Data Collection'),
    ('/preprocessing',   'Preprocessing'),
    ('/transformation',  'Transformation'),
    ('/eda',             'Exploratory Analysis'),
    ('/text_mining',     'Text Mining'),
    ('/data_mining',     'Data Mining'),
    ('/prediction',      'Failure Prediction'),
    ('/insights',        'BI Insights'),
    ('/about',           'About'),
    ('/etl_monitor',     'ETL Monitor'),
]

print("=" * 62)
print(f"{'Route':<22} {'Page':<25} {'Status':<8} {'Bytes'}")
print("=" * 62)

all_ok = True
for route, name in routes:
    r = client.get(route)
    ok = r.status_code == 200 and len(r.data) > 500
    tag = 'PASS' if ok else 'FAIL'
    if not ok:
        all_ok = False
    print(f"[{tag}] {route:<20} {name:<25} HTTP {r.status_code}  {len(r.data):,} bytes")

print("=" * 62)
print("ALL PAGES PASS" if all_ok else "SOME PAGES FAILED")
