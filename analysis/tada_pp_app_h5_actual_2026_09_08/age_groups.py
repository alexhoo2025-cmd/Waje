"""Event-day account age rules for the newly requested actual analysis."""
from datetime import date

def age_group(registration_date,activity_date):
    if registration_date is None:return 'unknown_registration'
    days=(activity_date-registration_date).days
    if days<0:return 'invalid_registration_date'
    return 'new_30d' if days<30 else 'old_over_30d'

if __name__=='__main__':
    r=date(2026,8,1)
    assert age_group(r,r)=='new_30d'
    assert age_group(r,date(2026,8,30))=='new_30d'
    assert age_group(r,date(2026,8,31))=='old_over_30d'
    assert age_group(None,r)=='unknown_registration'
    assert age_group(date(2026,8,2),r)=='invalid_registration_date'
    print('5 age-boundary tests passed; synthetic dates only')
