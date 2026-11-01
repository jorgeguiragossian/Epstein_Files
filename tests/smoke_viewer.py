"""Integration smoke check against a running local pilot viewer."""
import json
import argparse
from urllib.error import HTTPError
from urllib.request import Request, urlopen

BASE = 'http://127.0.0.1:8765'


def get(path):
    with urlopen(BASE + path,timeout=10) as response:
        return json.load(response)


def main():
    overview = get('/api/overview')
    assert overview['documents'] == 100 and overview['pages'] == 1787
    matches = get('/api/search?q=grand%20jury&dataset=6')
    assert matches['total_documents'] == 11 and matches['total_matching_pages'] == 97
    page = get('/api/documents/EFTA00008529?page=2')
    assert page['page']['number'] == 2 and page['page']['text']
    assert get('/api/search?quality=review')['total_documents'] == 52
    assert get('/api/search?q=zzznomatchpilot')['total_documents'] == 0
    assert overview['date_status_counts']=={'dated':17,'uncertain':3,'unreviewed':80}
    dated=get('/api/search?date_from=2019-06-18&date_to=2019-06-18')
    assert dated['total_documents']==1 and dated['results'][0]['id']=='EFTA00008529'
    assert get('/api/search?date_status=uncertain')['total_documents']==3
    assert get('/api/search?date_status=undated')['total_documents']==0
    assert get('/api/search?date_status=unreviewed')['total_documents']==80
    assert get('/api/search?date_from=2014-01-01&date_to=2014-01-01&q=EFTA02730265')['total_documents']==0
    assert get('/api/documents/EFTA00039806')['date_review']['evidence_page']==2
    for path, status in [('/api/documents/EFTA00008529?page=0',400),('/README.md',404),('/pdf/../../README.md',404),('/api/search?date_from=2021-02-29',400),('/api/search?date_from=2020-01-01&date_to=2019-01-01',400)]:
        try: get(path)
        except HTTPError as exc: assert exc.code == status, (path,exc.code)
        else: raise AssertionError(f'Expected HTTP {status} for {path}')
    with urlopen(Request(BASE + '/pdf/EFTA00008529',headers={'Range':'bytes=0-7'}),timeout=10) as response:
        body = response.read()
        assert response.status == 206 and len(body) == 8 and body.startswith(b'%PDF-')
    print('HTTP smoke passed: coverage, real search, filters, page text, input errors, file-route isolation, and PDF byte ranges.')


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url',default=BASE)
    BASE=parser.parse_args().base_url.rstrip('/')
    main()
