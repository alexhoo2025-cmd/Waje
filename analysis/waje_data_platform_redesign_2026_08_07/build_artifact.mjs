import fs from "node:fs";
import path from "node:path";

const root = path.dirname(new URL(import.meta.url).pathname);
const generatedAt = "2026-08-07T19:15:00+08:00";

function imageFigure(fileName, alt, caption) {
  const filePath = path.join(root, "diagrams", fileName);
  const data = fs.readFileSync(filePath).toString("base64");
  return `<figure style="margin:0"><img src="data:image/png;base64,${data}" alt="${alt}" style="display:block;width:100%;height:auto;border-radius:18px"><figcaption style="margin-top:12px;color:#5d6b82;font-size:14px;line-height:1.6">${caption}</figcaption></figure>`;
}

const sources = [
  {
    id: "platform_inventory",
    label: "Waje 平台页面盘点与数据开发重点确认（2026年8月10日）",
    query: {
      engine: "ANSI SQL",
      language: "SQL",
      executed_at: generatedAt,
      description: "复现当前五类系统定位、可见规模和主要问题；纳入 8 月 10 日确认的 Metabase 访问边界、数据开发重点和架构/权限决策归口。",
      sql: "SELECT 1 AS sort_order, '起源' AS system_name, '产品与用户分析' AS current_role, '8个一级模块；报表集市70项' AS verified_scale UNION ALL SELECT 2, 'ARES', '投放归因与执行', '5个可见一级模块' UNION ALL SELECT 3, 'BI', '经营与管理报表', '经营大盘至少32字段、7筛选' UNION ALL SELECT 4, 'GM', '用户维护与运营排障', 'Lifecycle Pool 7张表、7个导出' UNION ALL SELECT 5, 'Metabase', '受控业务数据访问、临时查询与看板', '非独立数据平台；部分业务数据仅经此入口访问'",
      filters: ["页面盘点：2026年8月3日至8月7日", "以8月7日负责人确认修正旧资料命名", "2026年8月10日补充：云主机 Metabase 是权限控制与风险隔离边界，部分业务数据仅可经此入口访问", "当前开发重点：用户分层、KYC 人脸识别认证、Impala→BigQuery；整体架构与权限控制由 Brooks 规划和确定"],
      metric_definitions: ["verified_scale 为当前已观察下限，不代表平台全量资产。"]
    }
  },
  {
    id: "origin_report_inventory",
    label: "起源分析平台报表集市目录（2026年8月3日人工核验）",
    href: "https://datagrowth.wajegame.com/tracking-web/iframe",
    query: {
      engine: "ANSI SQL",
      language: "SQL",
      executed_at: generatedAt,
      description: "复现五个报表组的条目数和 BQ 前缀数量。",
      sql: "SELECT 1 AS sort_order, '经营分析' AS report_group, 19 AS report_count, 9 AS bq_count UNION ALL SELECT 2, '玩法数值', 10, 5 UNION ALL SELECT 3, '游戏分析', 19, 9 UNION ALL SELECT 4, '增长分析', 10, 5 UNION ALL SELECT 5, '经济体系', 12, 6",
      filters: ["Waje Special 当前账号可见目录", "核验日期：2026年8月3日"],
      metric_definitions: [
        "report_count 为目录当前可见条目数。",
        "bq_count 为名称以 BQ- 开头的条目数，不等同于已确认一一重复数。"
      ]
    }
  },
  {
    id: "engine_version_inventory",
    label: "起源报表版本结构（按目录前缀）",
    href: "https://datagrowth.wajegame.com/tracking-web/iframe",
    query: {
      engine: "ANSI SQL",
      language: "SQL",
      executed_at: generatedAt,
      description: "复现 70 项中 BQ 前缀与非 BQ 条目的数量和占比。",
      sql: "SELECT 1 AS sort_order, 'BQ前缀' AS version_class, 34 AS report_count, 34.0/70.0 AS share UNION ALL SELECT 2, '非BQ' AS version_class, 36 AS report_count, 36.0/70.0 AS share",
      filters: ["仅按条目名称是否以 BQ- 开头分类"],
      metric_definitions: ["share = 同类条目数 / 70。"]
    }
  },
  {
    id: "quality_snapshot",
    label: "起源数据质量页面（2026年7月27日至8月2日）",
    href: "https://datagrowth.wajegame.com/tracking-web/burying/buryingPoint/dataQuality",
    query: {
      engine: "ANSI SQL",
      language: "SQL",
      executed_at: generatedAt,
      description: "复现全事件和 GAMEEND 的质量快照。",
      sql: "SELECT 3963905 AS total_received, 3833031 AS total_persisted, 130874 AS total_anomalous, 0 AS discarded, 130874.0/3963905.0 AS total_error_rate, 418338 AS gameend_received, 287464 AS gameend_persisted, 130874 AS gameend_anomalous, 130874.0/418338.0 AS gameend_invalid_rate",
      filters: ["日期：2026年7月27日至8月2日", "页面展示口径"],
      metric_definitions: [
        "全事件错误率 = 异常属性条数 / 接收条数。",
        "GAMEEND 异常率 = GAMEEND 异常属性条数 / GAMEEND 接收条数。"
      ]
    }
  },
  {
    id: "gm_workload",
    label: "GM Lifecycle Pool v2 报表结构盘点",
    query: {
      engine: "ANSI SQL",
      language: "SQL",
      executed_at: generatedAt,
      description: "复现连续 7 日生命周期分析的人工导出操作量估算。",
      sql: "SELECT 4 AS commonly_used_source_tables, 7 AS days, 4*7 AS export_operations, 252 AS rows_per_day, 18 AS metrics_per_row, 252*18 AS data_points_per_day",
      filters: ["4 张常用来源表", "连续 7 日"],
      metric_definitions: ["导出操作量 = 4 张常用来源表 × 7 天 = 28 次。"]
    }
  },
  {
    id: "historical_assets",
    label: "历史飞书分析资料目录盘点（2026年8月4日）",
    query: {
      engine: "ANSI SQL",
      language: "SQL",
      executed_at: generatedAt,
      description: "复现已入库的历史分析资料类型和数量。",
      sql: "SELECT '表格型' AS asset_type, 10 AS asset_count UNION ALL SELECT '正文/附件/图表型', 4",
      filters: ["轻量化游戏分析相关目录", "仅统计已识别子文档"],
      metric_definitions: ["asset_count 为目录下已识别资料数。"]
    }
  },
  {
    id: "solution_design",
    label: "Waje 数据平台优化整合方案（2026年8月7日）",
    query: {
      engine: "ANSI SQL",
      language: "SQL",
      executed_at: generatedAt,
      description: "复现方案中的核心指标、目标边界和实施阶段。",
      sql: "SELECT 1 AS sort_order, 'P0A' AS phase, '0-2周' AS timing, 'Brooks 架构/权限定案与治理底表' AS deliverable UNION ALL SELECT 2, 'P0B','0-4周','Impala/BQ对账与质量闸门' UNION ALL SELECT 3, 'P0C','并行需求','用户分层与KYC人脸认证' UNION ALL SELECT 4, 'P1','5-8周','统一首页、语义层、筛选下钻' UNION ALL SELECT 5, 'P2','9-12周','GM迁移、专题重组、旧表归档' UNION ALL SELECT 6, 'P3','12周后','质量告警与Gemini受控试点'",
      filters: ["建议周期，以阶段验收闸门为准"],
      metric_definitions: ["时间为产品建议，不代表已确认研发排期。"]
    }
  }
];

const manifest = {
  version: 1,
  surface: "report",
  title: "Waje数据平台架构梳理和优化整合方案",
  description: "当前平台与报表盘点、目标架构、报表重组、权限设计及分阶段实施方案。",
  generatedAt,
  sources,
  cards: [
    { id: "card_reports", dataset: "headline_reports", sourceId: "origin_report_inventory", description: "起源报表集市当前可见条目。", metrics: [{ label: "起源报表条目", field: "value", format: "number" }] },
    { id: "card_bq", dataset: "headline_bq", sourceId: "engine_version_inventory", description: "名称以 BQ- 开头的目录条目占比。", metrics: [{ label: "BQ前缀占比", field: "value", format: "percent" }] },
    { id: "card_bi", dataset: "headline_bi", sourceId: "platform_inventory", description: "当前经营大盘已观察到的字段下限。", metrics: [{ label: "BI可见字段", field: "value", format: "number" }] },
    { id: "card_gm", dataset: "headline_gm", sourceId: "gm_workload", description: "连续 7 日、4 张常用来源表的导出操作估算。", metrics: [{ label: "GM七日导出", field: "value", format: "number" }] },
    { id: "card_gameend", dataset: "headline_gameend", sourceId: "quality_snapshot", description: "GAMEEND 异常属性条数占接收量。", metrics: [{ label: "GAMEEND异常率", field: "value", format: "percent" }] }
  ],
  charts: [
    {
      id: "chart_report_groups",
      title: "起源报表集市各组条目数",
      subtitle: "经营和游戏分析各 19 项；完整目录共 70 项。",
      type: "bar",
      dataset: "report_groups",
      sourceId: "origin_report_inventory",
      encodings: {
        x: { field: "report_group", type: "nominal", label: "报表组" },
        y: { field: "report_count", type: "quantitative", aggregate: "sum", label: "条目数", format: "number" },
        tooltip: [
          { field: "report_count", type: "quantitative", label: "条目数", format: "number" },
          { field: "bq_count", type: "quantitative", label: "BQ前缀数", format: "number" },
          { field: "share", type: "quantitative", label: "目录占比", format: "percent" }
        ]
      },
      settings: { orientation: "horizontal", sort: "descending", showValues: true },
      layout: "full"
    },
    {
      id: "chart_engine_versions",
      title: "起源报表版本结构",
      subtitle: "按目录前缀分类；BQ 前缀占 48.6%。",
      type: "bar",
      dataset: "engine_versions",
      sourceId: "engine_version_inventory",
      encodings: {
        x: { field: "version_class", type: "nominal", label: "版本类别" },
        y: { field: "report_count", type: "quantitative", aggregate: "sum", label: "条目数", format: "number" },
        tooltip: [
          { field: "share", type: "quantitative", label: "占比", format: "percent" },
          { field: "caveat", type: "text", label: "说明" }
        ]
      },
      settings: { orientation: "horizontal", sort: "descending", showValues: true },
      layout: "full"
    }
  ],
  tables: [
    {
      id: "table_platforms",
      title: "当前平台功能与边界",
      subtitle: "页面盘点与负责人沟通结果；规模为当前已观察下限。",
      dataset: "platforms",
      sourceId: "platform_inventory",
      defaultSort: { field: "sort_order", direction: "asc" },
      density: "spacious",
      layout: "full",
      columns: [
        { field: "sort_order", label: "序号", type: "number" },
        { field: "system_name", label: "系统", type: "text" },
        { field: "current_role", label: "当前定位", type: "text" },
        { field: "current_content", label: "主要内容", type: "text" },
        { field: "verified_scale", label: "已确认规模", type: "text" },
        { field: "main_problem", label: "主要问题", type: "text" }
      ]
    },
    {
      id: "table_report_groups",
      title: "起源报表目录及优化归属",
      subtitle: "五个现有报表组映射到目标专题或主系统。",
      dataset: "report_group_details",
      sourceId: "origin_report_inventory",
      defaultSort: { field: "sort_order", direction: "asc" },
      density: "spacious",
      layout: "full",
      columns: [
        { field: "sort_order", label: "序号", type: "number" },
        { field: "report_group", label: "报表组", type: "text" },
        { field: "report_count", label: "数量", type: "number" },
        { field: "examples", label: "当前内容示例", type: "text" },
        { field: "target", label: "优化归属", type: "text" }
      ]
    },
    {
      id: "table_quality",
      title: "当前数据可信度问题",
      subtitle: "页面值、加载状态和数据质量问题必须使用不同处理方式。",
      dataset: "quality_issues",
      sourceId: "quality_snapshot",
      defaultSort: { field: "sort_order", direction: "asc" },
      density: "spacious",
      layout: "full",
      columns: [
        { field: "sort_order", label: "序号", type: "number" },
        { field: "evidence", label: "证据", type: "text" },
        { field: "interpretation", label: "正确解释", type: "text" },
        { field: "action", label: "处理动作", type: "text" }
      ]
    },
    {
      id: "table_target_roles",
      title: "目标系统职责边界",
      subtitle: "正式主题只保留一个主入口，其他系统提供摘要和跳转。",
      dataset: "target_roles",
      sourceId: "solution_design",
      defaultSort: { field: "sort_order", direction: "asc" },
      density: "spacious",
      layout: "full",
      columns: [
        { field: "sort_order", label: "序号", type: "number" },
        { field: "system_name", label: "系统", type: "text" },
        { field: "target_role", label: "目标职责", type: "text" },
        { field: "keep_build", label: "保留/新建", type: "text" },
        { field: "move_out", label: "明确移出", type: "text" }
      ]
    },
    {
      id: "table_kpis",
      title: "统一首页 10 个核心指标",
      subtitle: "跨部门首页指标；诊断字段进入对应专题。",
      dataset: "kpis",
      sourceId: "solution_design",
      defaultSort: { field: "sort_order", direction: "asc" },
      density: "spacious",
      layout: "full",
      columns: [
        { field: "sort_order", label: "#", type: "number" },
        { field: "metric_name", label: "指标", type: "text" },
        { field: "definition", label: "统一口径", type: "text" },
        { field: "primary_system", label: "主入口", type: "text" }
      ]
    },
    {
      id: "table_migration",
      title: "旧报表迁移矩阵",
      subtitle: "按保留、合并、迁移、归档重组现有资产。",
      dataset: "migration_matrix",
      sourceId: "solution_design",
      defaultSort: { field: "sort_order", direction: "asc" },
      density: "spacious",
      layout: "full",
      columns: [
        { field: "sort_order", label: "序号", type: "number" },
        { field: "current_asset", label: "当前资产", type: "text" },
        { field: "disposition", label: "处理", type: "text" },
        { field: "target_location", label: "目标位置", type: "text" },
        { field: "acceptance", label: "验收条件", type: "text" }
      ]
    },
    {
      id: "table_permissions",
      title: "角色与权限边界",
      subtitle: "角色、数据范围、粒度和操作类型四层控制。",
      dataset: "permissions",
      sourceId: "solution_design",
      defaultSort: { field: "sort_order", direction: "asc" },
      density: "spacious",
      layout: "full",
      columns: [
        { field: "sort_order", label: "序号", type: "number" },
        { field: "role", label: "角色", type: "text" },
        { field: "default_access", label: "默认权限", type: "text" },
        { field: "approval_required", label: "禁止/需审批", type: "text" }
      ]
    },
    {
      id: "table_roadmap",
      title: "分阶段实施路线",
      subtitle: "建议周期；BigQuery 与 Gemini 正式排期仍待确认。",
      dataset: "roadmap",
      sourceId: "solution_design",
      defaultSort: { field: "sort_order", direction: "asc" },
      density: "spacious",
      layout: "full",
      columns: [
        { field: "sort_order", label: "序号", type: "number" },
        { field: "phase", label: "阶段", type: "text" },
        { field: "timing", label: "建议周期", type: "text" },
        { field: "deliverable", label: "核心交付", type: "text" },
        { field: "gate", label: "验收闸门", type: "text" }
      ]
    }
  ],
  blocks: [
    { id: "title", type: "markdown", body: "# Waje数据平台架构梳理和优化整合方案" },
    {
      id: "executive_summary",
      type: "markdown",
      body: "## 执行摘要\n- **核心矛盾不是缺少报表，而是统一存储之上的治理分散。** 游戏、投放和收入数据已集中在 Google Cloud，但起源、ARES、BI、GM、Metabase 仍各自维护筛选、指标解释和分析路径。\n- **BigQuery 迁移应被定义为治理重构，而不是数据库替换。** 必须同时完成旧新引擎对账、统一 ID/维度、数据状态、权限和回滚；否则 Gemini 只会放大现有口径与权限风险。\n- **当前数据开发的并行重点是用户分层、KYC 人脸识别认证和 Impala → BigQuery 切换。** 用户分层和 KYC 需先明确数据字段、认证状态、最小权限、合规与审计，再进入正式指标和业务流程。\n- **系统按任务边界分工。** 起源做产品与用户分析，ARES 做投放归因与执行，BI 做经营/财务/结算与分发，GM 保留操作排障；云主机上的 Metabase 同时承担受控业务数据访问、权限控制、风险隔离和临时分析，部分业务数据只能经此入口访问。\n- **Brooks 负责整体数据平台架构与权限控制的规划和定案。** 后续系统边界、访问模型和实施排期应以该方案为准；首页收敛到 10 个核心指标，现有报表按保留、合并、迁移、归档处理。"
    },
    { id: "headline_strip", type: "metric-strip", cardIds: ["card_reports", "card_bq", "card_bi", "card_gm", "card_gameend"] },
    {
      id: "finding_current",
      type: "markdown",
      body: "## 数据集中，但使用链路仍然分裂\n**当前架构是一个数据环境、多套应用语义。** 起源、ARES、BI 是门户内三个并列业务前台；GM 是用户维护和运营排障后台；云主机上的 Metabase 是受控访问与风险隔离层，同时提供临时查询和看板，且部分业务数据只能经此入口访问。平台之间尚未形成统一的发现问题、解释原因、下钻明细和执行动作闭环。"
    },
    { id: "current_architecture", type: "html", body: imageFigure("current_architecture.png", "当前数据平台架构图", "实线表示主要数据供给，红色虚线表示当前仍依赖人工导出和拼接的分析链路。"), sourceId: "platform_inventory" },
    { id: "platform_table", type: "table", tableId: "table_platforms" },
    {
      id: "finding_reports",
      type: "markdown",
      body: "## 70 项报表反映的是历史堆叠，不是清晰的信息架构\n**起源报表集市已形成明显的迁移并存和主题重叠。** 五个分组中经营分析和游戏分析各 19 项；34 项带 BQ 前缀，占目录 48.6%。这一数字不能直接等同于 34 组重复报表，但足以说明迁移期资产治理已成为首要工作。"
    },
    { id: "report_groups_chart", type: "chart", chartId: "chart_report_groups" },
    {
      id: "version_interpretation",
      type: "markdown",
      body: "**BQ 前缀与非 BQ 条目不能按名称批量删除。** 每项必须在同筛选、同截止时间、同口径下完成 7-14 个完整日对账，再将旧版改为只读并归档。未找到 owner、来源或使用场景的报表不得继续扩建。"
    },
    { id: "engine_chart", type: "chart", chartId: "chart_engine_versions" },
    { id: "report_detail_table", type: "table", tableId: "table_report_groups" },
    {
      id: "finding_quality",
      type: "markdown",
      body: "## 数据质量问题必须先于业务解释处理\n**页面显示值不必然等于可信业务值。** 未成熟 D7 应显示 N/A；CAC 为 0 导致的 ROI NaN、LTV30 为 0、BI 的 No Data、ARES 的区服失败分别属于口径、数据源、加载或权限状态，不能统一解释为业务结果为 0。GAMEEND 在已观察窗口的异常率为 31.28%，是游戏局数、完局、玩法留存和 RTP 归因的 P0 阻断项。"
    },
    { id: "quality_table", type: "table", tableId: "table_quality" },
    {
      id: "target_architecture_intro",
      type: "markdown",
      body: "## 目标架构：一套可信数据与指标，多种任务工作台\n**BigQuery 上方必须补齐标准事实、共享维度和认证指标语义层。** 起源、ARES、BI、GM、Metabase 不再分别定义正式指标；Metabase 作为云主机上的受控访问与风险隔离层，承载最小授权、访问审计和受限数据入口。数据质量、血缘、调度和 SLA 横向治理，权限、脱敏、导出和审计形成安全边界。"
    },
    { id: "target_architecture", type: "html", body: imageFigure("target_architecture.png", "目标数据平台架构图", "Gemini 位于治理体系之后，只访问认证指标和白名单数据集。"), sourceId: "solution_design" },
    { id: "target_roles_table", type: "table", tableId: "table_target_roles" },
    {
      id: "ia_intro",
      type: "markdown",
      body: "## 报表从历史目录改为业务任务入口\n**每类问题只有一个主入口。** BI 承担管理汇报，起源承担产品分析，ARES 承担投放动作，GM 承担用户维护和排障；Metabase 承担云主机受控数据访问、风险隔离和敏捷分析，受限业务数据不应绕过该入口。临时专题仍须有 owner、有效期和转正式/下线状态。统一筛选和数据状态贯穿所有入口。"
    },
    { id: "information_architecture", type: "html", body: imageFigure("report_information_architecture.png", "目标报表与工作台结构图", "起源内优先建设新手、游戏/RTP、付费资产、H5/低端机、故障质量五类专题。"), sourceId: "solution_design" },
    {
      id: "kpi_intro",
      type: "markdown",
      body: "## 首页只保留 10 个可行动指标\n**首页用于判断健康度，不用于承载所有诊断字段。** 每个指标必须展示口径、分子分母、成熟条件、数据截止时间和质量状态；利润、ARPPU、复购、TX、胜率和页面性能等进入专题页。"
    },
    { id: "kpi_table", type: "table", tableId: "table_kpis" },
    {
      id: "migration_intro",
      type: "markdown",
      body: "## 报表重组以减少重复维护为验收目标\n**运营周报、新手、留存和首充合并到新手生命周期；游戏、场次、玩法、收益留存、TC 比和胜率合并到游戏/RTP。** 渠道结果归 ARES；GM 的七张分析表重组为起源三页，修改和实时排障仍留在 GM。"
    },
    { id: "migration_table", type: "table", tableId: "table_migration" },
    {
      id: "permission_intro",
      type: "markdown",
      body: "## 权限必须把看数、下钻、导出和修改分开\n**权限按角色、数据范围、数据粒度和操作类型四层控制。** Brooks 规划并确定整体权限控制方案；受限业务数据必须通过云主机 Metabase 的受控入口访问。查看、明细下钻、导出、创建报表、发布正式报表、修改指标和修改 GM 策略必须分别授权并进入审计。"
    },
    { id: "permission_table", type: "table", tableId: "table_permissions" },
    {
      id: "next_steps",
      type: "markdown",
      body: "## 下一步行动\n1. **0-2 周：** Brooks 输出整体架构与权限控制决策稿；冻结重复报表新增，完成系统、指标、权限、报表、埋点五张治理表；补齐 Metabase 受限数据目录、角色矩阵和访问审计责任人。\n2. **0-4 周：** 完成 Impala/BigQuery 并行对账、GAMEEND 修复、统一 ID/时间/币种和回滚方案。\n3. **并行需求：** 开发用户分层、KYC 人脸识别认证；在方案评审中确定用户范围、认证状态、字段、最小权限、导出和审计规则。\n4. **5-8 周：** 上线 10 指标首页、认证语义层、统一筛选、数据状态和上下文下钻。\n5. **9-12 周：** 迁移 GM 分析视图，建设新手、RTP、付费、H5/低端机和故障专题，归档旧表。\n6. **12 周后：** 建立报表健康度和质量告警，再启动 Gemini 白名单试点。"
    },
    { id: "roadmap_table", type: "table", tableId: "table_roadmap" },
    {
      id: "further_questions",
      type: "markdown",
      body: "## 待确认事项\n- Brooks 的架构与权限控制方案将覆盖哪些系统、数据集、角色、导出规则和审计责任？决策与评审节奏是什么？\n- BigQuery 迁移的里程碑、验收人、旧引擎并行周期和回滚期限是什么？\n- 用户分层和 KYC 人脸识别认证的权威字段、认证状态、合规要求、数据保留期和验收标准是什么？\n- 账号 ID、起源 ID、设备 ID、媒体、渠道、分包和游戏/玩法的权威映射表在哪里？\n- 哪些业务数据必须经云主机 Metabase 访问？对应角色、数据集、审批、导出限制与审计留存规则是什么？\n- 全量 BI/ARES/Metabase 报表资产、访问频率、数据源、刷新 SLA 和权限模型能否导出？\n- Gemini 首批白名单数据集、脱敏规则和审计保留期由谁审批？"
    }
  ]
};

const snapshot = {
  version: 1,
  generatedAt,
  status: "ready",
  datasets: {
    headline_reports: [{ value: 70 }],
    headline_bq: [{ value: 34 / 70 }],
    headline_bi: [{ value: 32 }],
    headline_gm: [{ value: 28 }],
    headline_gameend: [{ value: 130874 / 418338 }],
    report_groups: [
      { sort_order: 1, report_group: "经营分析", report_count: 19, bq_count: 9, non_bq_count: 10, share: 19 / 70 },
      { sort_order: 2, report_group: "玩法数值", report_count: 10, bq_count: 5, non_bq_count: 5, share: 10 / 70 },
      { sort_order: 3, report_group: "游戏分析", report_count: 19, bq_count: 9, non_bq_count: 10, share: 19 / 70 },
      { sort_order: 4, report_group: "增长分析", report_count: 10, bq_count: 5, non_bq_count: 5, share: 10 / 70 },
      { sort_order: 5, report_group: "经济体系", report_count: 12, bq_count: 6, non_bq_count: 6, share: 12 / 70 }
    ],
    engine_versions: [
      { sort_order: 1, version_class: "BQ前缀", report_count: 34, share: 34 / 70, caveat: "目录前缀计数；不等于已确认一一重复" },
      { sort_order: 2, version_class: "非BQ", report_count: 36, share: 36 / 70, caveat: "含旧引擎版本和少量无 BQ 对应项" }
    ],
    platforms: [
      { sort_order: 1, system_name: "起源", current_role: "产品与用户分析", current_content: "行为、留存、用户轨迹、埋点、专题报表", verified_scale: "8个一级模块；70项报表", main_problem: "首页无重点；BQ/旧版并存；质量状态不清" },
      { sort_order: 2, system_name: "ARES", current_role: "投放归因与执行", current_content: "数据中心、智投、渠道发行、设置、脚本", verified_scale: "5个可见一级模块", main_problem: "渠道与产品结果跨系统对账；依赖区服/权限" },
      { sort_order: 3, system_name: "BI", current_role: "经营与管理报表", current_content: "用户、游戏、收入、成本、充值、TX", verified_scale: "至少32字段、7筛选", main_problem: "与起源重合；仍以综合报表堆叠为主" },
      { sort_order: 4, system_name: "GM", current_role: "用户维护与运营排障", current_content: "用户明细、配置、Lifecycle Pool", verified_scale: "7张表、7个导出", main_problem: "操作与分析混杂；多日依赖人工导出" },
      { sort_order: 5, system_name: "Metabase", current_role: "受控业务数据访问、临时查询与看板", current_content: "云主机受控访问 GCP/BQ；权限控制、风险隔离、临时 SQL", verified_scale: "非独立数据平台；部分业务数据仅经此入口访问", main_problem: "受限数据目录、角色矩阵、导出规则与审计责任仍需明确" }
    ],
    report_group_details: [
      { sort_order: 1, report_group: "经营分析", report_count: 19, examples: "TC生命周期、运营周报、新增/首充/复充、大额付费、留存、H5曝光", target: "首页摘要 + 新手/付费；渠道部分转 ARES" },
      { sort_order: 2, report_group: "玩法数值", report_count: 10, examples: "TC比、胜率区间、人机组局、玩法重合、新手期", target: "游戏/RTP；机器人与数值诊断下沉" },
      { sort_order: 3, report_group: "游戏分析", report_count: 19, examples: "体彩、设备重复、场次、局数留存、游戏概况、收益留存、组局", target: "游戏/RTP + 版本体验" },
      { sort_order: 4, report_group: "增长分析", report_count: 10, examples: "首充累计留存、自然新增、Push、邀请", target: "新手生命周期；投放归因转 ARES" },
      { sort_order: 5, report_group: "经济体系", report_count: 12, examples: "TC、羊毛、付费曝光、任务、TX", target: "付费资产/风控；经营摘要进 BI" }
    ],
    quality_issues: [
      { sort_order: 1, evidence: "D7 留存曾显示 0", interpretation: "窗口包含未成熟 cohort", action: "排除未达到 D7 的新增用户；显示 N/A 和分子分母" },
      { sort_order: 2, evidence: "ROI CAC=0、ROI=NaN；LTV30=0", interpretation: "成本源、成熟窗口或链路未就绪", action: "修复并完成对账前不进入认证核心指标" },
      { sort_order: 3, evidence: "GAMEEND 异常率 31.28%", interpretation: "局数、完局、玩法留存和 RTP 可能受污染", action: "P0 修复字段契约、追踪键和事件级质量闸门" },
      { sort_order: 4, evidence: "H5 自动事件入库多为 0/1", interpretation: "可能未接入、另有链路或上报失败", action: "补页面性能、JS/接口错误、白屏和用户会话追踪" },
      { sort_order: 5, evidence: "BI No Data / ARES 区服失败", interpretation: "可能是加载、权限、接口或筛选状态", action: "与真实无业务数据分开显示" },
      { sort_order: 6, evidence: "分群、汇率等配置停留在 2023-2024", interpretation: "只能作为历史配置线索", action: "补 owner、版本、生效和失效时间" }
    ],
    target_roles: [
      { sort_order: 1, system_name: "起源", target_role: "产品健康、新手、游戏/RTP、付费、版本体验、故障质量", keep_build: "敏捷分析、轨迹、埋点；接收 GM 分析视图", move_out: "投放执行、财务大盘、GM 修改" },
      { sort_order: 2, system_name: "ARES", target_role: "成本、媒体/渠道归因、回收、ROI、预算动作", keep_build: "数据中心、智投、渠道发行", move_out: "完整产品行为、财务结算口径" },
      { sort_order: 3, system_name: "BI", target_role: "经营健康、利润、结算/TX、管理看板和推送", keep_build: "经营大盘重做", move_out: "产品明细和重复留存/事件报表" },
      { sort_order: 4, system_name: "GM", target_role: "用户维护、客服、策略配置、实时排障、操作审计", keep_build: "修改能力和实时明细", move_out: "多日趋势和正式分析报表" },
      { sort_order: 5, system_name: "Metabase", target_role: "受控业务数据访问、风险隔离、临时验证与专题看板", keep_build: "云主机受控入口、最小授权、访问审计、敏捷分析", move_out: "绕过受控入口直连受限数据；单独定义非认证指标" },
      { sort_order: 6, system_name: "Gemini", target_role: "认证指标解释、自然语言筛选、异常线索", keep_build: "治理完成后小范围试点", move_out: "原始敏感库直连和绕权问数" }
    ],
    kpis: [
      { sort_order: 1, metric_name: "DAU", definition: "认证账号 ID 日去重；排除测试账号；完整日", primary_system: "BI/起源" },
      { sort_order: 2, metric_name: "新增用户", definition: "首次满足注册/首登定义；与安装分开", primary_system: "起源" },
      { sort_order: 3, metric_name: "有效游戏用户", definition: "有效 GAMESTART 且局事实通过质量门槛", primary_system: "起源" },
      { sort_order: 4, metric_name: "成熟 D7 留存", definition: "仅纳入已达到 D7 的新增 cohort；显示分子分母", primary_system: "起源" },
      { sort_order: 5, metric_name: "付费金额", definition: "服务端支付成功，扣除退款/冲正，统一币种", primary_system: "BI" },
      { sort_order: 6, metric_name: "付费率", definition: "支付成功用户 / 认证活跃用户", primary_system: "BI/起源" },
      { sort_order: 7, metric_name: "D0/D1 首付费", definition: "新增 cohort 在 0/1 日首次成功支付", primary_system: "起源" },
      { sort_order: 8, metric_name: "投放 ROI", definition: "成熟窗口认证收入 / 认证投放成本；CAC=0 为 N/A", primary_system: "ARES" },
      { sort_order: 9, metric_name: "RTP 健康度", definition: "实际 RTP、理论/目标 RTP 及偏差；明确基础/完全口径", primary_system: "起源" },
      { sort_order: 10, metric_name: "数据可用率", definition: "按时且通过完整性、质量和对账的认证指标占比", primary_system: "BI/质量页" }
    ],
    migration_matrix: [
      { sort_order: 1, current_asset: "运营周报、新增/留存/首充、新手期", disposition: "合并", target_location: "起源：产品健康 + 新手生命周期", acceptance: "成熟 cohort、用户 ID、付费状态统一" },
      { sort_order: 2, current_asset: "游戏概况、场次、玩法、收益留存、TC比、胜率", disposition: "合并", target_location: "起源：游戏与 RTP", acceptance: "GAMEEND 修复；游戏/玩法/局映射统一" },
      { sort_order: 3, current_asset: "TC/TX、羊毛、任务、付费曝光", disposition: "分层合并", target_location: "起源付费资产；BI经营摘要", acceptance: "账务事实、币种、退款/TX状态统一" },
      { sort_order: 4, current_asset: "CT、自然新增、渠道结果", disposition: "迁移主入口", target_location: "ARES", acceptance: "媒体/渠道/分包与用户映射通过" },
      { sort_order: 5, current_asset: "Lifecycle Pool 7张表", disposition: "重组为3页", target_location: "起源：RTP总览、游戏生命周期、留存分层", acceptance: "一次多日查询/导出；GM并行7-14日一致" },
      { sort_order: 6, current_asset: "GM修改与排障", disposition: "保留", target_location: "GM", acceptance: "分析只读与修改权限分离；操作可审计" },
      { sort_order: 7, current_asset: "BI产品明细", disposition: "移除重复", target_location: "BI只留经营、财务、结算、分发", acceptance: "可跳转起源并继承筛选" },
      { sort_order: 8, current_asset: "14份历史飞书专题", disposition: "目录评审", target_location: "正式专题或归档库", acceptance: "数据可导出、口径可复现、owner明确" },
      { sort_order: 9, current_asset: "Metabase受控专题/临时看板", disposition: "保留受控入口；到期评审", target_location: "云主机 Metabase 或转正式系统", acceptance: "受限数据经该入口；有角色、数据集、用途、导出规则、审计和有效期" }
    ],
    permissions: [
      { sort_order: 1, role: "管理层", default_access: "BI 聚合看板和订阅", approval_required: "用户明细、原始订单、策略修改" },
      { sort_order: 2, role: "产品/策划", default_access: "起源聚合、脱敏下钻、保存视图", approval_required: "跨产品原始数据、大范围导出、GM修改" },
      { sort_order: 3, role: "投放/发行", default_access: "ARES所辖渠道成本、归因、策略", approval_required: "非本渠道、完整支付/身份明细" },
      { sort_order: 4, role: "运营/客服", default_access: "GM所辖用户、工单和必要配置", approval_required: "跨范围导出、修改指标口径" },
      { sort_order: 5, role: "数据/研发", default_access: "BQ模型、调度、质量、受控原始层", approval_required: "无审批导出敏感信息、代替业务改策略" },
      { sort_order: 6, role: "指标管理员", default_access: "指标、维度、报表目录和发布流程", approval_required: "直接修改原始事实" }
    ],
    roadmap: [
      { sort_order: 1, phase: "P0A", timing: "0-2周", deliverable: "Brooks 架构/权限定案；冻结重复建设；完成治理表", gate: "架构、权限、owner、用途、来源和状态明确" },
      { sort_order: 2, phase: "P0B", timing: "0-4周", deliverable: "Impala/BQ对账；统一ID、时间、币种；修复GAMEEND", gate: "7-14个完整日无未解释差异；有回滚方案" },
      { sort_order: 3, phase: "P0C", timing: "并行需求", deliverable: "用户分层、KYC人脸认证；字段、最小权限和审计评审", gate: "用户范围、认证状态、合规与验收标准明确" },
      { sort_order: 4, phase: "P1", timing: "5-8周", deliverable: "10指标首页、认证语义层、统一筛选/状态/下钻", gate: "同条件跨系统可对账；状态正确显示" },
      { sort_order: 5, phase: "P2", timing: "9-12周", deliverable: "GM七表迁三页；专题重组；旧表只读归档", gate: "GM并行7-14日一致；一次多日导出" },
      { sort_order: 6, phase: "P3", timing: "12周后", deliverable: "报表健康、自动告警、Gemini白名单试点", gate: "权限、脱敏、审计和安全评审通过" }
    ]
  }
};

const artifact = { surface: "report", manifest, snapshot, sources };
const out = path.join(root, "artifact.json");
fs.writeFileSync(out, JSON.stringify(artifact, null, 2));
console.log(out);
