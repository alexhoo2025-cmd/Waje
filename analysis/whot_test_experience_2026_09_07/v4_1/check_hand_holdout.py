"""Offline file-only shape feature checks; no capture or input commands."""
import hashlib,json,selectors,subprocess
from pathlib import Path
from shape_candidate import classify

def main():
    root=Path(__file__).resolve().parent
    labels=json.loads((root/'hand_shape_holdout.json').read_text())
    p=subprocess.Popen(['/tmp/whot-native-v4'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)
    sel=selectors.DefaultSelector();sel.register(p.stdout,selectors.EVENT_READ)
    results=[]
    try:
        for frame in labels['frames']:
            image=root.parent/'v3_1'/'captures'/f"a6c43124fc-{frame['index']}-hand.png"
            digest=hashlib.sha256(image.read_bytes()).hexdigest()
            for index,(x,expected) in enumerate(zip(frame['x_centers'],frame['shapes'])):
                rid=f"{frame['index']}-{index}"
                p.stdin.write(json.dumps({'op':'shape','request_id':rid,'path':str(image),'crop':[(x-21)/1176,96/381,42/1176,40/381]})+'\n');p.stdin.flush()
                if not sel.select(5):raise RuntimeError('offline_feature_timeout')
                features=json.loads(p.stdout.readline())
                if features.get('request_id')!=rid:raise RuntimeError('response_mismatch')
                candidate=classify(features)
                results.append(dict(frame=frame['index'],symbol_index=index,image_sha256=digest,expected=expected,candidate=candidate,agrees=candidate==expected,features=features))
    finally:
        p.terminate();p.wait(timeout=5);sel.close()
    result=dict(status='offline_holdout_only',frames=len(labels['frames']),symbols=len(results),correct=sum(r['agrees'] for r in results),live_input_enabled=False,limitations=labels['limitations'],results=results)
    out=root/'hand_shape_holdout_receipt.json'
    with out.open('x') as f:json.dump(result,f,indent=2)
    print(json.dumps({k:v for k,v in result.items() if k!='results'}))

if __name__=='__main__':main()
