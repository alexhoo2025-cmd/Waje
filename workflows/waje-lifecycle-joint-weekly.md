# Waje 联运生命周期数据手动周更新工作流

## 触发方式

每周二由用户手动触发，用户在消息中给出查询起止日期、输入 Excel 路径和特殊要求。没有自动调度，也不依赖后台常驻进程。

推荐触发语句：

```text
使用 $waje-lifecycle-joint-weekly，查询 YYYY-MM-DD 至 YYYY-MM-DD，更新指定 Excel；保留原文件，按查询范围生成新文件。
```

## 执行顺序

1. 在 Chrome 使用已登录会话打开认证入口和 `Lifecycle Pool v2 (Joint)` 页面。
2. 按日期选择器设置日期，点击 `查询历史记录`，等待页面完成。可以开 3 个页面并行，但不要在同一页面重复提交。
3. 对每个日期下载汇总、详细奖池、分游戏、活跃周期四个 Excel，归档到 `data/raw/lifecycle_joint/<run-date>/<query-date>/`；下载完成后记录 SHA-256。
4. 用 `scripts/update_workbook.mjs` 校验源数据并创建新 Excel：

```bash
node scripts/update_workbook.mjs \
  --start-date 2026-08-11 \
  --end-date 2026-08-17 \
  --input "/Users/robin/Desktop/waje data/新包生命周期V2 - 含联运2026.7.27-8.10_Joint修正版.xlsx" \
  --raw-root "/Users/robin/Documents/wajetan_analyst/data/raw/lifecycle_joint/2026-08-18" \
  --desktop-dir "/Users/robin/Desktop/waje data"
```

5. 如导出后新增行显示为 General 或格式丢失，运行：

```bash
node scripts/repair_workbook_styles.mjs \
  --input "/Users/robin/Desktop/waje data/新包生命周期V2 - 含联运2026.7.27-8.10_Joint修正版.xlsx" \
  --output "/Users/robin/Desktop/waje data/新包生命周期V2 - 含联运2026.8.11-8.17_Joint修正版.xlsx"
```

6. 检查 `validation-report.json`、四个 QA 预览和输出文件名；确认输入文件 SHA-256 未变化后交付。

## 文件命名

输出格式为：

`新包生命周期V2 - 含联运<开始日期>-<结束日期>_Joint修正版.xlsx`

日期用 `YYYY.M.D`，同年范围可简写结束日期的年月，例如 `2026.8.11-8.17`。不覆盖同名文件；如果同名文件已存在，应另存带运行时间的副本并报告。

## 失败处理

任何日期查不到、导出缺失、表头/行数不符、跨表勾稽失败、Excel 导出后校验失败，都停止交付，不用 0 或前一天数据补齐。保留已抓取原始文件和日志，向用户列出失败日期、失败区块和下一步需要的页面操作。
