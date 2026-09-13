import json,subprocess,hashlib
from pathlib import Path
from shape_candidate import classify

def main():
    root=Path(__file__).resolve().parent
    labels=json.loads((root/'settlement_replay_labels.json').read_text())
    image=(root/labels['image']).resolve()
    p=subprocess.Popen(['/tmp/whot-native-v4'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)
    results=[]
    try:
        for index,x in enumerate([24,73,121,169,217,267,316]):
            p.stdin.write(json.dumps({'op':'shape','request_id':str(index),'path':str(image),
                'crop':[(x-11)/427,50/191,22/427,25/191]})+'\n');p.stdin.flush()
            f=json.loads(p.stdout.readline())
            expected=labels['cards'][index]['shape'];candidate=classify(f)
            results.append({'index':index,'expected':expected,'original':f.get('shape'),'candidate':candidate,
                'agrees':candidate==expected,'features':{k:f.get(k) for k in ('fill','bbox_w','bbox_h','row_center','col_center','row_r2','top_width','bottom_width')}})
    finally:
        p.stdin.close();p.wait(timeout=5)
    receipt={'status':'candidate_only','image_sha256':hashlib.sha256(image.read_bytes()).hexdigest(),
             'unique_frames':1,'development_set_agreement':sum(x['agrees'] for x in results),
             'total_cards':len(results),'independent_validation':False,'live_input_enabled':False,'results':results}
    (root/'shape_candidate_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({k:v for k,v in receipt.items() if k!='results'}))
if __name__=='__main__':main()
