#!/usr/bin/env python3
"""Parse article snapshots into reusable logic, layout and chart metadata."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from wechat_common import now_iso, project_root, safe_name, write_json

try:
    from bs4 import BeautifulSoup
except ImportError:  # pragma: no cover - exercised only in minimal environments
    BeautifulSoup = None


METRIC_PATTERNS = {
    "留存": r"留存|retention|d[0-9]+",
    "付费": r"付费|充值|首充|复购|payment|payer|arpu|arppu",
    "LTV": r"ltv|生命周期价值",
    "RTP": r"rtp|回报率|真实回报比|预期回报比",
    "下注": r"下注|stake|wager|bet",
    "派奖": r"派奖|payout|win|奖金",
    "转化": r"转化|漏斗|conversion|funnel",
    "渠道": r"渠道|媒体|归因|campaign|source",
    "版本": r"版本|发版|release|version|包",
    "支付提现": r"支付|提现|cash.?out|withdraw",
    "社交": r"社交|邀请|好友|排行榜|分享|social|referral",
}

CHART_HINTS = [
    ("折线图", r"折线|趋势|line chart|line graph|时间序列"),
    ("柱状图", r"柱状|柱图|bar chart|bar graph"),
    ("饼图", r"饼图|pie chart|占比"),
    ("漏斗图", r"漏斗|funnel"),
    ("热力图", r"热力|heatmap|cohort"),
    ("散点图", r"散点|scatter|气泡"),
    ("表格", r"表格|table|明细|排行"),
    ("指标卡", r"指标卡|dashboard|看板|kpi"),
]


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def parse_dimensions(tag: Any) -> tuple[int | None, int | None, float | None]:
    def as_int(value: Any) -> int | None:
        try:
            return int(str(value).replace("px", "").strip())
        except (TypeError, ValueError):
            return None

    width = as_int(tag.get("width")) if hasattr(tag, "get") else None
    height = as_int(tag.get("height")) if hasattr(tag, "get") else None
    ratio = round(width / height, 4) if width and height else None
    return width, height, ratio


def chart_type_for(text: str, is_table: bool = False) -> str:
    if is_table:
        return "表格"
    for label, pattern in CHART_HINTS:
        if re.search(pattern, text, flags=re.I):
            return label
    return "未识别"


def extract_with_bs4(html: str) -> dict[str, Any]:
    soup = BeautifulSoup(html, "lxml")
    for node in soup(["script", "style", "noscript"]):
        node.decompose()
    title = clean_text((soup.find("h1") or soup.find("title") or soup.title).get_text(" ", strip=True) if (soup.find("h1") or soup.find("title") or soup.title) else "")
    headings = [{"level": int(tag.name[1]), "text": clean_text(tag.get_text(" ", strip=True))} for tag in soup.find_all(re.compile(r"^h[1-6]$")) if clean_text(tag.get_text(" ", strip=True))]
    paragraphs = [clean_text(tag.get_text(" ", strip=True)) for tag in soup.find_all("p")]
    paragraphs = [text for text in paragraphs if text]
    quotes = [clean_text(tag.get_text(" ", strip=True)) for tag in soup.find_all("blockquote")]
    quotes = [text for text in quotes if text]
    separators = len(soup.find_all(["hr"]))
    tables = []
    for table in soup.find_all("table"):
        rows = []
        for row in table.find_all("tr"):
            cells = [clean_text(cell.get_text(" ", strip=True)) for cell in row.find_all(["th", "td"])]
            if cells:
                rows.append(cells)
        if rows:
            tables.append({"rows": rows, "row_count": len(rows), "column_count": max(len(row) for row in rows)})
    images = []
    for index, image in enumerate(soup.find_all("img"), 1):
        src = image.get("src") or image.get("data-src") or image.get("data-original") or ""
        alt = clean_text(image.get("alt", ""))
        caption = ""
        parent = image.parent
        if parent and parent.name in {"figure", "p", "div"}:
            figcaption = parent.find("figcaption")
            caption = clean_text(figcaption.get_text(" ", strip=True)) if figcaption else ""
        width, height, ratio = parse_dimensions(image)
        context = " ".join(part for part in (alt, caption, image.get("title", "")) if part)
        images.append({"position": index, "src": src, "alt": alt, "caption": caption, "width": width, "height": height, "aspect_ratio": ratio, "chart_type": chart_type_for(context)})
    all_text = clean_text(soup.get_text(" ", strip=True))
    first_heading = soup.find(re.compile(r"^h[1-6]$"))
    intro_parts = []
    for node in soup.find_all(["p", "div"]):
        if first_heading and node is first_heading:
            break
        text = clean_text(node.get_text(" ", strip=True))
        if text and text not in intro_parts and len(text) > 10:
            intro_parts.append(text)
        if len(intro_parts) >= 2:
            break
    return {"title": title, "headings": headings, "paragraphs": paragraphs, "quotes": quotes, "separators": separators, "tables": tables, "images": images, "all_text": all_text, "intro": " ".join(intro_parts)[:500]}


def extract_fallback(html: str) -> dict[str, Any]:
    """Parse the report-critical HTML subset without optional third-party packages.

    The production path uses BeautifulSoup when available, but the pipeline must
    still preserve tables, images and headings in a clean Python environment.
    This deliberately keeps the fallback small and metadata-oriented rather than
    attempting to be a browser DOM implementation.
    """

    from html.parser import HTMLParser

    class FallbackParser(HTMLParser):
        def __init__(self) -> None:
            super().__init__(convert_charrefs=True)
            self.suppressed = 0
            self.active: tuple[str, int | None] | None = None
            self.buffer: list[str] = []
            self.title = ""
            self.headings: list[dict[str, Any]] = []
            self.paragraphs: list[str] = []
            self.quotes: list[str] = []
            self.separators = 0
            self.tables: list[dict[str, Any]] = []
            self.current_table: list[list[str]] | None = None
            self.current_row: list[str] | None = None
            self.current_cell: list[str] | None = None
            self.images: list[dict[str, Any]] = []
            self.text_parts: list[str] = []

        def _text(self) -> str:
            return clean_text(" ".join(self.buffer))

        def _finish_active(self) -> None:
            if not self.active:
                return
            kind, level = self.active
            value = self._text()
            if value:
                if kind == "title":
                    self.title = value
                elif kind == "heading":
                    self.headings.append({"level": level, "text": value})
                elif kind == "paragraph":
                    self.paragraphs.append(value)
                elif kind == "quote":
                    self.quotes.append(value)
            self.active = None
            self.buffer = []

        def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            tag = tag.lower()
            attrs_map = {key.lower(): value or "" for key, value in attrs}
            if tag in {"script", "style", "noscript", "template"}:
                self.suppressed += 1
                return
            if self.suppressed:
                return
            if tag in {"title", "p", "blockquote"} or re.fullmatch(r"h[1-6]", tag):
                self._finish_active()
                if tag == "title":
                    self.active = ("title", None)
                elif tag == "p":
                    self.active = ("paragraph", None)
                elif tag == "blockquote":
                    self.active = ("quote", None)
                else:
                    self.active = ("heading", int(tag[1]))
            elif tag == "table":
                self._finish_active()
                self.current_table = []
            elif tag == "tr" and self.current_table is not None:
                self._finish_active()
                self.current_row = []
            elif tag in {"th", "td"} and self.current_row is not None:
                self.current_cell = []
            elif tag == "img":
                width = parse_dimensions(attrs_map)[0]
                height = parse_dimensions(attrs_map)[1]
                ratio = round(width / height, 4) if width and height else None
                alt = clean_text(attrs_map.get("alt", ""))
                context = " ".join(value for value in (alt, attrs_map.get("title", "")) if value)
                self.images.append({
                    "position": len(self.images) + 1,
                    "src": attrs_map.get("src") or attrs_map.get("data-src") or attrs_map.get("data-original", ""),
                    "alt": alt,
                    "caption": "",
                    "width": width,
                    "height": height,
                    "aspect_ratio": ratio,
                    "chart_type": chart_type_for(context),
                })
            elif tag == "hr":
                self.separators += 1

        def handle_endtag(self, tag: str) -> None:
            tag = tag.lower()
            if tag in {"script", "style", "noscript", "template"} and self.suppressed:
                self.suppressed -= 1
                return
            if self.suppressed:
                return
            if tag in {"title", "p", "blockquote"} or re.fullmatch(r"h[1-6]", tag):
                self._finish_active()
            elif tag in {"th", "td"} and self.current_cell is not None:
                self.current_row = self.current_row or []
                self.current_row.append(clean_text(" ".join(self.current_cell)))
                self.current_cell = None
            elif tag == "tr" and self.current_table is not None and self.current_row is not None:
                if any(self.current_row):
                    self.current_table.append(self.current_row)
                self.current_row = None
            elif tag == "table" and self.current_table is not None:
                if self.current_table:
                    self.tables.append({
                        "rows": self.current_table,
                        "row_count": len(self.current_table),
                        "column_count": max(len(row) for row in self.current_table),
                    })
                self.current_table = None

        def handle_data(self, data: str) -> None:
            if self.suppressed:
                return
            value = clean_text(data)
            if not value:
                return
            self.text_parts.append(value)
            if self.current_cell is not None:
                self.current_cell.append(value)
            elif self.active:
                self.buffer.append(value)

    parser = FallbackParser()
    parser.feed(html)
    parser.close()
    parser._finish_active()
    text = clean_text(" ".join(parser.text_parts))
    intro = " ".join(parser.paragraphs[:2])[:500]
    return {
        "title": parser.title or (parser.headings[0]["text"] if parser.headings else ""),
        "headings": parser.headings,
        "paragraphs": parser.paragraphs,
        "quotes": parser.quotes,
        "separators": parser.separators,
        "tables": parser.tables,
        "images": parser.images,
        "all_text": text,
        "intro": intro or text[:500],
    }


def classify_article(record: dict[str, Any], extracted: dict[str, Any]) -> dict[str, Any]:
    text = extracted["all_text"]
    metric_terms = [label for label, pattern in METRIC_PATTERNS.items() if re.search(pattern, text, flags=re.I)]
    evidence_types = []
    if extracted["tables"]:
        evidence_types.append("table")
    if extracted["images"]:
        evidence_types.append("image_or_chart")
    if re.search(r"数据来源|样本|口径|时间范围|database|sample|method|source", text, flags=re.I):
        evidence_types.append("methodology_text")
    if re.search(r"案例|case study|用户|玩家|产品", text, flags=re.I):
        evidence_types.append("case_or_user_context")
    claim_count = len(re.findall(r"因此|说明|意味着|建议|结论|should|recommend|therefore|means", text, flags=re.I))
    recommendations = len(re.findall(r"建议|推荐|应当|可以考虑|下一步|recommend|should|action", text, flags=re.I))
    layout_patterns = []
    if extracted["headings"]:
        layout_patterns.append("章节层级")
    if extracted["tables"]:
        layout_patterns.append("表格证据")
    if extracted["images"]:
        layout_patterns.append("图表/图片证据")
    if extracted["quotes"]:
        layout_patterns.append("引用强调")
    if extracted["separators"]:
        layout_patterns.append("分隔线")
    if len(extracted["paragraphs"]) >= 3:
        layout_patterns.append("短段落")
    chart_types = Counter(image.get("chart_type", "未识别") for image in extracted["images"])
    framework = ["现象/问题", "用户与产品场景", "指标与数据口径", "分群/漏斗/队列/对比", "机制解释", "产品或运营动作", "验证指标"]
    return {
        "analysis_question": extracted["title"] or "待人工确认",
        "analysis_objects": metric_terms[:12],
        "metrics": metric_terms,
        "evidence_types": evidence_types,
        "claim_signal_count": claim_count,
        "recommendation_signal_count": recommendations,
        "layout_patterns": layout_patterns,
        "chart_types": dict(chart_types),
        "analysis_framework": framework,
        "confidence": "heuristic_pending_review",
    }


def parse_record(record: dict[str, Any]) -> dict[str, Any]:
    html = str(record.get("html", ""))
    extracted = extract_with_bs4(html) if BeautifulSoup else extract_fallback(html)
    if not record.get("title") and extracted.get("title"):
        record["title"] = extracted["title"]
    record["structure"] = {
        "intro": extracted["intro"],
        "headings": extracted["headings"],
        "paragraph_count": len(extracted["paragraphs"]),
        "paragraph_lengths": [len(item) for item in extracted["paragraphs"]],
        "paragraph_length_stats": {
            "min": min((len(item) for item in extracted["paragraphs"]), default=0),
            "max": max((len(item) for item in extracted["paragraphs"]), default=0),
            "avg": round(sum(len(item) for item in extracted["paragraphs"]) / len(extracted["paragraphs"]), 2) if extracted["paragraphs"] else 0,
        },
        "quotes": extracted["quotes"],
        "separators": extracted["separators"],
        "tables": extracted["tables"],
        "images": extracted["images"],
    }
    record["analysis"] = classify_article(record, extracted)
    record["parsed_at"] = now_iso()
    return record


def latest_manifest(raw_dir: Path) -> Path | None:
    manifests = sorted(raw_dir.glob("manifest-*.json"))
    return manifests[-1] if manifests else None


def write_article_note(root: Path, day: str, record: dict[str, Any]) -> Path:
    """Create a durable knowledge-base note from parsed public article metadata."""

    analysis = record.get("analysis", {})
    structure = record.get("structure", {})
    note_dir = root / "knowledge/03-竞品/公众号"
    note_dir.mkdir(parents=True, exist_ok=True)
    note_path = note_dir / f"{day}-{safe_name(str(record.get('article_id', 'article')))}-{str(record.get('content_hash', ''))[:12]}.md"
    lines = [
        "---",
        "type: source-note",
        "domain: competitor",
        "status: generated",
        f"updated: {day}",
        "tags: [wechat, social-casino, article-analysis]",
        f"source_access_status: {record.get('source_access_status', '')}",
        "---",
        "",
        f"# {record.get('title') or '未命名文章'}",
        "",
        f"- 文章 ID：`{record.get('article_id', '')}`",
        f"- 原文链接：{record.get('canonical_url') or '未提供'}",
        f"- 发布时间：{record.get('published_at') or '未提供'}",
        f"- 内容哈希：`{record.get('content_hash', '')}`",
        "",
        "> 本笔记由授权只读 API/授权导出自动生成；启发性标签需人工复核，不代表文章原作者结论已被 Waje 验证。",
        "",
        "## 文章结构",
        "",
        f"- 导语：{structure.get('intro') or '未识别'}",
        f"- 章节：{' → '.join(item.get('text', '') for item in structure.get('headings', [])) or '未识别'}",
        f"- 段落数/平均长度：{structure.get('paragraph_count', 0)} / {structure.get('paragraph_length_stats', {}).get('avg', 0)}",
        f"- 引用数/分隔线数：{len(structure.get('quotes', []))} / {structure.get('separators', 0)}",
        "",
        "## 分析标签",
        "",
        f"- 指标主题：{', '.join(analysis.get('metrics', [])) or '未识别'}",
        f"- 证据类型：{', '.join(analysis.get('evidence_types', [])) or '未识别'}",
        f"- 排版模式：{', '.join(analysis.get('layout_patterns', [])) or '未识别'}",
        f"- 图表类型：{', '.join(f'{key}（{value}）' for key, value in analysis.get('chart_types', {}).items()) or '未识别'}",
        f"- 分析链：{' → '.join(analysis.get('analysis_framework', []))}",
        "",
        "## 图片/表格元信息",
        "",
        f"- 图片：{len(structure.get('images', []))}；表格：{len(structure.get('tables', []))}",
    ]
    for image in structure.get("images", []):
        lines.append(f"- 图片 {image.get('position')}: `{image.get('chart_type')}`，{image.get('width') or '?'}×{image.get('height') or '?'}，{image.get('alt') or '无 alt'}")
    note_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return note_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=dt.datetime.now().astimezone().date().isoformat())
    args = parser.parse_args()
    root = project_root()
    raw_dir = root / "data/raw/wechat" / args.date
    processed_dir = root / "data/processed/wechat" / args.date
    manifest_path = latest_manifest(raw_dir)
    records = []
    if manifest_path:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for item in manifest.get("articles", []):
            path = root / item["path"]
            if path.exists():
                record = parse_record(json.loads(path.read_text(encoding="utf-8")))
                records.append(record)
                write_article_note(root, args.date, record)
    payload = {"schema_version": 1, "date": args.date, "source": "wechat_article_parser", "parsed_at": now_iso(), "article_count": len(records), "articles": records}
    target = processed_dir / "articles.json"
    write_json(target, payload)
    print(f"wechat parsing: {len(records)} articles; output={target.relative_to(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
