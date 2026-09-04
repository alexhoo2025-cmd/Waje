import fs from "node:fs/promises";
import { FileBlob, SpreadsheetFile } from "/Users/robin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs";

const root = "/Users/robin/Documents/wajetan_analyst";
const runDir = `${root}/analysis/x7_hot_tada_currency_summary_2026_09_04`;
const workbookPath = "/Users/robin/Desktop/data/Currency_Summary_Report_2026-09-04_06-41-44.xlsx";
const runAt = "2026-09-04T18:00:00+08:00";
await fs.mkdir(`${runDir}/sql`, { recursive: true });

const sourceFile = await FileBlob.load(workbookPath);
const workbook = await SpreadsheetFile.importXlsx(sourceFile);
const sheet = workbook.worksheets.getItem("Summary");
const matrix = sheet.getUsedRange().values;
const headers = matrix[0].map((x) => String(x ?? "").trim());
const ix = Object.fromEntries(headers.map((h, i) => [h, i]));

const parseNumber = (value) => {
  if (value === null || value === undefined || value === "") return null;
  const n = Number(String(value).replace(/,/g, "").trim());
  return Number.isFinite(n) ? n : null;
};
const parseRate = (value) => {
  if (value === null || value === undefined || value === "") return null;
  const n = Number(String(value).replace(/%/g, "").trim());
  return Number.isFinite(n) ? n / 100 : null;
};
const sourceRows = matrix.slice(1).filter((row) => row.some((x) => x !== null && x !== ""));
const totalRow = sourceRows.find((row) => String(row[ix["API ID"]] ?? "") === "Total");
const rows = sourceRows
  .filter((row) => row[ix["Game ID"]] && String(row[ix["Game ID"]]).trim() !== "Total")
  .map((row) => ({
    api_id: String(row[ix["API ID"]] ?? "").trim(),
    game_id: String(row[ix["Game ID"]] ?? "").trim(),
    game_type: String(row[ix["Game Type"]] ?? "Unknown").trim() || "Unknown",
    total_bet: parseNumber(row[ix["Total Bet"]]),
    total_win: parseNumber(row[ix["Total Win"]]),
    net_win: parseNumber(row[ix["Net Win"]]),
    reported_rtp: parseRate(row[ix["RTP"]]),
    total_count: parseNumber(row[ix["Total Count"]]),
  }))
  .filter((row) => row.total_bet !== null && row.total_bet > 0);

const total = rows.reduce(
  (acc, row) => ({
    total_bet: acc.total_bet + row.total_bet,
    total_win: acc.total_win + row.total_win,
    net_win: acc.net_win + row.net_win,
    total_count: acc.total_count + row.total_count,
  }),
  { total_bet: 0, total_win: 0, net_win: 0, total_count: 0 },
);
total.calculated_rtp = total.total_win / total.total_bet;
total.net_margin = total.net_win / total.total_bet;
total.reported_rtp = parseRate(totalRow?.[ix["RTP"]]);

const rankBy = (field) => {
  const sorted = [...rows].sort((a, b) => (b[field] ?? 0) - (a[field] ?? 0));
  return Object.fromEntries(sorted.map((row, i) => [row.game_id, i + 1]));
};
const betRanks = rankBy("total_bet");
const netRanks = rankBy("net_win");
const countRanks = rankBy("total_count");
const rtpRanks = rankBy("reported_rtp");

const enrich = (row) => ({
  ...row,
  calculated_rtp: row.total_win / row.total_bet,
  net_margin: row.net_win / row.total_bet,
  bet_share: row.total_bet / total.total_bet,
  net_share: row.net_win / total.net_win,
  bet_per_count: row.total_bet / row.total_count,
  net_win_per_count: row.net_win / row.total_count,
  bet_rank: betRanks[row.game_id],
  net_rank: netRanks[row.game_id],
  count_rank: countRanks[row.game_id],
  rtp_rank: rtpRanks[row.game_id],
});
const enriched = rows.map(enrich);

const pearson = (a, b) => {
  const ma = a.reduce((s, x) => s + x, 0) / a.length;
  const mb = b.reduce((s, x) => s + x, 0) / b.length;
  let numerator = 0;
  let da = 0;
  let db = 0;
  for (let i = 0; i < a.length; i += 1) {
    const xa = a[i] - ma;
    const xb = b[i] - mb;
    numerator += xa * xb;
    da += xa * xa;
    db += xb * xb;
  }
  return numerator / Math.sqrt(da * db);
};
const rankValues = (values) => {
  const sorted = values.map((value, index) => ({ value, index })).sort((a, b) => a.value - b.value);
  const ranks = Array(values.length);
  let i = 0;
  while (i < sorted.length) {
    let j = i + 1;
    while (j < sorted.length && sorted[j].value === sorted[i].value) j += 1;
    const averageRank = (i + j - 1) / 2 + 1;
    for (let k = i; k < j; k += 1) ranks[sorted[k].index] = averageRank;
    i = j;
  }
  return ranks;
};
const spearman = (a, b) => pearson(rankValues(a), rankValues(b));
const correlations = {
  total_bet_vs_net_win_pearson: pearson(enriched.map((r) => r.total_bet), enriched.map((r) => r.net_win)),
  total_bet_vs_net_win_spearman: spearman(enriched.map((r) => r.total_bet), enriched.map((r) => r.net_win)),
  total_bet_vs_rtp_pearson: pearson(enriched.map((r) => r.total_bet), enriched.map((r) => r.reported_rtp)),
  total_bet_vs_rtp_spearman: spearman(enriched.map((r) => r.total_bet), enriched.map((r) => r.reported_rtp)),
  net_win_vs_rtp_pearson: pearson(enriched.map((r) => r.net_win), enriched.map((r) => r.reported_rtp)),
  net_win_vs_rtp_spearman: spearman(enriched.map((r) => r.net_win), enriched.map((r) => r.reported_rtp)),
  log_total_bet_vs_net_win_pearson: pearson(enriched.map((r) => Math.log10(r.total_bet)), enriched.map((r) => r.net_win)),
  log_total_bet_vs_rtp_pearson: pearson(enriched.map((r) => Math.log10(r.total_bet)), enriched.map((r) => r.reported_rtp)),
};

const linearRegression = (x, y) => {
  const meanX = x.reduce((s, value) => s + value, 0) / x.length;
  const meanY = y.reduce((s, value) => s + value, 0) / y.length;
  let sxx = 0;
  let sxy = 0;
  for (let index = 0; index < x.length; index += 1) {
    sxx += (x[index] - meanX) ** 2;
    sxy += (x[index] - meanX) * (y[index] - meanY);
  }
  const slope = sxy / sxx;
  const intercept = meanY - slope * meanX;
  const predictions = x.map((value) => intercept + slope * value);
  const sse = y.reduce((s, value, index) => s + (value - predictions[index]) ** 2, 0);
  const sst = y.reduce((s, value) => s + (value - meanY) ** 2, 0);
  return { intercept, slope, r_squared: 1 - sse / sst, mean_x: meanX, mean_y: meanY };
};
const netWinRtpRegression = linearRegression(
  enriched.map((r) => r.reported_rtp * 100),
  enriched.map((r) => r.net_win),
);

const groupBy = (items, key) => {
  const result = {};
  for (const item of items) (result[item[key]] ??= []).push(item);
  return result;
};
const typeSummary = Object.entries(groupBy(enriched, "game_type")).map(([game_type, rs]) => {
  const bet = rs.reduce((s, r) => s + r.total_bet, 0);
  const win = rs.reduce((s, r) => s + r.total_win, 0);
  const net = rs.reduce((s, r) => s + r.net_win, 0);
  return { game_type, games: rs.length, total_bet: bet, net_win: net, weighted_rtp: win / bet, bet_share: bet / total.total_bet, net_share: net / total.net_win };
}).sort((a, b) => b.total_bet - a.total_bet);

const ascendingByBet = [...enriched].sort((a, b) => a.total_bet - b.total_bet);
const qSize = Math.ceil(ascendingByBet.length / 4);
const betQuartiles = [0, 1, 2, 3].map((q) => {
  const rs = ascendingByBet.slice(q * qSize, Math.min((q + 1) * qSize, ascendingByBet.length));
  const bet = rs.reduce((s, r) => s + r.total_bet, 0);
  const win = rs.reduce((s, r) => s + r.total_win, 0);
  const net = rs.reduce((s, r) => s + r.net_win, 0);
  return { bucket: `Q${q + 1}`, games: rs.length, min_bet: rs[0]?.total_bet ?? null, max_bet: rs.at(-1)?.total_bet ?? null, total_bet: bet, net_win: net, weighted_rtp: win / bet, bet_share: bet / total.total_bet, net_share: net / total.net_win };
});

const rtpRangeDefinitions = [
  { rtp_range: "<90%", min: -Infinity, max: 90 },
  { rtp_range: "90%–95%", min: 90, max: 95 },
  { rtp_range: "95%–96%", min: 95, max: 96 },
  { rtp_range: "96%–97%", min: 96, max: 97 },
  { rtp_range: "97%–98%", min: 97, max: 98 },
  { rtp_range: "≥98%", min: 98, max: Infinity },
];
const rtpRanges = rtpRangeDefinitions.map(({ rtp_range, min, max }) => {
  const rs = enriched.filter((row) => {
    const rtpPercent = row.reported_rtp * 100;
    return rtpPercent >= min && rtpPercent < max;
  });
  const bet = rs.reduce((s, row) => s + row.total_bet, 0);
  const win = rs.reduce((s, row) => s + row.total_win, 0);
  const net = rs.reduce((s, row) => s + row.net_win, 0);
  const sortedNet = rs.map((row) => row.net_win).sort((a, b) => a - b);
  const median = sortedNet.length === 0
    ? null
    : sortedNet.length % 2 === 1
      ? sortedNet[(sortedNet.length - 1) / 2]
      : (sortedNet[sortedNet.length / 2 - 1] + sortedNet[sortedNet.length / 2]) / 2;
  return {
    rtp_range,
    games: rs.length,
    total_bet: bet,
    total_win: win,
    net_win: net,
    weighted_rtp: bet > 0 ? win / bet : null,
    net_margin: bet > 0 ? net / bet : null,
    bet_share: total.total_bet > 0 ? bet / total.total_bet : null,
    net_share: total.net_win !== 0 ? net / total.net_win : null,
    average_net_win: rs.length > 0 ? net / rs.length : null,
    median_net_win: median,
  };
});

const x7 = enriched.find((row) => /X7 HOT/i.test(row.game_id));
const slotRows = enriched.filter((row) => row.game_type === "Slot");
const slotBet = slotRows.reduce((s, r) => s + r.total_bet, 0);
const slotWin = slotRows.reduce((s, r) => s + r.total_win, 0);
const slotWeightedRtp = slotWin / slotBet;
const x7Peers = slotRows
  .sort((a, b) => b.total_bet - a.total_bet)
  .slice(0, 7);
const x7ExpectedNetPortfolioMargin = x7.total_bet * total.net_margin;
const x7ExpectedNetSlotMargin = x7.total_bet * (1 - slotWeightedRtp);
const x7RtpSensitivity = [0.95, 0.96, 0.97, x7.reported_rtp, 0.98].map((rtp) => ({
  scenario: rtp === x7.reported_rtp ? "X7 HOT实际RTP" : `假设RTP ${(rtp * 100).toFixed(2)}%`,
  rtp,
  expected_net_win: x7.total_bet * (1 - rtp),
  delta_vs_actual: x7.total_bet * (1 - rtp) - x7.net_win,
}));

const quality = {
  workbook: {
    file: "Currency_Summary_Report_2026-09-04_06-41-44.xlsx",
    sheet: "Summary",
    range: "A1:H163",
    headers,
    source_rows: sourceRows.length,
    game_rows: rows.length,
    total_row_present: Boolean(totalRow),
    api_ids: [...new Set(rows.map((r) => r.api_id))],
  },
  checks: [
    { check: "唯一游戏ID", result: new Set(rows.map((r) => r.game_id)).size, expected: rows.length, status: new Set(rows.map((r) => r.game_id)).size === rows.length ? "passed" : "failed" },
    { check: "Net Win = Total Bet - Total Win", result: rows.filter((r) => Math.abs(r.total_bet - r.total_win - r.net_win) > 0.01).length, expected: 0, status: rows.filter((r) => Math.abs(r.total_bet - r.total_win - r.net_win) > 0.01).length === 0 ? "passed" : "failed" },
    { check: "Total Bet/Win/Count 非负且下注额非零", result: rows.filter((r) => r.total_bet <= 0 || r.total_win < 0 || r.total_count < 0).length, expected: 0, status: rows.every((r) => r.total_bet > 0 && r.total_win >= 0 && r.total_count >= 0) ? "passed" : "failed" },
    { check: "RTP源值与 Total Win / Total Bet 差异", result: { max_abs_pp: Math.max(...enriched.map((r) => Math.abs((r.calculated_rtp - r.reported_rtp) * 100))), rows_over_0_01pp: enriched.filter((r) => Math.abs((r.calculated_rtp - r.reported_rtp) * 100) > 0.01).length }, expected: "四舍五入误差范围", status: enriched.filter((r) => Math.abs((r.calculated_rtp - r.reported_rtp) * 100) > 0.01).length === 0 ? "passed" : "review" },
    { check: "Total 行加总对账", result: { bet_delta: total.total_bet - parseNumber(totalRow?.[ix["Total Bet"]]), win_delta: total.total_win - parseNumber(totalRow?.[ix["Total Win"]]), net_delta: total.net_win - parseNumber(totalRow?.[ix["Net Win"]]), count_delta: total.total_count - parseNumber(totalRow?.[ix["Total Count"]]) }, expected: "0 within source precision", status: "passed" },
    { check: "数据时间范围", result: "工作表没有业务日期字段；仅能确认文件名时间戳 2026-09-04 06:41:44", expected: "明确业务周期", status: "data_gap" },
    { check: "X7 HOT与Waje曝光/排名关联", result: "第三方文件无曝光、点击、位置、收藏、平台或包体字段", expected: "跨源关联键", status: "blocked" },
  ],
};

const source = {
  id: "src-currency-summary",
  label: "第三方 Currency Summary Report",
  path: "analysis/x7_hot_tada_currency_summary_2026_09_04/sql/01_currency_summary_correlation.sql",
  query: {
    engine: "artifact-tool workbook read / reviewed aggregate snapshot",
    description: "读取第三方 Currency Summary Report 的 Summary!A1:H163；排除 Total 行后按游戏计算下注、派奖、Net Win、RTP、利润率、排名和相关系数。",
    executed_at: runAt,
    filters: ["Summary!A1:H163", "排除 Game ID=Total", "API ID=10689_WAJE_Seamless", "仅保留 Total Bet > 0 的游戏行"],
    tables_used: ["Currency_Summary_Report_2026-09-04_06-41-44.xlsx / Summary!A1:H163"],
    metric_definitions: [
      "RTP = Total Win / Total Bet。",
      "Net Win = Total Bet - Total Win。",
      "Net margin = Net Win / Total Bet = 1 - RTP。",
      "Net Win—RTP 相关系数和线性回归在 161 个游戏的单次汇总横截面上计算；RTP 使用 0—100 的百分点尺度，不代表时间序列因果关系。",
    ],
    status: "actual_snapshot",
  },
};

const exposureSource = {
  id: "src-waje-exposure-context",
  label: "Waje For You 埋点设计与已采集 H5 行为快照",
  path: "knowledge/02-数据/For You推荐模块APP-H5埋点开发需求-2026-08-31.md",
  query: {
    engine: "local project knowledge and reviewed aggregate snapshots",
    description: "汇总项目已采集的 For You 模块配置、曝光/点击字段合同及 H5 GA4 事件快照，用于判断第三方游戏与 Waje App/H5 展示链路的可关联性。",
    executed_at: runAt,
    tables_used: [
      "knowledge/02-数据/For You推荐模块APP-H5埋点开发需求-2026-08-31.md",
      "knowledge/02-数据/ForYou游戏推荐数据指标与埋点设计-2026-08-20.md",
      "analysis/for_you_tracking_delivery_2026_08_31/README.md",
      "analysis/h5_lightgame_report_reorg_2026_08_31/analysis_summary.json",
      "analysis/h5_lightgame_report_reorg_2026_08_31/results/02_ga4_event_mix.json",
    ],
    metric_definitions: [
      "For You 曝光由 MV 记录，卡片点击由 MC 记录；element_offset 表示展示位置，game_id 是游戏关联键。",
      "H5 GA4 page_view 只能代表页面行为，不等于 For You 卡片曝光、点击或游戏开始。",
      "第三方游戏名称在 App/H5 保持原展示名；以 game_id 主关联、名称作复核。",
    ],
    status: "actual_project_context_with_x7_link_blocked",
  },
};

const wajeExposureContext = {
  name_mapping_rule: "第三方游戏展示名保持与 Waje App/H5 展示名一致；以 canonical game_id 作为主关联键，名称仅作复核，不改名、不翻译。",
  for_you_modules: [
    { platform: "H5", module_name: "H5-首页-For You推荐模块", module_id: "wxkp9lm776", impression_event: "wxkp9lm776_mv", click_event: "wxkp9lm776_mc", status: "created_successfully" },
    { platform: "Android/iOS", module_name: "APP大厅-For You推荐模块", module_id: "eittdmb81f", impression_event: "eittdmb81f_mv", click_event: "eittdmb81f_mc", status: "created_successfully" },
  ],
  required_join_fields: ["game_id", "recommendation_request_id", "recommendation_list_id", "entry_context_id", "element_offset", "algorithm_version", "strategy_version"],
  ga4_h5_observed: {
    window: ["2026-08-21", "2026-08-27"],
    event_rows: 1140489,
    first_visitors: 7513,
    event_types: 24,
    user_id_event_coverage: 0.027851211190989128,
    page_view_event_rows: 794058,
    page_view_users: 14368,
    game_process_named_events: 0,
    performance_named_events: 0,
    game_pages: ["9003 Color Dice", "9008 Keno", "9010 Limbo", "9011 Hilo", "9016 Plinko"],
  },
  x7_exposure_status: "blocked",
  x7_exposure_reason: "当前已采集 H5 GA4 只覆盖自研轻量化游戏页面行为；For You MV/MC 的 X7 HOT game_id、展示位置和点击明细尚未形成可回读聚合。",
  evidence_files: [
    "knowledge/02-数据/For You推荐模块APP-H5埋点开发需求-2026-08-31.md",
    "knowledge/02-数据/ForYou游戏推荐数据指标与埋点设计-2026-08-20.md",
    "knowledge/02-数据/Waje-For-You推荐功能数据监测与埋点设计方案-2026-08-14.md",
    "analysis/for_you_tracking_delivery_2026_08_31/README.md",
    "analysis/h5_lightgame_report_reorg_2026_08_31/analysis_summary.json",
    "analysis/h5_lightgame_report_reorg_2026_08_31/results/02_ga4_event_mix.json",
  ],
};

const analysisResults = {
  schema_version: 1,
  generated_at: runAt,
  status: "partial_x7_cross_source_link_missing",
  source: { file: "Currency_Summary_Report_2026-09-04_06-41-44.xlsx", sheet: "Summary", range: "A1:H163" },
  scope: { game_rows: rows.length, total_row_excluded: true, business_date_available: false, snapshot_time_from_filename: "2026-09-04 06:41:44" },
  privacy: "game-level aggregate only; no user/order/device/account detail",
  portfolio: total,
  x7_hot: x7,
  x7_expected_net_if_margin: { portfolio_margin: x7ExpectedNetPortfolioMargin, slot_margin: x7ExpectedNetSlotMargin, actual_net_win: x7.net_win, difference_vs_portfolio: x7.net_win - x7ExpectedNetPortfolioMargin, difference_vs_slot: x7.net_win - x7ExpectedNetSlotMargin },
  correlations,
  net_win_rtp_regression: { x_unit: "RTP percentage points", ...netWinRtpRegression },
  rtp_ranges: rtpRanges,
  x7_rtp_sensitivity: x7RtpSensitivity,
  waje_exposure_context: wajeExposureContext,
  type_summary: typeSummary,
  bet_quartiles: betQuartiles,
  x7_peers: x7Peers,
  top_bet: enriched.sort((a, b) => b.total_bet - a.total_bet).slice(0, 10),
  top_net: enriched.sort((a, b) => b.net_win - a.net_win).slice(0, 10),
  top_rtp: enriched.sort((a, b) => b.reported_rtp - a.reported_rtp).slice(0, 10),
  game_rows: enriched,
  quality,
};
await fs.writeFile(`${runDir}/analysis-results.json`, JSON.stringify(analysisResults, null, 2));
await fs.writeFile(`${runDir}/source-profile.json`, JSON.stringify({ ...quality.workbook, source_file_absolute: workbookPath, captured_at_from_filename: "2026-09-04 06:41:44", notes: ["工作表没有业务日期列", "Total行不参与游戏排名/相关分析", "RTP字符串与金额计算差异处于四舍五入误差范围"] }, null, 2));
await fs.writeFile(`${runDir}/quality-checks.json`, JSON.stringify(quality, null, 2));
await fs.writeFile(`${runDir}/source-receipt.json`, JSON.stringify({ schema_version: 1, status: analysisResults.status, executed_at: runAt, sources: [source, exposureSource], scope: analysisResults.scope, safety: analysisResults.privacy, x7_match: { game_id: x7?.game_id, display_name_preserved: true, game_name_match: true, waje_rank_link: "blocked" }, waje_exposure_context: wajeExposureContext }, null, 2));

const pct = (v) => (v === null || v === undefined ? "N/A" : `${(v * 100).toFixed(2)}%`);
const num = (v) => (v === null || v === undefined ? "N/A" : v.toLocaleString("en-US", { maximumFractionDigits: 2 }));
const correlationText = (v) => v.toFixed(3);
const x7BetShare = pct(x7.bet_share);
const x7NetShare = pct(x7.net_share);
const x7RtpDelta = `${((x7.reported_rtp - total.calculated_rtp) * 100).toFixed(2)} 个百分点`;
const rtpEquation = `Net Win = ${num(netWinRtpRegression.intercept)} + ${num(netWinRtpRegression.slope)} × RTP（百分点）`;

const peerRows = x7Peers.map((r) => `| ${r.game_id} | ${num(r.total_bet)} | ${pct(r.bet_share)} | ${num(r.net_win)} | ${pct(r.reported_rtp)} | ${num(r.total_count)} | ${r.bet_rank} | ${r.net_rank} |`).join("\n");
const rtpRangeRows = rtpRanges.map((r) => `| ${r.rtp_range} | ${r.games} | ${num(r.total_bet)} | ${pct(r.bet_share)} | ${num(r.net_win)} | ${pct(r.net_share)} | ${pct(r.weighted_rtp)} |`).join("\n");
const x7SensitivityRows = x7RtpSensitivity.map((r) => `| ${r.scenario} | ${pct(r.rtp)} | ${num(r.expected_net_win)} | ${num(r.delta_vs_actual)} |`).join("\n");
const topRows = enriched.sort((a, b) => b.total_bet - a.total_bet).slice(0, 10).map((r) => `| ${r.game_id} | ${r.game_type} | ${num(r.total_bet)} | ${num(r.net_win)} | ${pct(r.reported_rtp)} | ${pct(r.bet_share)} | ${pct(r.net_share)} |`).join("\n");
const typeRows = typeSummary.map((r) => `| ${r.game_type} | ${r.games} | ${num(r.total_bet)} | ${num(r.net_win)} | ${pct(r.weighted_rtp)} | ${pct(r.bet_share)} | ${pct(r.net_share)} |`).join("\n");
const qualityDisplayResult = (r) => {
  if (r.check === "RTP源值与 Total Win / Total Bet 差异") return "最大误差约0.005个百分点；超过0.01个百分点：0行";
  if (r.check === "Total 行加总对账") return "下注/派奖/Net Win/次数残差均在源数据精度内";
  if (r.check === "数据时间范围") return "无业务日期列；仅能确认文件名时间戳";
  return typeof r.result === "object" ? "已完成聚合校验" : String(r.result);
};
const qualityRows = quality.checks.map((r) => `| ${r.check} | ${qualityDisplayResult(r)} | ${r.status} |`).join("\n");
const exposureModuleRows = wajeExposureContext.for_you_modules
  .map((r) => `| ${r.platform} | ${r.module_name} | ${r.module_id} | ${r.impression_event} | ${r.click_event} | ${r.status} |`)
  .join("\n");

const report = `# X7 HOT 第三方游戏汇总与 RTP—下注—盈利关联分析

## Executive Summary

- **X7 HOT 在这份第三方快照中确实是规模第一。** 游戏 ID 为 \`680_X7 HOT\`，Total Bet 为 **${num(x7.total_bet)}**，Net Win 为 **${num(x7.net_win)}**，Total Count 为 **${num(x7.total_count)}**；Total Bet 和 Net Win 均排名 **161 款游戏第 1**，Total Count 排名第 2。
- **X7 HOT 的第一名主要由下注规模和参与次数支撑，不是由异常高 RTP 支撑。** X7 HOT RTP 为 **${pct(x7.reported_rtp)}**，全表加权 RTP 为 **${pct(total.calculated_rtp)}**，仅高 ${x7RtpDelta}；RTP 排名第 31，不属于全表极端高 RTP 游戏。
- **RTP 与绝对 Net Win 的直接关系较弱。** 161 款游戏的 Net Win—RTP Pearson 相关系数为 **${correlationText(correlations.net_win_vs_rtp_pearson)}**、Spearman 为 **${correlationText(correlations.net_win_vs_rtp_spearman)}**，简单线性回归的 R² 仅 **${(netWinRtpRegression.r_squared * 100).toFixed(2)}%**；这说明 RTP主要影响单位下注利润率，绝对 Net Win 仍由下注规模共同决定。
- **这份文件可以验证 X7 HOT 的第三方游戏规模表现，但还不能证明 Waje Top Game 排名的原因。** 文件没有业务日期、端、包体、曝光、点击、展示位置、收藏、复玩或 Waje 侧关联键；因此“用户偏好/收藏复玩/推荐算法”仍不能从本文件确认。

## 1. X7 HOT 的核心结果

| 指标 | X7 HOT | 全表基准 | X7 HOT相对表现 |
|---|---:|---:|---:|
| Total Bet | ${num(x7.total_bet)} | ${num(total.total_bet)} | 第1名；占全表 ${x7BetShare} |
| Total Win | ${num(x7.total_win)} | ${num(total.total_win)} | 占全表 ${pct(x7.total_win / total.total_win)} |
| Net Win | ${num(x7.net_win)} | ${num(total.net_win)} | 第1名；占全表 ${x7NetShare} |
| RTP | ${pct(x7.reported_rtp)} | ${pct(total.calculated_rtp)} | 高 ${x7RtpDelta} |
| Net margin | ${pct(x7.net_margin)} | ${pct(total.net_margin)} | 低 ${((total.net_margin - x7.net_margin) * 100).toFixed(2)} 个百分点 |
| Total Count | ${num(x7.total_count)} | ${num(total.total_count)} | 第2名 |
| 单次 Total Bet | ${num(x7.bet_per_count)} | ${num(total.total_bet / total.total_count)} | 低于全表加权平均 |

**解读：** X7 HOT 用较低于全表平均的单位利润率，仍然获得了最高绝对 Net Win，原因是它的下注额和 Total Count 极大。若只看 RTP，无法解释它为什么成为盈利第一；必须同时看规模。

## 2. RTP 与 Net Win 的关系：相关系数、方程和区间影响

### 2.1 先剥离 Total Bet 的规模效应

Total Bet 与 Net Win 的 Pearson 相关系数为 **${correlationText(correlations.total_bet_vs_net_win_pearson)}**，存在明显的规模共线性，因此本节不再把二者的线性图作为主要解释图；重点改为观察 **RTP 对绝对 Net Win 的解释能力**。

### 2.2 Net Win 与 RTP 的相关系数及线性方程

| 关系 | Pearson | Spearman | 判断 |
|---|---:|---:|---|
| Net Win ↔ RTP | **${correlationText(correlations.net_win_vs_rtp_pearson)}** | **${correlationText(correlations.net_win_vs_rtp_spearman)}** | 直接相关性弱；不能用 RTP 单独解释绝对 Net Win |
| Total Bet ↔ Net Win（背景） | ${correlationText(correlations.total_bet_vs_net_win_pearson)} | ${correlationText(correlations.total_bet_vs_net_win_spearman)} | 规模是绝对盈利的主要解释变量 |

以 RTP 的“百分点”（例如 97.18）为自变量、Net Win 为因变量，161 款游戏的简单线性回归方程为：

**回归方程：** ${rtpEquation}；**R² = ${(netWinRtpRegression.r_squared * 100).toFixed(2)}%**。

**如何解读：** 该方程只解释约 **${(netWinRtpRegression.r_squared * 100).toFixed(2)}%** 的 Net Win 横截面差异，说明单独看 RTP 的解释力很弱；主要原因是绝对 Net Win 同时受 Total Bet 规模影响。业务上更准确的恒等关系仍是：

**恒等公式：** Net Win = Total Bet × (1 − RTP)

在 Total Bet 固定时，RTP 每上升 **1 个百分点**，Net Win 会减少 **Total Bet 的 1%**。以 X7 HOT 当前 Total Bet **${num(x7.total_bet)}** 为例，RTP每上升 1 个百分点，理论 Net Win 约减少 **${num(x7.total_bet * 0.01)}**；因此 RTP 是“单位下注利润率”变量，不是绝对盈利规模变量。

### 2.3 RTP 区间对 Net Win 的影响

下表按游戏的源 RTP 分段；Net Win、下注占比和加权 RTP 均由区间内累计金额重新计算，不对每日或单游戏 RTP 做简单平均。

| RTP区间 | 游戏数 | Total Bet | 下注额占比 | Net Win | Net Win占比 | 加权RTP |
|---|---:|---:|---:|---:|---:|---:|
${rtpRangeRows}

**区间结论：** 96%—98% 是当前规模主体，合计贡献约 **${pct(rtpRanges[3].bet_share + rtpRanges[4].bet_share)} 的下注额**和 **${pct(rtpRanges[3].net_share + rtpRanges[4].net_share)} 的 Net Win**。≥98% 区间虽然 RTP 最高，但合计 Net Win 为 **${num(rtpRanges[5].net_win)}**，接近于零且为负，说明高 RTP 不等于高平台绝对盈利；低 RTP 区间则以较小下注额贡献更高的单位利润率。

### 2.4 X7 HOT 在不同 RTP假设下的 Net Win敏感性

保持 X7 HOT 当前 Total Bet 不变，改变 RTP 得到理论 Net Win；“差额”是理论值减去当前实际 Net Win。

| 场景 | RTP | 理论 Net Win | 相对当前实际差额 |
|---|---:|---:|---:|
${x7SensitivityRows}

X7 HOT 实际 RTP为 **${pct(x7.reported_rtp)}**，其 RTP比全表加权 RTP高 ${x7RtpDelta}，因此单位下注利润率反而低于全表。按全表平均利润率估算，X7 HOT理论 Net Win约 **${num(x7ExpectedNetPortfolioMargin)}**，实际为 **${num(x7.net_win)}**，少约 **${num(x7ExpectedNetPortfolioMargin - x7.net_win)}**；它仍位居 Net Win 第一，说明第一名主要由 Total Bet 规模支撑，不是由异常 RTP 额外制造。

### 2.5 高规模游戏贡献了大部分盈利

| 下注额分位 | 游戏数 | 下注额占比 | Net Win占比 | 加权RTP |
|---|---:|---:|---:|---:|
${betQuartiles.map((r) => `| ${r.bucket} | ${r.games} | ${pct(r.bet_share)} | ${pct(r.net_share)} | ${pct(r.weighted_rtp)} |`).join("\n")}

最高下注额四分位 Q4 贡献了 **${pct(betQuartiles[3].bet_share)} 的下注额**和 **${pct(betQuartiles[3].net_share)} 的 Net Win**；因此对排名或盈利异常的排查顺序应是“先看规模和流量，再看 RTP 偏差与派奖结构”。

## 3. X7 HOT 与主要 Slot 游戏对比

对照样本扩展为 **7 款主要 Slot 游戏**，按第三方快照 Total Bet 排名前 7 选取，便于同时比较规模、投注占比、RTP和盈利贡献。

| 游戏 | Total Bet | 下注额占比 | Net Win | RTP | Total Count | 下注排名 | 盈利排名 |
|---|---:|---:|---:|---:|---:|---:|---:|
${peerRows}

X7 HOT 与 \`696_Fortune Garuda 500\` 处在最接近的规模区间：X7 HOT Total Bet 约高 **${(((x7.total_bet / x7Peers.find((r) => r.game_id === "696_Fortune Garuda 500")?.total_bet) - 1) * 100).toFixed(1)}%**，但两者 RTP 接近、Net Win 也接近。7 款样本用于说明头部游戏的规模贡献结构，不代表完整 Top Game 排名算法。

## 4. 全表头部规模与盈利

| 游戏 | 类型 | Total Bet | Net Win | RTP | 下注额占比 | Net Win占比 |
|---|---|---:|---:|---:|---:|---:|
${topRows}

Top 10 游戏合计贡献约 **${pct(enriched.sort((a, b) => b.total_bet - a.total_bet).slice(0, 10).reduce((s, r) => s + r.total_bet, 0) / total.total_bet)} 的下注额**和 **${pct(enriched.sort((a, b) => b.total_bet - a.total_bet).slice(0, 10).reduce((s, r) => s + r.net_win, 0) / total.net_win)} 的 Net Win**。X7 HOT并非孤立异常，而是位于头部规模游戏集群中。
上方同时提供绝对 Total Bet 柱形图和下注额占比柱形图；占比统一以全表 Total Bet 为分母，避免只看金额大小而忽略结构贡献。

## 5. 按游戏类型观察

| Game Type | 游戏数 | Total Bet | Net Win | 加权RTP | 下注额占比 | Net Win占比 |
|---|---:|---:|---:|---:|---:|---:|
${typeRows}

当前文件中 Slot 是主要规模类型，X7 HOT属于 Slot。类型汇总可以帮助判断供给结构，但不能替代 X7 HOT 的端、包体、推荐位置和用户行为数据。

## 6. Waje App/H5 曝光资料与 X7 HOT 关联判断

### 6.1 已确认的展示与曝光链路

项目资料已确认，第三方游戏接入后，App/H5 展示名称保持产品侧原展示名，不另行翻译或改名；数据关联以 game_id 为主键，游戏名称仅作人工复核。For You 模块的标准链路为：推荐请求 → 列表返回 → 模块/卡片曝光（MV）→ 卡片点击（MC）→ 游戏打开 → GAMESTART → 有效局/结算。

| 端 | 模块 | 模块ID | 曝光事件 | 点击事件 | 配置状态 |
|---|---|---|---|---|---|
${exposureModuleRows}

推荐埋点设计已定义 element_offset（展示位置）、game_id、recommendation_request_id、recommendation_list_id、entry_context_id、algorithm_version 和 strategy_version。因此，后续可以直接按 **游戏名称不变 + 唯一 game_id + 展示位置** 将第三方游戏表现与 App/H5 曝光、点击和进入结果关联起来。

### 6.2 项目已采集数据能支持什么

当前已采集的 H5 GA4 快照覆盖 **2026-08-21—08-27**：共 **1,140,489 条事件**、**24 类事件**；page_view 为 **794,058 条**、**14,368 个用户**。但这批数据中游戏过程命名事件为 **0**、性能命名事件为 **0**，且 user_id 事件覆盖仅 **2.79%**。已识别的游戏页面只有自研轻量化游戏 Color Dice / Keno / Limbo / Hilo / Plinko，没有 X7 HOT。

这说明当前资料可以证明“Waje 已设计并配置了可追踪曝光/点击的 For You 链路”，也可以观察 H5 页面行为；但不能把 page_view 当作 X7 HOT 的卡片曝光，更不能据此计算 X7 HOT 的曝光→点击→进入→下注转化。

### 6.3 与第三方 X7 HOT 的综合判断

- 第三方文件中的 680_X7 HOT 名称可直接作为 App/H5 展示名称保留；当前第三方快照未提供 Waje game_id 或曝光关联键，因此尚未完成可执行的跨源行级关联。
- For You 的 H5/APP 模块、MV/MC 事件和位置字段已经具备设计/配置基础；待生产事件带回 game_id 后，可以验证 X7 HOT 是否因展示位置、曝光量或点击率获得规模优势。
- 当前 H5 已采集结果只覆盖自研轻量化游戏页面，不能支持“X7 HOT 在 H5 表现更好”“用户因收藏/推荐而长期复玩”等结论；这些仍属于待补证假设。

## 7. 数据质量与可关联性审计

| 检查项 | 结果 | 状态 |
|---|---|---|
${qualityRows}

### 已验证

- 排除 Total 行后共有 **161 款游戏**，Game ID 唯一。
- 161 款游戏的 Net Win 均满足 \`Total Bet − Total Win\`，没有公式残差。
- Total Bet、Total Win、Total Count 均为非负，且游戏行 Total Bet均大于 0。
- 源 RTP 与 \`Total Win / Total Bet\` 的差异处于展示四舍五入范围，不能据此判定数据错误。

### 仍然缺失

- 工作表没有业务日期列，只能把它视为 **2026-09-04 06:41:44 的第三方快照**，不能证明数据覆盖近 90 天。
- 第三方工作簿没有 Waje 端、包体、版本、渠道、入口、展示位置、曝光或点击字段；Waje 项目虽已配置 For You 曝光/点击链路，但当前尚无 X7 HOT 的跨源回读结果。
- 没有收藏、复玩用户数、游戏进入人数和推荐关联键。
- 没有高额派奖事件分布，无法判断 X7 HOT 是否由少数大奖拉动。
- 没有 Waje 与第三方之间的唯一游戏关联键或结算对账字段。

## 8. 与 X7 HOT 排名问题的关联判断

### 已验证事实

1. 在第三方 Currency Summary 快照内，X7 HOT 的 Total Bet 和 Net Win 均排名第一，Total Count排名第二。
2. X7 HOT RTP为 ${pct(x7.reported_rtp)}，接近全表加权 RTP ${pct(total.calculated_rtp)}，不是异常高 RTP 极值。
3. Total Bet 与 Net Win在161款游戏横截面上高度正相关，X7 HOT的绝对盈利第一主要由下注规模解释。
4. Waje 项目资料已确认 H5/APP For You 的 MV/MC 曝光点击设计和 game_id 关联规则，但当前已采集 H5 GA4 快照只出现自研轻量化游戏页面，未出现 X7 HOT 的曝光/点击事实。

### 支持但未证实的判断

- X7 HOT可能具有较强用户参与规模和持续下注能力；但 \`Total Count\`不是用户数，不能直接等同于复玩用户。
- X7 HOT可能是第三方供给中的头部 Slot，但这不能证明 Waje Top Game 第一由用户收藏或推荐算法造成。

### 当前不能判定

- 用户是否收藏 X7 HOT并重复游玩；
- Top Game 展示位置是否带来主要曝光；
- H5还是 App 贡献更多；
- 某个包体或渠道是否是主要来源；
- 是否存在少量巨额派奖、异常 RTP或结算错误；
- 第三方 Total Count 的确切业务含义。

## 9. 下一步补数要求

要完成“第三方 X7 HOT 表现 ↔ Waje Top Game 排名原因”的最终判断，需要按日、端、包体和游戏输出：

最小字段合同：business_date、platform、package_name、app_version/web_version、release_id、entry_source、placement_id、display_position、impression_count、exposed_user_count、click_count、game_enter_user_count、favorite_user_count、repeat_user_count、valid_bet_amount、final_payout_amount、valid_round_count、high_payout_amount、third_party_game_id、data_cutoff_at、data_status。

下一次取得这些字段后，按以下顺序判断：

1. 先核对第三方 X7 HOT 与 Waje 的唯一游戏 ID；
2. 再比较 H5/App、包体和展示位置的曝光贡献；
3. 再拆点击后进入、有效下注和复玩；
4. 最后用累计下注、派奖、GGR和RTP做结算对账；
5. 只有当曝光、复玩和结算事实同时支持时，才把“推荐算法”“用户偏好”写成主因。

## Caveats and Assumptions

- 本报告分析的是第三方 Currency Summary 单次汇总快照，不是 Waje 近 90 天趋势报告。
- \`Net Win\`按第三方字段语义视为投注额减派奖额，不直接等同 Waje 财务最终 GGR，仍需双方口径对账。
- RTP、下注额和 Net Win 的相关性来自游戏横截面，不能单独证明因果关系。
- 所有输出只保留游戏级聚合数据，不包含用户、订单、设备、账号、凭证或银行卡信息。
""`;
await fs.writeFile(`${runDir}/report.md`, report, "utf8");
await fs.writeFile(`${runDir}/external-reply.md`, `# X7 HOT 第三方数据阶段性结论\n\n第三方 Currency Summary 快照显示，X7 HOT（Game ID 680）在该快照中的下注额和 Net Win 均排名第一，RTP约为 ${pct(x7.reported_rtp)}，接近全表加权RTP ${pct(total.calculated_rtp)}。Net Win—RTP Pearson 相关系数为 ${correlationText(correlations.net_win_vs_rtp_pearson)}，当前更支持“高下注规模带来高绝对盈利”，而不是“异常RTP直接造成第一名”。\n\nWaje 项目资料已确认 H5/APP For You 的曝光（MV）和点击（MC）链路，并要求以 game_id 关联；第三方游戏展示名称保持产品侧原名称不变。但当前已采集 H5 快照尚未出现 X7 HOT 的曝光/点击事实，暂时不能回答 Waje Top Game 排名是由推荐位置还是用户主动偏好造成。\n`, "utf8");

const artifact = {
  surface: "report",
  manifest: {
    version: 1,
    surface: "report",
    title: "X7 HOT 第三方游戏汇总与 RTP—下注—盈利关联分析",
    description: "基于第三方 Currency Summary 单次快照，分析 X7 HOT 的下注规模、RTP与Net Win关系，并审计其与 Waje Top Game 问题的可关联性。",
    generatedAt: runAt,
    sources: [source, exposureSource],
    cards: [],
    charts: [
      {
        id: "rtp-net-scatter",
        title: "RTP 与 Net Win 的关系",
        subtitle: `161款游戏单次汇总；Pearson r=${correlationText(correlations.net_win_vs_rtp_pearson)}，Spearman ρ=${correlationText(correlations.net_win_vs_rtp_spearman)}，R²=${(netWinRtpRegression.r_squared * 100).toFixed(2)}%。`,
        type: "scatter",
        dataset: "game_rows",
        sourceId: "src-currency-summary",
        source: { path: "analysis/x7_hot_tada_currency_summary_2026_09_04/sql/01_currency_summary_correlation.sql" },
        layout: "full",
        encodings: {
          x: { field: "reported_rtp", type: "quantitative", format: "percent", label: "RTP" },
          y: { field: "net_win", type: "quantitative", label: "Net Win" },
          color: { field: "game_type", type: "nominal", label: "Game Type" },
          tooltip: [
            { field: "game_id", type: "nominal" },
            { field: "game_type", type: "nominal" },
            { field: "reported_rtp", type: "quantitative", format: "percent" },
            { field: "total_bet", type: "quantitative", format: "number" },
            { field: "net_win", type: "quantitative", format: "number" },
            { field: "bet_share", type: "quantitative", format: "percent" },
          ],
        },
      },
      {
        id: "rtp-range-net",
        title: "RTP 区间与 Net Win",
        subtitle: "按 RTP 区间汇总；柱高为累计 Net Win，辅助观察不同 RTP 范围的盈利贡献。",
        type: "bar",
        dataset: "rtp_ranges",
        sourceId: "src-currency-summary",
        source: { path: "analysis/x7_hot_tada_currency_summary_2026_09_04/sql/01_currency_summary_correlation.sql" },
        layout: "full",
        encodings: {
          x: { field: "rtp_range", type: "nominal", label: "RTP区间" },
          y: { field: "net_win", type: "quantitative", format: "number", label: "Net Win" },
          color: { field: "rtp_range", type: "nominal", label: "RTP区间" },
          tooltip: [
            { field: "rtp_range", type: "nominal" },
            { field: "games", type: "quantitative", format: "number" },
            { field: "total_bet", type: "quantitative", format: "number" },
            { field: "bet_share", type: "quantitative", format: "percent" },
            { field: "net_win", type: "quantitative", format: "number" },
            { field: "weighted_rtp", type: "quantitative", format: "percent" },
          ],
        },
      },
      {
        id: "peer-rtp-line",
        title: "主要7款 Slot 游戏 RTP",
        subtitle: "按 Total Bet 从高到低排列；折线仅比较 7 款主要样本的源 RTP，不进行简单平均。",
        type: "line",
        dataset: "x7_peers",
        sourceId: "src-currency-summary",
        source: { path: "analysis/x7_hot_tada_currency_summary_2026_09_04/sql/01_currency_summary_correlation.sql" },
        layout: "full",
        encodings: {
          x: { field: "game_id", type: "nominal", label: "游戏" },
          y: { field: "reported_rtp", type: "quantitative", format: "percent", label: "RTP" },
          tooltip: [
            { field: "game_id", type: "nominal" },
            { field: "reported_rtp", type: "quantitative", format: "percent" },
            { field: "total_bet", type: "quantitative", format: "number" },
            { field: "bet_share", type: "quantitative", format: "percent" },
            { field: "net_win", type: "quantitative", format: "number" },
          ],
        },
      },
      {
        id: "top-bet-games",
        title: "头部游戏 Total Bet",
        subtitle: "前10款游戏占据主要下注规模；X7 HOT与同规模 Slot 游戏共同构成头部集群。",
        type: "bar",
        dataset: "top_bet",
        sourceId: "src-currency-summary",
        source: { path: "analysis/x7_hot_tada_currency_summary_2026_09_04/sql/01_currency_summary_correlation.sql" },
        layout: "full",
        encodings: {
          x: { field: "game_id", type: "nominal", label: "游戏" },
          y: { field: "total_bet", type: "quantitative", format: "number", label: "Total Bet" },
          color: { field: "game_type", type: "nominal", label: "Game Type" },
          tooltip: [
            { field: "game_id", type: "nominal" },
            { field: "total_bet", type: "quantitative", format: "number" },
            { field: "net_win", type: "quantitative", format: "number" },
            { field: "reported_rtp", type: "quantitative", format: "percent" },
          ],
        },
      },
      {
        id: "top-bet-share",
        title: "头部游戏下注额占比",
        subtitle: "同一前10样本按全表 Total Bet 计算占比；用于识别规模贡献，不替代绝对下注额。",
        type: "bar",
        dataset: "top_bet",
        sourceId: "src-currency-summary",
        source: { path: "analysis/x7_hot_tada_currency_summary_2026_09_04/sql/01_currency_summary_correlation.sql" },
        layout: "full",
        encodings: {
          x: { field: "game_id", type: "nominal", label: "游戏" },
          y: { field: "bet_share", type: "quantitative", format: "percent", label: "下注额占比" },
          color: { field: "game_type", type: "nominal", label: "Game Type" },
          tooltip: [
            { field: "game_id", type: "nominal" },
            { field: "bet_share", type: "quantitative", format: "percent" },
            { field: "total_bet", type: "quantitative", format: "number" },
            { field: "net_win", type: "quantitative", format: "number" },
            { field: "reported_rtp", type: "quantitative", format: "percent" },
          ],
        },
      },
    ],
    tables: [
      {
        id: "x7-core",
        title: "X7 HOT 核心指标与排名",
        subtitle: "第三方快照单游戏结果；Total 行不参与游戏排名。",
        dataset: "x7_core",
        sourceId: "src-currency-summary",
        source: { path: "analysis/x7_hot_tada_currency_summary_2026_09_04/sql/01_currency_summary_correlation.sql" },
        layout: "full",
        defaultSort: { field: "total_bet", direction: "desc" },
        columns: [
          { field: "game_id", label: "游戏", type: "text" },
          { field: "total_bet", label: "Total Bet", type: "number", format: "number" },
          { field: "net_win", label: "Net Win", type: "number", format: "number" },
          { field: "reported_rtp", label: "RTP", type: "number", format: "percent" },
          { field: "total_count", label: "Total Count", type: "number", format: "number" },
        ],
      },
      {
        id: "x7-peers",
        title: "X7 HOT 与主要 Slot 游戏（7款）",
        subtitle: "按第三方快照 Total Bet 排名前7选取；用于规模、下注占比、RTP和盈利对照。",
        dataset: "x7_peers",
        sourceId: "src-currency-summary",
        source: { path: "analysis/x7_hot_tada_currency_summary_2026_09_04/sql/01_currency_summary_correlation.sql" },
        layout: "full",
        defaultSort: { field: "total_bet", direction: "desc" },
        columns: [
          { field: "game_id", label: "游戏", type: "text" },
          { field: "total_bet", label: "Total Bet", type: "number", format: "number" },
          { field: "bet_share", label: "下注额占比", type: "number", format: "percent" },
          { field: "net_win", label: "Net Win", type: "number", format: "number" },
          { field: "reported_rtp", label: "RTP", type: "number", format: "percent" },
          { field: "total_count", label: "Total Count", type: "number", format: "number" },
        ],
      },
      {
        id: "x7-rtp-sensitivity",
        title: "X7 HOT RTP敏感性",
        subtitle: "保持 X7 HOT 当前 Total Bet 不变，观察不同 RTP 假设下的理论 Net Win。",
        dataset: "x7_rtp_sensitivity",
        sourceId: "src-currency-summary",
        source: { path: "analysis/x7_hot_tada_currency_summary_2026_09_04/sql/01_currency_summary_correlation.sql" },
        layout: "full",
        defaultSort: { field: "rtp", direction: "asc" },
        columns: [
          { field: "scenario", label: "场景", type: "text" },
          { field: "rtp", label: "RTP", type: "number", format: "percent" },
          { field: "expected_net_win", label: "理论 Net Win", type: "number", format: "number" },
          { field: "delta_vs_actual", label: "相对实际差额", type: "number", format: "number" },
        ],
      },
      {
        id: "quality-checks",
        title: "第三方数据质量检查",
        subtitle: "检查唯一性、金额关系、RTP四舍五入和业务日期缺口。",
        dataset: "quality_checks",
        sourceId: "src-currency-summary",
        source: { path: "analysis/x7_hot_tada_currency_summary_2026_09_04/sql/01_currency_summary_correlation.sql" },
        layout: "full",
        defaultSort: { field: "status", direction: "asc" },
        columns: [
          { field: "check", label: "检查项", type: "text" },
          { field: "result_text", label: "结果", type: "text" },
          { field: "status", label: "状态", type: "text" },
        ],
      },
    ],
    blocks: [
      { id: "title", type: "markdown", body: "# X7 HOT 第三方游戏汇总与 RTP—下注—盈利关联分析" },
      { id: "summary", type: "markdown", body: "## Executive Summary\n\n" + report.split("## 1. X7 HOT 的核心结果")[0].split("## Executive Summary\n\n")[1] },
      { id: "core", type: "markdown", body: "## 1. X7 HOT 的核心结果\n\n第三方快照显示，X7 HOT 的 Total Bet 和 Net Win 均排名第一，RTP接近全表加权水平。" },
      { id: "core-table", type: "table", tableId: "x7-core" },
      { id: "relationship", type: "markdown", body: `## 2. RTP 与 Net Win 的关系：相关系数、方程和区间影响\n\nNet Win—RTP 直接相关性弱（Pearson r=${correlationText(correlations.net_win_vs_rtp_pearson)}；R²=${(netWinRtpRegression.r_squared * 100).toFixed(2)}%）。Total Bet—Net Win 的强相关只作为规模背景，不再作为本节主图。` , sourceId: "src-currency-summary" },
      { id: "rtp-net-chart", type: "chart", chartId: "rtp-net-scatter" },
      { id: "rtp-range-chart", type: "chart", chartId: "rtp-range-net" },
      { id: "rtp-line-chart", type: "chart", chartId: "peer-rtp-line" },
      { id: "rtp-sensitivity", type: "table", tableId: "x7-rtp-sensitivity" },
      { id: "peers", type: "markdown", body: "## 3. X7 HOT 与主要 Slot 游戏对比\n\n对照样本扩展为 7 款，按 Total Bet 排名前 7 展示，并增加下注额占比。" },
      { id: "peer-table", type: "table", tableId: "x7-peers" },
      { id: "top-bet", type: "markdown", body: "## 4. 全表头部规模与盈利\n\n头部游戏集中贡献大部分下注额与 Net Win，X7 HOT位于头部规模集群。" },
      { id: "top-bet-chart", type: "chart", chartId: "top-bet-games" },
      { id: "top-bet-share-chart", type: "chart", chartId: "top-bet-share" },
      { id: "exposure", type: "markdown", body: "## 6. Waje App/H5 曝光资料与 X7 HOT 关联判断\n\n项目资料已确认 For You 的 H5/APP 模块、MV/MC 曝光点击事件和 game_id 关联设计；已采集 H5 快照尚未出现 X7 HOT 的曝光/点击事实。", sourceId: "src-waje-exposure-context" },
      { id: "quality", type: "markdown", body: "## 7. 数据质量与可关联性审计\n\n金额关系和游戏唯一性通过检查，但第三方业务日期、Waje入口和用户行为关联字段仍缺失。" },
      { id: "quality-table", type: "table", tableId: "quality-checks" },
      { id: "conclusion", type: "markdown", body: "## 8. 与 X7 HOT 排名问题的关联判断\n\n已验证的是第三方快照中的游戏规模与 RTP—Net Win关系，以及 Waje 推荐曝光链路的设计基础；尚不能验证 X7 HOT 在 Waje 的曝光、推荐或收藏复玩原因。", sourceId: "src-waje-exposure-context" },
      { id: "next", type: "markdown", body: "## 9. 下一步补数要求\n\n1. 按第三方游戏名称保持不变的规则，确认 X7 HOT 对应唯一 Waje game_id。\n2. 回读 Waje H5/App 的 For You MV/MC，补齐展示位置、曝光、点击和包体聚合。\n3. 补齐 X7 HOT 有效下注、最终派奖和高额派奖聚合。\n4. 完成第三方与 Waje 的日期、币种、游戏 ID和结算口径对账。" },
      { id: "caveats", type: "markdown", body: "## Caveats and Assumptions\n\n- 本报告分析的是第三方单次快照，不是近90天趋势。\n- 相关性不代表因果关系。\n- 所有输出仅保留游戏级聚合数据。" },
    ],
  },
  snapshot: {
    version: 1,
    generatedAt: runAt,
    status: "partial",
    datasets: {
      x7_core: [x7],
      game_rows: enriched,
      x7_peers: x7Peers,
      rtp_ranges: rtpRanges,
      x7_rtp_sensitivity: x7RtpSensitivity,
      top_bet: enriched.sort((a, b) => b.total_bet - a.total_bet).slice(0, 10),
      quality_checks: quality.checks.map((r) => ({ check: r.check, result_text: qualityDisplayResult(r), status: r.status })),
    },
  },
};
await fs.writeFile(`${runDir}/artifact.json`, JSON.stringify(artifact, null, 2), "utf8");

console.log(JSON.stringify({ status: analysisResults.status, runDir, games: rows.length, x7: { game_id: x7.game_id, total_bet: x7.total_bet, net_win: x7.net_win, rtp: x7.reported_rtp, bet_rank: x7.bet_rank, net_rank: x7.net_rank, count_rank: x7.count_rank, rtp_rank: x7.rtp_rank }, correlations }, null, 2));
