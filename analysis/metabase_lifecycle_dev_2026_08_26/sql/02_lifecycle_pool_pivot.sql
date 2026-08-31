-- Waje GM Lifecycle V2 (Joint)
-- 02_lifecycle_pool_pivot.sql
-- 用途：将 pool_type 行转换为每日游戏/生命周期宽表。
-- 规则：先按每日快照聚合，再由查询卡片做查询期 SUM，避免重复累计快照。

WITH snapshot AS (
    SELECT
        DATE(DATE_SUB(FROM_UNIXTIME(src.time), INTERVAL 1 DAY)) AS business_date,
        'joint' AS data_scope,
        src.game_type AS game_id,
        src.lifecycle - 1 AS display_lifecycle,
        src.pool_type,
        src.data,
        src.data0,
        src.data1,
        src.data2,
        src.data3,
        src.data4,
        FROM_UNIXTIME(src.time) AS snapshot_time
    FROM whot_center.stat_lifecycle_pool_v2_log AS src
    WHERE src.change_type = 3
      AND src.data_type = 1
      [[AND {{business_date}}]]
),
pivoted AS (
    SELECT
        business_date,
        data_scope,
        game_id,
        display_lifecycle,
        MAX(CASE WHEN pool_type = 1 THEN data END) AS real_profit_raw,
        MAX(CASE WHEN pool_type = 2 THEN data END) AS expected_profit_raw,
        MAX(CASE WHEN pool_type = 3 THEN data END) AS adjusted_profit_raw,
        MAX(CASE WHEN pool_type = 4 THEN data END) AS entire_bet_raw,
        MAX(CASE WHEN pool_type = 5 THEN data END) AS bankruptcy_bet_raw,
        MAX(CASE WHEN pool_type = 6 THEN data END) AS bankruptcy_profit_raw,
        MAX(CASE WHEN pool_type = 7 THEN data END) AS control_bet_raw,
        MAX(CASE WHEN pool_type = 8 THEN data END) AS control_profit_raw,
        MAX(CASE WHEN pool_type = 12 THEN data END) AS expected_rtp_raw,
        MAX(CASE WHEN pool_type = 22 THEN data END) AS real_reserved_raw,
        MAX(CASE WHEN pool_type = 23 THEN data END) AS expected_reserved_raw,
        MAX(CASE WHEN pool_type IN (1002, 11002) THEN data END) AS recharge_amount_raw,
        MAX(CASE WHEN pool_type IN (1004, 11004) THEN data END) AS repeat_recharge_amount_raw,
        MAX(CASE WHEN pool_type IN (1006, 11006) THEN data END) AS withdraw_amount_raw,
        MAX(CASE WHEN pool_type IN (1007, 11007) THEN data END) AS controlled_user_count,
        MAX(CASE WHEN pool_type IN (1008, 11008) THEN data END) AS controlled_count,
        MAX(CASE WHEN pool_type IN (1009, 11009) THEN data END) AS absolute_bankrupt_user_count,
        MAX(CASE WHEN pool_type IN (1010, 11010) THEN data END) AS absolute_bankrupt_count,
        MAX(snapshot_time) AS snapshot_time
    FROM snapshot
    GROUP BY business_date, data_scope, game_id, display_lifecycle
)
SELECT
    business_date,
    data_scope,
    CASE WHEN game_id = 0 THEN 'all' ELSE 'game' END AS row_scope,
    game_id,
    display_lifecycle,
    real_profit_raw / 100.0 AS real_profit,
    expected_profit_raw / 100.0 AS expected_profit,
    adjusted_profit_raw / 100.0 AS adjusted_profit,
    entire_bet_raw / 100.0 AS entire_bet,
    bankruptcy_bet_raw / 100.0 AS bankruptcy_bet,
    bankruptcy_profit_raw / 100.0 AS bankruptcy_profit,
    control_bet_raw / 100.0 AS control_bet,
    control_profit_raw / 100.0 AS control_profit,
    expected_rtp_raw / 100.0 AS expected_rtp,
    real_reserved_raw / 100.0 AS real_reserved,
    expected_reserved_raw / 100.0 AS expected_reserved,
    recharge_amount_raw / 100.0 AS recharge_amount,
    repeat_recharge_amount_raw / 100.0 AS repeat_recharge_amount,
    withdraw_amount_raw / 100.0 AS withdraw_amount,
    controlled_user_count,
    controlled_count,
    absolute_bankrupt_user_count,
    absolute_bankrupt_count,
    (real_profit_raw - real_reserved_raw) / 100.0 AS actual_profit,
    (entire_bet_raw - bankruptcy_bet_raw - control_bet_raw) / 100.0 AS base_bet,
    (
        real_profit_raw - real_reserved_raw
        - bankruptcy_profit_raw - control_profit_raw
    ) / 100.0 AS base_actual_profit,
    CASE
        WHEN entire_bet_raw IS NULL OR entire_bet_raw = 0 THEN NULL
        ELSE 1.0 - (real_profit_raw - real_reserved_raw) / entire_bet_raw
    END AS entire_actual_rtp,
    CASE
        WHEN entire_bet_raw IS NULL OR entire_bet_raw = 0 THEN NULL
        ELSE entire_bet_raw * (10000 - expected_rtp_raw) / 10000.0 / 100.0
    END AS entire_expected_profit,
    (real_profit_raw - real_reserved_raw) / 100.0 AS entire_actual_profit,
    (
        entire_bet_raw * (10000 - expected_rtp_raw) / 10000.0
    ) / 100.0 AS entire_expected_profit_recomputed,
    (
        (entire_bet_raw - bankruptcy_bet_raw - control_bet_raw)
        * (10000 - expected_rtp_raw) / 10000.0
    ) / 100.0 AS base_expected_profit,
    snapshot_time,
    'gm_joint_v1' AS metric_version,
    CASE
        WHEN business_date IS NULL THEN 'missing'
        WHEN snapshot_time IS NULL THEN 'delayed'
        ELSE 'complete_candidate'
    END AS data_status
FROM pivoted;

-- 基础 RTP 的明细页和汇总页分母不同，不在本层生成唯一 base_actual_rtp。
