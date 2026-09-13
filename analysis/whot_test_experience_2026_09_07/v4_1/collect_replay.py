"""Read-only cropped evidence collection; no input capability."""
import subprocess,json,time,uuid,selectors
from pathlib import Path
from datetime import datetime,timezone

def main():
    root=Path(__file__).resolve().parent;batch=uuid.uuid4().hex[:10]
    out=root/('replay_'+batch+'.jsonl')
    p=subprocess.Popen(['/tmp/whot-native-v4'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True,bufsize=1)
    sel=selectors.DefaultSelector();sel.register(p.stdout,selectors.EVENT_READ)
    def call(op,**kw):
        rid=uuid.uuid4().hex
        p.stdin.write(json.dumps(dict(op=op,request_id=rid,**kw))+'\n');p.stdin.flush()
        if not sel.select(8):raise RuntimeError('capture_timeout')
        x=json.loads(p.stdout.readline())
        if x.get('request_id')!=rid or x.get('status')!='ok':raise RuntimeError(x.get('reason','invalid_response'))
        return x
    with out.open('x') as f:
        def emit(kind,**kw):
            r=dict(kind=kind,utc=datetime.now(timezone.utc).isoformat(),monotonic_ns=time.monotonic_ns(),**kw)
            f.write(json.dumps(r)+'\n');f.flush()
        try:
            s=call('status');ws=[w for w in s['windows'] if w['bounds']['Height']>300]
            if len(ws)!=1:raise RuntimeError('window_ambiguous')
            w=ws[0];i=call('inspect',pid=w['pid'])
            if i.get('origin')!='https://test-h5.wajetan.com' or i.get('path')!='/game/6001-whot':raise RuntimeError('wrong_route')
            emit('start',game_id=6001,input_enabled=False)
            print(json.dumps({'status':'ready','batch':batch,'log':str(out)}),flush=True)
            for n in range(240):
                current=call('inspect',pid=w['pid'])
                if (current.get('origin'),current.get('path'),current.get('content_bounds'))!=(i['origin'],i['path'],i['content_bounds']):raise RuntimeError('binding_changed')
                prefix=str(root.parent/'v3_1'/'captures'/f'{batch}-{n:03d}')
                started=time.monotonic_ns()
                frame=call('capture',window_id=w['id'],bounds=w['bounds'],screen_rect=i['content_bounds'],crop=[0,0,1,1],
                    allow_background_capture=True,regions={'hand':[.30,.74,.40,.25],'table':[.56,.35,.11,.28]},
                    save_prefix=prefix,save_regions=['hand','table'])
                emit('frame',index=n,capture_seq=frame.get('capture_seq'),elapsed_ms=(time.monotonic_ns()-started)/1e6,
                    frame_age_ms=frame.get('frame_age_ms'),paths=[prefix+'-hand.png',prefix+'-table.png'])
                time.sleep(.10)
            emit('completed',frames=240)
        except Exception as e:emit('failed',reason=str(e));print(json.dumps({'status':'failed','reason':str(e)}),flush=True)
        finally:
            p.terminate()
            try:p.wait(timeout=2)
            except subprocess.TimeoutExpired:p.kill();p.wait()
            sel.close()
    print(json.dumps({'status':'recorder_closed','log':str(out)}),flush=True)
if __name__=='__main__':main()
