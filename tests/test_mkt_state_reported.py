"""Display and year-over-year rules for the 2027 state-reported Marketplace table.

Run: python -m unittest discover -s tests
"""
import csv
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import build_dashboard as bd  # noqa: E402

REGISTER = bd.load_mkt_register()


def row(**k):
    r = {c: '' for c in bd.MKT_STATE_COLUMNS}
    r.update(state='CO', marketplace='Connect for Health Colorado', plan_year='2026',
             measure_type='oep_plan_selections_final', component='N', value='277228', includes_dental='N',
             excludes_bhp='Y', period_start='2025-11-01', as_of_date='2026-01-15',
             published_date='2026-04-23', days_into_oep='75', source_url='https://example.org/a.pdf',
             source_type='primary_state', quote='"x"', retrieved_at='2026-11-03',
             reviewer_status='approved')
    r.update(k)
    return r


def run(rows):
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / 'sr.csv'
        with open(p, 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=bd.MKT_STATE_COLUMNS, lineterminator='\n')
            w.writeheader()
            w.writerows(rows)
        saved, bd.MKT_STATE_CSV = bd.MKT_STATE_CSV, p
        try:
            _, _, table = bd.load_mkt_state_reported(REGISTER)
        finally:
            bd.MKT_STATE_CSV = saved
    return {t['st']: t for t in table}


NEXT = dict(plan_year='2027', value='280000', period_start='2026-11-01',
            as_of_date='2027-01-15', published_date='2027-01-20')


class DisplayRule(unittest.TestCase):
    def test_approved_2026_row_is_never_the_current_figure(self):
        t = run([row()])
        self.assertEqual(t['CO']['status'], 'none')
        self.assertNotIn('value', t['CO'])

    def test_2027_row_is_shown_with_2026_as_baseline_only(self):
        t = run([row(), row(**NEXT)])
        self.assertEqual(t['CO']['status'], 'reported')
        self.assertEqual(t['CO']['value'], 280000)
        self.assertEqual(t['CO']['yoy']['prior'], 277228)

    def test_committed_csv_shows_no_2026_row_as_current(self):
        _, _, table = bd.load_mkt_state_reported(REGISTER)
        self.assertEqual([t['st'] for t in table if t['status'] != 'none'], [])


class DentalUnknown(unittest.TestCase):
    def test_u_without_doc_series_is_not_comparable(self):
        t = run([row(includes_dental='U'), row(includes_dental='U', **NEXT)])
        self.assertIsNone(t['CO']['yoy'])

    def test_u_with_different_doc_series_is_not_comparable(self):
        t = run([row(includes_dental='U', doc_series='A'),
                 row(includes_dental='U', doc_series='B', **NEXT)])
        self.assertIsNone(t['CO']['yoy'])

    def test_u_with_same_doc_series_is_comparable(self):
        t = run([row(includes_dental='U', doc_series='C4HCO OE report'),
                 row(includes_dental='U', doc_series='C4HCO OE report', **NEXT)])
        self.assertEqual(t['CO']['yoy']['prior'], 277228)

    def test_u_never_matches_n(self):
        t = run([row(includes_dental='N', doc_series='S'),
                 row(includes_dental='U', doc_series='S', **NEXT)])
        self.assertIsNone(t['CO']['yoy'])

    def test_bad_dental_flag_fails_validation(self):
        with self.assertRaises(SystemExit):
            run([row(includes_dental='X')])


class ComponentRows(unittest.TestCase):
    """component=Y rows (subgroup counts) are detail only, never the current figure."""
    SUB = dict(plan_year='2027', period_start='2026-11-01', as_of_date='2026-11-02',
               published_date='2026-11-02', days_into_oep='', component='Y')

    def test_state_with_only_component_rows_is_not_reported(self):
        t = run([row(measure_type='aptc_recipients', value='53875', **self.SUB),
                 row(measure_type='enrolled_other', value='13829', **self.SUB)])
        self.assertEqual(t['CO']['status'], 'components_only')
        self.assertNotIn('value', t['CO'])

    def test_template_labels_components_only_as_subgroup_counts(self):
        tpl = (Path(bd.__file__).parent / 'template.html').read_text(encoding='utf-8')
        self.assertIn("r.status==='components_only'?' (subgroup counts only)'", tpl)

    def test_total_row_beats_component_rows(self):
        t = run([row(measure_type='aptc_recipients', value='53875', **self.SUB),
                 row(measure_type='enrolled_other', value='13829', **self.SUB),
                 row(measure_type='enrolled_other', value='67770', **{**self.SUB, 'component': 'N'})])
        self.assertEqual(t['CO']['status'], 'reported')
        self.assertEqual(t['CO']['value'], 67770)

    def test_subgroup_measure_must_be_component(self):
        with self.assertRaises(SystemExit):
            run([row(measure_type='aptc_recipients', value='53875', **{**self.SUB, 'component': 'N'})])

    def test_bad_component_flag_fails_validation(self):
        with self.assertRaises(SystemExit):
            run([row(component='')])


if __name__ == '__main__':
    unittest.main()
