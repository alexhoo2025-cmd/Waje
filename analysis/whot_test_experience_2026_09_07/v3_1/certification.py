"""Evidence gates, bound to the actual implementation and profile. No live clicks."""
import hashlib
import json
from pathlib import Path
from lab import ROOT, digest


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fingerprint(profile, binary):
    return digest({'profile': {k:v for k,v in profile.items() if k!='certification'},
                   'code': {p.name:file_hash(p) for p in sorted(ROOT.glob('*.py'))},
                   'native_source':file_hash(ROOT/'native.swift'), 'binary':file_hash(binary)})


def require_profile(profile, binary):
    r,v=profile['rules'],profile['vision']
    if r.get('status')!='verified' or v.get('status')!='calibrated':raise ValueError('profile_not_calibrated')
    if not r.get('valid_cards') or not r.get('points') or not v.get('regions'):
        raise ValueError('profile_incomplete')
    if profile.get('game_build') in (None,'unknown') or not profile.get('route'):
        raise ValueError('build_or_route_unverified')
    evidence=profile.get('certification',{})
    if evidence.get('fingerprint')!=fingerprint(profile,binary):raise ValueError('certification_stale')
    for kind in ('rules','vision200'):
        source=evidence.get(kind,{})
        path=Path(source.get('path',''))
        if not path.is_file() or file_hash(path)!=source.get('sha256'):raise ValueError('missing_'+kind+'_evidence')
        result=json.loads(path.read_text())
        if result.get('client_game_id')!=profile['client_game_id'] or result.get('status')!='passed':
            raise ValueError('invalid_'+kind+'_evidence')
        if kind=='vision200' and (result.get('unique_images',0)<200 or result.get('high_confidence_errors')!=0 or result.get('accepted_exact_rate',0)<.95):
            raise ValueError('vision_threshold_failed')
    return evidence['fingerprint']


def certify_pilot(store, game, fp, kind, match_ids):
    required={'pilot3':3,'continuous10':10}[kind]
    if len(match_ids)!=required or len(set(match_ids))!=required:raise ValueError('pilot_count')
    rows=[store.c.execute('select * from matches where id=?',(i,)).fetchone() for i in match_ids]
    if any(not r or r['game']!=game or r['phase']!='calibration' or not r['quality'] or
           not json.loads(r['quality']).get('eligible') or json.loads(r['meta']).get('certification_fingerprint')!=fp for r in rows):
        raise ValueError('pilot_not_qualified')
    # Every attempt in the interval must be supplied; failed attempts cannot be skipped.
    span=store.c.execute("select id from matches where game=? and phase='calibration' and started_at between ? and ?",
                        (game,min(r['started_at'] for r in rows),max(r['started_at'] for r in rows))).fetchall()
    if {r[0] for r in span}!=set(match_ids):raise ValueError('pilot_not_consecutive')
    with store.c:
        store.c.execute('insert into certifications values(?,?,?,?)',(game,fp,kind,json.dumps({'match_ids':match_ids})))
