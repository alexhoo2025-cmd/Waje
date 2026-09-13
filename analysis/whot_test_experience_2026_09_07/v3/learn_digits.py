"""Build visible glyph templates from explicitly reviewed, redacted card crops."""
import hashlib,json
from controller import Native
from lab import ROOT

SOURCES=[
 ('unresolved-dde9e41b149945b786188132708df025-hand.png',[0,0,1,.235],'11381213'),
 ('unresolved-dde9e41b149945b786188132708df025-table.png',[0,0,1,.235],'10'),
 ('calibration01-settlement-settlement_values.png',[.71,.345,.225,.06],'7101413'),
 ('settlement03-glyphs-digits.png',[0,0,1,.84],'13514')
]

def main():
    native=Native('/tmp/whot-native-v3');bank={};receipt=[]
    try:
        for name,roi,labels in SOURCES:
            path=ROOT/'captures'/name
            result=native.call(op='glyphs',path=str(path),crop=roi)
            glyphs=result['glyphs']
            print(name,'detected',len(glyphs),'expected',len(labels),'boxes',[x['box'] for x in glyphs])
            if len(glyphs)!=len(labels):raise ValueError('segmentation_requires_review:'+name)
            for label,glyph in zip(labels,glyphs):bank.setdefault(label,[]).append(glyph['signature'])
            receipt.append(dict(path=name,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),crop=roi,
                                labels=labels,annotation_source='assistant_visual_review',split='training'))
    finally:native.close()
    folder=ROOT/'visual_assets';folder.mkdir(exist_ok=True)
    (folder/'card_digits.json').write_text(json.dumps(bank)+'\n')
    (folder/'card_digit_training_receipt.json').write_text(json.dumps({'status':'training_only','sources':receipt,
        'unseen_digits':['6','9'],'holdout_passed':False},ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':main()
