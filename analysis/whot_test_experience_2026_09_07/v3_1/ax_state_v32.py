"""Parse full visible AX snapshots; never treat a diff as a complete hand.

Caller must use getAXState({disableDiffing:true, emit:false}).
This offline module has no click capability and emits no identities or URLs.
"""
import re

CARD = re.compile(r'^\s*(\d+) (?:checkbox|切换按钮)(?: \(([^)]*)\))? Description: (\d+) (circle|square|triangle|star|cross|whot),')


def parse_full(text):
    if 'There has been no change' in text or 'diff from the previous' in text:
        return {'status': 'reject', 'reason': 'incremental_snapshot'}
    lines = text.splitlines()
    out = {'status': 'ok', 'hand': [], 'draw': None, 'autoplay': False,
           'our_turn': False, 'settlement': False, 'seconds': None}
    hand_indent = None
    timer = False
    for line in lines:
        indent = len(line) - len(line.lstrip())
        if 'container Your hand' in line:
            hand_indent = indent
            continue
        if hand_indent is not None and line.strip() and indent <= hand_indent:
            hand_indent = None
        match = CARD.match(line)
        if match and hand_indent is not None:
            out['hand'].append({'index': int(match[1]), 'rank': int(match[3]),
                                'shape': match[4], 'enabled': 'disabled' not in (match[2] or '')})
        draw = re.match(r'^\s*(\d+) (?:button|按钮)(?: \(([^)]*)\))? (?:Description: )?Draw from deck, (\d+) cards remaining', line)
        if draw:
            out['draw'] = {'index': int(draw[1]), 'remaining': int(draw[3]),
                           'enabled': 'disabled' not in (draw[2] or '')}
        if 'Auto play - Touch to resume' in line:
            out['autoplay'] = True
        if re.search(r'(?:text|文本) YOUR TURN\s*$', line):
            out['our_turn'] = True
        if 'Round settlement' in line:
            out['settlement'] = True
        if timer:
            m = re.search(r'(?:text|文本) (\d+)\s*$', line)
            if m:
                out['seconds'] = int(m[1])
            timer = False
        if 'Turn time remaining' in line:
            timer = True
    return out


def eligible_observation(*, settled, autoplay_entries, continuous_count_verified):
    """User's <=3 autoplay-entry gate; unknown counts are not zero."""
    if not settled:
        return {'eligible': False, 'reason': 'settlement_missing'}
    if not continuous_count_verified or type(autoplay_entries) is not int or autoplay_entries < 0:
        return {'eligible': False, 'reason': 'autoplay_count_unknown'}
    return {'eligible': autoplay_entries <= 3,
            'reason': 'within_user_threshold' if autoplay_entries <= 3 else 'autoplay_threshold_exceeded',
            'cohort': 'manual' if autoplay_entries == 0 else 'mixed'}
