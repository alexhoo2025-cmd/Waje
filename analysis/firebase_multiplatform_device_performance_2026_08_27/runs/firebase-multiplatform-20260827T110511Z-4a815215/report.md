---
type: technical-analysis-report
status: quality_warning
updated: 2026-08-27
---

# Waje Firebase 多端设备与性能汇总分析报告

## 执行摘要

**当前状态：`quality_warning`。** At least one Firebase source/query is missing, delayed or blocked

- 数据范围：Firebase-only；Android/iOS 2026-08-20～2026-08-26，H5 2026-08-14～2026-08-21，时区 `Africa/Lagos`。
- 执行路径：`api_fallback`；Gemini 状态：`blocked_external_prerequisites`；本机 API 状态：`ok`。
- Android、iOS、H5 独立统计；事件数不解释为用户数，Sessions 不与 `session_start` 相加。
- H5 当前只形成行为基线；Web Vitals、白屏、核心请求、前端错误和游戏阶段均标记为 `data_gap` / `blocked`。

## 端侧现状

| 端侧 | 当前实际汇总 | 主要可用指标 | 状态 |
|---|---:|---|---|
| Android | 0 Analytics 事件；15.47M Performance 记录；535.2k 去标识化会话 | 会话开始事件、轨迹/网络 P95、HTTP 成功率、慢帧/冻结帧、Fatal/Non-fatal 事件量 | `provisional` |
| iOS | 237.5k Analytics 事件；2.45M Performance 记录 | 会话开始事件、轨迹/网络 P95、屏幕流畅度 | `immature` / `provisional` |
| H5 | 9.05M 行为事件 | page_view、session_start、first_visit、user_engagement | `provisional_behavior_only` |

## 数据覆盖与质量

| 检查项 | 状态 | 说明 |
|---|---|---|
| gemini_mcp_preflight | `blocked` | blocked_external_prerequisites |
| api_identity_preflight | `passed` | ready |
| query:source_inventory | `ok` |  |
| query:android_analytics_daily | `failed` | Network connection problem encountered, please try again.

If this problem persists, you may have encountered a bug in the bigquery client.
Please file a bug report in our public issue tracker:
https://issuetracker.google.com/issues/new?component=187149&template=0
Please include a brief description of the steps that led to this issue, as well
as any rows that can be made public from the following information:

========================================
== Platform ==
  CPython:3.12.14:macOS-26.5.1-arm64-arm-64bit
== bq version ==
  2.1.36
== Command line ==
  ['/Users/robin/google-cloud-sdk/platform/bq/bq.py', '--project_id=wajenigeria', '--project_id=wajenigeria', '--location=europe-west4', 'query', '--use_legacy_sql=false', '--format=json', '--max_rows=3000']
== UTC timestamp ==
  2026-08-27 11:06:39
== Error trace ==
Traceback (most recent call last):
  File "/Users/robin/.local/share/uv/python/cpython-3.12.14-macos-aarch64-none/lib/python3.12/http/client.py", line 603, in _get_chunk_left
    chunk_left = self._read_next_chunk_size()
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/robin/.local/share/uv/python/cpython-3.12.14-macos-aarch64-none/lib/python3.12/http/client.py", line 561, in _read_next_chunk_size
    return int(line, 16)
           ^^^^^^^^^^^^^
ValueError: invalid literal for int() with base 16: b''

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/Users/robin/.local/share/uv/python/cpython-3.12.14-macos-aarch64-none/lib/python3.12/http/client.py", line 621, in _read_chunked
    while (chunk_left := self._get_chunk_left()) is not None:
                         ^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/robin/.local/share/uv/python/cpython-3.12.14-macos-aarch64-none/lib/python3.12/http/client.py", line 605, in _get_chunk_left
    raise IncompleteRead(b'')
http.client.IncompleteRead: IncompleteRead(0 bytes read)

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/Users/robin/google-cloud-sdk/platform/bq/frontend/bigquery_command.py", line 297, in RunSafely
    return_value = self.RunWithArgs(*args, **kwds)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/robin/google-cloud-sdk/platform/bq/frontend/command_query.py", line 692, in RunWithArgs
    job = client_job.Query(client, query, **kwds)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/robin/google-cloud-sdk/platform/bq/clients/client_job.py", line 1303, in Query
    return ExecuteJob(bqclient, request, **kwds)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/robin/google-cloud-sdk/platform/bq/clients/client_job.py", line 698, in ExecuteJob
    job = RunJobSynchronously(
          ^^^^^^^^^^^^^^^^^^^^
  File "/Users/robin/google-cloud-sdk/platform/bq/clients/client_job.py", line 668, in RunJobSynchronously
    result = StartJob(
             ^^^^^^^^^
  File "/Users/robin/google-cloud-sdk/platform/bq/clients/client_job.py", line 433, in StartJob
    result = request.execute()
             ^^^^^^^^^^^^^^^^^
  File "/Users/robin/google-cloud-sdk/platform/bq/clients/bigquery_http.py", line 292, in execute
    return super().execute(
           ^^^^^^^^^^^^^^^^
  File "/Users/robin/google-cloud-sdk/platform/bq/third_party/googleapiclient/_helpers.py", line 135, in positional_wrapper
    return wrapped(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/robin/google-cloud-sdk/platform/bq/third_party/googleapiclient/http.py", line 921, in execute
    resp, content = _retry_request(
                    ^^^^^^^^^^^^^^^
  File "/Users/robin/google-cloud-sdk/platform/bq/clients/bigquery_http.py", line 76, in _RetryRequest
    resp, content = _ORIGINAL_GOOGLEAPI_CLIENT_RETRY_REQUEST(
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/robin/google-cloud-sdk/platform/bq/third_party/googleapiclient/http.py", line 192, in _retry_request
    resp, content = http.request(uri, method, *args, **kwargs)
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/robin/google-cloud-sdk/platform/bq/third_party/google_auth_httplib2/__init__.py", line 217, in request
    response, content = self.http.request(
                        ^^^^^^^^^^^^^^^^^^
  File "/Users/robin/google-cloud-sdk/platform/bq/third_party/httplib2/python3/__init__.py", line 1708, in request
    (response, content) = self._request(
                          ^^^^^^^^^^^^^^
  File "/Users/robin/google-cloud-sdk/platform/bq/third_party/httplib2/python3/__init__.py", line 1424, in _request
    (response, content) = self._conn_request(conn, request_uri, method, body, headers)
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/robin/google-cloud-sdk/platform/bq/third_party/httplib2/python3/__init__.py", line 1405, in _conn_request
    content = response.read()
              ^^^^^^^^^^^^^^^
  File "/Users/robin/.local/share/uv/python/cpython-3.12.14-macos-aarch64-none/lib/python3.12/http/client.py", line 488, in read
    return self._read_chunked(amt)
           ^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/robin/.local/share/uv/python/cpython-3.12.14-macos-aarch64-none/lib/python3.12/http/client.py", line 633, in _read_chunked
    raise IncompleteRead(b''.join(value)) from exc
http.client.IncompleteRead: IncompleteRead(1176 bytes read)

========================================

Unexpected exception in query operation: Network connection problem encountered,
please try again.

If this problem persists, you may have encountered a bug in the bigquery client.
Please file a bug report in our public issue tracker:
https://issuetracker.google.com/issues/new?component=187149&template=0
Please include a brief description of the steps that led to this issue, as well
as any rows that can be made public from the following information:

 |
| query:ios_analytics_daily | `ok` |  |
| query:h5_analytics_daily | `ok` |  |
| query:android_sessions_daily | `ok` |  |
| query:native_performance_daily | `ok` |  |
| query:native_performance_dimensions | `ok` |  |
| query:crashlytics_stability_daily | `ok` |  |
| query:quality_freshness | `data_gap` | Error in query string: Name last_modified_time not found inside t at [8:5]

 |
| raw_row_output | `passed` | all query outputs are aggregate JSON rows; raw CLI output is not persisted |
| h5_web_performance | `data_gap` | current H5 Firebase Analytics query has no Web Vitals, route-ready, request timing or frontend error contract |
| cross_endpoint_trend_gate | `immature` | publish endpoint trends only after seven complete days per endpoint |

## Analytics 事件与会话汇总

| 日期 | 端侧 | 包体/来源 | 版本 | 事件分类 | 事件名桶 | 事件数 |
|---|---|---|---|---|---|---:|
| 2026-08-20 | ios | com.wajegame.wajegame | 2.17.0 | lifecycle | user_engagement | 83 |
| 2026-08-20 | ios | com.wajegame.wajegame | 2.17.0 | page_or_screen | screen_view | 22 |
| 2026-08-20 | ios | com.wajegame.wajegame | 2.17.0 | lifecycle | session_start | 21 |
| 2026-08-20 | ios | com.wajegame.wajegame | 2.17.0 | notification | notification_open | 4 |
| 2026-08-20 | ios | com.wajegame.wajegame | 2.17.0 | lifecycle | first_open | 3 |
| 2026-08-21 | ios | com.wajegame.wajegame | 2.17.0 | lifecycle | user_engagement | 75 |
| 2026-08-21 | ios | com.wajegame.wajegame | 2.17.0 | page_or_screen | screen_view | 35 |
| 2026-08-21 | ios | com.wajegame.wajegame | 2.17.0 | lifecycle | session_start | 29 |
| 2026-08-21 | ios | com.wajegame.wajegame | 2.17.0 | lifecycle | first_open | 3 |
| 2026-08-21 | ios | com.wajegame.wajegame | 2.17.0 | notification | notification_open | 3 |
| 2026-08-21 | ios | com.wajegame.wajegame | 2.17.0 | notification | notification_foreground | 1 |
| 2026-08-21 | ios | com.wajegame.wajegame | 2.17.0 | other | os_update | 1 |
| 2026-08-22 | ios | com.wajegame.wajegame | 2.17.0 | lifecycle | user_engagement | 269 |
| 2026-08-22 | ios | com.wajegame.wajegame | 2.17.0 | page_or_screen | screen_view | 109 |
| 2026-08-22 | ios | com.wajegame.wajegame | 2.17.0 | lifecycle | session_start | 83 |
| 2026-08-22 | ios | com.wajegame.wajegame | 2.17.0 | notification | notification_open | 10 |
| 2026-08-22 | ios | com.wajegame.wajegame | 2.17.0 | lifecycle | first_open | 5 |
| 2026-08-22 | ios | com.wajegame.wajegame | 2.17.0 | other | app_exception | 1 |
| 2026-08-23 | ios | com.wajegame.wajegame | 2.17.0 | lifecycle | user_engagement | 1.2k |
| 2026-08-23 | ios | com.wajegame.wajegame | 2.17.0 | page_or_screen | screen_view | 466 |
| 2026-08-23 | ios | com.wajegame.wajegame | 2.17.0 | lifecycle | session_start | 249 |
| 2026-08-23 | ios | com.wajegame.wajegame | 2.17.0 | notification | notification_open | 35 |
| 2026-08-23 | ios | com.wajegame.wajegame | 2.17.0 | lifecycle | first_open | 17 |
| 2026-08-23 | ios | com.wajegame.wajegame | 2.17.0 | notification | notification_foreground | 4 |
| 2026-08-23 | ios | com.wajegame.wajegame | 2.17.0 | other | app_exception | 3 |
| 2026-08-23 | ios | com.wajegame.wajegame | 2.17.0 | other | firebase_campaign | 1 |
| 2026-08-24 | ios | com.wajegame.wajegame | 2.17.0 | lifecycle | user_engagement | 113.1k |
| 2026-08-24 | ios | com.wajegame.wajegame | 2.17.0 | page_or_screen | screen_view | 24.8k |
| 2026-08-24 | ios | com.wajegame.wajegame | 2.17.0 | other | rechargeAndWithdrawTotalTimes | 15.9k |
| 2026-08-24 | ios | com.wajegame.wajegame | 2.17.0 | other | rechargeFix | 11.1k |
| 2026-08-24 | ios | com.wajegame.wajegame | 2.17.0 | behavior_signal | recharge | 11.1k |
| 2026-08-24 | ios | com.wajegame.wajegame | 2.17.0 | other | rechargeDollar | 11.1k |
| 2026-08-24 | ios | com.wajegame.wajegame | 2.17.0 | lifecycle | session_start | 10.3k |
| 2026-08-24 | ios | com.wajegame.wajegame | unknown | other | rechargeAndWithdrawTotalTimes | 7.1k |
| 2026-08-24 | ios | com.wajegame.wajegame | unknown | other | rechargeDollar | 4.8k |
| 2026-08-24 | ios | com.wajegame.wajegame | unknown | behavior_signal | recharge | 4.8k |
| 2026-08-24 | ios | com.wajegame.wajegame | unknown | other | rechargeFix | 4.8k |
| 2026-08-24 | ios | com.wajegame.wajegame | 2.17.0 | behavior_signal | withdraw | 4.8k |
| 2026-08-24 | ios | com.wajegame.wajegame | unknown | behavior_signal | withdraw | 2.3k |
| 2026-08-24 | ios | com.wajegame.wajegame | 2.17.0 | lifecycle | first_open | 1.4k |
| 2026-08-24 | ios | com.wajegame.wajegame | 2.17.0 | other | recharge24HourDollar | 761 |
| 2026-08-24 | ios | com.wajegame.wajegame | 2.17.0 | other | recharge24Hour | 761 |
| 2026-08-24 | ios | com.wajegame.wajegame | 2.17.0 | notification | notification_foreground | 699 |
| 2026-08-24 | ios | com.wajegame.wajegame | 2.17.0 | behavior_signal | register | 542 |
| 2026-08-24 | ios | com.wajegame.wajegame | 2.17.0 | notification | notification_open | 539 |
| 2026-08-24 | ios | com.wajegame.wajegame | 2.17.0 | behavior_signal | firstCharge | 504 |
| 2026-08-24 | ios | com.wajegame.wajegame | 2.17.0 | other | recharge1Day | 475 |
| 2026-08-24 | ios | com.wajegame.wajegame | 2.17.0 | other | app_exception | 462 |
| 2026-08-24 | ios | com.wajegame.wajegame | 2.17.0 | other | withdraw1Day | 278 |
| 2026-08-24 | ios | com.wajegame.wajegame | 2.17.0 | other | register24Charge40 | 272 |
| 2026-08-24 | ios | com.wajegame.wajegame | 2.17.0 | other | firstCharge500 | 241 |
| 2026-08-24 | ios | com.wajegame.wajegame | 2.17.0 | other | firstCharge100 | 241 |
| 2026-08-24 | ios | com.wajegame.wajegame | 2.17.0 | other | firstCharge300 | 239 |
| 2026-08-24 | ios | com.wajegame.wajegame | 2.17.0 | other | firstCharge1000 | 225 |
| 2026-08-24 | ios | com.wajegame.wajegame | 2.17.0 | other | loginSecondaryRetention | 198 |
| 2026-08-24 | ios | com.wajegame.wajegame | 2.17.0 | other | firstWithdraw | 188 |
| 2026-08-24 | ios | com.wajegame.wajegame | 2.17.0 | other | firstRecharge1Day | 169 |
| 2026-08-24 | ios | com.wajegame.wajegame | unknown | behavior_signal | firstCharge | 54 |
| 2026-08-24 | ios | com.wajegame.wajegame | unknown | behavior_signal | register | 45 |
| 2026-08-24 | ios | com.wajegame.wajegame | 2.17.0 | other | firebase_campaign | 32 |
| 2026-08-24 | ios | com.wajegame.wajegame | unknown | other | recharge24Hour | 28 |
| 2026-08-24 | ios | com.wajegame.wajegame | unknown | other | recharge24HourDollar | 28 |
| 2026-08-24 | ios | com.wajegame.wajegame | unknown | other | firstCharge300 | 28 |
| 2026-08-24 | ios | com.wajegame.wajegame | unknown | other | firstCharge500 | 26 |
| 2026-08-24 | ios | com.wajegame.wajegame | unknown | other | firstCharge100 | 26 |
| 2026-08-24 | ios | com.wajegame.wajegame | unknown | other | recharge1Day | 25 |
| 2026-08-24 | ios | com.wajegame.wajegame | 2.17.0 | other | firstCharge1 | 24 |
| 2026-08-24 | ios | com.wajegame.wajegame | unknown | other | firstCharge1000 | 24 |
| 2026-08-24 | ios | com.wajegame.wajegame | 2.17.0 | other | os_update | 21 |
| 2026-08-24 | ios | com.wajegame.wajegame | unknown | other | firstWithdraw | 19 |
| 2026-08-24 | ios | com.wajegame.wajegame | unknown | other | register24Charge40 | 19 |
| 2026-08-24 | ios | com.wajegame.wajegame | unknown | other | firstRecharge1Day | 17 |
| 2026-08-24 | ios | com.wajegame.wajegame | unknown | other | withdraw1Day | 11 |
| 2026-08-24 | ios | com.wajegame.wajegame | 2.19.0 | lifecycle | user_engagement | 8 |
| 2026-08-24 | ios | com.wajegame.wajegame | 2.19.0 | page_or_screen | screen_view | 5 |
| 2026-08-24 | ios | com.wajegame.wajegame | unknown | other | loginSecondaryRetention | 4 |
| 2026-08-24 | ios | com.wajegame.wajegame | unknown | other | firstCharge1 | 3 |
| 2026-08-24 | ios | com.wajegame.wajegame | 2.19.0 | lifecycle | first_open | 2 |
| 2026-08-24 | ios | com.wajegame.wajegame | 2.19.0 | lifecycle | session_start | 2 |
| 2026-08-14 | h5 | waje_ng_firebase_h5 | unknown | page_or_screen | page_view | 161.1k |

## 原生 Performance 汇总

| 日期 | 端侧 | 包体 | 版本 | 性能记录 | 轨迹 P95(ms) | 网络 P95(ms) | 网络成功率 | 样本状态 |
|---|---|---|---|---:|---:|---:|---:|---|
| 2026-08-20 | Android | com.hfhy.waje.special | 2.10.36 | 2 | N/A | N/A | N/A | sample_too_small |
| 2026-08-20 | Android | com.hfhy.waje.special | 2.10.45 | 9 | N/A | N/A | N/A | sample_too_small |
| 2026-08-20 | Android | com.hfhy.waje.special | 2.11.2 | 9 | N/A | N/A | N/A | sample_too_small |
| 2026-08-20 | Android | com.hfhy.waje.special | 2.12.0 | 3 | N/A | N/A | N/A | sample_too_small |
| 2026-08-20 | Android | com.hfhy.waje.special | 2.13.0 | 8 | N/A | N/A | N/A | sample_too_small |
| 2026-08-20 | Android | com.hfhy.waje.special | 2.14.0 | 183 | N/A | N/A | 1.0 | sample_too_small |
| 2026-08-20 | Android | com.hfhy.waje.special | 2.15.0 | 184 | N/A | N/A | 1.0 | sample_too_small |
| 2026-08-20 | Android | com.hfhy.waje.special | 2.16.0 | 412 | N/A | N/A | 1.0 | sample_too_small |
| 2026-08-20 | Android | com.hfhy.waje.special | 2.17.0 | 901 | N/A | N/A | 1.0 | sample_too_small |
| 2026-08-20 | Android | com.hfhy.wajecasino.game | 2.14.0 | 2.1k | 216863.099 | 1388.922 | 0.9991673605328892 | eligible |
| 2026-08-20 | Android | com.hfhy.wajecasino.palmgame | 2.10.42 | 1.8k | 305439.405 | 3106.996 | 0.9987468671679198 | eligible |
| 2026-08-20 | Android | com.hfhy.wajecasino.palmgame | 2.15.0 | 424 | N/A | N/A | 1.0 | sample_too_small |
| 2026-08-20 | Android | com.hfhy.wajecasino.palmgame | 2.17.0 | 1.5k | 320797.162 | 5220.924 | 1.0 | eligible |
| 2026-08-20 | iOS | com.wajegame.wajegame | 2.17.0 | 2.0k | N/A | 1368.303 | 0.9394606494221244 | sample_too_small |
| 2026-08-21 | Android | com.hfhy.waje.special | 2.0.0 | 19 | N/A | N/A | 1.0 | sample_too_small |
| 2026-08-21 | Android | com.hfhy.waje.special | 2.10.29 | 2 | N/A | N/A | N/A | sample_too_small |
| 2026-08-21 | Android | com.hfhy.waje.special | 2.10.31 | 2 | N/A | N/A | N/A | sample_too_small |
| 2026-08-21 | Android | com.hfhy.waje.special | 2.10.32 | 6 | N/A | N/A | N/A | sample_too_small |
| 2026-08-21 | Android | com.hfhy.waje.special | 2.10.36 | 17 | N/A | N/A | N/A | sample_too_small |
| 2026-08-21 | Android | com.hfhy.waje.special | 2.10.45 | 51 | N/A | N/A | 1.0 | sample_too_small |
| 2026-08-21 | Android | com.hfhy.waje.special | 2.11.0 | 2 | N/A | N/A | N/A | sample_too_small |
| 2026-08-21 | Android | com.hfhy.waje.special | 2.11.1 | 18 | N/A | N/A | N/A | sample_too_small |
| 2026-08-21 | Android | com.hfhy.waje.special | 2.11.2 | 124 | N/A | N/A | N/A | sample_too_small |
| 2026-08-21 | Android | com.hfhy.waje.special | 2.12.0 | 12 | N/A | N/A | N/A | sample_too_small |
| 2026-08-21 | Android | com.hfhy.waje.special | 2.13.0 | 62 | N/A | N/A | N/A | sample_too_small |
| 2026-08-21 | Android | com.hfhy.waje.special | 2.14.0 | 165 | N/A | N/A | 1.0 | sample_too_small |
| 2026-08-21 | Android | com.hfhy.waje.special | 2.15.0 | 906 | N/A | N/A | 1.0 | sample_too_small |
| 2026-08-21 | Android | com.hfhy.waje.special | 2.16.0 | 1.9k | 610978.918 | 1658.557 | 1.0 | eligible |
| 2026-08-21 | Android | com.hfhy.waje.special | 2.17.0 | 5.2k | 574128.237 | 1889.313 | 1.0 | eligible |
| 2026-08-21 | Android | com.hfhy.waje.special | 2.19.0 | 4 | N/A | N/A | N/A | sample_too_small |
| 2026-08-21 | Android | com.hfhy.wajecasino.game | 2.14.0 | 8.6k | 224542.968 | 4417.905 | 0.9981362600952578 | eligible |
| 2026-08-21 | Android | com.hfhy.wajecasino.palmgame | 2.10.41 | 13 | N/A | N/A | 1.0 | sample_too_small |
| 2026-08-21 | Android | com.hfhy.wajecasino.palmgame | 2.10.42 | 8.7k | 299945.096 | 2762.591 | 0.99977079990832 | eligible |
| 2026-08-21 | Android | com.hfhy.wajecasino.palmgame | 2.15.0 | 1.7k | 164093.371 | N/A | 1.0 | sample_too_small |
| 2026-08-21 | Android | com.hfhy.wajecasino.palmgame | 2.17.0 | 6.0k | 156069.459 | 3350.394 | 0.998587570621469 | eligible |
| 2026-08-21 | iOS | com.wajegame.wajegame | 2.17.0 | 7.1k | 429072.991 | 2701.092 | 0.8906095551894564 | eligible |
| 2026-08-22 | Android | com.hfhy.waje.special | 2.0.0 | 8 | N/A | N/A | N/A | sample_too_small |
| 2026-08-22 | Android | com.hfhy.waje.special | 2.10.29 | 2 | N/A | N/A | N/A | sample_too_small |
| 2026-08-22 | Android | com.hfhy.waje.special | 2.10.33 | 3 | N/A | N/A | N/A | sample_too_small |
| 2026-08-22 | Android | com.hfhy.waje.special | 2.10.34 | 3 | N/A | N/A | N/A | sample_too_small |
| 2026-08-22 | Android | com.hfhy.waje.special | 2.10.35 | 11 | N/A | N/A | N/A | sample_too_small |
| 2026-08-22 | Android | com.hfhy.waje.special | 2.10.36 | 38 | N/A | N/A | 1.0 | sample_too_small |
| 2026-08-22 | Android | com.hfhy.waje.special | 2.10.45 | 98 | N/A | N/A | 1.0 | sample_too_small |
| 2026-08-22 | Android | com.hfhy.waje.special | 2.11.0 | 44 | N/A | N/A | N/A | sample_too_small |
| 2026-08-22 | Android | com.hfhy.waje.special | 2.11.1 | 53 | N/A | N/A | N/A | sample_too_small |
| 2026-08-22 | Android | com.hfhy.waje.special | 2.11.2 | 408 | N/A | N/A | 1.0 | sample_too_small |
| 2026-08-22 | Android | com.hfhy.waje.special | 2.11.4 | 22 | N/A | N/A | N/A | sample_too_small |
| 2026-08-22 | Android | com.hfhy.waje.special | 2.12.0 | 19 | N/A | N/A | N/A | sample_too_small |
| 2026-08-22 | Android | com.hfhy.waje.special | 2.13.0 | 85 | N/A | N/A | N/A | sample_too_small |
| 2026-08-22 | Android | com.hfhy.waje.special | 2.14.0 | 682 | N/A | N/A | 1.0 | sample_too_small |
| 2026-08-22 | Android | com.hfhy.waje.special | 2.15.0 | 3.8k | 687934.109 | 1566.139 | 1.0 | eligible |
| 2026-08-22 | Android | com.hfhy.waje.special | 2.16.0 | 6.8k | 888403.512 | 1923.323 | 1.0 | eligible |
| 2026-08-22 | Android | com.hfhy.waje.special | 2.17.0 | 22.4k | 874700.723 | 1906.463 | 0.999826056705514 | eligible |
| 2026-08-22 | Android | com.hfhy.wajecasino.game | 2.14.0 | 27.1k | 250357.471 | 4230.914 | 0.9969965870307167 | eligible |
| 2026-08-22 | Android | com.hfhy.wajecasino.palmgame | 2.10.41 | 7 | N/A | N/A | N/A | sample_too_small |
| 2026-08-22 | Android | com.hfhy.wajecasino.palmgame | 2.10.42 | 20.7k | 406621.046 | 4118.62 | 0.9976019184652278 | eligible |
| 2026-08-22 | Android | com.hfhy.wajecasino.palmgame | 2.15.0 | 5.7k | 182643.287 | 5710.125 | 1.0 | eligible |
| 2026-08-22 | Android | com.hfhy.wajecasino.palmgame | 2.17.0 | 20.7k | 215659.322 | 5093.969 | 0.9981687776590874 | eligible |
| 2026-08-22 | iOS | com.wajegame.wajegame | 2.17.0 | 39.1k | 676253.666 | 1905.911 | 0.9086764705882353 | eligible |
| 2026-08-23 | Android | com.hfhy.waje.special | 2.0.0 | 1.6k | N/A | 1303.269 | 0.9977753058954394 | sample_too_small |
| 2026-08-23 | Android | com.hfhy.waje.special | 2.10.28 | 3 | N/A | N/A | N/A | sample_too_small |
| 2026-08-23 | Android | com.hfhy.waje.special | 2.10.31 | 1 | N/A | N/A | N/A | sample_too_small |
| 2026-08-23 | Android | com.hfhy.waje.special | 2.10.32 | 39 | N/A | N/A | N/A | sample_too_small |
| 2026-08-23 | Android | com.hfhy.waje.special | 2.10.33 | 9 | N/A | N/A | N/A | sample_too_small |
| 2026-08-23 | Android | com.hfhy.waje.special | 2.10.34 | 70 | N/A | N/A | 1.0 | sample_too_small |
| 2026-08-23 | Android | com.hfhy.waje.special | 2.10.35 | 299 | N/A | N/A | 1.0 | sample_too_small |
| 2026-08-23 | Android | com.hfhy.waje.special | 2.10.36 | 1.1k | N/A | N/A | 1.0 | sample_too_small |
| 2026-08-23 | Android | com.hfhy.waje.special | 2.10.45 | 1.6k | 648357.859 | 1880.575 | 1.0 | eligible |
| 2026-08-23 | Android | com.hfhy.waje.special | 2.11.0 | 2.5k | 910525.477 | 4852.469 | 1.0 | eligible |
| 2026-08-23 | Android | com.hfhy.waje.special | 2.11.1 | 3.2k | 949853.38 | 2791.944 | 0.9984599589322382 | eligible |
| 2026-08-23 | Android | com.hfhy.waje.special | 2.11.2 | 13.0k | 718596.827 | 3176.953 | 0.9978134110787172 | eligible |
| 2026-08-23 | Android | com.hfhy.waje.special | 2.11.4 | 743 | N/A | N/A | 1.0 | sample_too_small |
| 2026-08-23 | Android | com.hfhy.waje.special | 2.12.0 | 2.2k | 902480.794 | 2697.6 | 1.0 | eligible |
| 2026-08-23 | Android | com.hfhy.waje.special | 2.13.0 | 5.0k | 787270.318 | 4339.28 | 1.0 | eligible |
| 2026-08-23 | Android | com.hfhy.waje.special | 2.14.0 | 20.1k | 673909.01 | 1672.722 | 0.9986852196778788 | eligible |
| 2026-08-23 | Android | com.hfhy.waje.special | 2.15.0 | 111.9k | 710235.405 | 2413.013 | 0.9990951396070321 | eligible |
| 2026-08-23 | Android | com.hfhy.waje.special | 2.16.0 | 176.0k | 725723.239 | 2599.511 | 0.9992286975103367 | eligible |
| 2026-08-23 | Android | com.hfhy.waje.special | 2.17.0 | 1.19M | 711771.39 | 2219.407 | 0.9988240951735224 | eligible |
| 2026-08-23 | Android | com.hfhy.wajecasino.game | 2.14.0 | 976.8k | 388622.405 | 2760.525 | 0.9978494258670184 | eligible |
| 2026-08-23 | Android | com.hfhy.wajecasino.palmgame | 2.10.41 | 375 | N/A | N/A | 1.0 | sample_too_small |

## Crashlytics 稳定性

- 当前只展示按 `event_id` 去重的事件量、按 `issue_id` 去重的问题数和 Fatal/Non-fatal 分类。
- 在官方字段、去重键、ANR 枚举和 Sessions 分母完成认证前，不计算崩溃率、ANR 率或受影响用户数。

| 日期 | 端侧 | 包体 | 版本 | 类型 | 去重事件 | 问题数 |
|---|---|---|---|---|---:|---:|
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.17.0 | non_fatal | 5 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.17.0 | non_fatal | 4 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.15.0 | non_fatal | 3 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.15.0 | non_fatal | 3 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.16.0 | non_fatal | 2 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.17.0 | non_fatal | 2 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.13.0 | non_fatal | 2 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.16.0 | non_fatal | 2 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.16.0 | non_fatal | 2 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.17.0 | non_fatal | 2 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.14.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.17.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.16.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.15.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.15.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.16.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.15.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.17.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.14.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.17.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.16.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.16.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.15.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.17.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.16.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.17.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.17.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.17.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.17.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.17.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.14.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.17.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.17.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.17.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.16.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.17.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.17.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.17.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.16.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.17.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.15.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.17.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.16.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.17.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.17.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.17.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.16.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_transsion_new | com.hfhy.wajecasino.game | 2.14.0 | non_fatal | 2 | 1 |
| 2026-08-20 | android_transsion_new | com.hfhy.wajecasino.game | 2.14.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_transsion_new | com.hfhy.wajecasino.game | 2.14.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_transsion_new | com.hfhy.wajecasino.game | 2.14.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_transsion_old | com.hfhy.wajecasino.palmgame | 2.17.0 | fatal | 5 | 1 |
| 2026-08-20 | android_transsion_old | com.hfhy.wajecasino.palmgame | 2.17.0 | fatal | 4 | 1 |
| 2026-08-20 | android_transsion_old | com.hfhy.wajecasino.palmgame | 2.17.0 | fatal | 2 | 1 |
| 2026-08-20 | android_transsion_old | com.hfhy.wajecasino.palmgame | 2.17.0 | fatal | 2 | 1 |
| 2026-08-20 | android_transsion_old | com.hfhy.wajecasino.palmgame | 2.17.0 | fatal | 2 | 1 |
| 2026-08-20 | android_transsion_old | com.hfhy.wajecasino.palmgame | 2.17.0 | fatal | 2 | 1 |
| 2026-08-20 | android_transsion_old | com.hfhy.wajecasino.palmgame | 2.17.0 | fatal | 2 | 1 |
| 2026-08-20 | android_transsion_old | com.hfhy.wajecasino.palmgame | 2.17.0 | fatal | 2 | 1 |
| 2026-08-20 | android_transsion_old | com.hfhy.wajecasino.palmgame | 2.17.0 | fatal | 2 | 1 |
| 2026-08-20 | android_transsion_old | com.hfhy.wajecasino.palmgame | 2.17.0 | fatal | 1 | 1 |
| 2026-08-20 | android_transsion_old | com.hfhy.wajecasino.palmgame | 2.17.0 | fatal | 1 | 1 |
| 2026-08-20 | android_transsion_old | com.hfhy.wajecasino.palmgame | 2.17.0 | fatal | 1 | 1 |
| 2026-08-20 | android_transsion_old | com.hfhy.wajecasino.palmgame | 2.17.0 | fatal | 1 | 1 |
| 2026-08-20 | android_transsion_old | com.hfhy.wajecasino.palmgame | 2.17.0 | fatal | 1 | 1 |
| 2026-08-20 | android_transsion_old | com.hfhy.wajecasino.palmgame | 2.17.0 | fatal | 1 | 1 |
| 2026-08-20 | android_transsion_old | com.hfhy.wajecasino.palmgame | 2.17.0 | fatal | 1 | 1 |
| 2026-08-20 | android_transsion_old | com.hfhy.wajecasino.palmgame | 2.17.0 | fatal | 1 | 1 |
| 2026-08-20 | android_transsion_old | com.hfhy.wajecasino.palmgame | 2.17.0 | fatal | 1 | 1 |
| 2026-08-20 | android_transsion_old | com.hfhy.wajecasino.palmgame | 2.17.0 | fatal | 1 | 1 |
| 2026-08-20 | android_transsion_old | com.hfhy.wajecasino.palmgame | 2.17.0 | fatal | 1 | 1 |
| 2026-08-20 | android_transsion_old | com.hfhy.wajecasino.palmgame | 2.17.0 | non_fatal | 1 | 1 |
| 2026-08-21 | android_main | com.hfhy.waje.special | 2.13.0 | non_fatal | 11 | 1 |
| 2026-08-21 | android_main | com.hfhy.waje.special | 2.17.0 | non_fatal | 5 | 1 |
| 2026-08-21 | android_main | com.hfhy.waje.special | 2.16.0 | non_fatal | 4 | 1 |
| 2026-08-21 | android_main | com.hfhy.waje.special | 2.16.0 | non_fatal | 4 | 1 |
| 2026-08-21 | android_main | com.hfhy.waje.special | 2.17.0 | non_fatal | 3 | 1 |
| 2026-08-21 | android_main | com.hfhy.waje.special | 2.15.0 | non_fatal | 3 | 1 |
| 2026-08-21 | android_main | com.hfhy.waje.special | 2.17.0 | non_fatal | 2 | 1 |
| 2026-08-21 | android_main | com.hfhy.waje.special | 2.17.0 | non_fatal | 2 | 1 |

## H5 性能与核心漏斗缺口

| 指标族 | 当前状态 | 不能直接推断的结论 |
|---|---|---|
| Web Vitals（LCP/INP/CLS/FCP/TTFB） | `data_gap` | 不能从 page_view 或停留事件推断加载速度 |
| 页面白屏/黑屏与前端错误 | `data_gap` | 不能判定网页稳定性 |
| 核心请求 P95 / 超时 / 重试 | `data_gap` | 不能定位弱网接口问题 |
| 游戏就绪 / 可下注 / 首局 | `blocked` | Firebase 行为事件不等于服务端成功 |

## 建议动作

- Gemini MCP 连接、trust 和安全 View 白名单未全部通过时，继续保持 API fallback，不启用自动自然语言查询。
- Android Performance 先按包体、版本、设备、系统和网络单维度做 P95 与成功率观察；样本不足 500 不进入正式排行。
- iOS 继续独立积累至少 7 个完整日，确认现有来源映射后再开放跨端趋势。
- H5 补齐 H5_NAVIGATION_PERF、H5_CORE_REQUEST、H5_GAME_READY、H5_BET_READY、H5_CLIENT_ERROR 等事件后，才能发布网页性能和核心漏斗指标。

## 审计边界

本报告只保存聚合结果、查询回执和状态，不保存原始事件行、用户标识、设备唯一标识、Cookie、Token、URL、请求体、响应体、订单或错误堆栈。
