"""Deterministic semantics independent of schema availability; no source guessing."""
from datetime import date,timedelta

STATES=('same_only','same_and_other','only_other','no_observed_return','unknown_return_surface')

def runtime_surface(client_type=None,display_mode=None,host_app=False,pwa_install_verified=False):
    if host_app or client_type in (1,2):return 'APP'
    if display_mode=='standalone' or (pwa_install_verified and display_mode in ('fullscreen','minimal-ui')):return 'PWA'
    if display_mode=='browser':return 'H5'
    return None

def target_day(anchor,day):
    if day<1:raise ValueError('Day numbering starts at 1')
    return date.fromisoformat(anchor)+timedelta(days=day-1)

def classify(anchor,surfaces,unknown_event=False,account_active=False,mature=True):
    if not mature:return 'immature'
    if anchor not in ('APP','H5','PWA'):return 'unknown_anchor'
    known={s for s in surfaces if s in ('APP','H5','PWA')}
    same=anchor in known;other=bool(known-{anchor})
    if same and other:return 'same_and_other'
    if same:return 'same_only'  # Confirmed same; unclassified extra events do not erase it.
    if unknown_event or (account_active and not known):return 'unknown_return_surface'
    if other:return 'only_other'
    return 'no_observed_return'

def subplatform_state(anchor_client,clients,unknown_event=False):
    same=anchor_client in clients;other=bool(set(clients)-{anchor_client})
    if same and other:return 'same_and_other'
    if same:return 'same_only'
    if unknown_event:return 'unknown_return_surface'
    if other:return 'only_other'
    return 'no_observed_return'

def weighted_rate(rows,numerator='same_surface_users',denominator='mature_users'):
    den=sum(r[denominator] for r in rows)
    return sum(r[numerator] for r in rows)/den if den else None
