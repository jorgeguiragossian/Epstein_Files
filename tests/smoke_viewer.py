"""Integration smoke check against a running local pilot viewer."""
import json
import argparse
from pathlib import Path
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
    assert overview['date_status_counts']=={'dated':36,'uncertain':4,'unreviewed':60}
    words=get('/api/words')
    assert (words['eligible_dated_documents'],words['excluded_without_reviewed_date'])==(36,64)
    assert get('/api/documents/EFTA00039826')['date_review']['date_type']=='letter'
    assert get('/api/documents/EFTA00008892')['date_review']['date_type']=='presentation'
    assert get('/api/documents/EFTA02212924')['date_review']['primary_date'] is None
    timeline=get('/api/timeframes')
    assert (timeline['selected_documents'],timeline['prepared_briefs'],timeline['date_evidence_only'])==(36,8,28)
    assert get('/api/timeframes?date_from=2017-05-23&date_to=2017-05-23')['selected_documents']==0
    dated=get('/api/search?date_from=2019-06-18&date_to=2019-06-18')
    assert dated['total_documents']==1 and dated['results'][0]['id']=='EFTA00008529'
    assert get('/api/search?date_status=uncertain')['total_documents']==4
    assert get('/api/search?date_status=undated')['total_documents']==0
    assert get('/api/search?date_status=unreviewed')['total_documents']==60
    assert get('/api/search?date_from=2014-01-01&date_to=2014-01-01&q=EFTA02730265')['total_documents']==0
    assert get('/api/documents/EFTA00039806')['date_review']['evidence_page']==2
    people=get('/api/people')['people']
    snapshot=json.loads((Path(__file__).resolve().parents[1]/'data/pilot/2026-11-01/people-coverage.json').read_text(encoding='utf-8'))
    assert len(people)==len(snapshot['people'])==22
    fields=('id','label','documents','pages','occurrences')
    assert sorted([{k:p[k] for k in fields} for p in people],key=lambda p:p['id'])==sorted(snapshot['people'],key=lambda p:p['id'])
    names={p['id']:p for p in people}
    assert names['ghislaine-maxwell']['documents']==19 and names['ghislaine-maxwell']['pages']==102
    person=get('/api/search?person=ghislaine-maxwell&date_from=2020-06-29&date_to=2020-06-29')
    assert person['total_documents']==3 and {r['id'] for r in person['results']}=={'EFTA00008631','EFTA00008892','EFTA00008920'}
    assert person['results'][0]['matching_pages'][0]==1
    page=get('/api/documents/EFTA00008631?page=1')
    assert any(m['id']=='ghislaine-maxwell' for m in page['page']['name_mentions'])
    assert get('/api/search?person=ghislaine-maxwell&dataset=1')['total_documents']==0
    expanded=get('/api/search?person=alan-dershowitz')
    assert expanded['total_documents']==1 and expanded['results'][0]['first_page']==14
    assert expanded['results'][0]['matching_pages']==[14]
    assert get('/api/search?person=ken-starr')['total_documents']==4
    email_metadata=json.loads((Path(__file__).resolve().parents[1]/'data/pilot/2026-11-01/email-summary.json').read_text(encoding='utf-8'))
    email_review=get('/api/emails')
    assert email_review['summary']==email_metadata['summary']
    assert email_review['summary']['unique_messages'] is None
    assert get('/api/emails?filter=repeats')['total_groups']==0
    inline=get('/api/emails?document=EFTA02212905')
    assert inline['total_groups']==1
    assert 'date_missing' in inline['results'][0]['representative']['flags']
    assert inline['results'][0]['representative']['parsed_timestamp_candidate'] is None
    assert 'May 18, 2017' in inline['results'][0]['representative']['body']
    for path, status in [('/api/documents/EFTA00008529?page=0',400),('/README.md',404),('/pdf/../../README.md',404),('/api/search?date_from=2021-02-29',400),('/api/search?date_from=2020-01-01&date_to=2019-01-01',400),('/api/search?person=unknown',400),('/api/emails?filter=invented',400),('/api/emails?document=../../README.md',400),('/api/emails?page=0',400)]:
        try: get(path)
        except HTTPError as exc: assert exc.code == status, (path,exc.code)
        else: raise AssertionError(f'Expected HTTP {status} for {path}')
    with urlopen(Request(BASE + '/pdf/EFTA00008529',headers={'Range':'bytes=0-7'}),timeout=10) as response:
        body = response.read()
        assert response.status == 206 and len(body) == 8 and body.startswith(b'%PDF-')
    print('HTTP smoke passed: coverage, search, person/date filters, email review, page evidence, input errors, file-route isolation, and PDF byte ranges.')


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url',default=BASE)
    BASE=parser.parse_args().base_url.rstrip('/')
    main()
