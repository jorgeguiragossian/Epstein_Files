"""Opt-in, source-bound label readings; never overwrite native extraction."""
import copy
import hashlib


def header_label_layer(extracted, file_id, source_sha256, review):
    if review['file_id'] != file_id or review['source_sha256'] != source_sha256 or extracted['source_sha256'] != source_sha256:
        raise ValueError('Header label review source mismatch')
    if review['reviewer'] != 'Codex' or not review['reviewed_on']:
        raise ValueError('Missing explicit editorial review')
    allowed = {'from': {'From', 'Front'}, 'to': {'To'}}
    seen = set()
    for item in review['labels']:
        page, line = item['page'], item['line']
        if (page, line) in seen or not 1 <= page <= len(extracted['pages']):
            raise ValueError('Duplicate or invalid label reference')
        seen.add((page, line))
        text = extracted['pages'][page - 1]['text']
        lines = text.splitlines()
        if hashlib.sha256(text.encode()).hexdigest() != item['page_text_sha256']:
            raise ValueError('Stale native page text')
        if not 1 <= line <= len(lines) or lines[line - 1] != item['native_line']:
            raise ValueError('Stale native line')
        if item['field'] not in allowed or item['native_line'].strip() not in allowed[item['field']]:
            raise ValueError('Only reviewed label-only From/To readings are supported')
    derived = copy.deepcopy(extracted)
    for item in review['labels']:
        page = derived['pages'][item['page'] - 1]
        lines = page['text'].splitlines(keepends=True)
        original = lines[item['line'] - 1]
        ending = '\r\n' if original.endswith('\r\n') else ('\n' if original.endswith('\n') else '')
        lines[item['line'] - 1] = item['field'].title() + ':' + ending
        page['text'] = ''.join(lines)
    derived['derived_text_layer'] = dict(kind='reviewed_header_labels_v1', native_extraction_preserved=True,
                                        file_id=file_id, source_sha256=source_sha256,
                                        reviewed_on=review['reviewed_on'], labels=copy.deepcopy(review['labels']))
    return derived
