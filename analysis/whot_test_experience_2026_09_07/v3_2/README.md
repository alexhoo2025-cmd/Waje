# WHOT 6001 老版受控测试 V3.2

这是 V3.1 的追加式派生实现。V3.1 历史文件和数据库保持不变；本目录用于新的
6001 受控测试批次、回放、结算和聚合报告。

## 当前固定口径

- 目标：新增 100 局受控结算；历史/校准记录不抵扣。
- 策略：`first_legal_play` 34 局、`reduce_high_point_cards` 33 局、
  `retain_special_or_wild_cards_until_needed` 33 局。
- 矩阵：2 人 60 局、3 人 20 局、4 人 20 局；BET 1/100/200/1000/5000
  分别 20/20/20/25/15 局；不进入 50,000 档。
- 页面 `+1.8` 只作为明确假设下的 `provisional_page_rtp`，服务端账本未对账前
  `formal_rtp_status=unverified`。
- 自动托管、人工接管、确认未知、规则未知、结算缺失的局保留为观察数据，不能
  进入正式策略比较。
- `matches.strategy_arm` 仅表示计划策略；`matches.control_source` 单独记录实际
  控制来源（`manual`、`autoplay`、`mixed_auto_play`、`unknown`），避免把托管结果
  误归因给策略。

## 当前进度（2026-09-09）

- 已记录 18 次 6001 匹配/对局观察，18 次可见结算；正式合格局仍为 0/100。
- 其中 `manual` 1 局、`autoplay` 4 局、`mixed_auto_play` 9 局、`uncontrolled_observation` 2 局、控制来源未知 2 局；连续观察均未
  满足逐回合证据门槛，因此不计算策略胜率或正式 RTP。
- 已复现 P0：BET1/BET100 均可能在首个受控动作前出现“Play cards automatically”，
  说明问题不依赖 BET 档位；同时记录页面奖励显示与余额净变化的口径差异。

## 命令

```sh
cd /Users/robin/Documents/wajetan_analyst
python3 -B analysis/whot_test_experience_2026_09_07/v3_2/legacy6001.py \
  --db analysis/whot_test_experience_2026_09_07/v3_2/legacy6001_v3_2.sqlite3 init
python3 -B analysis/whot_test_experience_2026_09_07/v3_2/legacy6001.py \
  --db analysis/whot_test_experience_2026_09_07/v3_2/legacy6001_v3_2.sqlite3 schedule --seed 6001
python3 -B -m unittest discover \
  -s analysis/whot_test_experience_2026_09_07/v3_2 -p 'test_*.py' -v
```

实时浏览器操作由普通 Chrome CUA 提供已经登录的 6001 页面。适配器必须先回读
完整状态，再调用 `choose_decision`，动作确认后调用 `Store.add_turn`；不能把
截图索引、页面余额或客户端按钮显示当作服务端结算事实。

## 状态和安全

`safe_route` 只接受 `https://test-h5.wajetan.com/game/6001-whot`，拒绝查询参数、
其他游戏、PWA/standalone 和外部搜索。所有输入 payload 都经过敏感字段门禁。
数据只写本地 SQLite，不写 BigQuery、Metabase、飞书或第三方通知服务。
