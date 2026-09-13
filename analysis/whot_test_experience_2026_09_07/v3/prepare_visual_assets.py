"""Fetch public render-font assets referenced by the observed Cocos build.
No cookies, gameplay state or user records are requested.
"""
import hashlib,json,urllib.request
from pathlib import Path
from lab import ROOT

BASE='https://test-h5.wajew.com/internal/6001/assets/whot/'
ALPHABET='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'

def uuid_decode(value):
    if len(value)!=22:return value
    raw=value[:2]+''.join(f'{(ALPHABET.index(value[i])<<6)|ALPHABET.index(value[i+1]):03x}' for i in range(2,22,2))
    return '-'.join([raw[:8],raw[8:12],raw[12:16],raw[16:20],raw[20:]])

def get(url):
    with urllib.request.urlopen(url,timeout=20) as r:return r.read()

def walk(value):
    yield value
    if isinstance(value,list):
        for x in value:yield from walk(x)
    elif isinstance(value,dict):
        for x in value.values():yield from walk(x)

def save(path,data):
    if path.exists() and path.read_bytes()!=data:raise ValueError('asset_changed_use_new_build_directory')
    if not path.exists():path.write_bytes(data)

def main():
    folder=ROOT/'visual_assets'/'6001-cdd3f';folder.mkdir(parents=True,exist_ok=True)
    config=json.loads(get(BASE+'config.cdd3f.json'))
    versions=config['versions'];native=dict(zip(versions['native'][::2],versions['native'][1::2]))
    pack=json.loads(get(BASE+'import/0c/0cc0bb1b0.1e990.json'))
    result=[]
    for name in ('Font2','fnt_whot_01'):
        descriptor=next(x[3] for x in walk(pack) if isinstance(x,list) and len(x)>3 and x[1]==name and isinstance(x[3],dict) and 'fontDefDictionary' in x[3])
        key=next(k for k,v in config['paths'].items() if v==['res/font/'+name,'cc.Texture2D'])
        uid=uuid_decode(key);url=BASE+'native/'+uid[:2]+'/'+uid+'.'+native[key]+'.png'
        image=get(url);save(folder/(name+'.png'),image)
        save(folder/(name+'.json'),(json.dumps(descriptor,ensure_ascii=False,indent=2)+'\n').encode())
        result.append(dict(name=name,url=url,sha256=hashlib.sha256(image).hexdigest(),chars=len(descriptor['fontDefDictionary'])))
    for name in ('game_multiple','jc-zimu','txz'):
        descriptor=next(x[3] for x in walk(pack) if isinstance(x,list) and len(x)>3 and x[1]==name and isinstance(x[3],dict) and 'fontDefDictionary' in x[3])
        sprite_name=descriptor['atlasName'].removesuffix('.png')
        candidates=[r for r in pack[5] if r and isinstance(r[0],list) and r[0] and isinstance(r[0][0],dict) and r[0][0].get('name')==sprite_name]
        if not candidates:
            result.append({'name':name,'status':'sprite_not_found'});continue
        asset=candidates[0];sprite=asset[0][0];key=pack[1][asset[-1][0]];uid=uuid_decode(key)
        url=BASE+'native/'+uid[:2]+'/'+uid+'.'+native[key]+'.png'
        image=get(url);save(folder/(name+'-atlas.png'),image)
        save(folder/(name+'-sprite.json'),(json.dumps(sprite,indent=2)+'\n').encode())
        save(folder/(name+'.json'),(json.dumps(descriptor,indent=2)+'\n').encode())
        result.append(dict(name=name,url=url,sha256=hashlib.sha256(image).hexdigest(),sprite=sprite))
    save(folder/'source_receipt_extended.json',(json.dumps({'build':'cdd3f','purpose':'visible_digit_templates','assets':result},indent=2)+'\n').encode())
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
