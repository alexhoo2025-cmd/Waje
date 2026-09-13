"""Focused replay of a manually labelled square request; not full certification."""
import json
from native_session import Session
from resident_calibration import ROOT

s=Session()
try:
    path=ROOT.parent/'v3_1'/'captures'/'native-9ce711c5b9-00134-effect.png'
    old=s.call('shape',path=str(path),crop=[.7375,.5125,.1825,.3025])
    new=s.call('shape',path=str(path),crop=[.70,.54,.18,.27])
    assert new['shape']=='square'
    print(json.dumps({'fixture':path.name,'manual_label':'square','old':old['shape'],'new':new['shape'],
                      'new_fill':new['fill'],'scope':'one independent square frame, other shapes require regression'}))
finally:s.close()
