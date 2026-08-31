# V5 数据预检结论

## 已验证

- 正式外部 Metabase：`http://35.181.27.61:3001/browse`，已登录，只执行未保存的只读聚合查询。
- 数据库：MySQL 8.0.39；会话时区 `Africa/Lagos`，UTC 偏移 +60 分钟。
- `risk_recharge`：40,676 行，时间范围为 2026-08-13 06:12 至 2026-08-28 08:36。它不能覆盖V5要求的6月16日至8月10日首充批次。
- `order_log`：索引估算约1.106亿行；分析主窗口内成功充值订单约8,773,218笔。可用于资金事实，但直接做历史用户级去重查询耗时较长。
- `game_record`：索引估算约2.706亿行，只有 `user_id + game` 索引，没有时间索引。与近期首充用户联结后只返回 `cashspin`，不能作为全部轻量化游戏事实源。
- `stat_game_bet_gain`：约2,087万行，具备 `gid + game_id` 索引；近期首充用户测试中可见 9008、9003、9010、9011、9016 等游戏ID。
- `stat_game_bet_gain`测试结果中每个游戏的记录数等于用户数，说明其更接近“用户×游戏累计快照”；`update_at`是最后更新时间，不能直接当作首次开局时间。

## 当前不能发布的结论

1. 不能用 `risk_recharge` 做6月16日—8月10日的上线前后首充路径比较。
2. 不能用 `stat_game_bet_gain.update_at`区分“付费前已玩”和“付费后首次玩”，因为缺少首次开局时间。
3. 不能从 `game_record`直接计算轻量化游戏首局、局数和下注，因为当前测试只覆盖CashSpin。
4. `robin@afuruika.net`已获得`wajenigeria`访问，并通过BigQuery API/CLI完成聚合查询；BigQuery MCP仍使用独立OAuth并返回`Auth required`。

## BigQuery新增发现

- `origin_hfyl`具备ORDER、GAMESTART、GAMEEND、BETREWARD、LOGIN和PV事件视图；`app_id=90006`为Waje Special。
- ORDER与GAMESTART完整覆盖主窗口，时间字段为13位毫秒时间戳。
- ORDER/GAMESTART服务器事件中的`client_type=0`且`package_channel`为空；无法直接拆H5自然、PWA、Facebook和Google。
- PV事件确认`client_type=3`为H5；画像表`device_type=Others`可作为H5/PWA合并代理。
- `pubwaje.user_profiles`覆盖至2026-06-30，静态画像覆盖2026-07-10至8月10；据此采用6月16—30日和7月14—28日两个等长15天路径窗口。
- 轻量化上线后，首充后7天内GAMESTART率由15.2%升至16.6%，但7天无GAMESTART仍为71.9%。
- 起源GAMESTART只返回统一`play_id`，没有实际轻量化`game_id`；单游戏归因仍为阻断。

## 继续执行的最短路径

- 使用拥有 `wajenigeria` 权限的 `robin@afuruika.net` 完成Google Cloud/BigQuery授权；
- 在BigQuery中定位首充事实、GAMESTART、结算、下注和渠道维度，全部在SQL内部关联后只返回聚合结果；
- 若企业BigQuery尚未同步这些服务端事实，则由数据开发提供受控首充路径聚合视图，至少包含首充时间、首次轻量化开局时间、首充后逐日局数/下注、复充标记和渠道维度；
- 在门禁通过前，V5状态保持 `blocked_required_source`，不发布虚假业务结论。
