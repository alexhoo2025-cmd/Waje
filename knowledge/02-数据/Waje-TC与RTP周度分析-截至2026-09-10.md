---
title: Waje TC回升，但EasyWin、Tower与Hilo仍需复核
status: provisional
updated: 2026-09-11
window: 2026-09-04/2026-09-10
comparison: 2026-08-28/2026-09-03
timezone: Asia/Hong_Kong
---

# Waje TC回升，但EasyWin、Tower与Hilo仍需复核

本期为2026年9月4—10日，基线为8月28日—9月3日，均为7个完整自然日。

## 核心结论

- TC由77.14%升至78.92%，增加1.78个百分点。成功充值增长1.75%，成功提现增长4.10%，资金流出增长更快。
- 完全下注额由172.96亿增至177.86亿，增长2.83%；实际RTP由96.403%升至96.726%，增加0.324个百分点。
- 有预期RTP的下注覆盖43.8%；在该范围内，实际RTP高于预期0.05个百分点，未出现全局性偏离。
- Tada下注增加3.20亿，Fish增加1.79亿；OMG减少0.92亿，RouletteV2减少0.67亿。
- EasyWin实际RTP 149.94%、较预期高52.97个百分点，但本期下注仅704.26万；Tower实际RTP 101.13%、较预期高4.40个百分点；Hilo实际RTP 88.98%、较预期低7.77个百分点。三者需按偏离幅度与下注规模共同复核。

## 数据边界

- TC来自企业BigQuery服务端成功充值与提现事件，按交易号去重；本次只读查询处理约8.04 GiB。
- RTP来自GM Lifecycle Pool v2 (Joint)。9月10日四表结构、重复键和跨表勾稽已通过。
- 注册渠道TC本期未展示：当前BigQuery同日画像无法完整覆盖历史注册用户，不能以未知渠道占比很高的结果替代。
- 缺少有效局数、最终结算状态、取消退款、Bonus、配置版本和用户级大奖分布；偏离是复核信号，不是故障或因果结论。

## 产物

- 本地HTML：`output/html/Waje-TC-RTP周度分析-截至2026-09-10.html`
- 飞书文档：<https://ksg964l11fam.sg.larksuite.com/docx/SxAOdwmGNo2nTKxP8o3lbGWGgBg>
- 查询、聚合、来源快照与质量回执：`analysis/tc_rtp_weekly_2026_09_11/`
- 参考报告：<https://ksg964l11fam.sg.larksuite.com/wiki/O4wuw0DsxiACgxkf5XAl6RTHgYO>
