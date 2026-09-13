"""Compare real, independently annotated images to the vision pipeline.

Never generates synthetic game samples. Manifests name canvas-only redacted
images, hashes, splits and expected visible-state fields.
"""
import argparse
import hashlib
import json
import time
from pathlib import Path
from controller import Native, Vision
from lab import ROOT, digest, percentile

REQUIRED_SCENES={'normal','special','occluded','countdown','autoplay','settlement'}
FIELDS=('phase','action_owner','pending_effect','autoplay','visible_hand','table_card','effective_shape')


def evaluate(manifest,profile,native):
    rows=manifest['frames'];seen=set();scenes=set();checks=[];times=[]
    if manifest.get('client_game_id')!=profile['client_game_id']:
        raise ValueError('version_mismatch')
    for row in rows:
        if row.get('split')!='holdout' or row.get('annotation_source')!='human_verified':
            raise ValueError('independent_holdout_annotations_required')
        path=Path(row['path']).resolve()
        sha=hashlib.sha256(path.read_bytes()).hexdigest()
        if sha!=row['sha256'] or sha in seen:
            raise ValueError('changed_or_duplicate_frame')
        seen.add(sha);scenes.add(row['scene'])
        before=time.perf_counter_ns()
        frame=native.call(op='analyze',path=str(path),regions=profile['vision']['regions'])
        state=Vision(profile).parse(frame,1000,dict(foreground=True,window_verified=True))
        elapsed=(time.perf_counter_ns()-before)/1e6;times.append(elapsed)
        fields={k:state.get(k)==row['expected'].get(k) for k in FIELDS}
        exact=all(fields.values());confident=state['capture_confidence']>=.98
        checks.append({'sha256':sha,'exact':exact,'high_confidence_error':confident and not exact,
                       'rejected':not confident,'field_matches':fields,'analysis_ms':elapsed})
    errors=sum(x['high_confidence_error'] for x in checks)
    recall=sum(x['exact'] and not x['rejected'] for x in checks)/len(checks) if checks else 0
    passed=len(seen)>=200 and REQUIRED_SCENES<=scenes and errors==0 and recall>=.95
    return {'status':'passed' if passed else 'failed','client_game_id':profile['client_game_id'],
            'profile_sha256':digest(profile),'unique_images':len(seen),'scenes':sorted(scenes),
            'high_confidence_errors':errors,'accepted_exact_rate':recall,'analysis_p95_ms':percentile(times),
            'checks':checks,'note':'Vision replay only; not a live match, latency SLA or gameplay certification.'}


def main():
    p=argparse.ArgumentParser();p.add_argument('--manifest',type=Path,required=True)
    p.add_argument('--profiles',type=Path,default=ROOT/'profiles.json');p.add_argument('--output',type=Path,required=True)
    p.add_argument('--native',type=Path,default=Path('/tmp/whot-native-v3'));a=p.parse_args()
    manifest=json.loads(a.manifest.read_text());profile=json.loads(a.profiles.read_text())[manifest['client_game_id']]
    worker=Native(a.native)
    try:result=evaluate(manifest,profile,worker)
    finally:worker.close()
    if a.output.exists():raise ValueError('use_new_receipt_path')
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='checks'},ensure_ascii=False))
    raise SystemExit(0 if result['status']=='passed' else 1)


if __name__=='__main__':main()
