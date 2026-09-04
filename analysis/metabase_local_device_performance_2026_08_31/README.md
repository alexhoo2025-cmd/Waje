# Waje 三端设备与性能总览（需求方案版）

本地入口：<http://127.0.0.1:3010/dashboard/6-waje>  
集合入口：<http://127.0.0.1:3010/collection/5-waje-device-performance-v1>

## 本次调整

新建并保存一张总览大看板，避免继续使用旧版四页拆分看板作为唯一入口。看板固定按以下顺序承载指标：

1. 数据源与完整性
2. Android Analytics
3. iOS Analytics
4. H5 Analytics
5. Android Sessions
6. Android/iOS 原生 Performance
7. Crashlytics 稳定性
8. 设备、系统、国家、运营商和网络维度排行
9. H5 性能采集缺口

Android、iOS、H5 的来源仍分别计算，不把不同端的事件、会话或性能样本直接相加。

## 已绑定筛选项

- 起始日期、结束日期：两个单日控件；同时填写表达日期区间。当前绑定 Analytics 三张行为卡片。
- 端侧：绑定 Analytics、Sessions、Performance、Crashlytics。
- 应用包体：绑定 Android/iOS Analytics、Sessions、Performance、Crashlytics 和设备网络排行。
- 应用版本：绑定 Android/iOS Analytics、Performance 和设备网络排行。
- 事件名称：绑定 Android/iOS/H5 Analytics。
- H5 浏览器：只绑定 H5 Analytics。
- 性能维度、维度值：绑定设备网络排行，用于选择设备型号、系统版本、国家、运营商或网络类型。

未采集的 H5 性能指标没有被做成可筛选的零值；仍显示为 `data_gap`。

## 聚合与阅读控制

Android/iOS Analytics 不再展示 500 行长表，改为按日期、包体、版本、事件聚合并将卡片返回上限降为 100 行；事件仍是事件次数，不是用户数。设备网络排行保留单维度 Top N 聚合。所有卡片只返回聚合结果，禁止从看板查看用户级或设备唯一标识明细。

## 验证

- 新看板空筛选重载：9/9 卡片加载，无错误。
- 设置“端侧=Android”后，iOS Analytics 返回 0 行，Android Analytics 返回 13 行，无错误。
- 旧版看板和报表未删除，作为历史入口保留。
- 本地 H2 文件在序列修复前已备份；BigQuery/Firebase 未写入。

完整对象、筛选变量和安全回执见 [`dashboard_receipt.json`](./dashboard_receipt.json)。

## 运行前提

Metabase 使用本地 JAR + H2 运行。关闭启动 Metabase 的终端进程后，`127.0.0.1:3010` 会停止；重新启动同一配置即可恢复看板。
