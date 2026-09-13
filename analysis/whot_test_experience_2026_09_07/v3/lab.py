"""WHOT dual-version experiment store and visible-state policy. Standard library only."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import sqlite3
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse, parse_qs

ROOT = Path(__file__).resolve().parent
ARMS = ('first_legal_play', 'reduce_high_point_cards', 'retain_special_or_wild_cards_until_needed')
GAMES = ('6001', '9006')
VERSION = 'visible-controller-v3.0'
FORBIDDEN = {'password', 'cookie', 'token', 'access_token', 'device_id', 'phone', 'email',
             'opponent_name', 'hidden_cards', 'deck_order', 'network_response'}


def now():
    return datetime.now(timezone.utc).isoformat()


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)


def digest(value):
    return hashlib.sha256(encoded(value).encode()).hexdigest()


def validate_payload(value):
    if isinstance(value, dict):
        for k, v in value.items():
            if k.lower() in FORBIDDEN:
                raise ValueError('forbidden_field:' + k)
            validate_payload(v)
    elif isinstance(value, list):
        for v in value:
            validate_payload(v)
    elif isinstance(value, float) and not math.isfinite(value):
        raise ValueError('nonfinite_number')


def gate(context, profile):
    u = urlparse(context.get('url', ''))
    reasons = []
    if u.scheme != 'https' or u.hostname != 'test-h5.wajew.com' or u.port not in (None, 443):
        reasons.append('wrong_origin')
    if context.get('browser_surface') != 'ordinary_chrome':
        reasons.append('wrong_browser_surface')
    if parse_qs(u.query).get('ux_mode') == ['standalone']:
        reasons.append('standalone')
    if context.get('client_game_id') != profile['client_game_id']:
        reasons.append('wrong_game')
    if not profile.get('route') or u.path != profile['route']:
        reasons.append('route_unverified_or_changed')
    if not context.get('foreground') or not context.get('window_verified'):
        reasons.append('window_not_verified')
    return reasons


def decide(state, rules, arm, at_ms=None):
    """Pure decision using a single monotonic clock domain; never issues clicks."""
    at_ms = time.monotonic_ns() / 1e6 if at_ms is None else at_ms
    started = time.perf_counter_ns()
    out = dict(action='wait', reason='not_actionable', state_seq=state.get('state_seq'),
               policy_version=VERSION, strategy_arm=arm, candidates=[], chosen_card=None,
               expires_at_ms=state.get('deadline_ms'))

    def end(action, reason, **fields):
        out.update(action=action, reason=reason, **fields)
        out['policy_compute_ms'] = (time.perf_counter_ns() - started) / 1e6
        return out

    if arm not in ARMS:
        return end('stop', 'unknown_strategy')
    if state.get('client_game_id') != rules.get('client_game_id'):
        return end('stop', 'rules_version_mismatch')
    if rules.get('status') != 'verified':
        return end('stop', 'rules_unverified')
    if not state.get('foreground') or not state.get('window_verified'):
        return end('stop', 'window_not_verified')
    if state.get('autoplay'):
        return end('stop', 'mixed_auto_play')
    captured = state.get('captured_at_ms')
    if captured is None or not 0 <= at_ms - captured <= 750:
        return end('rescan', 'stale_frame')
    if state.get('capture_confidence', 0) < .98:
        return end('rescan' if state.get('rescan_count', 0) < 1 else 'stop', 'uncertain_state')
    if state.get('phase') not in ('player_turn', 'special_resolution'):
        return end('wait', 'not_actionable')
    deadline = state.get('deadline_ms')
    if deadline is None or deadline - at_ms < 300:
        return end('stop', 'deadline_missing_or_expired')
    if state.get('action_owner') != 'self':
        return end('wait', 'not_our_action_window')
    pending = state.get('pending_effect', 'unknown')
    hand = state.get('visible_hand')
    if pending != 'none':
        effect = rules.get('effects', {}).get(pending)
        if not effect:
            return end('stop', 'unresolved_rule')
        if effect.get('resolution') == 'automatic':
            return end('wait', 'automatic_effect')
        if pending not in state.get('available_actions', []):
            return end('rescan', 'effect_button_not_visible')
        if pending == 'whot_shape_selection':
            if hand is None:
                return end('stop', 'missing_hand')
            shapes = rules['shapes']
            target = max(shapes, key=lambda x: (sum(c['shape'] == x for c in hand), -shapes.index(x)))
            return end('select_shape', 'visible_hand_majority', target_shape=target)
        return end(effect['action'], 'verified_special_window')
    if state.get('phase') != 'player_turn' or not hand:
        return end('stop', 'missing_normal_turn_state')
    table = state.get('table_card') or {}
    active_shape = state.get('effective_shape')
    if table.get('rank') is None or active_shape not in rules['shapes']:
        return end('stop', 'effective_shape_unknown')
    valid_deck = set(rules.get('valid_cards', []))
    if not valid_deck or any(f"{c['rank']}:{c['shape']}" not in valid_deck for c in hand):
        return end('stop', 'card_outside_verified_deck')
    candidates = [dict(c, index=i) for i, c in enumerate(hand)
                  if c['rank'] == rules['wild_rank'] or c['rank'] == table['rank'] or c['shape'] == active_shape]
    out['candidates'] = candidates
    if not candidates:
        return end('draw', 'no_legal_card')
    if arm == ARMS[0]:
        chosen = candidates[0]
    else:
        points = rules.get('points', {})
        if any(f"{c['rank']}:{c['shape']}" not in points for c in candidates):
            return end('stop', 'scoring_unverified')
        pool = candidates
        if arm == ARMS[2]:
            opponents = state.get('opponent_visible_card_counts')
            if not opponents:
                return end('stop', 'opponent_counts_unknown')
            defensive = [c for c in pool if c['rank'] in rules.get('blocking_ranks', [])]
            ordinary = [c for c in pool if c['rank'] not in rules.get('special_ranks', [])]
            pool = (defensive or pool) if min(opponents) <= 2 else (ordinary or pool)
        chosen = max(pool, key=lambda c: (points[f"{c['rank']}:{c['shape']}"], -c['index']))
    return end('play', 'fixed_strategy', chosen_card=chosen)


def percentile(values, q=.95):
    if not values:
        return None
    v = sorted(values)
    x = (len(v) - 1) * q
    return v[int(x)] + (v[min(int(x) + 1, len(v) - 1)] - v[int(x)]) * (x - int(x))


def wilson(wins, n):
    if not n:
        return None
    p, z = wins / n, 1.96
    denom = 1 + z*z/n
    mid = (p + z*z/(2*n))/denom
    half = z * math.sqrt(p*(1-p)/n + z*z/(4*n*n))/denom
    return [mid-half, mid+half]


def eligibility(meta, settlement, events):
    reasons = []
    if meta.get('phase') == 'historical':
        return {'eligible': False, 'reasons': ['historical_evidence_only'], 'coverage': None}
    if not settlement.get('visible') or settlement.get('result') not in ('win','loss','draw'):
        reasons.append('settlement_missing')
    if not settlement.get('end_reason') or settlement['end_reason'] == 'unknown':
        reasons.append('end_reason_unknown')
    for field in ('ruleset_version','game_build','vision_profile_version','controller_version','room_id'):
        if not meta.get(field) or meta[field] == 'unknown':
            reasons.append('missing_' + field)
    if meta.get('actual_player_count') != 2 or meta.get('stake') is None:
        reasons.append('experiment_conditions_unknown')
    if settlement.get('quality') == 'mixed_auto_play' or any(e.get('type') in ('autoplay','capture_gap','invalid_scope','unresolved_state') or e.get('quality')=='mixed_auto_play' for e in events):
        reasons.append('control_or_capture_failure')
    opportunities = {e['turn_id'] for e in events if e.get('type') == 'turn_open'}
    actions = [e for e in events if e.get('type') == 'action_confirmed']
    decision_ids = {e['decision_id'] for e in events if e.get('type') == 'decision'}
    good = [e for e in actions if e.get('accepted') is True and e.get('legal') is True
            and e.get('timeout') is False and e.get('timing_source') == 'monotonic_observed'
            and isinstance(e.get('click_latency_ms'),(int,float)) and e['click_latency_ms'] >= 0
            and e.get('context_complete') is True and e.get('decision_id') in decision_ids]
    denominator = settlement.get('observed_turn_opportunities')
    continuous = settlement.get('continuous_capture_verified') is True
    coverage = len({e.get('turn_id') for e in good} & opportunities)/denominator if continuous and denominator and denominator == len(opportunities) else None
    if coverage is None or coverage < .95:
        reasons.append('turn_coverage_unproven')
    if len(actions) != len(good):
        reasons.append('invalid_or_unverified_action')
    latency = percentile([e['click_latency_ms'] for e in good])
    if latency is None or latency > 2000:
        reasons.append('latency_gate')
    if not any(e.get('type') == 'match_start' for e in events):
        reasons.append('start_missing')
    return {'eligible': not reasons, 'reasons': reasons, 'coverage': coverage, 'click_p95_ms': latency}


SCHEMA = '''
CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS slots(game TEXT NOT NULL, ordinal INTEGER NOT NULL, arm TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status IN ('pending','assigned','complete')), match_id TEXT,
 PRIMARY KEY(game,ordinal), UNIQUE(match_id));
CREATE TABLE IF NOT EXISTS matches(id TEXT PRIMARY KEY, game TEXT NOT NULL CHECK(game IN ('6001','9006')),
 phase TEXT NOT NULL CHECK(phase IN ('historical','calibration','formal','scenario')),
 arm TEXT NOT NULL, started_at TEXT NOT NULL, finished_at TEXT, meta TEXT NOT NULL,
 settlement TEXT, quality TEXT, source_hash TEXT);
CREATE TABLE IF NOT EXISTS events(match_id TEXT NOT NULL REFERENCES matches(id), seq INTEGER NOT NULL,
 kind TEXT NOT NULL, payload TEXT NOT NULL, hash TEXT NOT NULL, PRIMARY KEY(match_id,seq));
CREATE TABLE IF NOT EXISTS certifications(game TEXT NOT NULL, fingerprint TEXT NOT NULL,
 kind TEXT NOT NULL, evidence TEXT NOT NULL, PRIMARY KEY(game,fingerprint,kind));
CREATE TABLE IF NOT EXISTS history_lineage(id TEXT PRIMARY KEY, source_hash TEXT NOT NULL, original TEXT NOT NULL);
'''


class Store:
    def __init__(self, path, readonly=False):
        self.c = sqlite3.connect(f'file:{Path(path).resolve()}?mode=ro' if readonly else str(path),uri=readonly)
        self.c.row_factory = sqlite3.Row
        self.c.execute('PRAGMA foreign_keys=ON')
        if readonly:
            self.c.execute('PRAGMA query_only=ON')
        else:
            self.c.execute('PRAGMA journal_mode=WAL')
            self.c.execute('PRAGMA synchronous=FULL')
            self.c.executescript(SCHEMA)

    def init_schedule(self, seed=60019006):
        with self.c:
            previous = self.c.execute("select value from metadata where key='seed'").fetchone()
            if previous and int(previous[0]) != seed:
                raise ValueError('schedule_seed_immutable')
            self.c.execute("insert or ignore into metadata values('seed',?)",(str(seed),))
            for game in GAMES:
                rng = random.Random(seed+int(game))
                order = []
                for _ in range(33):
                    block = list(ARMS)
                    rng.shuffle(block)
                    order.extend(block)
                order.append(ARMS[0])
                self.c.executemany('insert or ignore into slots values(?,?,?,\'pending\',NULL)',
                                   [(game,i+1,arm) for i,arm in enumerate(order)])

    def import_history(self, source):
        original_hash = hashlib.sha256(Path(source).read_bytes()).hexdigest()
        old = sqlite3.connect(f'file:{Path(source).resolve()}?mode=ro',uri=True)
        old.row_factory = sqlite3.Row
        count = 0
        with self.c:
            for row in old.execute('select * from matches'):
                raw = dict(row)
                id_ = 'v2:' + row['match_id']
                existing = self.c.execute('select source_hash from history_lineage where id=?',(id_,)).fetchone()
                if existing:
                    if existing[0] != digest(raw):
                        raise ValueError('historical_source_changed')
                    continue
                meta = dict(client_game_id='6001',phase='historical',original_eligibility=row['eligibility_status'],
                            original_timing_status='unverified',source_database_sha256=original_hash)
                settlement = dict(result=row['result'],visible=bool(row['settlement_visible']),
                                  displayed_value=row['displayed_settlement_delta'])
                self.c.execute('insert into matches values(?,?,?,?,?,?,?,?,?,?)',
                    (id_,'6001','historical',row['strategy_arm'],row['observed_at'],row['completed_at'],encoded(meta),
                     encoded(settlement),encoded({'eligible':False,'reasons':['historical_evidence_only']}),digest(raw)))
                self.c.execute('insert into history_lineage values(?,?,?)',(id_,digest(raw),encoded(raw)))
                count += 1
        old.close()
        return {'inserted':count,'source_sha256':original_hash}

    def begin(self, meta):
        validate_payload(meta)
        game, phase = str(meta['client_game_id']), meta['phase']
        if game not in GAMES or phase not in ('formal','calibration','scenario'):
            raise ValueError('invalid_scope')
        if self.c.execute("select 1 from matches where finished_at is null and phase!='historical'").fetchone():
            raise ValueError('unfinished_match_must_be_resolved')
        with self.c:
            self.c.execute('BEGIN IMMEDIATE')
            if phase == 'formal':
                fp = meta.get('certification_fingerprint')
                certs = {r[0] for r in self.c.execute('select kind from certifications where game=? and fingerprint=?',(game,fp))}
                if not {'rules','vision200','pilot3','continuous10'} <= certs:
                    raise ValueError('calibration_not_passed')
                slot = self.c.execute("select * from slots where game=? and status='pending' order by ordinal limit 1",(game,)).fetchone()
                if not slot:
                    raise ValueError('no_pending_slot')
                meta = dict(meta,strategy_arm=slot['arm'])
            if meta.get('strategy_arm') not in ARMS:
                raise ValueError('strategy_required')
            id_ = str(uuid.uuid4())
            self.c.execute('insert into matches values(?,?,?,?,?,?,?,NULL,NULL,NULL)',
                           (id_,game,phase,meta['strategy_arm'],now(),None,encoded(meta)))
            if phase == 'formal':
                self.c.execute("update slots set status='assigned',match_id=? where game=? and ordinal=?",(id_,game,slot['ordinal']))
            self._append(id_,1,{'type':'match_start','at':now(),'controller_version':VERSION})
        return id_

    def _append(self, match_id, seq, event):
        validate_payload(event)
        record = self.c.execute('select * from matches where id=?',(match_id,)).fetchone()
        if not record or record['finished_at']:
            raise ValueError('match_not_active')
        previous = self.c.execute('select hash from events where match_id=? and seq=?',(match_id,seq)).fetchone()
        if previous:
            if previous[0] != digest(event):
                raise ValueError('event_conflict')
            return
        last = self.c.execute('select coalesce(max(seq),0) from events where match_id=?',(match_id,)).fetchone()[0]
        if seq != last+1:
            raise ValueError('non_contiguous_event_seq')
        self.c.execute('insert into events values(?,?,?,?,?)',(match_id,seq,event['type'],encoded(event),digest(event)))

    def append(self, match_id, seq, event):
        with self.c:
            self._append(match_id,seq,event)

    def finish(self, match_id, settlement):
        validate_payload(settlement)
        with self.c:
            row = self.c.execute('select * from matches where id=?',(match_id,)).fetchone()
            if not row:
                raise ValueError('unknown_match')
            if row['finished_at']:
                if row['settlement'] != encoded(settlement):
                    raise ValueError('settlement_conflict')
                return json.loads(row['quality'])
            events = [json.loads(r[0]) for r in self.c.execute('select payload from events where match_id=? order by seq',(match_id,))]
            quality = eligibility(json.loads(row['meta']),settlement,events)
            self.c.execute('update matches set finished_at=?,settlement=?,quality=? where id=?',
                           (now(),encoded(settlement),encoded(quality),match_id))
            if row['phase'] == 'formal':
                if quality['eligible']:
                    self.c.execute("update slots set status='complete' where match_id=?",(match_id,))
                else:
                    self.c.execute("update slots set status='pending',match_id=NULL where match_id=?",(match_id,))
        return quality

    def progress(self):
        history = self.c.execute("select settlement from matches where phase='historical'").fetchall()
        results = [json.loads(x[0]).get('result') for x in history]
        games = {}
        for game in GAMES:
            rows = self.c.execute("select * from matches where game=? and phase='formal'",(game,)).fetchall()
            valid = [r for r in rows if r['quality'] and json.loads(r['quality'])['eligible']]
            stats = []
            for arm in ARMS:
                cohort = [r for r in valid if r['arm']==arm]
                wins = sum(json.loads(r['settlement'])['result']=='win' for r in cohort)
                stats.append(dict(strategy=arm,qualified=len(cohort),wins=wins,win_rate=wins/len(cohort) if cohort else None,
                                  wilson95=wilson(wins,len(cohort))))
            games[game] = dict(target=100,qualified=len(valid),strategies=stats,
                              attempts=len(rows),rtp=None,rtp_status='settlement_semantics_unverified')
        return dict(as_of=now(),status='partial',calibration=[dict(r) for r in self.c.execute("select game,count(*) attempts,sum(finished_at is not null) finished from matches where phase='calibration' group by game")],historical=dict(observed=len(results),wins=results.count('win'),
                    losses=results.count('loss'),unknown=results.count('unknown')),games=games,
                    open_matches=[dict(r) for r in self.c.execute("select id,game,phase from matches where finished_at is null and phase!='historical'")])


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--db',type=Path,default=ROOT/'samples.sqlite3')
    sub=p.add_subparsers(dest='cmd',required=True)
    sub.add_parser('init')
    imp=sub.add_parser('import-v2'); imp.add_argument('source',type=Path)
    sub.add_parser('status')
    for name in ('begin','append','finish'):
        a=sub.add_parser(name); a.add_argument('input',type=Path)
        if name!='begin': a.add_argument('--match',required=True)
        if name=='append': a.add_argument('--seq',type=int,required=True)
    a=p.parse_args(); s=Store(a.db,readonly=a.cmd=='status')
    if a.cmd=='init': s.init_schedule(); result=s.progress()
    elif a.cmd=='import-v2': result=s.import_history(a.source)
    elif a.cmd=='status': result=s.progress()
    else:
        payload=json.loads(a.input.read_text())
        if a.cmd=='begin': result={'match_id':s.begin(payload)}
        elif a.cmd=='append': s.append(a.match,a.seq,payload); result={'status':'recorded'}
        else: result=s.finish(a.match,payload)
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__': main()
