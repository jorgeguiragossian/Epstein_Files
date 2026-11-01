"""Offline checks for coverage, page references, and conservative classification."""
import importlib.util
import json
import io
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('pilot', ROOT / 'scripts/pilot.py')
pilot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pilot)


def pdf_with_lines(path, pages):
    writer = PdfWriter()
    for lines in pages:
        page = writer.add_blank_page(width=612, height=792)
        font = DictionaryObject({NameObject('/Type'): NameObject('/Font'), NameObject('/Subtype'): NameObject('/Type1'), NameObject('/BaseFont'): NameObject('/Helvetica')})
        page[NameObject('/Resources')] = DictionaryObject({NameObject('/Font'): DictionaryObject({NameObject('/F1'): writer._add_object(font)})})
        stream = DecodedStreamObject()
        encoded_lines = [line.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)') for line in lines]
        content = 'BT /F1 12 Tf 50 740 Td 15 TL ' + ' T* '.join(f'({line}) Tj' for line in encoded_lines) + ' ET'
        stream.set_data(content.encode('ascii'))
        page[NameObject('/Contents')] = writer._add_object(stream)
    with path.open('wb') as out:
        writer.write(out)


class PilotTests(unittest.TestCase):
    def test_missing_cached_download_and_html_response(self):
        for body, expected in [(b'%PDF-1.7\nfixture', 'downloaded'), (b'<html>Age verification</html>', 'non_pdf_response')]:
            with self.subTest(expected=expected), tempfile.TemporaryDirectory() as temp:
                out = Path(temp)
                item = {'dataset': 1, 'file_id': 'EFTA00000001', 'filename': 'EFTA00000001.pdf', 'url': 'https://www.justice.gov/epstein/files/DataSet%201/EFTA00000001.pdf'}
                pilot.save(out / 'selection.json', {'files': [item]})
                pilot.save(out / 'downloads.json', {'files': [dict(item, status='downloaded', local_path='cache/missing.pdf', sha256='old-hash')]})
                response = io.BytesIO(body)
                response.status = 200
                response.url = item['url']
                response.headers = {'Content-Type': 'application/pdf' if expected == 'downloaded' else 'text/html'}
                with patch.object(pilot.urllib.request, 'urlopen', return_value=response) as request, patch.object(pilot.time, 'sleep'):
                    pilot.download(out, age_confirmed=True)
                self.assertEqual(request.call_count, 1)
                records = pilot.read(out / 'downloads.json')['files']
                self.assertEqual(len(records), 1)
                self.assertEqual(records[0]['status'], expected)
                self.assertEqual(len(list((out / 'cache').glob('*.pdf'))), 1 if expected == 'downloaded' else 0)

    def test_deterministic_coverage(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            inventory = ROOT / 'data/inventory/2026-11-01/observed-files.csv'
            pilot.select(out, inventory)
            selected = pilot.read(out / 'selection.json')['files']
            self.assertEqual(len(selected), 100)
            self.assertEqual(len({row['url'] for row in selected}), 100)
            counts = {dataset: sum(row['dataset'] == dataset for row in selected) for dataset in range(1, 13)}
            self.assertEqual(counts, {d:13 if d == 6 else 17 if d == 7 else 7 for d in range(1, 13)})
            for d in (1, 2, 3, 4, 5, 8, 9, 10, 11, 12):
                subset = [r for r in selected if r['dataset'] == d]
                self.assertEqual(subset[0]['zero_based_pool_position'], 0)
                self.assertEqual(subset[-1]['zero_based_pool_position'], subset[-1]['observed_pool_size'] - 1)

    def test_page_evidence_and_false_positive_controls(self):
        with tempfile.TemporaryDirectory() as temp:
            path, target = Path(temp) / 'fixture.pdf', Path(temp) / 'extraction.json'
            pdf_with_lines(path, [['EFTA00000001'],
                ['From: sender@example.org', 'To: recipient@example.org', 'Sent: January 2, 2001', 'Subject: Example',
                 'A meeting mentioned on 2002-03-04 is not necessarily the date of this document.'],
                ['To: readers', 'Date: 2003-04-05', 'This standalone heading is not an email header block.']])
            pilot.extract_one(path, target)
            result = pilot.read(target)
            metrics = result['metrics']
            self.assertEqual(metrics['page_count'], 3)
            self.assertEqual(metrics['pages_processed'], 3)
            self.assertEqual(metrics['email_header_candidate_count'], 1)
            self.assertEqual(result['email_header_candidates'][0]['page'], 2)
            self.assertIsNone(metrics['document_date'])
            self.assertTrue(all(not d['validated'] for d in metrics['date_candidates']))
            self.assertEqual({d['page'] for d in metrics['date_candidates']}, {2, 3})
            self.assertEqual(metrics['page_metrics'][0]['substantive_alphanumeric_characters'], 0)
            self.assertTrue(metrics['ocr_review_needed'])
            self.assertNotIn('sender@example.org', json.dumps(metrics))


if __name__ == '__main__':
    unittest.main()
