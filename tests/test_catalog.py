import importlib.util
import hashlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('catalog_script', ROOT / 'scripts/catalog.py')
catalog = importlib.util.module_from_spec(spec)
spec.loader.exec_module(catalog)


def html(file='EFTA1.pdf', extra=''):
    return (f"<a href='/epstein/files/DataSet%201/{file}'>file</a>" + extra).encode()


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = catalog.connect(Path(self.temp.name) / 'catalog.sqlite')

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def test_parser_scopes_links_and_refuses_access_pages(self):
        files, pages = catalog.parse_listing(html(extra="<a href='?page=12'>last</a><a href='https://evil.example/epstein/files/x.pdf'>bad</a><a href='/epstein/doj-disclosures/data-set-2-files?page=99'>other</a>").decode(), 1)
        self.assertEqual((len(files), pages), (1, 13))
        with self.assertRaises(ValueError):
            catalog.parse_listing('<h1>Access denied</h1>', 1)

    def test_observations_are_idempotent_and_provenance_is_retained(self):
        catalog.record(self.db, 1, 0, html(), '2026-11-01', 'snapshot-a')
        catalog.record(self.db, 1, 0, html(), '2026-11-01', 'snapshot-a')
        catalog.record(self.db, 1, 0, html(), '2026-11-07', 'snapshot-b')
        self.assertEqual(self.db.execute('SELECT count(*) FROM files').fetchone()[0], 1)
        self.assertEqual(self.db.execute('SELECT count(*) FROM observations').fetchone()[0], 2)
        row = self.db.execute('SELECT first_seen,last_seen FROM files').fetchone()
        self.assertEqual(tuple(row), ('2026-11-01', '2026-11-07'))
        with self.assertRaises(ValueError):
            catalog.record(self.db, 1, 1, html(), '2026-11-07', 'same-content')
        self.assertEqual(self.db.execute('SELECT count(*) FROM observations').fetchone()[0], 2)

    def test_forbidden_stops_batch_preserving_successful_observation(self):
        catalog.record(self.db, 1, 0, html(extra="<a href='?page=2'>last</a>"), '2026-11-01', 'snapshot-a')
        error = catalog.urllib.error.HTTPError(catalog.listing_url(1, 1), 403, 'Forbidden', {}, None)
        with patch.object(catalog.urllib.request, 'urlopen', side_effect=error) as fetch:
            self.assertEqual(catalog.crawl(self.db, 12, .5, cache=Path(self.temp.name)), 1)
            self.assertEqual(fetch.call_count, 1)
        self.assertEqual(self.db.execute('SELECT count(*) FROM observations').fetchone()[0], 1)
        self.assertEqual(self.db.execute('SELECT status,http_status FROM attempts').fetchone()[:], ('access_blocked', 403))

    def test_export_does_not_turn_a_partial_listing_into_an_exact_total(self):
        catalog.record(self.db, 1, 0, html(extra="<a href='?page=2'>last</a>"), '2026-11-01', 'snapshot-a')
        pilot = Path(self.temp.name) / 'pilot'
        pilot.mkdir()
        for name in ('downloads.json', 'metrics.json'):
            (pilot / name).write_text('{"files": []}')
        out = Path(self.temp.name) / 'export'
        catalog.export(self.db, out, pilot)
        value = json.loads((out / 'catalog.json').read_text())
        self.assertIsNone(value['current_total_files'])
        self.assertEqual(value['datasets'][0]['listing_coverage'], 'partial')
        self.assertEqual(value['datasets'][0]['observed_listing_pages'], 1)
        self.assertEqual(value['datasets'][0]['advertised_listing_pages'], 3)
        self.assertEqual(value['datasets'][0]['next_unobserved_listing_page'], 1)
        self.assertEqual(value['observed_url_extensions'], {'.pdf': 1})
        self.assertEqual(value['datasets'][1]['observed_file_urls'], 0)
        self.assertEqual(value['datasets'][1]['listing_coverage'], 'partial')
        self.assertIsNone(value['datasets'][1]['advertised_listing_pages'])
        restored = catalog.connect(Path(self.temp.name) / 'restored.sqlite')
        try:
            catalog.restore(restored, out)
            for table in ('observations', 'files', 'appearances', 'attempts'):
                self.assertEqual([tuple(r) for r in self.db.execute('SELECT * FROM ' + table)],
                                 [tuple(r) for r in restored.execute('SELECT * FROM ' + table)])
        finally:
            restored.close()

    def test_same_efta_stem_does_not_merge_different_file_formats(self):
        body = html('EFTA1.pdf', "<a href='/epstein/files/DataSet%201/EFTA1.avi'>video</a>")
        catalog.record(self.db, 1, 0, body, '2026-11-07', 'snapshot')
        rows = self.db.execute('SELECT file_id,filename FROM files ORDER BY filename').fetchall()
        self.assertEqual([tuple(r) for r in rows], [('EFTA1', 'EFTA1.avi'), ('EFTA1', 'EFTA1.pdf')])

    def test_browser_import_rejects_wrong_page_and_modified_snapshot(self):
        snapshot = Path(self.temp.name) / 'page.dom.html'
        snapshot.write_bytes(html())
        metadata = dict(url=catalog.listing_url(1, 1), captured_at_utc='2026-11-07T00:00:00Z',
                        sha256=hashlib.sha256(html()).hexdigest())
        snapshot.with_suffix('.json').write_text(json.dumps(metadata))
        with patch.object(catalog, 'ROOT', Path(self.temp.name)):
            with self.assertRaises(ValueError):
                catalog.import_browser(self.db, 1, 0, snapshot)
            snapshot.write_bytes(html('changed.pdf'))
            with self.assertRaises(ValueError):
                catalog.import_browser(self.db, 1, 1, snapshot)
            self.assertEqual(self.db.execute('SELECT count(*) FROM observations').fetchone()[0], 0)
            snapshot.write_bytes(html())
            catalog.import_browser(self.db, 1, 1, snapshot)
            self.assertEqual(self.db.execute('SELECT count(*) FROM observations').fetchone()[0], 1)


if __name__ == '__main__':
    unittest.main()
