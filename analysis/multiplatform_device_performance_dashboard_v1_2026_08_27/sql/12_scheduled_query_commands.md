# BigQuery 定时刷新命令

前提：目标数据集已创建；执行身份具备 BigQuery Data Transfer / Scheduled Query 创建权限，并能读取所有 Firebase 源表、写入 `waje_device_performance_mart`。

BigQuery `--schedule` 使用 UTC。下列日任务对应 Lagos 时间 06:30 起的预刷新；12:30 Lagos 的最终刷新重复同一序列。生产环境应由同一个受控编排任务按顺序执行，不能依赖多个独立计划任务恰好按时完成。

| 顺序 | UTC 计划 | Lagos 时间 | SQL |
|---|---:|---:|---|
| 1 | 05:30 | 06:30 | `02_refresh_event_session_daily.sql` |
| 2 | 05:45 | 06:45 | `03_refresh_native_performance_daily.sql` |
| 3 | 06:00 | 07:00 | `05_refresh_stability_daily.sql` |
| 4 | 06:10 | 07:10 | `06_refresh_core_funnel_daily.sql` |
| 5 | 06:20 | 07:20 | `07_refresh_endpoint_coverage_daily.sql` |
| 6 | 06:35 | 07:35 | `09_refresh_native_performance_rank_daily.sql` |
| 7 | every 15 minutes | every 15 minutes | `04_refresh_native_performance_15m.sql` |

示例（仅在管理员确认 Transfer 权限和运行身份后执行）：

```bash
bq --project_id=wajenigeria --location=europe-west4 query \
  --use_legacy_sql=false \
  --schedule='every day 05:30' \
  --display_name='Waje Device Performance - Event Session D+1' \
  < sql/02_refresh_event_session_daily.sql
```

最终刷新使用同一 SQL，在 UTC 11:30 至 12:35 按上述顺序再运行一次。若任一来源的数据截止时间落后预期，`mart_endpoint_coverage_daily` 必须显示 `delayed`；不得将缺失日期插入为零。
