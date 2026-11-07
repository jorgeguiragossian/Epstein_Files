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


def header_fragment_layer(extracted, file_id, source_sha256, review):
    """Exclude a reviewed unresolved fragment from scanning, retaining it verbatim."""
    if review['file_id'] != file_id or review['source_sha256'] != source_sha256 or extracted['source_sha256'] != source_sha256:
        raise ValueError('Header fragment source mismatch')
    if review['reviewer'] != 'Codex' or not review['reviewed_on']:
        raise ValueError('Missing fragment review')
    derived = copy.deepcopy(extracted)
    seen = set()
    for item in review['fragments']:
        page, line = item['page'], item['line']
        if (page, line) in seen or not 1 <= page <= len(extracted['pages']):
            raise ValueError('Duplicate or invalid fragment reference')
        seen.add((page, line))
        text = extracted['pages'][page - 1]['text']
        lines = text.splitlines()
        if hashlib.sha256(text.encode()).hexdigest() != item['page_text_sha256']:
            raise ValueError('Stale fragment page text')
        if not 1 < line < len(lines) or lines[line - 1] != item['native_line']:
            raise ValueError('Stale fragment line')
        # This scoped layer supports only a fragment bracketed by explicit labels.
        if lines[line - 2].strip() != 'To:' or lines[line].strip() != 'Cc:':
            raise ValueError('Fragment is not in the reviewed To/Cc header interval')
        mutable = derived['pages'][page - 1]['text'].splitlines(keepends=True)
        ending = '\r\n' if mutable[line - 1].endswith('\r\n') else ('\n' if mutable[line - 1].endswith('\n') else '')
        mutable[line - 1] = ending
        derived['pages'][page - 1]['text'] = ''.join(mutable)
    derived['derived_text_layer'] = dict(kind='reviewed_header_fragments_v1', native_extraction_preserved=True,
                                        file_id=file_id, source_sha256=source_sha256,
                                        reviewed_on=review['reviewed_on'], unresolved_fragments=copy.deepcopy(review['fragments']))
    return derived
