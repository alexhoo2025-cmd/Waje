from pathlib import Path
import html,re,json,xml.etree.ElementTree as ET
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
def txt(x,y,lines,size=21,color='#203c50'):
 return ''.join(f'<text x="{x}" y="{y+i*(size+10)}" font-family="Noto Sans SC" font-size="{size}" text-anchor="middle" fill="{color}">{html.escape(t)}</text>' for i,t in enumerate(lines))
def box(x,y,w,h,lines,fill='#eaf2f8',size=21):return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="{fill}" stroke="#8ca9bc"/>'+txt(x+w/2,y+32,lines,size)
def line(points):return f'<polyline points="{points}" fill="none" stroke="#678ba2" stroke-width="2.5"/>'
def down(x,y):return f'<polygon points="{x-6},{y-8} {x+6},{y-8} {x},{y+2}" fill="#678ba2"/>'
def start(title,h):return f'<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="{h}" viewBox="0 0 1080 {h}"><rect width="1080" height="{h}" rx="18" fill="#f7fafc"/>'+txt(540,40,[title],26)
s=start('两人局：优先级控制 → 保护或普通匹配',800)
s+=box(360,70,360,65,['先读取更高优先级控制'],'#dcebf5')
for x in [185,540,895]:s+=line(f'540,135 540,162 {x},162 {x},195')+down(x,195)
for x,label in [(185,'已命中：优先执行'),(540,'未命中 → 4.44%'),(895,'未命中 → 95.56%')]:
 s+=f'<rect x="{x-135}" y="168" width="270" height="24" fill="#f7fafc"/>'+txt(x,185,[label],18)+line(f'{x},193 {x},200')+down(x,200)
s+=box(45,205,280,102,['水位指定机器人','必赢或必输'],'#eee9f7')
s+=box(400,205,280,102,['保护路径','指定必输机器人'],'#e3f1e9')
s+=box(755,205,280,102,['普通路径','优先寻找真人'],'#eaf2f8')
for x in [185,540]:
 s+=line(f'{x},307 {x},340')+down(x,340)+box(x-140,347,280,85,['等待约8—13秒'], '#fff2dc')
s+=line('895,307 895,340')+down(895,340)+box(755,347,280,112,['有真人 → 真人局','否则继续等5—10秒'],'#fff2dc',20)
s+=line('895,459 895,490')+down(895,490)+box(755,498,280,125,['仍无真人才第二次随机','52.63% 选必赢机器人','47.37% 选必输机器人'],'#eee9f7',18)
s+=line('185,432 185,646 540,646 540,666')+line('540,432 540,666')+line('895,623 895,646 540,646')+down(540,666)
s+=box(235,677,610,82,['检查指定类型库存：空闲 → 真人＋机器人','该类型忙满 → 本次匹配失败'],'#eaf2f8',20)
s+=txt(540,788,['图中概率为示例；真人局与机器人局均需开桌前复查'],17)
(P/'two-player.svg').write_text(s+'</svg>')
s=start('四人局：审核真人 → 按人数征求降级同意',735)
s+=box(245,70,590,82,['逐人审核：本人状态＋与组内每个人的关系'],'#dcebf5',20)
s+=line('540,152 540,184')+down(540,184)
s+='<polygon points="540,188 670,243 540,298 410,243" fill="#fff2dc" stroke="#bc9958"/>'+txt(540,240,['当前有几名真人？'],20)
for x in [190,540,890]:s+=line(f'540,298 540,323 {x},323 {x},360')+down(x,360)
s+=box(45,370,290,165,['1或2人','询问是否转两人匹配','需要决定者全部同意','→ 完整两人流程'],'#eaf2f8',21)
s+=box(395,370,290,165,['3人','全部同意 → 三人真人局','截止恰好2人同意','→ 转完整两人流程'],'#eaf2f8',19)
s+=box(745,370,290,165,['4人','四人均已通过审核','→ 四人真人局'],'#e3f1e9',21)
s+=box(75,565,930,90,['不足4人：人数稳定满5秒后首轮询问，玩家有5秒决定','未成局则继续等待；最后一轮在第35—45秒，最晚45秒结束'],'#fff2dc',20)
s+=txt(540,695,['关键：三人／四人是纯真人；转两人后才可能再次进入机器人路径'],19)
(P/'four-player.svg').write_text(s+'</svg>')
def inline(s):
 s=html.escape(s,quote=True)
 s=re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)',r'<a href="\2">\1</a>',s)
 return re.sub(r'\*\*(.+?)\*\*',r'<b><span background-color="light-blue">\1</span></b>',s)
md=(P/'explanation.md').read_text();out=[]
for para in md.split('\n\n'):
 if not para.strip():continue
 if para.startswith('# '):out.append('<title>'+inline(para[2:])+'</title>')
 elif para.startswith('## '):out.append('<h1>'+inline(para[3:])+'</h1>')
 elif para.startswith('### '):out.append('<h2>'+inline(para[4:])+'</h2>')
 elif para.startswith('!['):
  name=re.search(r'\]\((.+)\.png\)',para)[1];out.append('<whiteboard type="svg" path="@./analysis/whot_robot_explainer_2026_09_08/'+name+'.svg"/>')
 elif para.startswith('|'):
  lines=para.splitlines();rows=[[c.strip() for c in l.strip('|').split('|')] for l in lines];cols=rows[0]
  out.append('<table><colgroup>'+''.join(f'<col width="{1020//len(cols)}"/>' for _ in cols)+'</colgroup><thead><tr>'+''.join('<th background-color="light-gray"><p>'+inline(c)+'</p></th>' for c in cols)+'</tr></thead><tbody>')
  for row in rows[2:]:out.append('<tr>'+''.join('<td vertical-align="top"><p>'+inline(c)+'</p></td>' for c in row)+'</tr>')
  out.append('</tbody></table>')
 elif re.match(r'\d+\. ',para):out.append('<ol>'+''.join('<li>'+inline(re.sub(r'^\d+\. ','',l))+'</li>' for l in para.splitlines())+'</ol>')
 elif para.startswith('- '):out.append('<ul>'+''.join('<li>'+inline(l[2:])+'</li>' for l in para.splitlines())+'</ul>')
 else:out.append('<p>'+inline(para)+'</p>')
xml='\n'.join(out);ET.fromstring('<doc>'+xml+'</doc>')
(ROOT/'draft_24935f41_folder/draft.xml').write_text(xml);(P/'release.xml').write_text(xml)
print(json.dumps({'characters':len(md),'tables':xml.count('<table>'),'diagrams':xml.count('<whiteboard '),'source_revision':json.loads((P/'source-receipt.json').read_text())['revision']},ensure_ascii=False))
