-- Run once by a project identity with bigquery.datasets.create in wajenigeria.
-- Target location must remain europe-west4 because all V1 Firebase sources are there.
CREATE SCHEMA IF NOT EXISTS `wajenigeria.waje_device_performance_mart`
OPTIONS(
  location = 'europe-west4',
  description = 'Waje cross-platform device, performance, event, session, stability and funnel aggregate mart. Aggregate-only; no raw identifiers, URL, request body, response body, order or payment detail.'
);
