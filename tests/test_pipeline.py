"""Sanity checks for actual CMS Sample 1 analysis. Run after building the SQLite DB.

python -m unittest discover -s tests -v
"""
import json
import sqlite3
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / 'data/processed/medicare_claims.sqlite'
METRICS = ROOT / 'outputs/metrics.json'


@unittest.skipUnless(DB.exists() and METRICS.exists(), 'Build DB and report first')
class PipelineChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = sqlite3.connect(DB)
        cls.m = json.loads(METRICS.read_text(encoding='utf-8'))

    @classmethod
    def tearDownClass(cls):
        cls.c.close()

    def test_source_rows(self):
        self.assertEqual(self.c.execute('SELECT COUNT(*) FROM beneficiaries_2008').fetchone()[0], 116352)
        self.assertEqual(self.c.execute('SELECT COUNT(*) FROM inpatient_claims').fetchone()[0], 66773)
        self.assertEqual(self.c.execute('SELECT COUNT(*) FROM claims_2008').fetchone()[0], 27701)

    def test_join_and_claim_segment_uniqueness(self):
        self.assertEqual(self.m['quality_flags']['unmatched_beneficiaries'], 0)
        self.assertEqual(self.m['composite_key_duplicate_groups'], 0)
        self.assertEqual(self.m['overall']['distinct_claim_ids'], 27682)
        self.assertEqual(self.m['overall']['distinct_beneficiaries'], 15864)

    def test_record_quality_flags(self):
        self.assertEqual(self.m['quality_flags']['negative_payments'], 22)
        self.assertEqual(self.m['quality_flags']['missing_utilization_days'], 23)
        self.assertEqual(self.m['quality_flags']['invalid_dates'], 0)

    def test_aggregations_are_consistent(self):
        self.assertEqual(sum(row['claim_segment_rows'] for row in self.m['age_group']), 27701)
        self.assertEqual(sum(row['claim_segment_rows'] for row in self.m['admission_month']), 27701)
        self.assertEqual(sum(row['claim_segment_rows'] for row in self.m['admission_years']), 66773)
        self.assertAlmostEqual(self.m['overall']['avg_nonnegative_payment'], 9323.60, places=2)
        self.assertAlmostEqual(self.m['overall']['avg_recorded_utilization_days'], 5.63, places=2)

    def test_no_row_level_data_in_aggregates(self):
        for fp in (ROOT / 'outputs').glob('*.csv'):
            with fp.open(encoding='utf-8') as source:
                head = source.readline()
            self.assertNotIn('DESYNPUF_ID', head)
            self.assertNotIn('CLM_ID', head)


if __name__ == '__main__':
    unittest.main()
