WITH lifecycle_pool_query ("lifecycle", "records", "user_days", "recharge_amount", "repurchase_amount", "full_bet_amount", "revenue_amount", "repurchase_amount_share_of_recharge", "nonzero_repurchase_rows", "user_day_share", "coverage") AS (
  VALUES
  (1, 203, 1200640.0, 572751591.0, 0, 4303564256.77, 27923951.27, 0.0, 0, 0.129731, '2025-03-17 至 2026-07-27（非连续）'),
  (2, 203, 1195625.0, 1010053384.0, 0, 8141820050.93, 208612284.11, 0.0, 0, 0.129189, '2025-03-17 至 2026-07-27（非连续）'),
  (3, 203, 3378483.0, 7359670654.0, 0, 60402501395.78, 1577410187.24, 0.0, 0, 0.365049, '2025-03-17 至 2026-07-27（非连续）'),
  (4, 203, 3480118.0, 30931029255.0, 0, 219722814717.97, 7296247294.38, 0.0, 0, 0.376031, '2025-03-17 至 2026-07-27（非连续）')
)
SELECT * FROM lifecycle_pool_query;
