"""Same-session continuation, with no homepage/refresh/upgrade path."""
import re

ROI=[.45,.77,.35,.18]
def verified_target(regions,expected_bet):
    def words(name):return ' '.join(x['value'] for x in regions.get(name,{}).get('text',[])).upper().strip()
    title_words=words('title');effect_words=words('effect')
    title_ok=any(x in title_words for x in ('VICTORY','LOSE','DEFEAT'))
    header_ok=all(x in effect_words for x in ('BALANCE','POINTS','CARDS LEFT'))
    if not(title_ok or header_ok):raise ValueError('not_settlement')
    bet=re.fullmatch(r'BET\s*:\s*(\d+)',words('bet'))
    if bet:
        if int(bet[1])!=expected_bet:raise ValueError('bet_mismatch')
    else:
        # On wide result layouts the BET pill can be occluded by the result
        # rows. The settlement header is already verified above; accept only
        # when a signed result row carries the exact absolute BET value.
        signed=[]
        for v in regions.get('effect',{}).get('text',[]):
            raw=v.get('value','').replace(',','').strip()
            if re.fullmatch(r'[+\-]\d+(?:\.\d+)?',raw):signed.append(abs(float(raw)))
        if expected_bet not in signed:raise ValueError('bet_mismatch')
    matches=[v for v in regions.get('again',{}).get('text',[]) if re.fullmatch(r'PLAY\s+AGAIN(?:\s+\d+)?',v['value'].upper().strip())]
    if len(matches)!=1:raise ValueError('play_again_not_verified')
    x,y,w,h=matches[0]['box']
    if not(.45<=x<x+w<=.82 and .80<=y<y+h<=.97):raise ValueError('button_outside_verified_roi')
    return [x+w/2,y+h/2]

def submit(s,w,b,expected_bet,emit):
    if not s.allow_input:raise PermissionError('input_disabled')
    s.call('focus_test_window',pid=w['pid'],window_id=w['id'])
    cb=b['content_bounds']
    f=s.call('capture',window_id=w['id'],bounds=w['bounds'],screen_rect=cb,crop=[0,0,1,1],allow_background_capture=True,
             regions={'title':[.3,.08,.4,.17],'bet':[.43,.475,.14,.06],'again':ROI,'effect':[.28,.22,.4,.4]})
    point=verified_target(f['regions'],expected_bet)
    emit('same_room_continuation_intent',point=point,bet=expected_bet)
    ack=s.call('click',window_id=w['id'],bounds=w['bounds'],point=[cb[0]+point[0]*cb[2],cb[1]+point[1]*cb[3]],
               canvas_screen=cb,expected_origin=b['origin'],expected_path=b['path'],expected_capture_seq=f['capture_seq'])
    emit('same_room_continuation_submitted',ack=ack,accepted_by_game=None)
