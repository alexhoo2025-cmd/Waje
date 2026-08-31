-- Admin-run only. This is a design script; it is not executed in this run.
-- The dataset is colocated with the Waje BigQuery sources.
CREATE SCHEMA IF NOT EXISTS `wajenigeria.waje_device_performance_mart`
OPTIONS (
  location = 'europe-west4',
  description = 'Aggregate-only Waje device, performance, event and quality marts for Metabase.'
);
