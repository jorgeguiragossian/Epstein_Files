"""Validate local OCR/transcription evidence without replacing native extraction."""
import argparse
import hashlib
import json
from pathlib import Path


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def local_path(folder,relative):
    path=(folder/relative).resolve()
    if not path.is_relative_to(folder.resolve()):
        raise ValueError('OCR evidence outside batch folder')
    return path


def validate(folder, review_filename='ocr-transcription-review.json'):
    review=read(local_path(folder,review_filename))
    downloads={r['file_id']:r for r in read(folder/'downloads.json')['files']}
    metrics={r['file_id']:r for r in read(folder/'metrics.json')['files']}
    key=review['file_id'];item=downloads[key];metric=metrics[key]
    if digest(local_path(folder,item['local_path']))!=review['source_sha256'] or metric['sha256']!=review['source_sha256'] or item['sha256']!=review['source_sha256']:
        raise ValueError('Changed OCR source PDF')
    extraction_path=local_path(folder,metric['extraction_path'])
    extracted=read(extraction_path)
    if (digest(extraction_path)!=review['native_extraction_sha256'] or extracted['source_sha256']!=review['source_sha256']
            or len(extracted['pages'])!=metric['page_count']):
        raise ValueError('Changed native extraction')
    if any(review['eligibility'].values()):
        raise ValueError('OCR review cannot enable dates, verified transactions or identity inference')
    for page in review['page_findings']:
        number=page['pdf_page']
        if not isinstance(number,int) or not 1<=number<=len(extracted['pages']):
            raise ValueError('Invalid reviewed OCR page')
        if hashlib.sha256(extracted['pages'][number-1]['text'].encode()).hexdigest()!=page['native_text_sha256']:
            raise ValueError('Changed native page')
    images={}
    for attempt in review['ocr_attempts']:
        image=local_path(folder,attempt['image_path']);result=local_path(folder,attempt['result_path'])
        if digest(image)!=attempt['image_sha256'] or digest(result)!=attempt['result_sha256']:
            raise ValueError('Changed OCR image or result')
        value=read(result)
        if value['image_sha256']!=attempt['image_sha256'] or value['engine']!='Windows.Media.Ocr' or value['language']!='en-US':
            raise ValueError('OCR result image/engine mismatch')
        if len(value['lines'])!=attempt['recognized_lines'] or len(value['text'])!=attempt['recognized_characters']:
            raise ValueError('Changed OCR measurement')
        images[attempt['image_path']]=(attempt['pdf_page'],value['width'],value['height'])
    layer=review['transcription_layer'];path=local_path(folder,layer['local_path'])
    if digest(path)!=layer['sha256']:
        raise ValueError('Changed editorial transcription layer')
    transcription=read(path)
    if transcription['source_sha256']!=review['source_sha256'] or transcription['native_extraction_preserved'] is not True:
        raise ValueError('Invalid transcription source binding')
    readings=transcription['readings']
    if len({r['id'] for r in readings})!=len(readings):
        raise ValueError('Duplicate editorial reading')
    indexed={r['id']:r for r in readings}
    for field in review['reviewed_fields']:
        value=indexed[field['id']]
        if (value['pdf_page']!=field['pdf_page'] or value['kind']!=field['kind']
                or value['status']!=field['status'] or value['image_path']!=field['image_path']
                or value['region_pixels']!=field['region_pixels']
                or hashlib.sha256(value['literal_reading'].encode()).hexdigest()!=field['literal_sha256']):
            raise ValueError('Stale editorial field reading')
        if field['image_path'] not in images:
            raise ValueError('Editorial reading needs an OCR source image')
        page,width,height=images[field['image_path']]
        left,top,right,bottom=field['region_pixels']
        if page!=field['pdf_page'] or not 0<=left<right<=width or not 0<=top<bottom<=height:
            raise ValueError('Invalid editorial source region')
    if {f['id'] for f in review['reviewed_fields']}!=set(indexed):
        raise ValueError('Incomplete editorial reading review')
    return dict(reviewed_pdf_pages=len(review['page_findings']),local_ocr_attempts=len(review['ocr_attempts']),
                source_assisted_literal_readings=len(readings),native_extraction_preserved=True,
                primary_date_assigned=False,verified_transactions=False,public_site_integration=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--review',default='ocr-transcription-review.json',help='Review metadata path relative to batch folder')
    args=parser.parse_args()
    print(json.dumps(validate(args.out,args.review),indent=2))
