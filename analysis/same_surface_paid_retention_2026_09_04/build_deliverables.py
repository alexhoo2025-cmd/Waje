"""Build one evidence model for the offline report and its Lark counterpart."""
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo

ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parents[1]
OLD=ROOT.parent/'all_platform_cohort_value_2026_09_04'

def load(name):return json.loads((ROOT/'results'/name).read_text())
def pct(x):return '未成熟／不可计算' if x is None else f'{100*x:.2f}%'

def main():
    recent=load('04_same_surface_recent.json');assert recent['status']=='ok'
    detail=load('06c_latest_app_dimensions_bounded.sql'.replace('.sql','.json'));assert detail['status']=='ok'
    raw=recent['aggregate_rows'];app=[r for r in raw if r['origin_surface']=='APP' and r['mature_users']>0]
    d2=[r for r in app if r['day_number']==2]
    den=sum(r['mature_users'] for r in d2);same=sum(r['same_surface_users'] for r in d2);unknown=sum(r['unknown_return_surface_users'] for r in d2)
    daily=[]
    for r in app:
        if r['day_number'] not in (2,3):continue
        daily.append({**r,'platform':'Android' if r['anchor_client']==2 else 'iOS',
                      'date':r['cohort_date'][5:], 'day':f'第{r["day_number"]}日',
                      'observed_rate':r['same_surface_users']/r['mature_users'],
                      'rate_display':pct(r['same_surface_users']/r['mature_users']),
                      'unknown_display':pct(r['unknown_return_surface_users']/r['mature_users'])})
    dimensions=[]
    for r in detail['aggregate_rows']:
        dimensions.append({**r,'platform':'Android' if r['anchor_client']==2 else 'iOS',
                           'rate_display':pct(r['observed_same_app_rate'])})
    datasets={'recent_raw':raw,'recent_daily':daily,'app_dimensions':dimensions}
    for key,name in [('packages','首日包名'),('versions','首日版本'),('amounts','首笔金额相对分组')]:
        datasets[key]=[r for r in dimensions if r['dimension']==name]
    datasets['devices']=sorted([r for r in dimensions if r['dimension']=='首日设备型号'],key=lambda r:-r['users'])[:8]
    datasets['amount_chart']=[r for r in datasets['amounts'] if r['platform']=='Android']
    datasets['amount_chart'].sort(key=lambda r:r['value'])
    knownapp=[]
    for p,client in [('Android',2),('iOS',1)]:
        rr=[r for r in d2 if r['anchor_client']==client];n=sum(r['mature_users'] for r in rr)
        knownapp.append({'platform':p,'users':n,'same_app':sum(r['same_surface_users'] for r in rr)/n,
                         'same_subplatform':sum(r['same_subplatform_users']+r['same_and_other_subplatform_users'] for r in rr)/n})
    datasets['app_comparison']=knownapp
    # Historical account-level results are explicitly a background, not a substitute.
    historical=[];hist_sql=[]
    for m in ('2026-06','2026-07','2026-08'):
        q=json.loads((OLD/'paid_retention_server_success_v1'/f'13_paid_retention_server_success_{m}.json').read_text())
        assert q['status']=='ok'
        hist_sql.append((PROJECT/q['sql_file']).read_text())
        source_rows=[r for r in q['aggregate_rows'] if r['breakdown']=='平台' and r['platform']!='平台未识别']
        grouped=defaultdict(list)
        for r in source_rows:
            p=r['platform']+'来源' if r['platform'] in ('Android','iOS') else '网页来源（未分运行形态）'
            grouped[r['payer_group'],p,r['day_number']].append(r)
        wide={}
        for (g,p,day),rr in grouped.items():
            if day not in (2,14,30,60,90):continue
            key=(g,p);row=wide.setdefault(key,{'group':g,'platform':p,'month':m[5:]+'月','cohort_month':m})
            n=sum(r['eligible_users'] for r in rr);cohort=sum(r['cohort_users'] for r in rr)
            rate=sum(r['retained_users'] or 0 for r in rr)/n if n>=10 and all(r['retained_users'] is not None for r in rr) else None
            row[f'd{day}_value']=rate;row[f'd{day}']=pct(rate)+('＊' if 0<n<cohort else '')
        historical.extend(wide.values())
    datasets['history_new']=[r for r in historical if r['group'].startswith('新增付费')]
    datasets['history_first']=[r for r in historical if r['group'].startswith('首次付费')]
    datasets['history_chart']=datasets['history_first']
    gaps=[
        {'segment':'APP新增付费','status':'近期观察已验证','detail':'9月1—2日批次第2日；9月1日批次第3日。不能外推6—8月。'},
        {'segment':'APP首次付费','status':'起点端缺失','detail':'9月首充成功事件端字段未识别，不能使用注册端替代。'},
        {'segment':'浏览器H5','status':'运行形态未识别','detail':'网页事件存在，但尚不能排除PWA与APP内WebView。'},
        {'segment':'实际安装PWA','status':'运行形态未识别','detail':'未找到经验证的安装／独立运行标记，不按渠道名推断。'},
        {'segment':'6—8月同端短留／长留','status':'全量查询未执行','detail':'试算约61.7GiB，超过项目查询门槛；需按日按端聚合源或新的查询授权。'},
        {'segment':'同人群付费率／LTV','status':'待同口径重算','detail':'不以旧画像注册分母或其他人群LTV填补。'}]
    datasets['coverage']=gaps
    source_files=['01_client_runtime_probe.json','02_server_anchor_probe.json','03_web_runtime_probe.json','04_same_surface_recent.json','06c_latest_app_dimensions_bounded.json']
    sources=[]
    for id_,label,files in [('runtime','起点端与运行形态核验',source_files[:3]),('recent','近期同端回访与APP下钻',source_files[3:])]:
        sources.append({'id':id_,'label':label,'path':f'analysis/{ROOT.name}/results/'+files[0],
          'query':{'engine':'Google Cloud BigQuery','language':'SQL','description':'只读聚合结果；2026年9月1—3日，业务日Africa/Lagos。',
          'sql':'\n\n'.join((ROOT/'sql'/f.replace('.json','.sql')).read_text() for f in files),
          'metric_definitions':['新增付费=注册当日服务端支付成功；起点取注册事件实际端。','APP包含Android+iOS；子端迁移另记。',
            '确认同端回访为已识别活跃的观察下界；端未知不算流失。','首日包、版本、设备取注册后首条同子端客户端活跃事件；金额分组仅为样本内排序四分位，不代表价格档位。']}})
    sources.append({'id':'history','label':'6—8月历史账号回访背景（非同端留存）','path':'analysis/all_platform_cohort_value_2026_09_04/paid_retention_server_success_v1/execution_receipt.json',
      'query':{'engine':'Google Cloud BigQuery','language':'SQL','description':'按历史画像首平台分组，账号任意端活跃；不能解释为首充发生端留存。','sql':'\n\n'.join(hist_sql)}})
    now=datetime.now(ZoneInfo('Asia/Hong_Kong')).isoformat(timespec='seconds')
    manifest={'version':1,'surface':'report','title':'Waje 三端付费留存诊断｜APP实测与H5/PWA数据边界',
      'description':'阶段版：同端观察与历史账号回访分开呈现；H5重点、APP与PWA独立章节。','generatedAt':now,
      'sources':sources,'accessIssues':['尚未完成6—8月全量同端重算、网页运行形态识别和同人群LTV。'],'cards':[],'charts':[],'tables':[],'blocks':[]}
    b=manifest['blocks']
    def md(id_,body,src=None):
        item={'id':id_,'type':'markdown','body':body}
        if src:item['sourceId']=src
        b.append(item)
    def col(field,label,fmt=None):
        r={'field':field,'label':label,'type':'number' if fmt else 'text'}
        if fmt:r['format']=fmt
        return r
    def table(id_,title,dataset,columns,source='recent'):
        manifest['tables'].append({'id':id_,'title':title,'dataset':dataset,'sourceId':source,'layout':'full','density':'spacious','columns':columns})
        b.append({'id':id_+'-block','type':'table','tableId':id_})
    def bar(id_,title,dataset,x,y,color=None,source='recent'):
        enc={'x':{'field':x,'type':'nominal','label':'注册子端' if x=='platform' else '首笔金额相对分组'},'y':{'field':y,'type':'quantitative','format':'percent','label':'回访率'}}
        if color:enc['color']={'field':color,'type':'nominal','label':'月份'}
        manifest['charts'].append({'id':id_,'title':title,'type':'bar','dataset':dataset,'sourceId':source,'layout':'full','encodings':enc,
                                  'valueFormat':'percent','labels':{'values':'all'},'legend':{'position':'bottom'}})
        b.append({'id':id_+'-block','type':'chart','chartId':id_})
    md('title','# '+manifest['title'])
    md('summary','## 执行摘要\n\n'
       f'**近期APP同端回访已能验证。** 9月1—2日注册当日付费、且注册端可识别为APP的 **{den:,}人** 中，第2日 **{same:,}人（{pct(same/den)}）** 确认回到APP；另有 **{unknown}人** 活跃但回访端未识别，不计为流失。\n\n'
       '**三端尚不能公平排名。** 当前成功首充事件缺少可用的发生端；网页日志尚不能可靠区分浏览器H5、安装PWA和APP内WebView。原来的账号留存不能直接换名为同端留存。\n\n'
       '**APP有可执行的进一步核查方向。** 已对9月2日付费批次拆出首日包名、版本、设备型号和首笔金额相对分组；差异只作为关联线索，不能据此认定版本或支付档位造成流失。\n\n'
       '**本版为阶段结果，不是完整历史结案。** 6—8月全量同端查询因超过项目门槛未执行；历史账号回访只放在独立背景章节，不与近期同端结果计算环比。')
    md('definitions','## 01｜先明确比较对象\n\n'
       '- 新增付费：注册当天支付成功，注册日及实际注册端为起点。\n'
       '- 首次付费：历史首次支付成功，首充日及首充实际端为起点；不能使用注册端代替。\n'
       '- 第N日：起点日后的第N个自然日；第2日即次日。同端活跃不要求再次付费。\n'
       '- APP总层包含Android与iOS；iOS转到Android属于APP内迁移，APP层仍算同端。\n'
       '- 已识别同端、同端且跨端、仅跨端、未观察到回访、回访端未知分别计数；有未知端事件时，不轻率标记“仅跨端”。\n\n'
       '**时间与来源：** 本次实际端查询窗口为9月1—3日，使用源业务日（Africa/Lagos，UTC+1）；完整历史要求及成熟窗口见下表。', 'recent')
    table('coverage-table','三端及两类人群的完成情况','coverage',[col('segment','分析对象'),col('status','当前状态'),col('detail','影响与下一步')],'runtime')
    md('app','## 02｜APP：近期回访与针对性拆解\n\n'
       '**先看相同注册窗口。** 以下Android／iOS均使用9月1—2日注册当日付费批次，纵轴表示第2日确认回到APP的比例。它衡量APP总层回访，不把Android与iOS之间切换算作APP流失；iOS观察量较少，不据此做优劣排名。','recent')
    bar('app-return','第2日确认回到APP：按注册子端拆分','app_comparison','platform','same_app')
    table('recent-table','近期逐批次回访：分母与未知端同时保留','recent_daily',
          [col('date','注册日'),col('platform','注册子端'),col('day','观察日'),col('mature_users','同批用户','number'),col('rate_display','确认APP回访'),col('unknown_display','端未知占比')])
    md('app-package','### 包名与版本：先控制人群构成再判断版本效果\n\n'
       '**下面只看最新已到次日的9月2日批次。** 包名、版本和设备来自注册后的首条同子端客户端活跃记录，不是最新画像回填。版本与包、渠道、金额及设备构成可能同时变化；不能把不同组的回访差异直接解释为版本效果。小于10人的分组不单列。','recent')
    dimcols=[col('platform','注册子端'),col('value','分组'),col('users','用户数','number'),col('rate_display','确认APP回访')]
    table('package-table','9月2日新增付费批次：首日包名','packages',dimcols)
    table('version-table','9月2日新增付费批次：首日版本','versions',dimcols)
    md('app-money','### 首笔金额：金额较高不代表已证明留存更好\n\n'
       '下图是Android样本按首笔成功付费金额排序后的四组，第1组最低、第4组最高。分组为等人数的相对位置，不等于固定价格档位；同金额用户可能分在相邻组。需要固定包名、版本和来源后再比较，当前只作描述。','recent')
    bar('amount-return','Android：首笔金额相对分组与次日APP回访','amount_chart','value','observed_same_app_rate')
    md('app-device','### 设备：型号可观察，性能档位尚未认证\n\n'
       '下表按人数列出前8个设备型号，仅用于定位复核对象；没有RAM和机型档位映射时，不将其直接命名为“低端机问题”。单日分组差异还可能受渠道、版本与付费金额影响。','recent')
    table('device-table','9月2日新增付费批次：人数最多的8个设备型号','devices',dimcols)
    md('h5','## 03｜H5重点：先区分网页运行形态，再定位承接问题\n\n'
       '**网页活跃并非没有采集，但纯H5分母尚不能建立。** 在本次9月1—3日、满足分组隐私阈值的 **11,246,238条** 网页事件中，未发现已检测的PWA／独立运行／WebView标记及相关自定义键。这个结果只描述本次核查窗口，不证明全部历史都没有标记。\n\n'
       '**本专题不再把来源渠道当运行形态。** 仅有网页类型或渠道码的记录进入“网页运行形态未识别”，不并入纯H5或PWA正式分母。已有画像分组的6—8月账号回访放在历史背景章节。\n\n'
       '**H5后续针对性拆解：** 自然／投放×入口×浏览器×首日游戏路径；先区分注册到付费的转化损失与付费后的回访，再检查是否迁移至APP或PWA。加载、首局完成等因素仅在同一用户起点及可用事件契约下分析，不能用未验证字段形成原因结论。','runtime')
    md('pwa','## 04｜PWA：不凭渠道名补出一个结果\n\n'
       '**PWA同端留存暂不可计算。** 尚缺可核验的实际独立运行、安装及启动证据，不能把渠道名含PWA的用户合并为“安装PWA用户”。H5／PWA之间的迁移比例也因此不能计算。\n\n'
       '补齐后采用与APP、H5相同的留存指标，并单独比较安装前来源、安装到首充时长、桌面启动与浏览器回访。APP内WebView必须优先识别为APP，避免误并入网页端。','runtime')
    md('first-pay','## 05｜首次付费：首充实际端是当前关键缺口\n\n'
       '**首充成功与首充发生端是两件事。** 本次服务端支付成功可识别，但9月1—3日成功首充事件的端字段均未识别。按有效时间去重得到的首充标记样本也全部落在“起点端未识别”，不能用最近登录端或画像注册端填回。\n\n'
       '后续应使用可追溯的同订单上下文或首充事件自身的实际端。起点冲突、重复首充标记和画像匹配缺失分别留痕，不能静默排除后声称完成三端首充比较。','runtime')
    md('history','## 06｜6—8月历史背景：账号回访，不是同端留存\n\n'
       '**下列数字保留历史经营背景，但不用于三端同端排名。** 人群按旧查询的历史画像首平台分组；回访允许发生在任一端。两类人群都与本次实际端查询不同，不能和49.18%直接计算环比。网页来源将旧网页与候选渠道合并，仍不区分H5与PWA。\n\n'
       '＊表示仅部分批次达到观察日。8月第60／90日尚未成熟；第30日也只覆盖月初批次，不能据此评价整月长留。','history')
    hc=[col('month','月份'),col('platform','画像来源')]+[col('d'+str(d),'第'+str(d)+'日') for d in (2,14,30,60,90)]
    table('history-new','新增付费：历史账号回访背景','history_new',hc,'history')
    table('history-first','首次付费：历史账号回访背景','history_first',hc,'history')
    md('value','## 07｜辅助价值：保持同人群、同起点、同定义\n\n'
       '**付费率、复充率和LTV本轮不填旧值。** 旧画像注册分母不能自动替代实际注册端分母，其他人群的H5联运LTV也不能填入两类付费人群。\n\n'
       '成功支付继续以服务端支付成功为准，不使用创建订单；LTV则须单独核对原认证定义、收入范围、币种与退款处理，不能因为使用支付成功事件就把充值金额命名为LTV。各端专属累计价值和阶段增量仍待重算。')
    md('actions','## 08｜优先动作与验收条件\n\n'
       '1. **APP分析：** 用已识别的近期结果定位主要包、版本与金额分组；扩大窗口并控制构成后，再判断稳定差异。\n'
       '2. **实际端补齐：** 为注册、成功首充和活跃事件提供可核验的运行形态与宿主APP上下文；未知端不填默认H5。\n'
       '3. **历史回补：** 提供经认证的“按日、按实际端”聚合源，或另行授权适当查询额度。全量历史试算约61.7GiB，当前未执行，不以抽样结果冒充全量。\n'
       '4. **重新验收：** 同端确认回访不超过账号回访；未知端不算流失；五类状态守恒；APP总计与Android／iOS明细不重复加总。\n'
       '5. **交付状态：** HTML与飞书使用同一份数据和正文；当前为部分完成的阶段报告，不把已生成页面等同于历史分析已完成。')
    artifact={'surface':'report','manifest':manifest,'snapshot':{'version':1,'generatedAt':now,'status':'partial','datasets':datasets}}
    (ROOT/'artifact.json').write_text(json.dumps(artifact,ensure_ascii=False,indent=2),encoding='utf-8')
    (ROOT/'report.md').write_text(markdown(artifact),encoding='utf-8')
    (ROOT/'chart_map.json').write_text(json.dumps([{'id':x['id'],'type':x['type'],'dataset':x['dataset'],'question':x['title'],'footprint':'full width','qa':'HTML official reader, plus Lark source-equivalent image and table'} for x in manifest['charts']],ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'status':'partial','same_app_rate':same/den,'tables':len(manifest['tables']),'charts':len(manifest['charts'])},ensure_ascii=False))

def markdown(a):
    m=a['manifest'];out=[];tables={t['id']:t for t in m['tables']}
    for b in m['blocks']:
        if b['type']=='markdown':out.append(b['body'])
        elif b['type']=='table':
            t=tables[b['tableId']];cols=t['columns'];rows=a['snapshot']['datasets'][t['dataset']]
            out.append('### '+t['title']+'\n\n| '+' | '.join(c['label'] for c in cols)+' |\n|'+'|'.join('---' for c in cols)+'|\n'+'\n'.join('| '+' | '.join(str(r.get(c['field'],'—')) for c in cols)+' |' for r in rows))
    return '\n\n'.join(out)+'\n'

if __name__=='__main__':main()
