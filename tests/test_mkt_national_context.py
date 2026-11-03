"""Display rule for the National Context card: only reviewer-approved rows render.

Run: python -m unittest discover -s tests
"""
import csv
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import build_dashboard as bd  # noqa: E402

NATIONAL_OEP = {'total': 23130860}


def row(**k):
    r = {c: '' for c in bd.MKT_NATCTX_COLUMNS}
    r.update(source_org='Example Org', publication='Example brief', pub_date='2026-10-28',
             url='https://example.org/brief', measure='individual_market_enrollment',
             scope='individual market', period='2026-06', value='21900000',
             is_estimate='yes', reviewer_status='approved')
    r.update(k)
    return r


def run(rows):
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / 'natctx.csv'
        with open(p, 'w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=bd.MKT_NATCTX_COLUMNS, lineterminator='\n')
            w.writeheader()
            w.writerows(rows)
        saved, bd.MKT_NATCTX_CSV = bd.MKT_NATCTX_CSV, p
        try:
            return bd.load_mkt_national_context([], NATIONAL_OEP)
        finally:
            bd.MKT_NATCTX_CSV = saved


def values(groups):
    return [i['value'] for g in groups for i in g['items']]


class DisplayRule(unittest.TestCase):
    def test_pending_row_is_not_rendered(self):
        self.assertEqual(run([row(reviewer_status='pending')]), [])

    def test_approved_row_is_rendered(self):
        self.assertEqual(values(run([row()])), [21900000.0])

    def test_only_approved_rows_render_when_mixed(self):
        g = run([row(), row(value='20500000', reviewer_status='pending')])
        self.assertEqual(values(g), [21900000.0])

    def test_pending_row_is_still_validated(self):
        with self.assertRaises(SystemExit):
            run([row(reviewer_status='pending', measure='unmapped_measure')])

    def test_bad_reviewer_status_fails_validation(self):
        with self.assertRaises(SystemExit):
            run([row(reviewer_status='maybe')])

    def test_rejected_row_is_not_rendered(self):
        self.assertEqual(run([row(reviewer_status='rejected')]), [])

    def test_rejected_row_is_kept_and_still_validated(self):
        with self.assertRaises(SystemExit):
            run([row(reviewer_status='rejected', measure='unmapped_measure')])

    def test_rejected_is_not_a_state_row_status(self):
        self.assertNotIn('rejected', bd.MKT_REVIEW)

    def test_committed_csv_shows_kff_and_mfa_sep29_only(self):
        g = bd.load_mkt_national_context([], NATIONAL_OEP)
        ind = {i['source']: i for grp in g if grp['key'] == 'individual_market'
               for i in grp['items'] if i['measure'] == 'individual_market_enrollment'}
        self.assertEqual(ind['Mark Farrah Associates']['value'], 22000000.0)
        self.assertEqual(ind['KFF (Mark Farrah Associates data)']['value'], 20500000.0)
        self.assertNotIn(21900000.0, values(g))
        _, rows = bd._read_csv_rows(bd.MKT_NATCTX_CSV)
        self.assertIn(('21900000', 'rejected'), {(r['value'], r['reviewer_status']) for r in rows})


if __name__ == '__main__':
    unittest.main()
