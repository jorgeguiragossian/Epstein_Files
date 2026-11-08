"""Write local Python API reference responses for the static-adapter tests."""
import json
import sys
from pathlib import Path
from urllib.parse import urlsplit,parse_qs
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'viewer'))
from server import Catalog

catalog=Catalog()
paths=['/api/overview','/api/people','/api/documents/EFTA00039806?page=2','/api/emails?document=EFTA02212905','/api/emails?filter=repeats','/api/emails?filter=reviewed','/api/emails?filter=boundary',
 '/api/search','/api/search?q=grand%20jury&dataset=6','/api/search?person=ghislaine-maxwell&date_from=2020-06-29&date_to=2020-06-29',
 '/api/search?q=EFTA00008529','/api/search?q=Epstein&quality=review','/api/search?q=SDNY_GM','/api/search?date_status=unreviewed','/api/search?person=alan-dershowitz']
rows=[]
paths+=['/api/coverage','/api/emails?filter=unreviewed','/api/emails?filter=sender','/api/emails?filter=recipient','/api/emails?filter=date']
paths+=['/api/words','/api/words?date_from=2020-01-01&date_to=2020-12-31','/api/words?dataset=6','/api/words?person=ghislaine-maxwell','/api/words?exclude=epstein%2Ccourt','/api/words?date_from=1900-01-01&date_to=1900-01-02']
paths+=['/api/words?date_from=2018-10-10&date_to=2018-10-10&dataset=10','/api/search?date_status=uncertain&q=EFTA02212924','/api/documents/EFTA02730477?page=1']
paths+=['/api/timeframes','/api/timeframes?date_from=2021-04-01&date_to=2021-04-30','/api/timeframes?dataset=6','/api/timeframes?person=ghislaine-maxwell','/api/timeframes?date_from=1900-01-01&date_to=1900-01-02','/api/timeframes?date_from=2017-05-23&date_to=2017-05-23']
paths+=['/api/documents/EFTA00032045?page=1','/api/documents/EFTA00039023?page=2','/api/emails?document=EFTA00014597','/api/emails?document=EFTA00021826','/api/emails?document=EFTA00032045','/api/search?q=EFTA00009713&date_status=uncertain']
paths+=['/api/documents/EFTA00018844','/api/timeframes?date_from=2019-07-24&date_to=2019-07-24','/api/words?date_from=2023-06-28&date_to=2023-06-28']
paths+=['/api/documents/EFTA00064578?page=6','/api/emails?document=EFTA00073640','/api/emails?document=EFTA00079911&page=2','/api/emails?document=EFTA00082128','/api/search?q=EFTA00075976&date_status=dated','/api/search?dataset=9&quality=review']
paths+=['/api/documents/EFTA00078194','/api/documents/EFTA00075976?page=3','/api/timeframes?date_from=2021-12-01&date_to=2021-12-01','/api/words?date_from=2008-06-18&date_to=2008-06-18','/api/search?q=EFTA00078194&date_from=2020-10-23&date_to=2020-10-23']
paths+=['/api/documents/EFTA01280951?page=2','/api/documents/EFTA01281641?page=2','/api/documents/EFTA01283668?page=3','/api/search?q=EFTA01280951&date_from=2015-11-01&date_to=2015-11-30','/api/emails?document=EFTA01283668','/api/search?dataset=10']
paths+=['/api/search?period_from=2015-11-30&period_to=2015-11-30','/api/search?period_from=2015-12-01&period_to=2015-12-01','/api/search?period_from=2015-11-01&date_status=uncertain','/api/search?period_to=2014-08-01','/api/search?period_from=2018-06-30&dataset=10&person=jeffrey-epstein','/api/search?period_from=2015-11-01&date_status=dated','/api/documents/EFTA01262784?page=7']
for path in paths:
    url=urlsplit(path);q={k:v[0] for k,v in parse_qs(url.query).items()}
    if url.path=='/api/overview':result=catalog.overview()
    elif url.path=='/api/coverage':result=catalog.coverage()
    elif url.path=='/api/words':result=catalog.words(**q)
    elif url.path=='/api/timeframes':result=catalog.timeframes(**q)
    elif url.path=='/api/people':result=catalog.people()
    elif url.path.startswith('/api/documents/'):result=catalog.document(url.path.rsplit('/',1)[-1],q.get('page',1))
    elif url.path=='/api/emails':result=catalog.emails(q.get('filter','all'),q.get('document',''),q.get('page',1))
    else:result=catalog.search(**q)
    rows.append({'path':path,'result':result})
(ROOT/'tmp').mkdir(exist_ok=True)
(ROOT/'tmp/pages-golden.json').write_text(json.dumps(rows,ensure_ascii=False),encoding='utf-8')
print(f'Prepared {len(rows)} reference responses.')
