-- Waje GM Lifecycle V2 (Joint)
-- 01_lifecycle_snapshot_base.sql
-- 用途：读取每日历史快照，转换业务日期和展示生命周期。
-- 本文件是开发模板，不在生产库执行写操作。
-- 上线前必须确认 whot_center 数据库/会话时区。

SELECT
    DATE(DATE_SUB(FROM_UNIXTIME(src.time), INTERVAL 1 DAY)) AS business_date,
    'joint' AS data_scope,
    CASE
        WHEN src.pool_type IN (
            10001, 10002, 10004, 10005, 10006, 10007, 10008,
            1031, 1032, 1033,
            11001, 11002, 11003, 11004, 11005, 11006,
            11007, 11008, 11009, 11010, 11011
        ) THEN 'new'
        WHEN src.pool_type IN (1021, 1022, 1025) THEN 'all'
        WHEN src.pool_type = 12 THEN 'shared'
        ELSE 'all'
    END AS population_type,
    src.game_type AS game_id,
    src.lifecycle - 1 AS display_lifecycle,
    src.lifecycle AS source_lifecycle,
    src.data_type,
    src.pool_type,
    src.change_type,
    src.data,
    src.data0,
    src.data1,
    src.data2,
    src.data3,
    src.data4,
    FROM_UNIXTIME(src.time) AS snapshot_time,
    src.remark,
    CASE
        WHEN src.change_type = 3 AND src.data_type = 1 THEN 'complete_candidate'
        ELSE 'excluded'
    END AS source_status
FROM whot_center.stat_lifecycle_pool_v2_log AS src
WHERE src.change_type = 3
  AND src.data_type = 1
  -- Metabase Field Filter：实际配置时映射到 Model 的 business_date。
  [[AND {{business_date}}]]
  [[AND {{game_id}}]]
  [[AND {{display_lifecycle}}]];

-- 固定门禁：
-- 1. 业务日期 D 对应次日落库快照 D+1；
-- 2. data_type=1 是历史主口径，不能与 data_type=2 混用；
-- 3. game_id=0 是全局/生命周期经营指标，不作为具体游戏展示。
