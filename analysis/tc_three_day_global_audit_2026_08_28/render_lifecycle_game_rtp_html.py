#!/usr/bin/env python3
"""Render a portable, source-bounded HTML report from the audited aggregates."""

from __future__ import annotations

import base64
import html
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "lifecycle_game_rtp_14d"
HTML_OUT = ROOT / "output/html/Waje-近3日全产品TC比拆解分析与审计-2026-08-28.html"


def pct(value, digits=2):
    return "N/A" if value is None else f"{value * 100:.{digits}f}%"


def pp(value, digits=2):
    return "N/A" if value is None else f"{value * 100:+.{digits}f}pp"


def amount(value):
    if value is None:
        return "N/A"
    if abs(value) >= 100_000_000:
        return f"{value / 100_000_000:.2f}亿"
    if abs(value) >= 10_000:
        return f"{value / 10_000:.2f}万"
    return f"{value:,.0f}"


def data_uri(path: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def table(headers, rows, class_name=""):
    head = "".join(f"<th>{html.escape(str(item))}</th>" for item in headers)
    body = "".join(
        "<tr>" + "".join(f"<td>{value}</td>" for value in row) + "</tr>"
        for row in rows
    )
    return f'<div class="table-wrap {class_name}"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def main():
    overview = json.loads((OUT / "overview.json").read_text(encoding="utf-8"))
    comparison = json.loads((OUT / "game_lifecycle_comparison.json").read_text(encoding="utf-8"))
    game_rows = json.loads((OUT / "game_summary_weighted.json").read_text(encoding="utf-8"))
    new_user = json.loads((OUT / "new_user_context.json").read_text(encoding="utf-8"))
    quality = json.loads((OUT / "quality-checks.json").read_text(encoding="utf-8"))
    source = json.loads((OUT / "source-receipt.json").read_text(encoding="utf-8"))

    first_name = "第一周（8月14—20日）"
    second_name = "第二周（8月21—27日）"
    total_first = next(row for row in overview if row["period"] == first_name and row["display_lifecycle"] == "1—4合计")
    total_second = next(row for row in overview if row["period"] == second_name and row["display_lifecycle"] == "1—4合计")
    delta = total_second["actual_rtp"] - total_first["actual_rtp"]

    stage_rows = []
    for lifecycle in range(1, 5):
        first = next(row for row in overview if row["period"] == first_name and row["display_lifecycle"] == lifecycle)
        second = next(row for row in overview if row["period"] == second_name and row["display_lifecycle"] == lifecycle)
        stage_rows.append([
            str(lifecycle), amount(first["full_bet"]), pct(first["actual_rtp"]), amount(second["full_bet"]),
            pct(second["actual_rtp"]), pp(second["actual_rtp"] - first["actual_rtp"]),
            f"{pct(second['expected_rtp'])}（{pct(second['expected_bet_coverage'])}）",
        ])

    detail_rows = sorted(comparison, key=lambda row: row["second_full_bet"], reverse=True)

    figures = [
        ("生命周期1—4两周加权RTP总览", "实际RTP按完整下注重算；金色短线只代表配置字段有值的下注覆盖部分。", "01_生命周期两周加权RTP总览.png"),
        ("游戏×生命周期RTP变化热力图", "第二周相对第一周的实际RTP变化，空白代表两周均无有效下注。", "02_游戏生命周期RTP变化热力图.png"),
        ("分游戏汇总：下注贡献与RTP变化", "每点来自“生命周期奖池分游戏汇总”的单款游戏；规模与变化需同时阅读。", "03_游戏下注贡献与RTP变化散点图.png"),
        ("重点游戏RTP优先级", "用于复核优先级排序，不等同于真实损失或TC的因果贡献。", "04_重点游戏生命周期RTP优先级.png"),
        ("新增用户付费背景", "仅反映包体/渠道同期结构；当前没有game_id，不能归因到具体游戏。", "05_新增用户付费背景.png"),
    ]
    figure_html = "".join(
        f'<figure><img src="{data_uri(OUT / "assets" / filename)}" alt="{html.escape(title)}"/><figcaption><strong>{html.escape(title)}</strong><br/>{html.escape(caption)}</figcaption></figure>'
        for title, caption, filename in figures
    )

    top_table = table(
        ["游戏", "第一周实际RTP", "第二周实际RTP", "变化", "第二周下注额", "有效观察日"],
        [[html.escape(row["game"]), pct(row["first_actual_rtp"]), pct(row["second_actual_rtp"]), pp(row["actual_rtp_delta_pp"]), amount(row["second_full_bet"]), str(row["second_active_days"])] for row in game_rows[:10]],
    )
    all_detail = table(
        ["游戏", "生命周期", "第一周RTP", "第二周RTP", "变化", "第二周下注额", "状态"],
        [[html.escape(row["game"]), str(row["display_lifecycle"]), pct(row["first_actual_rtp"]), pct(row["second_actual_rtp"]), pp(row["actual_rtp_delta_pp"]), amount(row["second_full_bet"]), html.escape(row["data_status"])] for row in detail_rows],
        "dense",
    )
    new_user_table = table(
        ["包体/渠道", "新增人数", "新增付费人数", "首充人数", "D1成熟样本", "D3成熟样本", "D7成熟样本"],
        [[html.escape(row["segment"]), f"{row['new_users']:,.0f}", f"{row['new_payers']:,.0f}", f"{row['first_payers']:,.0f}", f"{row['d1_weight']:,.0f}", f"{row['d3_weight']:,.0f}", f"{row['d7_weight']:,.0f}"] for row in new_user],
    )
    stage_table = table(["生命周期", "第一周下注额", "第一周实际RTP", "第二周下注额", "第二周实际RTP", "变化", "第二周配置预期RTP（覆盖）"], stage_rows)
    partial_expected = f"{pct(total_second['expected_bet_coverage'])}"
    quality_count = len(quality["checks"])
    complete_dates = len(source["dates"])

    document = f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/><title>Waje近14日游戏×生命周期RTP验证</title>
<style>
  :root {{ color-scheme: light; --ink:#17324d; --muted:#64748b; --line:#dbe6f1; --panel:#f7fbff; --blue:#2563eb; --gold:#b7791f; --warn:#fff7e7; }}
  * {{ box-sizing:border-box; }} body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif; color:var(--ink); background:#f1f5f9; line-height:1.6; }}
  main {{ width:min(1280px, calc(100% - 36px)); margin:28px auto 54px; background:#fff; padding:54px 62px; border-radius:18px; box-shadow:0 10px 30px #17324d12; }}
  h1 {{ font-size:34px; line-height:1.2; margin:0 0 12px; }} h2 {{ font-size:24px; margin:48px 0 16px; padding-top:4px; }} h3 {{ font-size:18px; margin:24px 0 10px; }}
  .meta {{ color:var(--muted); margin:0; }} .tag {{ display:inline-block; padding:4px 10px; background:#eff6ff; color:#1d4ed8; border-radius:999px; font-size:13px; margin-right:8px; }}
  .callout {{ margin:28px 0; padding:18px 22px; border-left:5px solid var(--blue); background:#eff6ff; border-radius:10px; }}
  .grid {{ display:grid; grid-template-columns:repeat(3, minmax(0,1fr)); gap:14px; margin:22px 0; }} .kpi {{ border:1px solid var(--line); background:var(--panel); padding:18px; border-radius:12px; }} .kpi .label {{ color:var(--muted); font-size:14px; }} .kpi strong {{ display:block; font-size:28px; margin-top:5px; }} .kpi small {{ color:var(--muted); }}
  .table-wrap {{ overflow-x:auto; border:1px solid var(--line); border-radius:12px; }} table {{ width:100%; border-collapse:collapse; font-size:14px; }} th {{ background:#eef5fb; color:#25445f; white-space:nowrap; }} th,td {{ padding:10px 12px; border-bottom:1px solid var(--line); text-align:right; }} th:first-child,td:first-child {{ text-align:left; }} tr:last-child td {{ border-bottom:0; }} .dense table {{ font-size:12px; }}
  figure {{ margin:30px 0; border:1px solid var(--line); border-radius:14px; padding:12px; background:#fff; }} figure img {{ display:block; width:100%; height:auto; border-radius:8px; }} figcaption {{ color:var(--muted); padding:10px 5px 2px; font-size:14px; }} figcaption strong {{ color:var(--ink); }}
  details {{ margin-top:18px; border:1px solid var(--line); border-radius:12px; padding:0 16px; }} summary {{ cursor:pointer; padding:14px 0; color:#1d4ed8; font-weight:650; }} .warning {{ background:var(--warn); border-left-color:var(--gold); }} .sources {{ color:var(--muted); font-size:13px; border-top:1px solid var(--line); margin-top:44px; padding-top:20px; }}
  @media (max-width:720px) {{ main {{ width:100%; margin:0; border-radius:0; padding:30px 20px; }} .grid {{ grid-template-columns:1fr; }} h1 {{ font-size:27px; }} }}
  @media print {{ body {{ background:#fff; }} main {{ width:100%; box-shadow:none; margin:0; padding:22px; }} figure {{ break-inside:avoid; }} }}
</style></head><body><main>
  <div><span class="tag">TC审计补充</span><span class="tag">V2 Joint</span><span class="tag">14个完整日</span></div>
  <h1>近14日游戏 × 生命周期 RTP 验证</h1>
  <p class="meta">业务日期：2026-08-14—2026-08-27 ｜ 生命周期：页面展示 1—4 ｜ 数据范围：GM Lifecycle Pool V2（Joint）</p>
  <div class="callout"><strong>结论先行：</strong>生命周期1—4合计的加权实际RTP从第一周 <strong>{pct(total_first['actual_rtp'])}</strong> 变为第二周 <strong>{pct(total_second['actual_rtp'])}</strong>，变化 <strong>{pp(delta)}</strong>。该结果验证的是全产品的游戏与生命周期池回报结构；由于当前来源没有包体、渠道、归因或最终结算维度，不能将此变化直接归因给H5、某渠道TC或任一新游戏。</div>
  <section><h2>1. 两周全局回报结构</h2><div class="grid"><div class="kpi"><div class="label">第一周完全下注额</div><strong>{amount(total_first['full_bet'])}</strong><small>加权实际RTP {pct(total_first['actual_rtp'])}</small></div><div class="kpi"><div class="label">第二周完全下注额</div><strong>{amount(total_second['full_bet'])}</strong><small>加权实际RTP {pct(total_second['actual_rtp'])}</small></div><div class="kpi"><div class="label">实际RTP变化</div><strong>{pp(delta)}</strong><small>完全下注与完全实际盈利累计重算</small></div></div>{stage_table}</section>
  <section><h2>2. 分游戏加权RTP与生命周期深钻</h2><p>上表与两张游戏总览图直接使用“生命周期奖池分游戏汇总”中的完全下注额、完全实际盈利计算每款游戏的两周加权RTP；下方热力图和明细表再按生命周期1—4拆分。实际RTP为 <code>1 − Σ完全实际盈利 ÷ Σ完全下注额</code>；不平均每日或分组百分比。</p>{top_table}{figure_html}</section>
  <section><h2>3. 新增用户付费背景</h2><p>新增用户报表仅提供包体/渠道 × cohort 日期的新增、首充、付费与留存字段；没有 <code>game_id</code>，故只作为同期用户结构背景，不与单款游戏RTP作伪精确关联。留存成熟度不足时不以0替代。</p>{new_user_table}</section>
  <section><h2>4. 关键数据限制与下一步</h2><div class="callout warning"><strong>配置预期回报字段覆盖不完整：</strong>第二周仅覆盖 {partial_expected} 的完全下注额。对配置字段为0或缺失的联运游戏，报告不从“完全预期盈利”反推预期RTP，也不将其当作0回报。</div><ol><li><strong>已验证：</strong>{complete_dates}/14日原始导出完整稳定，累计 {quality_count} 项行数、唯一键和实际RTP重算检查通过。</li><li><strong>不能判定：</strong>当前V2（Joint）无包体/渠道与最终结算事实，无法证明“某游戏导致某渠道TC偏高”。</li><li><strong>P0补数：</strong>建立认证聚合事实层：业务日、包体/渠道、游戏、生命周期、有效真金下注、最终结算派奖、有效局数、游戏/配置版本及数据截止时间。</li><li><strong>早期游戏：</strong>Hilo、Plinko、tower在第二周首次出现，未满两个完整周，只保留观察与后续复核，不作稳定性或因果结论。</li></ol></section>
  <details><summary>展开：全部游戏 × 生命周期1—4明细（124行）</summary>{all_detail}</details>
  <div class="sources"><strong>来源与回执</strong><br/>GM Lifecycle Pool V2（Joint）2026-08-14—27日页面导出快照；Origin「BQ-新增付费用户分析」8个包体/渠道Sheet。完整聚合、源文件哈希、质量检查、SQL模板和图表位于项目分析包；所有结果为聚合数据，不含用户、订单、设备、账户或身份明细。</div>
</main></body></html>"""
    HTML_OUT.write_text(document, encoding="utf-8")
    (OUT / "report-receipt.json").write_text(json.dumps({
        "status": "partial",
        "delivery": "local_static_html_fallback",
        "html": str(HTML_OUT.relative_to(ROOT)),
        "markdown": str((OUT / "report.md").relative_to(ROOT)),
        "artifact": str((OUT / "artifact.json").relative_to(ROOT)),
        "quality": str((OUT / "quality-checks.json").relative_to(ROOT)),
        "reason": "The standard portable artifact builder requires a runnable SQL string for every chart, while this analysis uses audited GM UI export snapshots. No unexecuted SQL was presented as a source query.",
        "visual_qa": "five static chart assets inspected; browser-file HTML rendering blocked by browser URL policy",
        "access_limit": "No certified package/channel/game/final-settlement aggregate view is available for causal TC attribution."
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(HTML_OUT)


if __name__ == "__main__":
    main()
