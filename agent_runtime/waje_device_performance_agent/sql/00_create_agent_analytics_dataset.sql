-- Run once by a data-platform identity, not by the Agent Runtime identity.
-- The Agent Runtime receives only BigQuery Data Viewer on this dataset.
CREATE SCHEMA IF NOT EXISTS `wajenigeria.agent_analytics`
OPTIONS(
  location = 'europe-west4',
  description = 'Waje approved aggregate-only views for the device and performance Agent Runtime. No user, session, device identifier, URL, payload, order, payment or stack detail.'
);
