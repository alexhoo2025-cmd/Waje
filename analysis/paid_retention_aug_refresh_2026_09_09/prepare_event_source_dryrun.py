"""Prepare an unexecuted alternative to assess the cost of source reconciliation."""
from pathlib import Path
import json
P=Path(__file__).resolve().parent
s=(P/'02_august_population_comparison.sql').read_text()
s=s.replace('`wajenigeria.origin_hfyl.view_user_version_daily`','`wajenigeria.origin_hfyl.view_metaevent_active_events`')
(P/'05_august_event_source_comparison.sql').write_text(s)
(P/'05_august_event_source_comparison.scope.json').write_text(json.dumps({'start':'2026-08-01','end':'2026-09-09','purpose':'Dry-run alternative activity source; not approved as equivalent definition'}))
