# WHOT 对局样本库与快速策略引擎 V1

## 目标

仅用于 `test-h5.wajew.com` 的 WHOT 6001 测试。以可见牌面模拟正常玩家，避免倒计时托管，逐步比较策略臂的胜率、结算单位和决策耗时。测试筹码只作为页面显示单位；不充值、不提现、不使用隐藏牌或客户端篡改。

## 本地数据结构

数据库：`whot_samples.sqlite3`

- `matches`：每局一行，只保留端、房间显示单位、对手匿名别名、结果、结算显示单位、剩余点数和证据状态。
- `turns`：每个可观察回合一行，区分 `human`、`bot`、`auto_play`；保留可见牌型、动作、决策耗时、倒计时风险和特殊效果。
- `strategy_metrics`：按策略臂汇总胜率、95% Wilson 下界、超时率、平均决策耗时和分数。
- `policy_versions`：策略版本审计。

不保存账号、Cookie、Token、隐藏手牌、完整浏览器响应或设备标识。

## 决策顺序

1. 读取当前弃牌的数字和牌型、自己的可见手牌、对手可见手牌数、剩余秒数。
2. 过滤合法牌：WHOT 20、同数字或同牌型；没有合法牌立即抽牌。
3. 默认优先清理高点数合法牌；保留 WHOT 20，除非它是唯一合法牌或进入一张牌收尾。
4. 剩余 2 秒以内，不进入复杂选择；优先执行最快的非 WHOT 合法牌，降低被托管概率。
5. 打出 WHOT 20 时，仅选择能连接自己下一张牌的公开牌型；牌型转盘选择单独记录。

## 数据驱动调整

- 每个策略臂至少 5 局前不切换主策略，只输出观察结果。
- 达到门槛后按 `0.7 × Wilson95下界 + 0.3 × 胜率 - 0.1 × 超时率` 选臂；决策耗时作为诊断，不替代胜率。
- 人工控制局和机器人托管局分开统计；机器人样本用于学习特殊牌、加二、WHOT 牌型选择、Last Card 和响应时间，不计入人工胜率。
- 任何 payout 缺失、结算页未展示或状态延迟的局，保留 `observed_only`，不把缺失值补成 0。

## 复跑

```bash
python3 analysis/whot_test_experience_2026_09_07/whot_sample_db.py init
python3 analysis/whot_test_experience_2026_09_07/whot_sample_db.py ingest
python3 analysis/whot_test_experience_2026_09_07/whot_sample_db.py ingest-jsonl \
  analysis/whot_test_experience_2026_09_07/manual_observations.jsonl
python3 analysis/whot_test_experience_2026_09_07/whot_sample_db.py report
```

决策接口示例：

```bash
python3 analysis/whot_test_experience_2026_09_07/whot_sample_db.py recommend \
  --state-json '{"table_rank":3,"table_shape":"triangle","hand":[{"rank":20,"shape":"wild"},{"rank":12,"shape":"triangle"}],"opponent_card_count":4,"seconds_remaining":4}'
```

当前样本仍不足以证明长期优势或 RTP 超过 1；只用于优化响应速度、比较策略臂和评估机器人行为。
