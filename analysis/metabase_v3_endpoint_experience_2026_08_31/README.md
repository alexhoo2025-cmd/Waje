# Waje 端侧体验问题总览 V3（本机 Metabase）

## 主入口

- 本机地址：`http://127.0.0.1:3010/dashboard/9-waje-v3`
- 标题：`Waje / 端侧体验问题总览 / V3（体验定位主入口）`
- 数据源：`wajenigeria` 项目的 Firebase Analytics、Performance 与 Crashlytics 已入库表。
- 数据区域：`europe-west4`；业务日期按 `Africa/Lagos` 解释。

## 使用目的

面向产品、研发和数据值班，优先回答：当前是哪个端、包体、版本、设备或运营商出现了可行动的体验问题？

主页面只使用只读 SQL 的聚合结果；不会展示用户标识、会话标识、设备唯一标识、完整 URL、请求正文、订单、支付明细或崩溃堆栈。

## 主页面卡片

| 区域 | Metabase 问题 | 输出粒度 | 关键口径 |
|---|---|---|---|
| 核心体验 | V3 - 核心体验健康矩阵（P95） | 端侧 × 包体 | 轨迹 P95、网络 P95、HTTP 200–399 成功率、慢帧/冻结帧；样本少于 500 时为 N/A。 |
| 数据可信度 | V3 - 数据可信度与体验观测状态 | 数据源 | 截止时间、覆盖天数、状态、H5 缺口、Android Sessions/Performance 开关冲突。 |
| 回归定位 | V3 - Android 版本 P95 回归异常 | Android 包体 × 版本 | 当日 P95 相对窗口内日 P95 中位数；连续 7 日和样本门槛不满足时只标为未成熟。 |
| 网络定位 | V3 - 网络质量异常 Top5（运营商，主入口） | 端侧 × 包体 × 运营商 | 网络响应 P95、HTTP 成功率、样本量；仅 Top 5。 |
| 设备定位 | V3 - 设备型号异常 Top5（轨迹P95） | 端侧 × 包体 × 设备型号 | 轨迹 P95、网络 P95、样本量；仅 Top 5。 |
| 稳定性 | V3 - Android 稳定性事件与问题数（主入口） | 包体 × 版本 × 错误类型 | 去重事件数与问题数；不显示崩溃率、ANR 率或受影响用户数。 |
| 影响范围 | V3 - 会话与行为影响范围 | 端侧 × 包体 × 版本 | 事件数、`session_start`、页面/屏幕、互动和客户端行为信号；仅作影响范围，不视为业务成功。 |

## 顶部筛选器

- 起始日期、结束日期：单值日期参数，分别映射到所有支持的聚合 SQL；默认查询本身固定在当前已验证窗口 `2026-08-20` 至 `2026-08-26`。
- 端侧、应用包体、应用版本：自动连接到同名的聚合 SQL 参数。
- 国家：仅连接采集该字段的设备诊断卡片；未采集的卡片不会被过滤为 0。

## 重要边界

- Android、iOS 的性能数值不合并成跨端总 P95。
- `session_start` 是事件计数，Android 去标识化会话只在 Sessions 专用数据集中单独定义，不与其相加。
- HTTP 成功率仅描述网络响应健康，不代表登录、下注或支付成功。
- Crashlytics 导出记录不等于崩溃率；在去重键、ANR 枚举与会话分母完成核验前，不计算率指标。
- H5 目前只有行为基线；LCP、INP、CLS、FCP、TTFB、白屏、核心请求 P95、前端错误、游戏就绪和可下注均以 `data_gap`/`blocked` 呈现，不伪造性能正常结论。

## 后续迁移

当前为“Firebase 原始表上的只读聚合 SQL”试运行层。后续管理员提供 `wajenigeria/europe-west4` 的安全聚合视图后，保持字段别名和筛选器不变，仅替换查询来源。

## 本机服务恢复

本看板运行在本机 Metabase JAR 上；浏览器显示“`127.0.0.1` 拒绝连接”通常表示服务进程已停止，不表示看板、H2 配置或 BigQuery 连接被删除。

当前恢复使用以下配置：

```bash
cd /Users/robin/Documents/wajetan_analyst
env \
  MB_DB_TYPE=h2 \
  MB_DB_FILE="$PWD/.local/metabase/metabase-data/metabase" \
  MB_JETTY_HOST=127.0.0.1 \
  MB_JETTY_PORT=3010 \
  JAVA_TOOL_OPTIONS="-Xms256m -Xmx1024m" \
  "$PWD/.local/metabase/jre/Contents/Home/bin/java" \
  -jar "$PWD/.local/metabase/metabase.jar"
```

启动完成后，访问 `http://127.0.0.1:3010/api/health` 应返回 `{"status":"ok"}`；随后重新加载主入口即可。H2 文件位于 `.local/metabase/metabase-data/`，不要在 Metabase 运行时手动移动或编辑它。
