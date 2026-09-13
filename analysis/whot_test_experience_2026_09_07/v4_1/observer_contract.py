"""Convert calibration candidates without inventing recognized confidence."""
def normalize_card(raw):
    return {k:raw.get(k) for k in ('rank','shape','point','confidence','rank_score','shape_score','shape_evidence')}

def action_readiness(cards,route,frame_age_ms,calibration):
    reasons=[]
    if route!='/game/6001-whot':reasons.append('wrong_route')
    if frame_age_ms is None or frame_age_ms<0 or frame_age_ms>750:reasons.append('stale_or_unknown_frame_age')
    if calibration.get('status')!='passed':reasons.append('vision_uncalibrated')
    if not cards:reasons.append('no_hand_observed')
    for c in cards:
        if c.get('shape') in (None,'unknown'):reasons.append('shape_unknown')
        if c.get('confidence') is None or c['confidence']<.98:reasons.append('card_confidence_unverified')
    return {'ready':not reasons,'reasons':sorted(set(reasons))}
