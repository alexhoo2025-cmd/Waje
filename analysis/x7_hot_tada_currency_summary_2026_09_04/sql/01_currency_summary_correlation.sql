-- Calculation contract for the third-party Currency Summary workbook.
-- Input snapshot: Currency_Summary_Report_2026-09-04_06-41-44.xlsx, Summary!A1:H163.
-- This SQL is a reproducible semantic contract; it was not executed against
-- Waje BigQuery or the third-party platform. The shipped values come from the
-- reviewed workbook snapshot and are aggregate-only.
-- RTP/Net Win analysis uses RTP as 0-100 percentage points (e.g. 97.18),
-- and reports both the direct cross-sectional relationship and RTP bands.

WITH games AS (
  SELECT
    api_id,
    game_id,
    game_type,
    total_bet,
    total_win,
    net_win,
    rtp,
    total_count
  FROM currency_summary_snapshot
  WHERE game_id IS NOT NULL
    AND game_id <> 'Total'
),
derived AS (
  SELECT
    *,
    SAFE_DIVIDE(net_win, total_bet) AS net_margin,
    LOG10(total_bet) AS log10_total_bet,
    SAFE_DIVIDE(total_bet, total_count) AS bet_per_count,
    SAFE_DIVIDE(net_win, total_count) AS net_win_per_count
  FROM games
  WHERE total_bet > 0
),
rtp_range AS (
  SELECT
    CASE
      WHEN rtp < 0.90 THEN '<90%'
      WHEN rtp < 0.95 THEN '90%–95%'
      WHEN rtp < 0.96 THEN '95%–96%'
      WHEN rtp < 0.97 THEN '96%–97%'
      WHEN rtp < 0.98 THEN '97%–98%'
      ELSE '≥98%'
    END AS rtp_range,
    COUNT(*) AS games,
    SUM(total_bet) AS total_bet,
    SUM(total_win) AS total_win,
    SUM(net_win) AS net_win,
    SAFE_DIVIDE(SUM(total_win), SUM(total_bet)) AS weighted_rtp,
    SAFE_DIVIDE(SUM(total_bet), SUM(SUM(total_bet)) OVER ()) AS bet_share,
    SAFE_DIVIDE(SUM(net_win), SUM(SUM(net_win)) OVER ()) AS net_share
  FROM derived
  GROUP BY 1
),
relationship AS (
  SELECT
    COUNT(*) AS games,
    CORR(net_win, rtp * 100) AS net_win_rtp_pearson,
    COVAR_POP(net_win, rtp * 100) / NULLIF(VAR_POP(rtp * 100), 0) AS net_win_rtp_slope_per_rtp_pp,
    AVG(net_win) - (COVAR_POP(net_win, rtp * 100) / NULLIF(VAR_POP(rtp * 100), 0)) * AVG(rtp * 100) AS net_win_rtp_intercept
  FROM derived
)
SELECT
  game_id,
  game_type,
  total_bet,
  total_win,
  net_win,
  rtp,
  net_margin,
  total_count,
  bet_per_count,
  net_win_per_count
FROM derived
ORDER BY total_bet DESC;

-- RTP-band view for the report's second chart/table.
SELECT * FROM rtp_range ORDER BY rtp_range;

-- Direct Net Win ↔ RTP relationship. The equation is:
-- Net Win = net_win_rtp_intercept + net_win_rtp_slope_per_rtp_pp × RTP_percentage_points.
SELECT * FROM relationship;
