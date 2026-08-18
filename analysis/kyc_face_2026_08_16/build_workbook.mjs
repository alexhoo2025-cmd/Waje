import fs from "node:fs/promises";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const ROOT = "/Users/robin/Documents/wajetan_analyst";
const ANALYSIS_PATH = `${ROOT}/analysis/kyc_face_2026_08_16/analysis.json`;
const NORMALIZED_PATH = `${ROOT}/analysis/kyc_face_2026_08_16/normalized.csv`;
const OUTPUT_PATH = `${ROOT}/output/Waje-KYC人脸识别分析数据底表-2026-08-16.xlsx`;
const PREVIEW_DIR = "/tmp/waje_kyc_xlsx_20260817/previews";

const analysis = JSON.parse(await fs.readFile(ANALYSIS_PATH, "utf8"));
const csv = (await fs.readFile(NORMALIZED_PATH, "utf8")).replace(/^\uFEFF/, "").trimEnd();
const csvRows = csv.split(/\r?\n/).map((line) => line.split(","));
const headers = csvRows[0];
const rawRows = csvRows.slice(1).map((row) => row.map((v, i) => {
  if (i === 0) return new Date(`${v}T00:00:00`);
  if (i === 1 || i === 2 || i === 3) return v;
  return v === "" ? null : Number(v);
}));

const wb = Workbook.create();
const sheetNames = [
  "00_阅读说明", "01_核心结论", "02_认证漏斗", "03_BVN_NIN", "04_人脸失败与重试",
  "05_App_H5包体版本", "06_提现结果", "07_配置事件", "08_评论处理", "09_数据质量",
  "数据_标准化", "数据_计算", "数据_来源映射",
];
for (const name of sheetNames) wb.worksheets.add(name);

const C = {
  navy: "#16324F", blue: "#2F80C5", blue2: "#DCEEFE", sky: "#EFF8FF",
  green: "#42A67A", green2: "#E7F7EE", yellow: "#F3B82C", yellow2: "#FFF6D8",
  red: "#D85B5B", red2: "#FDECEC", text: "#18324A", muted: "#5A7187",
  line: "#CBDDEA", white: "#FFFFFF", panel: "#F7FBFD", gray: "#E9F0F5",
};

function baseSheet(sheet) {
  sheet.showGridLines = false;
  sheet.getRange("A1:Z200").format.font = { name: "Arial", size: 10, color: C.text };
}

function title(sheet, text, subtitle, endCol = "H") {
  sheet.getRange(`A1:${endCol}2`).merge();
  sheet.getRange("A1").values = [[text]];
  sheet.getRange(`A1:${endCol}2`).format = {
    fill: C.navy, font: { name: "Arial", size: 20, bold: true, color: C.white },
    verticalAlignment: "center", horizontalAlignment: "left",
  };
  sheet.getRange(`A3:${endCol}3`).merge();
  sheet.getRange("A3").values = [[subtitle]];
  sheet.getRange(`A3:${endCol}3`).format = {
    fill: C.sky, font: { name: "Arial", size: 10, color: C.muted },
    verticalAlignment: "center", wrapText: true,
  };
  sheet.getRange("A1:A3").format.rowHeight = 27;
}

function section(sheet, row, text, endCol = "H") {
  sheet.getRange(`A${row}:${endCol}${row}`).merge();
  sheet.getRange(`A${row}`).values = [[text]];
  sheet.getRange(`A${row}:${endCol}${row}`).format = {
    fill: C.blue2, font: { bold: true, size: 12, color: C.navy },
    verticalAlignment: "center",
  };
  sheet.getRange(`A${row}`).format.rowHeight = 24;
}

function headerStyle(range) {
  range.format = {
    fill: C.navy, font: { bold: true, color: C.white },
    horizontalAlignment: "center", verticalAlignment: "center", wrapText: true,
    borders: { preset: "inside", style: "thin", color: C.line },
  };
}

function bodyStyle(range) {
  range.format = {
    verticalAlignment: "center", wrapText: true,
    borders: { insideHorizontal: { style: "thin", color: C.line } },
  };
}

function addTable(sheet, rangeAddress, name) {
  const t = sheet.tables.add(rangeAddress, true, name);
  t.style = "TableStyleMedium2";
  t.showBandedColumns = false;
  t.showFilterButton = true;
  return t;
}

function pct(v, digits = 1) { return `${(v * 100).toFixed(digits)}%`; }
function pp(v, digits = 1) { return `${(v * 100).toFixed(digits)}pp`; }
function num(v) { return Math.round(v).toLocaleString("en-US"); }

// 数据_标准化
{
  const s = wb.worksheets.getItem("数据_标准化");
  baseSheet(s);
  s.getRangeByIndexes(0, 0, 1, headers.length).values = [headers];
  s.getRangeByIndexes(1, 0, rawRows.length, headers.length).values = rawRows;
  headerStyle(s.getRangeByIndexes(0, 0, 1, headers.length));
  bodyStyle(s.getRangeByIndexes(1, 0, rawRows.length, headers.length));
  s.getRange(`A2:A${rawRows.length + 1}`).format.numberFormat = "yyyy-mm-dd";
  s.getRange(`E2:AB${rawRows.length + 1}`).format.numberFormat = "#,##0";
  s.getRange("A:AB").format.columnWidth = 14;
  s.getRange("A:A").format.columnWidth = 12;
  s.getRange("B:D").format.columnWidth = 20;
  s.freezePanes.freezeRows(1);
  s.freezePanes.freezeColumns(4);
  addTable(s, `A1:AB${rawRows.length + 1}`, "NormalizedKycData");
}

// 数据_计算：所有比率均由计数公式计算；计数来自标准化数据的 SUMIFS。
{
  const s = wb.worksheets.getItem("数据_计算");
  baseSheet(s);
  title(s, "数据计算区", "只读计算区。汇总计数由“数据_标准化”按流程和端 SUMIFS；比率由计数公式生成。", "AE");
  const calcHeaders = [
    "流程", "端", "可观测触发/人群", "实际调用", "未调用", "请求人脸", "人脸请求次数", "最终成功", "最终失败", "无最终结果",
    "行动率", "到达人脸率", "成功/请求", "成功/已有结果", "无结果率", "端到端", "调用后成功",
    "BVN调用", "BVN通过", "BVN通过率", "NIN调用", "NIN通过", "NIN通过率", "人均请求次数",
    "人像不匹配", "请求接口失败", "三方错误", "当前保留原因", "人像不匹配占比", "接口失败占比", "说明"
  ];
  s.getRange("A5:AE5").values = [calcHeaders];
  headerStyle(s.getRange("A5:AE5"));
  const groups = [
    ["主动填写", "全部"], ["主动填写", "App"], ["主动填写", "H5"],
    ["提现触发", "全部"], ["提现触发", "App"], ["提现触发", "H5"],
  ];
  s.getRange("A6:B11").values = groups;
  const maxRow = rawRows.length + 1;
  function sumifs(col, row) {
    const base = `SUMIFS('数据_标准化'!$${col}$2:$${col}$${maxRow},'数据_标准化'!$B$2:$B$${maxRow},$A${row}`;
    return `=IF($B${row}="全部",${base}),${base},'数据_标准化'!$C$2:$C$${maxRow},$B${row}))`;
  }
  for (let row = 6; row <= 11; row++) {
    const actual = sumifs("E", row).slice(1);
    const notCalled = sumifs("K", row).slice(1);
    const sourceTrigger = sumifs("AB", row).slice(1);
    s.getRange(`C${row}`).formulas = [[`=IF($A${row}="主动填写",${actual}+${notCalled},${sourceTrigger})`]];
    s.getRange(`D${row}`).formulas = [[sumifs("E", row)]];
    s.getRange(`E${row}`).formulas = [[sumifs("K", row)]];
    s.getRange(`F${row}`).formulas = [[sumifs("P", row)]];
    s.getRange(`G${row}`).formulas = [[sumifs("Q", row)]];
    s.getRange(`H${row}`).formulas = [[sumifs("R", row)]];
    s.getRange(`I${row}`).formulas = [[sumifs("S", row)]];
    s.getRange(`J${row}`).formulas = [[`=F${row}-H${row}-I${row}`]];
    s.getRange(`K${row}:Q${row}`).formulas = [[
      `=IFERROR(D${row}/C${row},0)`, `=IFERROR(F${row}/D${row},0)`, `=IFERROR(H${row}/F${row},0)`,
      `=IFERROR(H${row}/(H${row}+I${row}),0)`, `=IFERROR(J${row}/F${row},0)`,
      `=IFERROR(H${row}/C${row},0)`, `=IFERROR(H${row}/D${row},0)`
    ]];
    s.getRange(`R${row}`).formulas = [[sumifs("F", row)]];
    s.getRange(`S${row}`).formulas = [[sumifs("L", row)]];
    s.getRange(`T${row}`).formulas = [[`=IFERROR(S${row}/R${row},0)`]];
    s.getRange(`U${row}`).formulas = [[sumifs("G", row)]];
    s.getRange(`V${row}`).formulas = [[sumifs("N", row)]];
    s.getRange(`W${row}`).formulas = [[`=IFERROR(V${row}/U${row},0)`]];
    s.getRange(`X${row}`).formulas = [[`=IFERROR(G${row}/F${row},0)`]];
    s.getRange(`Y${row}`).formulas = [[sumifs("U", row)]];
    s.getRange(`Z${row}`).formulas = [[sumifs("V", row)]];
    s.getRange(`AA${row}`).formulas = [[sumifs("W", row)]];
    s.getRange(`AB${row}`).formulas = [[`=SUM(Y${row}:AA${row})`]];
    s.getRange(`AC${row}:AD${row}`).formulas = [[`=IFERROR(Y${row}/AB${row},0)`, `=IFERROR(Z${row}/AB${row},0)`]];
    s.getRange(`AE${row}`).values = [[row <= 8 ? "主动填写的触发分母为“实际调用+未调用”的推算可观测人群" : "提现触发人数来自源表字段"]];
  }
  bodyStyle(s.getRange("A6:AE11"));
  s.getRange("C6:J11").format.numberFormat = "#,##0";
  s.getRange("K6:Q11").format.numberFormat = "0.0%";
  s.getRange("R6:S11").format.numberFormat = "#,##0";
  s.getRange("T6:T11").format.numberFormat = "0.0%";
  s.getRange("U6:V11").format.numberFormat = "#,##0";
  s.getRange("W6:W11").format.numberFormat = "0.0%";
  s.getRange("X6:X11").format.numberFormat = "0.00";
  s.getRange("Y6:AB11").format.numberFormat = "#,##0";
  s.getRange("AC6:AD11").format.numberFormat = "0.0%";
  s.getRange("A:AE").format.columnWidth = 13;
  s.getRange("A:B").format.columnWidth = 14;
  s.getRange("AE:AE").format.columnWidth = 42;
  s.freezePanes.freezeRows(5);
  s.freezePanes.freezeColumns(2);
  addTable(s, "A5:AE11", "KycCalcSummary");

  section(s, 14, "周趋势（提现触发；用户日）", "J");
  s.getRange("A15:J15").values = [["周期", "端", "触发", "实际调用", "请求人脸", "最终成功", "行动率", "到达人脸率", "成功/请求", "无结果率"]];
  headerStyle(s.getRange("A15:J15"));
  const weekRows = analysis.weekly.filter(x => x.flow === "提现触发").map(x => [
    x.period, x.platform, x.trigger, x.actual, x.face_request, x.face_success,
    x.action_rate, x.face_reach_rate, x.face_success_request_rate, x.face_unresolved_rate
  ]);
  s.getRangeByIndexes(15, 0, weekRows.length, 10).values = weekRows;
  bodyStyle(s.getRangeByIndexes(15, 0, weekRows.length, 10));
  s.getRange(`C16:F${15 + weekRows.length}`).format.numberFormat = "#,##0";
  s.getRange(`G16:J${15 + weekRows.length}`).format.numberFormat = "0.0%";
  addTable(s, `A15:J${15 + weekRows.length}`, "WeeklyKycSummary");
}

// 00 阅读说明
{
  const s = wb.worksheets.getItem("00_阅读说明");
  baseSheet(s);
  title(s, "Waje KYC／人脸识别分析数据底表", "统计期：2026-07-23 至 2026-08-16｜数据单位：用户日｜8月17日未完整日已排除", "J");
  section(s, 5, "先看这四点", "J");
  const notes = [
    ["1", "这不是25天唯一用户数", "源表为日期×包名日汇总；跨日同一用户会重复出现，因此区间汇总按“用户日”解释。"],
    ["2", "三种成功率必须分开", "端到端=人脸成功/风险触发；调用后成功=人脸成功/实际调用；已有结果成功=成功/(成功+失败)。"],
    ["3", "“无最终结果”不是纯放弃", "请求人脸后既无成功也无失败，可能包含退出、未完成、超时或在途；没有明细事件前不能全部命名为放弃。"],
    ["4", "当前数据止于人脸", "没有银行卡校验和最终提现结果，不能用“人脸成功”替代“提现成功”。"],
  ];
  s.getRange("A6:C9").values = notes;
  s.getRange("A6:A9").format = { fill: C.blue2, font: { bold: true, color: C.blue }, horizontalAlignment: "center" };
  s.getRange("B6:B9").format.font = { bold: true, color: C.navy };
  bodyStyle(s.getRange("A6:C9"));
  s.getRange("A:A").format.columnWidth = 7;
  s.getRange("B:B").format.columnWidth = 28;
  s.getRange("C:C").format.columnWidth = 75;

  section(s, 11, "工作表导航", "J");
  s.getRange("A12:C24").values = sheetNames.map((name, idx) => [idx + 1, name, ({
    "00_阅读说明":"口径、限制与导航", "01_核心结论":"关键数据、问题、机会与建议", "02_认证漏斗":"提现触发完整漏斗、流失贡献与周趋势",
    "03_BVN_NIN":"两种身份认证方式和端侧差异", "04_人脸失败与重试":"失败原因、无结果、重试压力与接口尖峰",
    "05_App_H5包体版本":"App/H5对比及版本/KYC事件切窗", "06_提现结果":"当前数据边界和补数要求",
    "07_配置事件":"版本、KYC调整、线上机制与候选方案", "08_评论处理":"Ryan点评、数据证据与处理结论",
    "09_数据质量":"覆盖、粒度、缺失维度与异常校验", "数据_标准化":"100条窗口内标准记录", "数据_计算":"公式汇总与周趋势", "数据_来源映射":"CSV、飞书文档、用户评论和字段来源"
  })[name]]);
  headerStyle(s.getRange("A12:C12"));
  s.getRange("A12:C12").values = [["序号", "工作表", "用途"]];
  bodyStyle(s.getRange("A13:C24"));
  s.freezePanes.freezeRows(3);
}

// 01 核心结论
{
  const s = wb.worksheets.getItem("01_核心结论");
  baseSheet(s);
  title(s, "核心结论：7月27日H5降门槛后覆盖扩大，认证质量未同步", "H5首充带币触发门槛900→500；前后比较以App作参照，仍按相关性而非因果解释。", "L");
  const kpis = [
    ["风险触发", "='数据_计算'!C9", "用户日"], ["端到端", "='数据_计算'!P9", "触发→人脸成功"],
    ["调用后成功", "='数据_计算'!Q9", "实际调用→人脸成功"], ["已有结果成功", "='数据_计算'!N9", "成功/(成功+失败)"],
    ["无最终结果", "='数据_计算'!O9", "请求后无成功/失败"], ["NIN-BVN", "='数据_计算'!W9-'数据_计算'!T9", "通过率差"],
  ];
  for (let i = 0; i < kpis.length; i++) {
    const col = 1 + i * 2;
    const a = String.fromCharCode(64 + col), b = String.fromCharCode(64 + col + 1);
    s.getRange(`${a}5:${b}5`).merge(); s.getRange(`${a}5`).values = [[kpis[i][0]]];
    s.getRange(`${a}6:${b}7`).merge(); s.getRange(`${a}6`).formulas = [[kpis[i][1]]];
    s.getRange(`${a}8:${b}8`).merge(); s.getRange(`${a}8`).values = [[kpis[i][2]]];
    s.getRange(`${a}5:${b}8`).format = { fill: i === 4 ? C.yellow2 : C.sky, borders: { preset: "outside", style: "thin", color: C.line }, horizontalAlignment: "center", verticalAlignment: "center" };
    s.getRange(`${a}5`).format.font = { bold: true, color: C.muted };
    s.getRange(`${a}6`).format.font = { bold: true, size: 18, color: i === 4 ? C.red : C.navy };
    s.getRange(`${a}8`).format.font = { size: 9, color: C.muted };
  }
  s.getRange("A6:B7").format.numberFormat = "#,##0";
  s.getRange("C6:L7").format.numberFormat = "0.0%";
  section(s, 10, "四个核心判断", "L");
  const h5ConfigPhases = analysis.phases.filter(x => x.flow === "提现触发" && x.platform === "H5");
  const h5Before = h5ConfigPhases[0], h5After = h5ConfigPhases[1];
  const conclusions = [
    ["口径", "48.3% 与旧报告 46%—50%一致；59.2%与旧报告60.74%同为“已调用身份认证→人脸成功”。不是数据冲突，是分母不同。"],
    ["最大流失", `最终失败只有 ${num(analysis.summary["提现触发"]["全部"].face_fail)} 用户日；更大的损失是未调用、调用后未到人脸、请求后无最终结果。`],
    ["H5配置", `7/27门槛900→500后，日均触发增长${pct((h5After.trigger/h5After.days)/(h5Before.trigger/h5Before.days)-1)}；成功/请求由${pct(h5Before.face_success_request_rate)}降至${pct(h5After.face_success_request_rate)}，无结果由${pct(h5Before.face_unresolved_rate)}升至${pct(h5After.face_unresolved_rate)}。`],
    ["认证方式", `NIN通过率 ${pct(analysis.summary["提现触发"]["全部"].nin_pass_rate)}，比BVN高 ${pp(analysis.opportunity.bvn_to_nin_gap_pp)}；H5 BVN通过率只有 ${pct(analysis.summary["提现触发"]["H5"].bvn_pass_rate)}。`],
  ];
  s.getRange("A11:B14").values = conclusions;
  s.getRange("A11:A14").format = { fill: C.blue2, font: { bold: true, color: C.navy }, horizontalAlignment: "center" };
  bodyStyle(s.getRange("A11:B14"));
  s.getRange("A:A").format.columnWidth = 16; s.getRange("B:B").format.columnWidth = 100;
  section(s, 16, "可执行机会空间（不是预测）", "L");
  s.getRange("A17:D20").values = [
    ["机会", "测算", "建议动作", "护栏"],
    ["App行动率对齐H5", Math.round(analysis.opportunity.app_extra_success_at_current_downstream), "优化触发页说明、按钮和返回路径；A/B验证", "欺诈放行率、客服投诉"],
    ["H5人脸成功/请求对齐App", Math.round(analysis.opportunity.h5_extra_face_success), "先修接口尖峰与SDK链路，再优化拍摄指导", "超时率、SDK错误率"],
    ["H5无结果率对齐App", Math.round(analysis.opportunity.h5_extra_resolved), "补齐退出/超时埋点与可恢复重试", "只代表更多形成结果，不等于全部成功"],
  ];
  headerStyle(s.getRange("A17:D17")); bodyStyle(s.getRange("A18:D20"));
  s.getRange("B18:B20").format.numberFormat = "#,##0";
  s.getRange("A:D").format.columnWidth = 26; s.getRange("C:D").format.columnWidth = 42;
  s.freezePanes.freezeRows(3);
}

// 02 认证漏斗
{
  const s = wb.worksheets.getItem("02_认证漏斗"); baseSheet(s);
  title(s, "提现触发认证漏斗", "漏斗止于人脸最终成功，不等同于最终提现成功。", "N");
  section(s, 5, "总体漏斗（2026-07-23—08-16）", "H");
  s.getRange("A6:C10").values = [["阶段", "用户日", "较上一步保留率"], ["风险提现触发", null, 1], ["实际调用BVN/NIN", null, null], ["请求人脸", null, null], ["最终人脸成功", null, null]];
  s.getRange("B7:B10").formulas = [["='数据_计算'!C9"], ["='数据_计算'!D9"], ["='数据_计算'!F9"], ["='数据_计算'!H9"]];
  s.getRange("C8:C10").formulas = [["=B8/B7"], ["=B9/B8"], ["=B10/B9"]];
  headerStyle(s.getRange("A6:C6")); bodyStyle(s.getRange("A7:C10"));
  s.getRange("B7:B10").format.numberFormat = "#,##0"; s.getRange("C7:C10").format.numberFormat = "0.0%";
  const funnel = s.charts.add("bar", s.getRange("A6:B10"));
  funnel.title = "触发到人脸成功：30,015 → 14,499"; funnel.hasLegend = false; funnel.yAxis = { numberFormatCode: "#,##0" };
  funnel.setPosition("E6", "N20");

  section(s, 22, "全流程流失贡献", "H");
  s.getRange("A23:C27").values = [["流失阶段", "用户日", "占全部流失"]].concat(analysis.losses.map(x => [x.stage, x.count, x.share]));
  headerStyle(s.getRange("A23:C23")); bodyStyle(s.getRange("A24:C27"));
  s.getRange("B24:B27").format.numberFormat = "#,##0"; s.getRange("C24:C27").format.numberFormat = "0.0%";
  const lossChart = s.charts.add("bar", s.getRange("A23:B27"));
  lossChart.title = "最大损失发生在人脸最终失败之前"; lossChart.hasLegend = false; lossChart.yAxis = { numberFormatCode: "#,##0" };
  lossChart.setPosition("E23", "N38");

  section(s, 40, "三周趋势（全部端）", "N");
  s.getRange("A41:E44").values = [["周期", "行动率", "到达人脸率", "成功/请求", "无结果率"]].concat(
    analysis.weekly.filter(x => x.flow === "提现触发" && x.platform === "全部").map(x => [x.period, x.action_rate, x.face_reach_rate, x.face_success_request_rate, x.face_unresolved_rate])
  );
  headerStyle(s.getRange("A41:E41")); bodyStyle(s.getRange("A42:E44")); s.getRange("B42:E44").format.numberFormat = "0.0%";
  const trend = s.charts.add("line", s.getRange("A41:E44")); trend.title = "行动率改善，但到达人脸率回落"; trend.hasLegend = true; trend.yAxis = { numberFormatCode: "0%", min: 0, max: 1 };
  trend.setPosition("G41", "N57");
  s.getRange("A:A").format.columnWidth = 28; s.getRange("B:C").format.columnWidth = 18;
  s.freezePanes.freezeRows(3);
}

// 03 BVN/NIN
{
  const s = wb.worksheets.getItem("03_BVN_NIN"); baseSheet(s);
  title(s, "BVN 与 NIN：NIN稳定更好，H5 BVN最弱", "统计对象为提现触发流程。通过率=通过人数/调用人数。", "L");
  s.getRange("A5:G8").values = [["端", "BVN调用", "BVN通过", "BVN通过率", "NIN调用", "NIN通过", "NIN通过率"], ["全部", null, null, null, null, null, null], ["App", null, null, null, null, null, null], ["H5", null, null, null, null, null, null]];
  const calcRows = [9, 10, 11];
  for (let i = 0; i < 3; i++) {
    const r = 6 + i, c = calcRows[i];
    s.getRange(`B${r}:G${r}`).formulas = [[`='数据_计算'!R${c}`, `='数据_计算'!S${c}`, `='数据_计算'!T${c}`, `='数据_计算'!U${c}`, `='数据_计算'!V${c}`, `='数据_计算'!W${c}`]];
  }
  headerStyle(s.getRange("A5:G5")); bodyStyle(s.getRange("A6:G8"));
  s.getRange("B6:C8").format.numberFormat = "#,##0"; s.getRange("E6:F8").format.numberFormat = "#,##0"; s.getRange("D6:D8").format.numberFormat = "0.0%"; s.getRange("G6:G8").format.numberFormat = "0.0%";
  s.getRange("I5:K8").values = [["端", "BVN", "NIN"], ["全部", null, null], ["App", null, null], ["H5", null, null]];
  s.getRange("J6:K8").formulas = [["=D6", "=G6"], ["=D7", "=G7"], ["=D8", "=G8"]];
  headerStyle(s.getRange("I5:K5")); bodyStyle(s.getRange("I6:K8")); s.getRange("J6:K8").format.numberFormat = "0.0%";
  const chart = s.charts.add("bar", s.getRange("I5:K8")); chart.title = "NIN通过率在两端均领先"; chart.hasLegend = true; chart.yAxis = { numberFormatCode: "0%", min: 0, max: 1 };
  chart.setPosition("I10", "R26");
  section(s, 10, "问题定位", "G");
  s.getRange("A11:C14").values = [
    ["问题", "数据", "动作"],
    ["H5 BVN通过率最低", pct(analysis.summary["提现触发"]["H5"].bvn_pass_rate), "拆分不存在、姓名不匹配、冻结、系统错误；提供可执行纠错提示"],
    ["NIN明显领先", `高${pp(analysis.opportunity.bvn_to_nin_gap_pp)}`, "默认优先NIN；BVN失败后允许切换NIN并保留进度"],
    ["上限机会", `${num(analysis.opportunity.bvn_only_pass_opportunity)} 用户日`, "按BVN-only切NIN的观察差额估算；仅作为上限，不是预测"],
  ];
  headerStyle(s.getRange("A11:C11")); bodyStyle(s.getRange("A12:C14"));
  s.getRange("A:A").format.columnWidth = 24; s.getRange("B:B").format.columnWidth = 20; s.getRange("C:C").format.columnWidth = 60;
  s.freezePanes.freezeRows(3);
}

// 04 人脸失败与重试
{
  const s = wb.worksheets.getItem("04_人脸失败与重试"); baseSheet(s);
  title(s, "人脸失败、无结果与请求压力", "先看用户级明确失败，再看失败尝试原因；人像不匹配占比不能解释为用户失败率。", "N");
  s.getRange("A5:F8").values = [["端", "请求用户日", "明确失败/请求", "无结果率", "不匹配/当前失败原因", "请求接口/当前原因"], ["全部", null, null, null, null, null], ["App", null, null, null, null, null], ["H5", null, null, null, null, null]];
  const rows = [9, 10, 11];
  for (let i = 0; i < rows.length; i++) {
    const r = 6 + i, c = rows[i];
    s.getRange(`B${r}:F${r}`).formulas = [[`='数据_计算'!F${c}`, `=IFERROR('数据_计算'!I${c}/'数据_计算'!F${c},0)`, `='数据_计算'!O${c}`, `='数据_计算'!AC${c}`, `='数据_计算'!AD${c}`]];
  }
  headerStyle(s.getRange("A5:F5")); bodyStyle(s.getRange("A6:F8")); s.getRange("B6:B8").format.numberFormat = "#,##0"; s.getRange("C6:F8").format.numberFormat = "0.0%";
  section(s, 10, "请求接口失败尖峰", "N");
  s.getRange("A11:D19").values = [["日期", "端", "接口失败次数", "占当日当前原因"]].concat(analysis.top_request_errors.map(x => [new Date(`${x.date}T00:00:00`), x.platform, x.count, x.count / x.all_current_reasons]));
  headerStyle(s.getRange("A11:D11")); bodyStyle(s.getRange("A12:D19")); s.getRange("A12:A19").format.numberFormat = "yyyy-mm-dd"; s.getRange("C12:C19").format.numberFormat = "#,##0"; s.getRange("D12:D19").format.numberFormat = "0.0%";
  s.getRange("E11:F19").values = [["日期·端", "接口失败次数"]].concat(analysis.top_request_errors.map(x => [`${x.date.slice(5)} ${x.platform}`, null]));
  for (let r = 12; r <= 19; r++) s.getRange(`F${r}`).formulas = [[`=C${r}`]];
  headerStyle(s.getRange("E11:F11")); bodyStyle(s.getRange("E12:F19")); s.getRange("F12:F19").format.numberFormat = "#,##0";
  const spike = s.charts.add("bar", s.getRange("E11:F19")); spike.title = "接口失败集中在H5少数日期"; spike.hasLegend = false; spike.yAxis = { numberFormatCode: "#,##0" };
  spike.setPosition("H11", "N28");
  section(s, 30, "解读与动作", "N");
  s.getRange("A31:D34").values = [
    ["优先级", "证据", "动作", "验证指标/护栏"],
    ["P0", `H5占${pct(analysis.summary["提现触发"]["H5"].request_error_attempts / analysis.summary["提现触发"]["全部"].request_error_attempts)}接口失败`, "按8/1、8/5、8/13回查网关、SDK版本、超时、供应商request_id", "接口失败占比<5%；不提高欺诈放行"],
    ["P0", `请求后无结果${num(analysis.summary["提现触发"]["全部"].face_unresolved)}用户日`, "补充退出、超时、关闭、相机权限、弱网和在途状态", "无结果率；平均完成时长；恢复后完成率"],
    ["P1", `明确失败/请求${pct(analysis.summary["提现触发"]["全部"].face_fail_request_rate)}；不匹配占当前失败尝试${pct(analysis.summary["提现触发"]["全部"].mismatch_share_retained)}`, "实时光线/遮挡/角度提示；连续两次失败后增强说明并提供替代/人工复核", "首次成功率、重试挽回率；欺诈识别率"],
  ];
  headerStyle(s.getRange("A31:D31")); bodyStyle(s.getRange("A32:D34"));
  section(s, 36, "分母校验", "N");
  s.getRange("A37:D40").values = [
    ["指标", "分子", "分母", "用途"],
    ["明确失败/请求人脸", analysis.summary["提现触发"]["全部"].face_fail, analysis.summary["提现触发"]["全部"].face_request, "用户层失败率"],
    ["不匹配/当前失败原因", analysis.summary["提现触发"]["全部"].mismatch_attempts, analysis.summary["提现触发"]["全部"].retained_fail_reasons, "当前失败尝试构成，不是用户率"],
    ["不匹配/历史失败尝试", analysis.summary["提现触发"]["全部"].mismatch_attempts, analysis.summary["提现触发"]["全部"].history_fail_attempts, "辅助诊断；成功后部分原因已清除"],
  ];
  headerStyle(s.getRange("A37:D37")); bodyStyle(s.getRange("A38:D40")); s.getRange("B38:C40").format.numberFormat = "#,##0";
  s.getRange("A:A").format.columnWidth = 14; s.getRange("B:B").format.columnWidth = 32; s.getRange("C:D").format.columnWidth = 48;
  s.freezePanes.freezeRows(3);
}

// 05 App/H5 包体版本
{
  const s = wb.worksheets.getItem("05_App_H5包体版本"); baseSheet(s);
  title(s, "App/H5 与7月27日H5配置切点", "线上配置确认H5首充带币触发门槛于7月27日23:20由900降至500；按调整前后比较，并以App作横向参照。", "N");
  const clients = [analysis.summary["提现触发"]["App"], analysis.summary["提现触发"]["H5"]];
  s.getRange("A5:J7").values = [["端", "包名", "触发", "行动率", "到达人脸率", "成功/请求", "已有结果成功", "无结果率", "人均请求", "端到端"],
    ["App", "com.hfhy.waje.special", clients[0].trigger, clients[0].action_rate, clients[0].face_reach_rate, clients[0].face_success_request_rate, clients[0].face_success_completed_rate, clients[0].face_unresolved_rate, clients[0].attempts_per_user, clients[0].e2e_rate],
    ["H5", "com.wajegame.web", clients[1].trigger, clients[1].action_rate, clients[1].face_reach_rate, clients[1].face_success_request_rate, clients[1].face_success_completed_rate, clients[1].face_unresolved_rate, clients[1].attempts_per_user, clients[1].e2e_rate]];
  headerStyle(s.getRange("A5:J5")); bodyStyle(s.getRange("A6:J7")); s.getRange("C6:C7").format.numberFormat = "#,##0"; s.getRange("D6:H7").format.numberFormat = "0.0%"; s.getRange("I6:I7").format.numberFormat = "0.00"; s.getRange("J6:J7").format.numberFormat = "0.0%";
  s.getRange("L5:P7").values = [["端", "行动率", "到达人脸率", "成功/请求", "无结果率"], ["App", clients[0].action_rate, clients[0].face_reach_rate, clients[0].face_success_request_rate, clients[0].face_unresolved_rate], ["H5", clients[1].action_rate, clients[1].face_reach_rate, clients[1].face_success_request_rate, clients[1].face_unresolved_rate]];
  headerStyle(s.getRange("L5:P5")); bodyStyle(s.getRange("L6:P7")); s.getRange("M6:P7").format.numberFormat = "0.0%";
  const chart = s.charts.add("bar", s.getRange("L5:P7")); chart.title = "H5前段更顺，但人脸结果更弱"; chart.hasLegend = true; chart.yAxis = { numberFormatCode: "0%", min: 0, max: 1 };
  chart.setPosition("L9", "T27");
  section(s, 10, "差异解释与补数", "J");
  s.getRange("A11:D16").values = [
    ["主题", "App", "H5", "判断"],
    ["触发后行动", pct(clients[0].action_rate), pct(clients[1].action_rate), "H5更高；App触发页/文案/返回路径是机会点"],
    ["到达人脸", pct(clients[0].face_reach_rate), pct(clients[1].face_reach_rate), "H5更高"],
    ["成功/请求", pct(clients[0].face_success_request_rate), pct(clients[1].face_success_request_rate), "H5低4.0pp；优先排查技术和拍摄体验"],
    ["无结果", pct(clients[0].face_unresolved_rate), pct(clients[1].face_unresolved_rate), "H5高2.6pp"],
    ["配置分析", "App门槛900", "H5门槛500", "7/27前后可观察；仍缺config_version、首充金额段和渠道"],
  ];
  headerStyle(s.getRange("A11:D11")); bodyStyle(s.getRange("A12:D16"));
  section(s, 30, "7月27日H5门槛调整前后（提现触发）", "N");
  const phaseRows = analysis.phases.filter(x => x.flow === "提现触发" && x.platform !== "全部").map(x => [
    x.phase_short, x.platform, x.days, x.trigger, x.action_rate, x.face_reach_rate, x.face_success_request_rate, x.face_unresolved_rate, x.face_fail_request_rate, x.e2e_rate
  ]);
  s.getRange(`A31:J${31 + phaseRows.length}`).values = [["阶段", "端", "天数", "触发", "行动率", "调用→人脸", "成功/请求", "无结果率", "明确失败/请求", "端到端"]].concat(phaseRows);
  headerStyle(s.getRange("A31:J31")); bodyStyle(s.getRange(`A32:J${31 + phaseRows.length}`));
  s.getRange(`C32:D${31 + phaseRows.length}`).format.numberFormat = "#,##0"; s.getRange(`E32:J${31 + phaseRows.length}`).format.numberFormat = "0.0%";
  const phaseChartRows = analysis.phases.filter(x => x.flow === "提现触发" && x.platform === "全部").map(x => [x.phase_short, x.e2e_rate, x.face_success_request_rate, x.face_unresolved_rate]);
  s.getRange(`L31:O${31 + phaseChartRows.length}`).values = [["阶段", "端到端", "成功/请求", "无结果率"]].concat(phaseChartRows);
  headerStyle(s.getRange("L31:O31")); bodyStyle(s.getRange(`L32:O${31 + phaseChartRows.length}`)); s.getRange(`M32:O${31 + phaseChartRows.length}`).format.numberFormat = "0.0%";
  const phaseChart = s.charts.add("line", s.getRange(`L31:O${31 + phaseChartRows.length}`)); phaseChart.title = "H5门槛900→500前后：转化与无结果变化"; phaseChart.hasLegend = true; phaseChart.yAxis = { numberFormatCode: "0%", min: 0, max: 1 };
  phaseChart.setPosition("L37", "T55");
  section(s, 57, "事件解释", "N");
  s.getRange("A58:D62").values = [["阶段", "事件", "可见变化", "结论边界"]].concat(
    analysis.phases.filter(x => x.flow === "提现触发" && x.platform === "全部").map(x => [x.phase_short, x.event, `行动${pct(x.action_rate)}；成功/请求${pct(x.face_success_request_rate)}；端到端${pct(x.e2e_rate)}`, "有真实配置切点，但CSV无config_version与首充金额，仍不做因果断言"])
  );
  headerStyle(s.getRange("A58:D58")); bodyStyle(s.getRange("A59:D62"));
  s.getRange("A:A").format.columnWidth = 20; s.getRange("B:C").format.columnWidth = 26; s.getRange("D:D").format.columnWidth = 55;
  s.freezePanes.freezeRows(3);
}

// 06 提现结果边界
{
  const s = wb.worksheets.getItem("06_提现结果"); baseSheet(s);
  title(s, "提现影响：当前只能看到人脸，不能看到钱是否提走", "缺少银行校验、提现提交与提现成功字段，任何“提现成功率”结论都会失真。", "K");
  section(s, 5, "当前可见链路", "K");
  s.getRange("A6:G8").values = [["风险触发", "实际调用", "请求人脸", "人脸成功", "银行校验", "提现提交", "提现成功"],
    [analysis.summary["提现触发"]["全部"].trigger, analysis.summary["提现触发"]["全部"].actual, analysis.summary["提现触发"]["全部"].face_request, analysis.summary["提现触发"]["全部"].face_success, "N/A", "N/A", "N/A"],
    ["已提供", "已提供", "已提供", "已提供", "未导出", "未导出", "未导出"]];
  headerStyle(s.getRange("A6:G6")); bodyStyle(s.getRange("A7:G8")); s.getRange("A7:D7").format.numberFormat = "#,##0";
  section(s, 10, "下一版数据必须补齐", "K");
  s.getRange("A11:D17").values = [
    ["字段/事件", "用途", "最小维度", "验收"],
    ["phone_bound / phone_bvn_result", "评估新手机号流程", "日期、端、包、flow_version、结果码", "成功+失败+退出可对账"],
    ["bank_match_result", "定位银行卡不存在/实名不匹配", "结果码、认证方式", "每个失败有唯一原因"],
    ["withdraw_submit", "看认证后是否继续", "日期、端、流程版本", "不小于withdraw_success"],
    ["withdraw_success", "真实业务结果", "金额段、端、流程版本", "与支付/资产流水对账"],
    ["event_time / received_at", "区分超时与在途", "毫秒时间戳", "P75/P90时长可算"],
    ["request_id / provider_code", "定位供应商与接口问题", "脱敏请求ID、错误码", "失败原因覆盖率>95%"],
  ];
  headerStyle(s.getRange("A11:D11")); bodyStyle(s.getRange("A12:D17"));
  s.getRange("A:A").format.columnWidth = 28; s.getRange("B:D").format.columnWidth = 44;
  s.freezePanes.freezeRows(3);
}

// 07 配置事件
{
  const s = wb.worksheets.getItem("07_配置事件"); baseSheet(s);
  title(s, "机制与线上配置状态地图", "机制文档、线上配置快照和CSV分别取证；90为身份匹配阈值，60为人脸相似度阈值。", "L");
  s.getRange("A5:F17").values = [
    ["日期/对象", "状态", "已知机制/配置", "线上生效证据", "报告处理", "来源"],
    ["2026-07-23—07-26", "调整前基线", "H5 config_11首充带币门槛900", "沟通记录+历史配置", "作为7/27调整前基线", "用户截图/配置表"],
    ["2026-07-27 23:20", "线上配置变更", "H5 firstRechargeBalance 900→500", "配置更新记录；当前值500", "调整前后比较；App作参照", "kyc认证/Pf4y9V"],
    ["2026-07-27后", "无后续调整", "沟通确认该KYC配置未再调整", "项目沟通记录", "7/27—8/16合并观察", "用户提供"],
    ["当前触发矩阵", "线上配置", "App自然/非自然900；H5 500；iOS 1000", "线上数值工作簿", "报告按端解释覆盖差异", "kyc认证/Pf4y9V"],
    ["身份匹配", "线上配置", "matchPercent=90", "kyc认证工作表", "身份/KYC阈值，不等于人脸阈值", "kyc认证/Pf4y9V"],
    ["人脸总开关", "线上配置", "withdraw_face_open=true", "人脸识别配置正式值", "确认人脸流程开启", "人脸识别配置/3KVm1s"],
    ["每日次数/间隔", "线上配置", "高级IDV 10次/日、60秒间隔；人脸5次/日", "人脸识别配置正式值", "补限额/冷却事件后评估影响", "人脸识别配置/3KVm1s"],
    ["人脸相似度", "线上配置", "faceMatchPercent=60", "人脸识别配置正式值", "失败分析按人脸阈值60解释", "人脸识别配置/3KVm1s"],
    ["face_reg_time", "配置缺口", "正式配置单元格为空", "人脸识别配置快照", "研发确认空值语义和线上最终值", "人脸识别配置/3KVm1s"],
    ["旧风险提现流程", "机制", "风险识别→BVN/NIN→官方人像→活体→FaceMatch→返回提现", "机制文档", "用于定义完整状态机", "KYC机制拆解"],
    ["手机号→BVN→银行卡", "计划/待核验上线", "绑定手机、查BVN、BVN与银行卡匹配", "CSV无flow_version及新流程字段", "不评估效果", "XGUP..."],
    ["数据追踪", "缺口", "CSV无config_version、首充金额段、限额命中和阈值分数", "本次数据质量检查", "不做因果断言；列为P0埋点", "两份CSV"],
  ];
  headerStyle(s.getRange("A5:F5")); bodyStyle(s.getRange("A6:F17"));
  s.getRange("A:A").format.columnWidth = 24; s.getRange("B:B").format.columnWidth = 20; s.getRange("C:E").format.columnWidth = 42; s.getRange("F:F").format.columnWidth = 20;
  s.getRange("B6:B17").conditionalFormats.add("containsText", { text: "缺口", format: { fill: C.yellow2, font: { color: C.red } } });
  s.getRange("B6:B17").conditionalFormats.add("containsText", { text: "线上配置", format: { fill: C.green2, font: { color: C.green } } });
  s.freezePanes.freezeRows(5);
}

// 08 评论处理
{
  const s = wb.worksheets.getItem("08_评论处理"); baseSheet(s);
  title(s, "Ryan点评与处理结论", "先拆无结果，再拆有结果者成功/失败，最后分析失败尝试原因。", "J");
  s.getRange("A5:E10").values = [
    ["点评/问题", "Ryan原意", "最新数据证据", "报告处理", "仍需补数"],
    ["分析顺序", "NIN/BVN成功后先看放弃，再看非放弃者成功/失败，最后看失败原因", "请求23,767；无结果4,416；有结果19,351；成功16,894；失败2,457", "正文新增分层漏斗", "身份通过人数"],
    ["863-625-160=78", "示例说明真正人脸失败应排除未继续者", "评论数字与旧正文884/639/160/85不是同一快照", "不强行对账，仅采用逻辑", "保留报表版本/刷新时间"],
    ["放弃的定义", "包含黑屏、摄像头打不开、进入页面后不操作退出", `无最终结果${num(analysis.summary["提现触发"]["全部"].face_unresolved)}用户日`, "统一改称“无最终结果”", "主动退出、黑屏、权限、超时、在途原因"],
    ["人像不匹配92.3%", "需确认是否真是用户失败率", `明确失败/请求${pct(analysis.summary["提现触发"]["全部"].face_fail_request_rate)}；不匹配/当前原因${pct(analysis.summary["提现触发"]["全部"].mismatch_share_retained)}`, "拆为用户结果和尝试原因两层", "不可变尝试事件表"],
    ["合规", "不涉及个人敏感内容", "当前均为聚合用户日", "不导出人脸、姓名、号码", "保持聚合"],
  ];
  headerStyle(s.getRange("A5:E5")); bodyStyle(s.getRange("A6:E10"));
  s.getRange("A:A").format.columnWidth = 28; s.getRange("B:E").format.columnWidth = 36;
  s.getRange("D6:D10").format = { fill: C.green2, font: { bold: true, color: C.green } };
  s.freezePanes.freezeRows(5);
}

// 09 数据质量
{
  const s = wb.worksheets.getItem("09_数据质量"); baseSheet(s);
  title(s, "数据质量与可用边界", "先判断数据能回答什么，再解释指标；不把缺失维度补零。", "K");
  s.getRange("A5:D13").values = [
    ["检查项", "结果", "状态", "说明"],
    ["源文件行数", "52+52", "通过", "每份26天×2包体"],
    ["报告窗口", "25天×2包体×2流程=100行", "通过", "2026-07-23—08-16"],
    ["未完整日", "2026-08-17", "已排除", "避免把日内未完成当成失败"],
    ["日期连续性", "两个流程均25天", "通过", "无缺日"],
    ["日期×包名重复", "0", "通过", "汇总粒度唯一"],
    ["空值", "非适用字段外为0", "通过", "主动填写无每日触发字段属结构性空值"],
    ["漏斗单调性", "请求≤实际；成功+失败≤请求", "通过", "剩余定义为无最终结果"],
    ["失败原因完整性", `当前保留${num(analysis.summary["提现触发"]["全部"].retained_fail_reasons || 7883)}次`, "有局限", "成功后清除部分失败原因，当前分布非全部历史"],
  ];
  headerStyle(s.getRange("A5:D5")); bodyStyle(s.getRange("A6:D13"));
  s.getRange("C6:C13").conditionalFormats.add("containsText", { text: "通过", format: { fill: C.green2, font: { color: C.green } } });
  s.getRange("C6:C13").conditionalFormats.add("containsText", { text: "局限", format: { fill: C.yellow2, font: { color: C.red } } });
  section(s, 15, "当前不支持的分析", "K");
  s.getRange("A16:C22").values = [["缺失维度/结果", "影响", "报告处理"]].concat(analysis.quality.unsupported_dimensions.map(x => [x, "无法形成可靠细钻或最终业务结论", "显示“数据暂不支持”，不推断"]));
  headerStyle(s.getRange("A16:C16")); bodyStyle(s.getRange("A17:C22"));
  s.getRange("A:A").format.columnWidth = 30; s.getRange("B:B").format.columnWidth = 40; s.getRange("C:D").format.columnWidth = 48;
  s.freezePanes.freezeRows(5);
}

// 数据来源映射
{
  const s = wb.worksheets.getItem("数据_来源映射"); baseSheet(s);
  title(s, "数据来源与字段映射", "所有结论可回溯到CSV、线上KYC/人脸配置、机制文档或Ryan点评。", "K");
  s.getRange("A5:E12").values = [
    ["来源", "类型", "用途", "状态", "位置/链接"],
    ["主动填写人脸认证统计", "CSV", "主动流程内部诊断", "已纳入", analysis.files["主动填写"].path],
    ["提现触发人脸认证统计", "CSV", "主漏斗、端侧与失败分析", "已纳入", analysis.files["提现触发"].path],
    ["KYC人脸识别分析", "飞书正文", "历史46%—50%基线", "已读取", "https://ksg964l11fam.sg.larksuite.com/wiki/M1dswwA1NiZ8L3kO2vSlZMNKgxd"],
    ["人脸识别分析报告", "飞书正文", "历史60.74%口径", "已读取", "https://ksg964l11fam.sg.larksuite.com/wiki/UZaww1fGpibKcJkEisil3VSRgHf"],
    ["线上KYC配置", "飞书电子表格", "7/27门槛变更与当前触发矩阵", "已下载核对", "https://ksg964l11fam.sg.larksuite.com/sheets/WWBBsLNl4hTFnbtI9arlmGsqgoc?sheet=Pf4y9V"],
    ["线上人脸识别配置", "飞书电子表格", "开关、次数、间隔、阈值", "已下载核对", "https://ksg964l11fam.sg.larksuite.com/sheets/WWBBsLNl4hTFnbtI9arlmGsqgoc?sheet=3KVm1s"],
    ["Ryan 7月24日点评", "用户提供的评论原文", "修正漏斗顺序与放弃定义", "已纳入", "先无结果→再成功/失败→最后失败原因"],
  ];
  headerStyle(s.getRange("A5:E5")); bodyStyle(s.getRange("A6:E12"));
  section(s, 14, "标准字段映射", "K");
  s.getRange("A15:D26").values = [
    ["标准字段", "源字段", "定义", "备注"],
    ["trigger", "每日触发人数", "风险提现触发用户日", "主动填写流程以实际调用+未调用推算可观测人群"],
    ["actual", "实际调用BVN/NIN人数", "发生身份认证调用的用户日", "去重口径按源表"],
    ["face_request", "请求人脸识别人数", "到达人脸并发起请求", "人数，不是次数"],
    ["face_attempts", "请求人脸识别次数", "人脸请求总次数", "用于人均重试压力"],
    ["face_success", "最终人脸识别成功人数", "最终成功用户日", "不等于提现成功"],
    ["face_fail", "最终人脸识别失败人数", "最终失败用户日", "不含无结果"],
    ["face_unresolved", "计算字段", "请求-成功-失败", "退出/未完成/超时/在途的保守合并"],
    ["action_rate", "计算字段", "实际调用/触发", "主动填写为推算分母"],
    ["face_success_request", "计算字段", "最终成功/请求人脸", "含无结果的请求口径"],
    ["face_success_completed", "计算字段", "最终成功/(最终成功+最终失败)", "只看已有结果"],
    ["e2e", "计算字段", "最终成功/风险触发", "主业务漏斗口径"],
  ];
  headerStyle(s.getRange("A15:D15")); bodyStyle(s.getRange("A16:D26"));
  s.getRange("A:A").format.columnWidth = 28; s.getRange("B:B").format.columnWidth = 34; s.getRange("C:D").format.columnWidth = 48; s.getRange("E:E").format.columnWidth = 80;
  s.freezePanes.freezeRows(5);
}

// 统一页面细节与输出。
for (const name of sheetNames) {
  const s = wb.worksheets.getItem(name);
  const used = s.getUsedRange();
  if (used) used.format.verticalAlignment = "center";
}

await fs.mkdir(PREVIEW_DIR, { recursive: true });
const previewSheets = ["00_阅读说明", "01_核心结论", "02_认证漏斗", "03_BVN_NIN", "04_人脸失败与重试", "05_App_H5包体版本", "06_提现结果", "07_配置事件", "08_评论处理", "09_数据质量", "数据_标准化", "数据_计算", "数据_来源映射"];
for (const name of previewSheets) {
  const blob = await wb.render({ sheetName: name, autoCrop: "all", scale: 0.9, format: "png" });
  await fs.writeFile(`${PREVIEW_DIR}/${name}.png`, new Uint8Array(await blob.arrayBuffer()));
}

await fs.mkdir(`${ROOT}/output`, { recursive: true });
const out = await SpreadsheetFile.exportXlsx(wb);
await out.save(OUTPUT_PATH);
const inspect = await wb.inspect({ kind: "sheet,formula,drawing", maxChars: 8000, tableMaxRows: 5, tableMaxCols: 8, options: { maxResults: 300 } });
await fs.writeFile(`${ROOT}/analysis/kyc_face_2026_08_16/workbook_inspect.ndjson`, inspect.ndjson ?? JSON.stringify(inspect, null, 2), "utf8");
console.log(JSON.stringify({ output: OUTPUT_PATH, previews: PREVIEW_DIR, rows: rawRows.length, sheets: sheetNames.length }, null, 2));
