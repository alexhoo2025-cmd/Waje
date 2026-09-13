"""Capture current authorized document evidence, excluding identity and notice envelopes."""
import json, subprocess
from pathlib import Path
BASE = Path(__file__).resolve().parent / 'robot_replay_2026_09_08'
CLI = '/Users/robin/.local/node-v24.18.1-darwin-arm64/lib/node_modules/@larksuite/cli/bin/lark-cli'
BASE.mkdir(exist_ok=True)
for label, doc in [('phase2_before', 'O8uod8284o4Qv0xFkDBl96qqgQV'), ('robot_policy', 'TuwcdRgPcoyxJKx7FPOltifpgXe'), ('game_rules', 'N2jKdw0rLof78FxpCHulX7XggPh')]:
    path = BASE / (label + '.json')
    if path.exists():
        print(label, 'existing capture preserved')
        continue
    res = json.loads(subprocess.check_output([CLI, 'docs', '+fetch', '--as', 'user', '--doc', doc, '--detail', 'full'], text=True))
    assert res.get('ok'), res
    data = res['data']['document']
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    print(label, data['revision_id'], len(data['content']))
