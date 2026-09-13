"""Resume a visible BET lobby tile by exact OCR amount, never an upgrade control."""
def start_bet(s,w,b,expected_bet):
    s.call('focus_test_window',pid=w['pid'],window_id=w['id']);cb=b['content_bounds'];roi=[.08,.30,.86,.56]
    f=s.call('capture',window_id=w['id'],bounds=w['bounds'],screen_rect=cb,crop=[0,0,1,1],allow_background_capture=True,
             regions={'room':roi,'effect':roi})
    values=f['regions']['room'].get('text',[])
    normalized=[v['value'].upper().replace(' ','') for v in values]
    assert any(v==f'ASSETS{expected_bet}+' for v in normalized),f'not_bet{expected_bet}_lobby'
    amount=[v for v in values if v['value'].replace(',','').strip()==str(expected_bet)]
    assert len(amount)==1,f'ambiguous_bet{expected_bet}'
    x,y,width,height=amount[0]['box']
    # The Canvas hit target is the tile, not the lower edge of the amount
    # glyph. Move to the stable vertical center of that tile while retaining
    # the exact OCR amount as the selection witness.
    p=[x+width/2,max(0.05,y-0.08)]
    ack=s.call('click',window_id=w['id'],bounds=w['bounds'],point=[cb[0]+p[0]*cb[2],cb[1]+p[1]*cb[3]],canvas_screen=cb,
               expected_origin=b['origin'],expected_path=b['path'],expected_capture_seq=f['capture_seq'])
    return {'operation':f'bet{expected_bet}_entry_click','input_result':ack,'accepted_by_game':None}

def start1000(s,w,b):
    return start_bet(s,w,b,1000)

def start2000(s,w,b):
    return start_bet(s,w,b,2000)

def start5000(s,w,b):
    return start_bet(s,w,b,5000)
