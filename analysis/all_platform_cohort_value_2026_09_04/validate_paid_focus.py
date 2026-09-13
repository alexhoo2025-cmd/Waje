"""Validate payer-retention results separately from superseded registration analysis."""
import json
import math
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parent
HTML=ROOT.parents[1]/'output/html/Waje-全平台用户生命周期与付费价值分析-H5自然新增重点-2026-09-04.html'


def main():
    a=json.loads((ROOT/'artifact.json').read_text());m=a['manifest'];d=a['snapshot']['datasets']
    failures=[];checks=[]
    def check(name,ok):
        checks.append({'check':name,'status':'passed' if ok else 'failed'})
        if not ok:failures.append(name)
    raw=[];jobs=[]
    for month in ('2026-06','2026-07','2026-08'):
        r=json.loads((ROOT/'paid_retention_server_success_v1'/f'13_paid_retention_server_success_{month}.json').read_text())
        check(month+'查询完成且未截断',r['status']=='ok' and r['execution']['row_count']<3000)
        jobs.append(r['execution']['job_id']);raw+=r['aggregate_rows']
    keys=[(r['cohort_month'],r['payer_group'],r['platform'],r['package_name'],r['channel'],r['day_number']) for r in raw]
    check('月×人群×端×包×渠道×留存日无重复',len(keys)==len(set(keys)))
    check('有效分母与留存率一致',all(
        0<=r['eligible_users']<=r['cohort_users'] and
        ((r['retention_rate'] is None and r['eligible_users']<10) or
         (r['retained_users'] is not None and 0<=r['retained_users']<=r['eligible_users']
          and math.isclose(r['retention_rate'],r['retained_users']/r['eligible_users'],abs_tol=1e-12))) for r in raw))
    original={(r['payer_group'],r['cohort_month'],r['platform'],r['day_number']):r for r in raw if r['breakdown']=='平台'}
    same=True
    for r in d['paid_retention_platform']:
        if r['platform']=='APP（Android+iOS）':
            parts=[original[r['payer_group'],r['cohort_month'],p,r['day_number']] for p in ('Android','iOS')]
            same &= r['cohort_users']==sum(x['cohort_users'] for x in parts) and r['eligible_users']==sum(x['eligible_users'] for x in parts)
            if r['retained_users'] is not None:
                same &= r['retained_users']==sum(x['retained_users'] for x in parts)
        else:same &= r==original[r['payer_group'],r['cohort_month'],r['platform'],r['day_number']]
    check('已交付源值一致且APP按分子分母汇总',same)
    check('付费率使用同批注册人数且非创建订单',all(0<=r['paid_users']<=r['registered_users'] and math.isclose(r['payment_rate'],r['paid_users']/r['registered_users']) for r in d['registration_day_payment']))
    check('8月60／90日不补零',all(r['retention_rate'] is None for r in d['paid_retention_platform'] if r['cohort_month']=='2026-08' and r['day_number']>=60))
    text='\n'.join(b.get('body','') for b in m['blocks'])
    check('主线为两类付费用户且撤回旧付费率',all(s in text for s in ['注册当日','首次付费','PWA','支付成功']) and not any(s in text for s in ['58.05%','问题不在回访本身']))
    check('无需分析的渠道模块未进入成品',not re.search(r'phoenix|phenix|firebase|h5phx',json.dumps(a),re.I))
    check('中文正文及必要数据边界',not re.search(r'Executive Summary|\bcohort\b|\bsession\b',text,re.I) and '待确认' in text and '尚未计算' in text)
    check('全部数据图表与来源关联',all(o['sourceId'] in {s['id'] for s in m['sources']} for k in ('charts','tables') for o in m[k]))
    check('LTV降幅保留但明确辅助口径',all(x in text for x in ['99.99','231.63','-5.9%','-9.6%','不是上文两类付费人群自己的LTV']))
    html=HTML.read_text()
    check('自包含HTML且嵌入付费专题',bool(html) and m['title'] in html and not re.search('https?://',html))
    browser=json.loads((ROOT/'browser_verification.json').read_text())
    check('桌面／窄屏与来源交互通过',browser.get('ok') is True and browser.get('viewports')==[1440,390] and browser.get('sourceDialog')=='passed')
    result={'overall_assessment':'partial_pending_business_definitions' if not failures else 'needs_revision',
            'data_cutoff':'2026-09-03','query_job_ids':jobs,'checks':checks,'failures':failures,
            'remaining':['新增付费窗口待业务确认','PWA生产渠道映射待确认','各端两类付费人群专属LTV未计算'],
            'retired':['创建订单口径的付费率、ARPU与付费人数结论','全量注册留存作为主结论']}
    (ROOT/'paid_focus_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'assessment':result['overall_assessment'],'failure_count':len(failures),'failures':failures},ensure_ascii=False))
    return 1 if failures else 0

if __name__=='__main__':raise SystemExit(main())
