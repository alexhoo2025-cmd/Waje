# 报表数据自动采集｜精简交接摘要

归档整理日：2026-09-11。原任务：01a014ad-5e7f-7073-8de8-2ef9dbe6d028，项目 /Users/robin/Documents/wajetan_analyst。这是置顶且systemError的同名任务；未操作另一个旧同名任务019fef57-8ee9-7de1-81e6-9b9f96653423。

## 状态与恢复边界

原任务近期连续context window / remote compact错误。无可调用的原生compact工具；CUA禁止操作Codex应用，故没有成功改写或缩短原任务模型上下文。本文件是人工精简的交接摘要，原历史通过应用归档保留，不删除，不复制完整聊天或工具日志。已审阅最近10轮摘要及下列本地回执；不是全历史逐条总结。失败轮工具未返回完整请求，不推断其未完成业务意图。没有重跑采集、写入飞书或创建新任务。

## 最近已完成：Origin新包新增用户分析

最新用户确认：所有来源完整日期均更新，未成熟指标留空，不因D3未成熟跳过整行；成熟真实0保留。此规则取代该任务早先“近3天整行排除”及所有零值清空做法，仅用于本次Origin报表，不能推广到Joint等其他报表。

- 写入起点窗口：2026-08-24至09-06；观测截止2026-09-07，Asia/Hong_Kong。8个Sheet、43字段、14个日期，无整行排除。
- row_policy=stratified；清空1856个未成熟字段；保留9/5、9/6数据行。该两日保留首日、次日、次留、首充次留和非Dn指标，3日及更长窗口留空（仅此次窗口适用，后续按新的截止日重算）。
- 2026-09-08最终回执status=ok；飞书历史revision 778→787，16个范围、8个插入操作，回读ok。该revision是当时状态，非今日在线核验。
- 关键回执：data/outputs/origin_new_user/2026-09-08-9-6-stratified/local-update-final/final-run-receipt.json；同目录stratified-maturity-validation.json、lark-readback-validation.json、maturity-ledger.json。
- 项目输出：data/outputs/origin_new_user/2026-09-08-9-6-stratified/local-output/新用户数据分析2026.8.5-9.6_new_AI更新版_字段成熟度版.xlsx。
- 原任务交付的桌面副本：/Users/robin/Desktop/waje data/新用户数据分析2026.8.5-9.6_new_AI更新版_字段成熟度版.xlsx（本次未重新核对文件哈希）。
- 飞书：https://ksg964l11fam.sg.larksuite.com/wiki/At8gwdbXUiPa0WkXvKqlSUNKg5d?sheet=gjy6I1
- 主要脚本：scripts/update_origin_new_user_workbook.mjs、prepare_origin_new_user_run.py、finalize_origin_new_user_run.py、validate_origin_new_user_stratified_maturity.py、validate_origin_new_user_lark_readback.py。
- 保护8/23及以前历史、WAJEBETH5/PWA额外列和PWA条件格式；PWA首列历史别名不擅改，使用日期及43字段内容核对映射。

## Joint生命周期最近交付

data/outputs/lifecycle_joint/2026-09-07/run-receipt.json实际status=degraded：纳入9/4–9/6，9/3仍被排除；包含既有重复键警告，不称无条件完全成功。当时revision1593→1598。原任务称四表回读通过，但本次不重新执行业务验收。

- 本地：/Users/robin/Desktop/waje data/新包生命周期V2 - 含联运2026.9.4-9.6_Joint修正版.xlsx。
- 证据目录：data/outputs/lifecycle_joint/2026-09-07/；validation-report.json、maturity-report.json、lark-backup-complete/backup-index.json。
- 飞书：https://ksg964l11fam.sg.larksuite.com/wiki/ZBD4wPBsricBWMktFqilAGxlgte
- 后续先核对9/3排除的具体原因，不照搬Origin字段级成熟度规则。

## 后续接手最小步骤

1. 读取当前AGENTS.md/CLAUDE.md及本次相关的Origin或Joint技能；先明确新请求窗口、币种、渠道与观测截止，不自动更新至今天。
2. 先读最新回执与用户定稿文件，重新读在线revision并比较跨端修改；不直接执行旧生成器覆盖用户后续修改。
3. 查询仅取最小必要窗口；按现行项目要求做scope日期检查、只读校验与适用的dry-run。采集、备份、校验、新副本写入、回读缺一不可。
4. auth_required、query_stale、未成熟、缺失和历史重复键按真实状态保留；不补零、不推测成功；不保留凭据或个人记录。
5. 当前没有已确认的新业务执行任务。用户下次给出日期/报表要求后再继续。原任务更早还有Play评价采集背景，相关现状未在本次复核，不从此摘要恢复执行旧计划。
