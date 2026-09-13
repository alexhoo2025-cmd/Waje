"""Append verified image readbacks; preserve original settlement source bytes."""
import hashlib,json,sqlite3
from pathlib import Path

ROOT=Path(__file__).resolve().parent

def append_readback(match_id,image_path,fields):
    image_path=Path(image_path).resolve()
    digest=hashlib.sha256(image_path.read_bytes()).hexdigest()
    with sqlite3.connect(ROOT/'derived.sqlite3') as db:
        row=db.execute('SELECT source_hash,payload FROM live_matches WHERE id=?',(match_id,)).fetchone()
        if row is None:raise ValueError('unknown_match')
        original=json.loads(row[1]);inserted=0
        for field,value in fields.items():
            if field not in ('page_settlement_displayed','page_settlement_raw','page_settlement_semantics'):
                raise ValueError('field_not_allowed')
            evidence=json.dumps({'match_id':match_id,'image':str(image_path.relative_to(ROOT.parent)),
                                 'image_sha256':digest,'method':'manual_visible_first_row_readback'},sort_keys=True)
            rid=hashlib.sha256(json.dumps([match_id,field,value,digest],sort_keys=True).encode()).hexdigest()
            cur=db.execute('INSERT OR IGNORE INTO revisions VALUES(?,?,?,?,?,?,?)',
                           (rid,row[0],field,json.dumps(original.get(field)),json.dumps(value),
                            'Later visible settlement readback; does not certify gross/net semantics or strategy eligibility.',evidence))
            inserted+=cur.rowcount
        return {'match_id':match_id,'inserted_revisions':inserted,'image_sha256':digest,
                'original_source_unchanged':db.execute('SELECT source_hash FROM live_matches WHERE id=?',(match_id,)).fetchone()[0]==row[0]}

if __name__=='__main__':
    print(json.dumps(append_readback('v41-native-calibration-027',
        ROOT.parent/'v3_1'/'captures'/'ui-check-016a92ac-returns.png',
        {'page_settlement_displayed':1.8,'page_settlement_raw':'+1.8','page_settlement_semantics':'unverified_gross_vs_net'})))
