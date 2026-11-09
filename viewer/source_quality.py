"""Validate scoped quality metadata without promoting dates or replacing native text."""
import hashlib


def attach_quality(prepared, quality, component=None):
    rows = {r['file_id']: r for r in quality['files']}
    if len(rows) != len(quality['files']) or set(rows) != {m['file_id'] for m, _, _, _ in prepared}:
        raise ValueError('Quality review document coverage changed')
    if component is not None and (component['file_id'] not in rows or any(component.get(k) for k in
            ('whole_document_review', 'complete_component_segmentation', 'primary_date_assigned',
             'native_text_replaced', 'verified_legal_status'))):
        raise ValueError('Unsupported component review promotion')
    for metric, _, extracted, _ in prepared:
        row = rows[metric['file_id']]
        if row['source_sha256'] != metric['sha256']:
            raise ValueError('Quality review source changed')
        pages = {p['page']: p['text'] for p in extracted['pages']}
        hashes = row['inspected_page_text_sha256']
        if set(map(int, hashes)) != set(row['visually_inspected_pdf_pages']):
            raise ValueError('Quality page scope changed')
        for number, expected in hashes.items():
            if int(number) not in pages or hashlib.sha256(pages[int(number)].encode()).hexdigest() != expected:
                raise ValueError('Quality native page changed')
        review = dict(file_id=metric['file_id'], source_sha256=metric['sha256'], notes='Initial acquisition triage: ' + row['notes'],
                      review_scope='Initial acquisition scope: ' + quality['method'], date_observations=[],
                      inspected_pdf_pages=row['visually_inspected_pdf_pages'])
        if component is not None and metric['file_id'] == component['file_id']:
            if component['source_sha256'] != metric['sha256'] or component['pdf_pages'] != len(pages):
                raise ValueError('Component review source changed')
            evidence = component['page_evidence']
            if {p['pdf_page'] for p in evidence} != set(component['visually_inspected_pdf_pages']):
                raise ValueError('Component page scope changed')
            for ev in evidence + component['component_start_observations']:
                text = pages.get(ev['pdf_page'])
                if text is None or hashlib.sha256(text.encode()).hexdigest() != ev['native_text_sha256']:
                    raise ValueError('Component native page changed')
                if 'native_quote' in ev and (not ev['native_quote'] or ev['native_quote'] not in text):
                    raise ValueError('Component quote absent')
                if ev.get('primary_date_assigned'):
                    raise ValueError('Component date promotion unsupported')
            review['component_assessment'] = component
        metric['source_quality_review'] = review
