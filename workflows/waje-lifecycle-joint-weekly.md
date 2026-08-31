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

## 飞书在线工作簿直接更新流程

当用户要求直接更新飞书生命周期工作簿时，使用上次实际同步且最大日期最新的在线工作簿作为目标。本流程当前目标为 `ZBD4wPBsricBWMktFqilAGxlgte`，不要仅依据迁移方案配置中的旧链接判断目标。

### 1. 写入前预检与备份

1. 使用 `lark-cli auth status --json --verify` 确认 `identity=user`、`verified=true`、`tokenStatus=valid` 和 Sheets 写权限。
2. 读取 `revision-get`、`workbook-info`、四个 `sheet-info`，记录 Sheet ID、真实末行、列数、行高、列宽、隐藏区和合并区。
3. 优先使用 `+workbook-export` 生成 XLSX 备份；若缺少 Drive/Export scope，不绕过权限，改用完整分块 `+csv-get` 值快照 + `+cells-get` 样式快照 + revision/history 记录，并将备份状态标为 `structured_snapshot_complete`。
4. 大表禁止单次 `+table-get` 作为备份：详细奖池、分游戏表按 500 行分块读取，并逐块检查 `complete=true`、`truncated=false`。

### 2. GM 查询与原始归档

1. 固定使用已登录 Chrome 的 `Lifecycle Pool v2 (Joint)` 页面；最多 3 个查询页并行。
2. 日期必须通过可见日期选择器选择，再读取 `input.value` 核对精确日期，最后点击 `查询历史记录`。
3. 下载不要依赖浏览器 download event；优先监听下载目录中的新 `.xlsx` 文件，按日期和导出按钮顺序立即复制为 `summary.xlsx`、`detail.xlsx`、`game.xlsx`、`active.xlsx`。
4. 原始文件按日期归档并记录 SHA-256；不使用下载文件名判定数据归属。
5. 结果行数动态读取：详细奖池按实际游戏数 × 生命周期 0–11，分游戏按实际游戏数，活跃表按返回的生命周期 1–11；目标写入时再筛选详细 0–4、活跃 1–4。

### 2.1 查询完成与新游戏新鲜度门禁

1. 每个页面必须写入查询回执：`目标日期 → 日期控件回读值 → 点击查询时间 → 首次可用行数 → 稳定确认时间 → 四个导出文件 SHA-256`。不能用浏览器下载文件名或按钮顺序作为日期/区块证据。
2. “四表行数可用”只代表候选完成，不能立即导出。至少间隔 30–45 秒读取两次 `summary/detail/game/active` 的行数和标准化内容指纹；只有两次一致、没有加载/登录/验证码状态，才进入导出。
3. 对上线未满 7 天的新游戏，报告生成前比较相邻日期的：
   - `date × game` 分游戏行全字段指纹；
   - `date × lifecycle × game` 生命周期明细全字段指纹。
4. 若整体四表或其他游戏仍变化、目标新游戏却在上述两个粒度同时完全静态，标记 `data_static_suspect`。该状态不是“无新增有效局”、RTP、羊毛、机器人或系统故障结论。
5. `data_static_suspect` 出现后，禁止为该游戏输出日趋势、产品表现、实际/预期回报判断、生命周期集中度解释或羊毛倾向。先做独立复查：重新选择相同日期、再次点击 `查询历史记录`，导出到新的不可覆盖目录，再逐表、逐游戏、逐生命周期比对。
6. 独立复查与首次一致时，可保留源端静态信号并标记 `source_static_confirmed`；若任一标准化表值不同，标记 `source_query_mismatch`，冻结已生成结论和任何待写入更正，等待数据拥有方确认规范快照。不得自动用复查值覆盖飞书或本地历史。

### 3. 写入前数据合同

1. 先读取导出表头再生成 payload；GM 原始汇总末尾的 `修改` 字段不写入飞书 `原始数据总数`，目标范围固定为日期 + 前 9 个指标字段 A:J。
2. 目标字段宽度必须硬校验：汇总 A:J、详细 A:U、分游戏 A:S、活跃 A:AE；宽度不匹配时禁止写入。
3. 空值使用空字符串或空单元格对象；`+cells-set` 不接受 JSON `null` 作为普通 `value`。
4. 日期禁止写文本 `2026/8/23`。必须写入 Excel/Lark 日期序列值，并为日期列显式设置 `cell_styles.number_format = "yyyy/m/d"`。
5. 写入前断言：日期列为数值 payload、百分比为小数、金额为数值、文本字段保持文本、每个 payload 的行列数与目标范围完全一致。

### 4. 飞书批量写入与验收

1. 只在所有日期和四表勾稽通过后插入新行；插入前确认无合并区、隐藏行、公式或跨表引用受到影响，并使用 `inherit-style before`。
2. 详细奖池按约 290 行/批写入，其他 Sheet 按单个连续范围写入；每批记录 revision 和 `updated_cells_count`。
3. 写入后使用 `+csv-get` 回读新增区域，逐单元格与 `source-data.json` 比对；使用 `+table-get --no-header` 验证日期列 `dtype=datetime64[ns]`、格式为 `yyyy/m/d`。
4. 回读历史前缀并比较行级值；扫描 `#REF!`、`#DIV/0!`、`#VALUE!`、`#NAME?`、`#N/A`。
5. 对新增区域首行和末行回读 `cell_styles`、`border_styles`、行高；条件格式若因插行自动扩展，使用 `+cond-format-list` 验证颜色和范围。
6. 只有数据、类型、格式、历史前缀和结构检查全部通过，才将运行状态标记为 `ok`。

## 文件命名

输出格式为：

`新包生命周期V2 - 含联运<开始日期>-<结束日期>_Joint修正版.xlsx`

日期用 `YYYY.M.D`，同年范围可简写结束日期的年月，例如 `2026.8.11-8.17`。不覆盖同名文件；如果同名文件已存在，应另存带运行时间的副本并报告。

## 失败处理

任何日期查不到、导出缺失、表头/行数不符、跨表勾稽失败、Excel 导出后校验失败，都停止交付，不用 0 或前一天数据补齐。保留已抓取原始文件和日志，向用户列出失败日期、失败区块和下一步需要的页面操作。
