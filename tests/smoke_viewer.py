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
    assert overview['documents'] == 190 and overview['pages'] == 2826
    wave9 = get('/api/documents/EFTA00007501')
    assert wave9['date_review']['status']=='unreviewed'
    assert wave9['source_quality_review']['ocr_assessment']['inspected_pdf_pages']==[1]
    assert wave9['source_quality_review']['ocr_assessment']['native_replacement_accepted'] is False
    assert 'Aug 20, 2006' in wave9['page']['text']
    assert get('/api/emails?document=EFTA00005707')['total_groups']==0
    matches = get('/api/search?q=grand%20jury&dataset=6')
    assert matches['total_documents'] == 11 and matches['total_matching_pages'] == 97
    page = get('/api/documents/EFTA00008529?page=2')
    assert page['page']['number'] == 2 and page['page']['text']
    assert get('/api/search?quality=review')['total_documents'] == 95
    assert get('/api/search?q=zzznomatchpilot')['total_documents'] == 0
    assert overview['date_status_counts']=={'dated':71,'uncertain':49,'unreviewed':70}
    words=get('/api/words')
    assert (words['eligible_dated_documents'],words['excluded_without_reviewed_date'])==(71,119)
    reporting=get('/api/words?date_basis=reporting_period')
    assert (reporting['eligible_reporting_period_documents'],reporting['excluded_without_reviewed_period'],reporting['selected_documents'])==(6,184,6)
    selected=get('/api/words?date_basis=reporting_period&date_from=2015-11-30&date_to=2015-11-30')
    assert (selected['selected_documents'],selected['selected_pages'])==(1,2)
    assert all(s['file_id']=='EFTA01280951' for term in selected['terms'] for s in term['sources'])
    assert get('/api/words?date_basis=reporting_period&date_from=2015-12-01&date_to=2015-12-01')['selected_documents']==0
    assert get('/api/documents/EFTA00039826')['date_review']['date_type']=='letter'
    assert get('/api/documents/EFTA00008892')['date_review']['date_type']=='presentation'
    assert get('/api/documents/EFTA02212924')['date_review']['primary_date'] is None
    assert get('/api/documents/EFTA00018844')['date_review']['date_type']=='court_order'
    assert get('/api/documents/EFTA00034623')['date_review']['primary_date']=='2019-07-24'
    assert get('/api/documents/EFTA00009713')['date_review']['status']=='uncertain'
    memo=get('/api/search?q=EFTA00034623&date_from=2019-07-23&date_to=2019-07-23')
    assert memo['total_documents']==0
    timeline=get('/api/timeframes')
    assert (timeline['selected_documents'],timeline['prepared_briefs'],timeline['date_evidence_only'],timeline['source_checked_briefs'])==(71,36,35,36)
    assert get('/api/timeframes?date_from=2017-05-23&date_to=2017-05-23')['selected_documents']==0
    dated=get('/api/search?date_from=2019-06-18&date_to=2019-06-18')
    assert dated['total_documents']==1 and dated['results'][0]['id']=='EFTA00008529'
    assert get('/api/search?date_status=uncertain')['total_documents']==49
    assert get('/api/search?date_status=undated')['total_documents']==0
    assert get('/api/search?date_status=unreviewed')['total_documents']==70
    assert get('/api/search?date_from=2014-01-01&date_to=2014-01-01&q=EFTA02730265')['total_documents']==0
    assert get('/api/documents/EFTA00039806')['date_review']['evidence_page']==2
    people=get('/api/people')['people']
    snapshot=json.loads((Path(__file__).resolve().parents[1]/'data/pilot/2026-11-01/people-coverage.json').read_text(encoding='utf-8'))
    assert len(people)==len(snapshot['people'])==22
    fields=('id','label','documents','pages','occurrences')
    assert {p['id'] for p in people}=={p['id'] for p in snapshot['people']}
    for old in snapshot['people']:
        current=next(p for p in people if p['id']==old['id'])
        assert all(current[k]>=old[k] for k in ('documents','pages','occurrences'))
    names={p['id']:p for p in people}
    assert names['ghislaine-maxwell']['documents']==27 and names['ghislaine-maxwell']['pages']==119
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
    assert email_review['summary']['candidate_occurrences']==194
    assert email_review['summary']['source_review']['reviewed_candidates']==120
    assert email_review['summary']['unique_messages'] is None
    assert get('/api/emails?filter=repeats')['total_groups']==0
    inline=get('/api/emails?document=EFTA02212905')
    assert inline['total_groups']==1
    assert 'date_missing' in inline['results'][0]['representative']['flags']
    assert inline['results'][0]['representative']['parsed_timestamp_candidate'] is None
    assert 'May 18, 2017' in inline['results'][0]['representative']['body']
    added=get('/api/documents/EFTA00032045?page=1')
    assert added['date_review']['primary_date']=='2020-07-06' and added['page']['text'].startswith('Front ')
    new_email=get('/api/emails?document=EFTA00032045')['results'][0]['representative']
    assert new_email['derived_text_layer']['kind']=='reviewed_header_labels_v1'
    assert new_email['native_header_evidence'][0]['text']=='Front '
    assert '\n'.join(s['text'] for s in new_email['body_partition']['spans'])==new_email['body']
    assert get('/api/documents/EFTA00075976')['date_review']['evidence_page']==3
    assert get('/api/documents/EFTA00059374')['date_review']['primary_date']=='2019-08-10'
    assert get('/api/documents/EFTA00078194')['date_review']['status']=='uncertain'
    assert get('/api/documents/EFTA00039153')['date_review']['status']=='uncertain'
    assert get('/api/search?q=EFTA00078194&date_from=2020-10-23&date_to=2020-10-23')['total_documents']==0
    assert get('/api/search?q=EFTA00073640&date_from=2021-11-30&date_to=2021-11-30')['total_documents']==0
    assert get('/api/search?q=EFTA00073640&date_from=2021-12-01&date_to=2021-12-01')['total_documents']==1
    assert get('/api/documents/EFTA01262784')['date_review']['primary_date']=='2019-06-27'
    period=get('/api/search?period_from=2015-11-30&period_to=2015-11-30')
    assert {r['id'] for r in period['results']}=={'EFTA01280951'}
    assert get('/api/search?period_from=2015-12-01&period_to=2015-12-01')['total_documents']==0
    assert get('/api/search?period_from=2015-11-01&date_status=uncertain')['total_documents']==5
    assert get('/api/search?period_from=2015-11-01&date_status=dated')['total_documents']==0
    layout=get('/api/documents/EFTA01280951?page=2')
    assert layout['source_quality_review']['layout_status']=='multiple_date_amount_columns_flattened'
    assert layout['date_review']['status']=='uncertain'
    assert get('/api/search?q=EFTA01280951&date_from=2015-11-01&date_to=2015-11-30')['total_documents']==0
    assert get('/api/documents/EFTA01281641')['source_quality_review']['layout_status']=='handwriting_ocr_inadequate_separate_editorial_layer'
    assert get('/api/emails?document=EFTA01283668')['total_groups']==0
    wave=get('/api/emails?document=EFTA00073640')['results']
    assert any(r['representative']['source_review']['header_status']=='source_order_mismatch' for r in wave)
    assert get('/api/documents/EFTA00064578?page=6')['date_review']['primary_date']=='2022-03-10'
    assert get('/api/emails')['summary']['body_partitions']['annotated_candidates']==53
    mismatch=get('/api/emails?document=EFTA02215291&filter=boundary')['results'][0]['representative']
    assert mismatch['source_review']['boundary_status']=='source_order_mismatch' and not mismatch.get('body_partition')
    assert get('/api/emails?document=EFTA02216544')['results'][0]['representative']['source_review']['boundary_status']=='calendar_alert_not_correspondence'
    assert get('/api/documents/EFTA02215926?page=3')['date_review']['primary_date']=='2017-06-14'
    assert get('/api/documents/EFTA02213471')['date_review']['primary_date']=='2017-05-19'
    assert get('/api/documents/EFTA02213987')['date_review']['status']=='uncertain'
    assert get('/api/documents/EFTA02216544')['date_review']['primary_date'] is None
    assert get('/api/search?q=EFTA02215291&date_from=2017-06-15&date_to=2017-06-15')['total_documents']==0
    assert get('/api/timeframes?dataset=11&date_from=2017-05-01&date_to=2017-07-31')['date_evidence_only']==8
    compound=get('/api/documents/EFTA02857524?page=80')['source_quality_review']['component_assessment']
    assert not compound['whole_document_review'] and len(compound['visually_inspected_pdf_pages'])==14
    assert get('/api/documents/EFTA02731708')['page']['text'].strip()=='EFTA02731708'
    assert get('/api/documents/EFTA02731593')['date_review']['primary_date']=='2023-06-22'
    assert get('/api/documents/EFTA02857524')['date_review']['status']=='uncertain'
    assert get('/api/documents/EFTA02731708')['date_review']['primary_date'] is None
    assert get('/api/search?q=EFTA02731593&date_from=2023-06-21&date_to=2023-06-21')['total_documents']==0
    photo=get('/api/documents/EFTA00000002')
    assert photo['page']['text'].strip()=='EFTA00000002' and photo['date_review']['status']=='uncertain'
    log=get('/api/documents/EFTA00003158')
    assert 'three local Windows OCR passes' in log['source_quality_review']['notes']
    assert 'sample_log_row_literal' not in json.dumps(log) and 'literal_reading' not in json.dumps(log)
    assert get('/api/emails?document=EFTA00003158')['total_groups']==0
    assert log['date_review']['status']=='uncertain' and log['date_review']['primary_date'] is None
    assert get('/api/search?q=EFTA00003158&date_from=2019-08-12&date_to=2019-08-12')['total_documents']==0
    added=get('/api/documents/EFTA00003601?page=2')
    assert added['page_count']==2 and added['page']['number']==2 and added['date_review']['status']=='uncertain'
    assert 'Partial camera overlay' in get('/api/documents/EFTA00003726')['source_quality_review']['notes']
    assert get('/api/emails?document=EFTA00003601')['total_groups']==0
    overlay=get('/api/documents/EFTA00003726')['date_review']
    assert overlay['status']=='uncertain' and overlay['primary_date'] is None
    assert added['date_review']['inspected_pdf_pages']==[1,2]
    assert get('/api/search?q=EFTA00003726&date_from=2020-01-01&date_to=2025-12-31')['total_documents']==0
    receipt=get('/api/documents/EFTA00004231')
    assert receipt['date_review']['status']=='dated'
    assert receipt['source_quality_review']['ocr_assessment']['native_replacement_accepted'] is False
    assert get('/api/documents/EFTA00005586?page=119')['page']['number']==119
    assert get('/api/emails?document=EFTA00004577')['total_groups']==0
    assert 'literal_reading' not in json.dumps(receipt)
    assert receipt['date_review']['primary_date']=='2020-07-17' and receipt['date_review']['date_type']=='evidence_received'
    assert get('/api/documents/EFTA00005586')['date_review']['status']=='uncertain'
    assert get('/api/search?q=EFTA00003931&date_from=2020-07-27&date_to=2020-07-27')['total_documents']==0
    assert get('/api/timeframes?dataset=3&date_from=2020-07-17&date_to=2020-07-17')['date_evidence_only']==1
    for path, status in [('/api/documents/EFTA00008529?page=0',400),('/README.md',404),('/pdf/../../README.md',404),('/api/words?date_basis=unknown',400),('/api/search?date_from=2021-02-29',400),('/api/search?period_from=2021-02-29',400),('/api/search?period_from=2021-01-01&period_to=2020-01-01',400),('/api/search?date_from=2020-01-01&date_to=2019-01-01',400),('/api/search?person=unknown',400),('/api/emails?filter=invented',400),('/api/emails?document=../../README.md',400),('/api/emails?page=0',400)]:
        try: get(path)
        except HTTPError as exc: assert exc.code == status, (path,exc.code)
        else: raise AssertionError(f'Expected HTTP {status} for {path}')
    for source_id in ('EFTA00008529','EFTA00032045'):
        with urlopen(Request(BASE + '/pdf/'+source_id,headers={'Range':'bytes=0-7'}),timeout=10) as response:
            body = response.read()
            assert response.status == 206 and len(body) == 8 and body.startswith(b'%PDF-')
    print('HTTP smoke passed: coverage, search, person/date filters, email review, page evidence, input errors, file-route isolation, and PDF byte ranges.')


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url',default=BASE)
    BASE=parser.parse_args().base_url.rstrip('/')
    main()
