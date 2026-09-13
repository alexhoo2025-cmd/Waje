# WHOT 测试与策略系统 V2

V2 将历史 V1 回执迁移到独立数据库，并提供只读质量报告、显式策略规则、77局平衡排期和未来对局的原子记录入口。V1 文件不会被修改。

## 主要文件

- `whot_lab_v2.py`：数据库迁移、质量检查、排期、规则决策和只读报告。
- `whot_samples_v2.sqlite3`：V2 样本库。
- `ruleset_observed_v1.json`：已确认规则和未确认边界。
- `experiment_schedule.json`：剩余77局平衡排期。
- `quality_checks.json`：当前质量门禁。
- `analysis_snapshot.json`：报告使用的只读分析快照。
- `whot_test_sop_v2.md`：普通 Chrome、站内入口和五秒决策规范。

## 初始化与迁移

```bash
python3 analysis/whot_test_experience_2026_09_07/v2/whot_lab_v2.py init
python3 analysis/whot_test_experience_2026_09_07/v2/whot_lab_v2.py migrate \
  --receipt-out analysis/whot_test_experience_2026_09_07/v2/migration_receipt.json
python3 analysis/whot_test_experience_2026_09_07/v2/whot_lab_v2.py schedule --count 77 \
  --output analysis/whot_test_experience_2026_09_07/v2/experiment_schedule.json
python3 analysis/whot_test_experience_2026_09_07/v2/whot_lab_v2.py recompute-metrics
```

重复执行迁移不会新增重复对局；若来源内容发生变化，则依据来源哈希更新对应记录。

## 只读检查

```bash
python3 analysis/whot_test_experience_2026_09_07/v2/whot_lab_v2.py quality
python3 analysis/whot_test_experience_2026_09_07/v2/whot_lab_v2.py report
```

`quality` 和 `report` 以 SQLite `mode=ro` 与 `query_only=ON` 打开数据库，不刷新派生指标。

进入牌局前先执行浏览器门禁；PWA、外部搜索和其他游戏路径返回非零退出码：

```bash
python3 analysis/whot_test_experience_2026_09_07/v2/whot_lab_v2.py validate-gate \
  --state-json '{"browser_surface":"external_chrome","current_url":"https://test-h5.wajew.com/game/6001-whot","entry_method":"site_home_card_6001"}'
```

## 策略决策

策略必须在每局开始时显式指定，不由历史小样本自动选取：

```bash
python3 analysis/whot_test_experience_2026_09_07/v2/whot_lab_v2.py recommend \
  --strategy-arm reduce_high_point_cards \
  --state-json '{"ruleset_version":"observed_v1","is_player_turn":true,"pending_effect":"none","capture_confidence":0.95,"rescan_count":0,"table_card":{"rank":3,"shape":"triangle"},"visible_hand":[{"rank":20,"shape":"wild"},{"rank":12,"shape":"triangle"}],"opponent_visible_card_counts":[4],"seconds_remaining":4}'
```

输出包含动作、选择的牌、WHOT目标图案、理由、合法动作数、计算耗时和执行截止时间。

## 记录新对局

先按 `live_observation_template.json` 生成一份局级 JSON，再执行：

```bash
python3 analysis/whot_test_experience_2026_09_07/v2/whot_lab_v2.py record-live \
  --input /absolute/path/to/one_match.json \
  --receipt-out /absolute/path/to/one_match_receipt.json
```

输入若包含密码、Cookie、Token、手机号、邮箱、用户/设备/会话标识、隐藏牌或请求/响应正文，会被拒绝。

## 测试

```bash
python3 -m unittest discover \
  -s analysis/whot_test_experience_2026_09_07/v2 \
  -p 'test_*.py' -v
```

当前历史样本只用于探索性复盘。正式策略选择要求同规则、同房间、同下注档位，每组至少25个合格完整局，并通过覆盖、托管、非法动作和时延门禁。
