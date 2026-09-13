"""Channel-name attribution; never an inference about the runtime of an individual bet."""
from pathlib import Path
import collections,csv,json,re

P=Path(__file__).resolve().parent
APP_ALIASES={
    'WAJESPECIAL': 'APP_Android',
    'PAGOOGLEPLAY': 'APP_Android',
    'PAWAJESPECIA': 'APP_Android',
    'PAWAJEPALM2': 'APP_Android',
    'PAWAJEPALMS': 'APP_Android',
    'PAPAWJBETCY2': 'APP_Android',
    'PAWAJEXENDER': 'APP_Android',
    'PAWAJESPOPAY': 'APP_Android',
    'PACHAMPIONS': 'APP_Android',
}
EMPTY={'','UNKNOWN','NULL','NONE','-9999','0'}

def classify(code, labels=()):
    code=(code or '').strip()
    if code.upper() in EMPTY:
        return 'unmapped','missing_or_placeholder_channel'
    names=' '.join([code,*labels]).upper()
    is_pwa='PWA' in names
    is_h5='H5' in names
    is_ios=bool(re.search(r'IOS',names))
    if is_ios and (is_h5 or is_pwa):
        return 'unmapped','conflicting_explicit_names'
    if is_pwa:
        return 'PWA_named','explicit_pwa_name_not_installation_evidence'
    if is_h5:
        return 'H5','explicit_h5_name'
    if is_ios:
        return 'APP_iOS','explicit_ios_name'
    if code.upper() in APP_ALIASES:
        return APP_ALIASES[code.upper()],'verified_app_channel_alias'
    return 'unmapped','name_requires_confirmation'

def main():
    dictionary=json.loads((P/'queries/06_channel_dictionary.result.json').read_text())
    profiles=json.loads((P/'queries/07_profile_channel_probe.result.json').read_text())
    labels=collections.defaultdict(set)
    for row in dictionary:
        if row['channel_label']:labels[row['channel']].add(row['channel_label'])
    evidence=collections.defaultdict(lambda:collections.Counter())
    for row in profiles:
        code=row['download_channel'] or row['first_channel'] or ''
        key=(row['first_package_name'] or 'unknown',str(row['first_client_type']))
        evidence[code][key]+=row['profile_rows']
    output=[]
    for code in sorted(set(labels)|set(evidence)):
        names=sorted(labels[code])
        group,basis=classify(code,names)
        output.append({
            'channel':code,'labels':names,'platform_group':group,
            'basis':basis,'quality':'provisional_channel_attribution',
            'profile_evidence':[
                {'first_package':k[0],'first_client_type':k[1],'profile_rows':n}
                for k,n in evidence[code].most_common()
            ],
        })
    receipt={
        'scope':'channel_attribution_not_actual_betting_runtime',
        'sources':['queries/06_channel_dictionary.result.json','queries/07_profile_channel_probe.result.json'],
        'date':'2026-09-08','rows':output,
        'channel_counts':dict(collections.Counter(r['platform_group'] for r in output)),
        'rules':[
            'Use download/first channel attached to the chosen registration profile; never last login platform',
            'Explicit PWA-named channels are shown separately; installation is not established',
            'Generic OS in the channel dictionary does not override H5/iOS names',
            'APP alias list is restricted to observed named channels with native-package corroboration',
            'Unclear names remain unmapped; profile evidence is available for review, not automatic reassignment',
            'Profile row counts are historical record counts, not distinct users or current-window coverage',
            'Current mapping effective dates are unavailable; do not claim historical configuration validation',
        ],
    }
    (P/'channel-mapping.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    with (P/'channel-mapping.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['渠道','渠道名称','渠道归属','映射依据','质量状态'])
        for r in output:w.writerow([r['channel'],' / '.join(r['labels']),r['platform_group'],r['basis'],r['quality']])
    print(json.dumps({'channels':len(output),'groups':receipt['channel_counts'],'actual_runtime_certified':False},ensure_ascii=False))

def test():
    cases=[
        ('PAWAJEH5OP',[], 'H5'),('PAWAJEIOS',['wajeios'],'APP_iOS'),
        ('PAWAJEH5PWA',[], 'PWA_named'),('PAWAJEH5PW',[], 'H5'),
        ('WajeSpecial',['WajeSpecial主包'],'APP_Android'),
        ('PAPAWAJECYW',['wajecyw'],'unmapped'),
        ('PAPAWJBETCY',['wajebetcy'],'unmapped'),
        ('PAOPAYLIANYU',['opay lianyunH5'],'H5'),
        ('12345',['waje-iOS-fb-0609-03'],'APP_iOS'),
        ('12345',['waje-h5','waje-ios'],'unmapped'),
        ('Unknown',['wajeH5'],'unmapped'),('',[],'unmapped'),
    ]
    for code,labels,expected in cases:assert classify(code,labels)[0]==expected,(code,labels)
    return len(cases)

if __name__=='__main__':
    print(json.dumps({'classification_tests_passed':test()}));main()
