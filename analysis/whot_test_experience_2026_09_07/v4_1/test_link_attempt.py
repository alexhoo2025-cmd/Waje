import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from link_attempt import link

class LinkTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.db=Path(self.tmp.name)/'test.sqlite3';self.source=Path(self.tmp.name)/'attempt.json'
        self.data=dict(match_id='test',game_id=6001,bet=1,actual_players=2,balance_before=10,balance_after_debit=9,events=[{'kind':'submit','at':None}])
        self.source.write_text(json.dumps(self.data))
        with sqlite3.connect(self.db) as db:
            db.execute('CREATE TABLE live_matches(id TEXT PRIMARY KEY,payload TEXT)')
            db.execute('INSERT INTO live_matches VALUES (?,?)',('test',json.dumps(dict(self.data,attempt_source='attempt.json'))))
    def test_idempotent_and_no_new_match(self):
        self.assertEqual(link(self.db,self.source)['inserted_events'],1)
        self.assertEqual(link(self.db,self.source)['inserted_events'],0)
        with sqlite3.connect(self.db) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM live_matches').fetchone()[0],1)
            self.assertIsNone(db.execute('SELECT observed_at FROM operation_events').fetchone()[0])
    def test_changed_source_rejected(self):
        link(self.db,self.source)
        self.data['events'].append({'kind':'extra'})
        self.source.write_text(json.dumps(self.data))
        with self.assertRaisesRegex(ValueError,'source_changed'): link(self.db,self.source)
    def test_wrong_bet_rejected(self):
        self.data['bet']=500;self.source.write_text(json.dumps(self.data))
        with self.assertRaisesRegex(ValueError,'identity_mismatch:bet'):link(self.db,self.source)

if __name__=='__main__':unittest.main()
