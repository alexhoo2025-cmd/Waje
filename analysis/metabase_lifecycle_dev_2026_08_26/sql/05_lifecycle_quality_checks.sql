-- Waje GM Lifecycle V2 (Joint)
-- 05_lifecycle_quality_checks.sql
-- 用途：Model/View 上线前的只读质量校验模板。

-- 1. 重复快照：同一业务日、游戏、生命周期、pool_type 不应有多条有效快照。
SELECT
    DATE(DATE_SUB(FROM_UNIXTIME(time), INTERVAL 1 DAY)) AS business_date,
    game_type AS game_id,
    lifecycle - 1 AS display_lifecycle,
    pool_type,
    COUNT(*) AS snapshot_rows
FROM whot_center.stat_lifecycle_pool_v2_log
WHERE change_type = 3
  AND data_type = 1
  [[AND {{snapshot_time}}]]
GROUP BY business_date, game_id, display_lifecycle, pool_type
HAVING COUNT(*) > 1;

-- 2. 日期完整性：缺失业务日返回状态，不补成 0。
SELECT
    calendar.business_date,
    CASE WHEN fact.business_date IS NULL THEN 'missing' ELSE 'present' END AS data_status
FROM <approved_business_date_calendar> AS calendar
LEFT JOIN (
    SELECT DISTINCT business_date
    FROM model_lifecycle_v2_joint_daily
) AS fact ON fact.business_date = calendar.business_date
WHERE calendar.business_date BETWEEN {{date_start}} AND {{date_end}}
ORDER BY calendar.business_date;

-- 3. 零分母：RTP、TC、流充比和折损系数不能产生 Infinity/NaN。
SELECT
    business_date,
    display_lifecycle,
    game_id,
    entire_bet,
    base_bet,
    CASE WHEN entire_bet = 0 THEN 'no_denominator' ELSE 'has_denominator' END AS entire_rtp_status,
    CASE WHEN base_bet = 0 THEN 'no_denominator' ELSE 'has_denominator' END AS base_rtp_status,
    data_status
FROM model_lifecycle_v2_joint_daily
WHERE business_date BETWEEN {{date_start}} AND {{date_end}};

-- 4. 版本/包体/渠道覆盖率：只返回聚合覆盖，不返回明细。
SELECT
    business_date,
    COUNT(*) AS rows_total,
    SUM(CASE WHEN app_version IN ('unknown', 'not_available') THEN 1 ELSE 0 END) AS rows_without_app_version,
    SUM(CASE WHEN package_id IN ('unknown', 'not_available') THEN 1 ELSE 0 END) AS rows_without_package,
    SUM(CASE WHEN distribution_channel_id IN ('unknown', 'not_available') THEN 1 ELSE 0 END) AS rows_without_channel,
    SUM(CASE WHEN attribution_media_id IN ('unknown', 'not_available') THEN 1 ELSE 0 END) AS rows_without_media
FROM model_lifecycle_v2_joint_daily
WHERE business_date BETWEEN {{date_start}} AND {{date_end}}
GROUP BY business_date
ORDER BY business_date;

-- 5. 口径门禁：检查是否混入 V1、data_type=2 或非 Joint 数据。
SELECT
    data_scope,
    metric_version,
    data_status,
    COUNT(*) AS row_count
FROM model_lifecycle_v2_joint_daily
WHERE business_date BETWEEN {{date_start}} AND {{date_end}}
GROUP BY data_scope, metric_version, data_status
ORDER BY data_scope, metric_version, data_status;

-- 6. 留存成熟度：D2/D3/D7 未成熟时只能返回 N/A/immature。
SELECT
    cohort_date,
    display_lifecycle,
    population_type,
    retention_day,
    cohort_user_count,
    retention_user_count,
    CASE
        WHEN DATE_ADD(cohort_date, INTERVAL retention_day DAY) > CURRENT_DATE THEN 'immature'
        WHEN cohort_user_count = 0 THEN 'no_denominator'
        ELSE 'mature'
    END AS maturity_status
FROM <authorized_lifecycle_retention_model>
WHERE cohort_date BETWEEN {{date_start}} AND {{date_end}};

-- 7. 跨表勾稽：Q02 按游戏汇总与 Q03 游戏汇总、Q03 与 Q01 必须一致。
-- 实际实现：分别保存 Q02/Q03 的聚合结果后按 game_id 对账；差异进入
-- blocked_reconciliation，不在 Dashboard 中静默隐藏。
