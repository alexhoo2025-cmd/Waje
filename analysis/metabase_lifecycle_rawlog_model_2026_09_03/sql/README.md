# DBA handoff: Lifecycle V2 Joint performance optimization

The current Metabase connection is configured as read-only. It rejected `CREATE TABLE` with `Running in read-only mode`, even though `SHOW GRANTS` returned a privileged underlying database user. Run these scripts through the approved direct MySQL/DBA channel, not through Metabase.

1. Run `01_create_mart.sql` once after DBA lock/rollback review.
2. Run `02_refresh_mart.sql` for the initial 2026-08-01 through 2026-09-02 load.
3. Schedule the refresh at 04:30 Africa/Lagos after the source snapshot; reprocess only the latest three complete business dates.
4. Run `03_validate_mart.sql`, reconcile a stable seven-day window, and only then repoint the Metabase Model from raw CTE logic to the mart table.

The source table currently has about 4.8 million rows and only separate indexes on `game_type`, `lifecycle`, `pool_type`, `change_type`, and `time`. The proposed composite refresh index is required to avoid repeated broad scans.
