"""Reproduce selected-card number-band contamination from immutable crops.

Shape identity here is a manually inspected fixture, not a new vision accuracy
claim. Native number boxes are remapped to the original full-canvas coordinates.
"""
import json
from native_session import Session
from resident_calibration import ROOT,selected_hand_complete

def remap(numbers,roi):
    return [dict(n,box=[roi[0]+n['box'][0]*roi[2],roi[1]+n['box'][1]*roi[3],
                        n['box'][2]*roi[2],n['box'][3]*roi[3]]) for n in numbers]

def main():
    prefix=ROOT.parent/'v3_1'/'captures'/'native-7f3614d35a-00062'
    s=Session()
    try:
        hand=s.call('analyze',path=str(prefix)+'-hand.png',regions={'hand':[0,0,1,1]})['regions']['hand']['numbers']
        raised=s.call('analyze',path=str(prefix)+'-raised.png',regions={'raised':[0,0,1,1]})['regions']['raised']['numbers']
    finally:s.close()
    hand=remap(hand,[.30,.775,.40,.22]);raised=remap(raised,[.30,.735,.40,.23])
    assert len(raised)==1 and raised[0]['rank']==11
    fixture=dict(raised[0],shape='triangle',rank_score=raised[0]['confidence'],shape_evidence={'marker_consistent':True})
    cards=[n for n in hand if n['rank'] is not None]
    region=dict(cards=cards,numbers=hand,number_group_count=len(hand))
    accepted=selected_hand_complete(region,[fixture])
    assert accepted
    print(json.dumps({'fixture':'native-7f3614d35a-00062','strict_number_completeness':len(hand)==len(cards),
                      'selected_symbol_completeness':accepted,'number_groups':len(hand),
                      'remaining_rank_count':len(cards),'shape_label_source':'manual_fixture',
                      'live_action_certified':False}))

if __name__=='__main__':main()
