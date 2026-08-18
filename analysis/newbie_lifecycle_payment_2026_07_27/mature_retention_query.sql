WITH mature_retention_query ("lifecycle_day", "retention_rate", "new_users", "cohort_count", "maturity_cutoff") AS (
  VALUES
  ('D1', 0.477035, 5271653, 1985, '2026-07-26'),
  ('D3', 0.317167, 5229060, 1969, '2026-07-24'),
  ('D7', 0.183359, 5138905, 1937, '2026-07-20'),
  ('D15', 0.109973, 4958483, 1873, '2026-07-12'),
  ('D30', 0.072012, 4619920, 1752, '2026-06-27'),
  ('D60', 0.047579, 3901745, 1503, '2026-05-28')
)
SELECT * FROM mature_retention_query;
