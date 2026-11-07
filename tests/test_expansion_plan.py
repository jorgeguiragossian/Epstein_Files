import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('expansion_plan', ROOT / 'scripts/plan-expansion.py')
plan = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plan)


def row(number, extension='pdf', **changes):
    name = f'EFTA{number:08d}.{extension}'
    return dict(dataset='8', filename=name, url=f'https://www.justice.gov/epstein/files/DataSet%208/{name}',
                listing_pages_observed='1;2', download_status='not_downloaded', **changes)


class ExpansionPlanTests(unittest.TestCase):
    def test_exclusions_formats_url_scope_and_deterministic_spacing(self):
        source = [row(n) for n in range(20)]
        processed = row(21); processed['download_status'] = 'pilot_download_record'
        external = row(22); external['url'] = external['url'].replace('www.justice.gov', 'example.org')
        source += [processed, external, row(23, 'xlsx')]
        excluded = {source[0]['url']}
        selected, coverage = plan.choose(source, excluded)
        self.assertEqual(len(selected), 10)
        self.assertEqual(selected[0]['filename'], 'EFTA00000001.pdf')
        self.assertEqual(selected[-1]['filename'], 'EFTA00000019.pdf')
        self.assertEqual(coverage[7]['eligible_observed_pdfs'], 19)
        self.assertEqual(coverage[5]['selected'], 0)
        self.assertEqual(selected, plan.choose(list(reversed(source)), excluded)[0])
        self.assertTrue(all(r['first_observed_listing_page'] == 1 for r in selected))

    def test_small_pools_and_bad_filename(self):
        self.assertEqual(len(plan.choose([row(1)], set())[0]), 1)
        self.assertEqual(plan.choose([], set())[0], [])
        bad = row(1); bad['filename'] = 'other.pdf'
        with self.assertRaises(ValueError):
            plan.choose([bad], set())
        with self.assertRaises(ValueError):
            plan.choose([], set(), per_dataset=100)
