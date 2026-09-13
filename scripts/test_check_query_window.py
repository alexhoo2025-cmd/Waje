import json,tempfile,unittest
from pathlib import Path
from check_query_window import check

class QueryWindowTests(unittest.TestCase):
    def run_case(self,sql,scope=True):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'q.sql';p.write_text(sql)
            if scope:p.with_suffix('.scope.json').write_text(json.dumps({'start':'2026-08-01','end':'2026-09-09'}))
            return check(p)
    def test_allowed(self):
        self.assertEqual(self.run_case("SELECT COUNT(*) FROM t WHERE target_day BETWEEN DATE '2026-08-01' AND DATE '2026-09-09'")['literal_dates_checked'],2)
    def test_historical_scan_blocked(self):
        with self.assertRaisesRegex(ValueError,'outside'):self.run_case("SELECT COUNT(*) FROM t WHERE target_day BETWEEN DATE '2020-01-01' AND DATE '2026-09-09'")
    def test_missing_contract(self):
        with self.assertRaisesRegex(ValueError,'Missing'):self.run_case('SELECT COUNT(*) FROM t',False)
    def test_dynamic_requires_review(self):
        with self.assertRaisesRegex(ValueError,'resolve'):self.run_case('SELECT COUNT(*) FROM t WHERE target_day BETWEEN @start AND @end')
    def test_comments_not_date_bounds(self):
        with self.assertRaisesRegex(ValueError,'No literal'):self.run_case("-- DATE '2026-08-01'\nSELECT COUNT(*) FROM t")
    def test_comments_do_not_expand_scope(self):
        self.assertEqual(self.run_case("-- DATE '2020-01-01'\nSELECT COUNT(*) FROM t WHERE target_day=DATE '2026-08-01'")['literal_dates_checked'],1)

if __name__=='__main__':unittest.main()
