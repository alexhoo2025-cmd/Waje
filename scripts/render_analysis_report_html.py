#!/usr/bin/env python3
"""Render a Markdown analysis note as a self-contained, reader-friendly HTML report.

The renderer is deliberately dependency-free so it can run in the existing local
report jobs.  It supports the Markdown structures used by this project: front
matter, headings, paragraphs, block quotes, lists, code fences, tables, links,
and local/remote images.  It escapes source Markdown by default.
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def split_front_matter(source: str) -> tuple[dict[str, str], str]:
    """Return lightweight YAML-like metadata and the Markdown body."""
    lines = source.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, source
    try:
        closing = next(index for index, line in enumerate(lines[1:], 1) if line.strip() == "---")
    except StopIteration:
        return {}, source
    metadata: dict[str, str] = {}
    for line in lines[1:closing]:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip()
    return metadata, "\n".join(lines[closing + 1:]).lstrip("\n")


def safe_href(value: str) -> str:
    """Allow ordinary report links but never emit script/data execution URLs."""
    cleaned = value.strip()
    lowered = cleaned.lower()
    if lowered.startswith(("javascript:", "data:text/html", "vbscript:")):
        return "#"
    return cleaned


def inline_markdown(value: str) -> str:
    """Escape text and restore the small inline Markdown subset used in reports."""
    rendered = html.escape(value, quote=True)
    rendered = re.sub(
        r"!\[([^\]]*)\]\(([^\s)]+)(?:\s+&quot;[^)]*&quot;)?\)",
        lambda match: (
            f'<img src="{safe_href(match.group(2))}" alt="{match.group(1)}" loading="lazy">'
        ),
        rendered,
    )
    rendered = re.sub(
        r"\[([^\]]+)\]\(([^\s)]+)(?:\s+&quot;[^)]*&quot;)?\)",
        lambda match: (
            f'<a href="{safe_href(match.group(2))}" target="_blank" rel="noopener noreferrer">'
            f"{match.group(1)}</a>"
        ),
        rendered,
    )
    rendered = re.sub(r"`([^`]+)`", r"<code>\1</code>", rendered)
    rendered = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", rendered)
    rendered = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", rendered)
    return rendered


def table_cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def is_table_divider(line: str) -> bool:
    cells = table_cells(line)
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell or "") for cell in cells)


def slug(index: int) -> str:
    return f"section-{index}"


def render_body(markdown: str) -> tuple[str, list[tuple[int, str, str]]]:
    """Convert constrained project Markdown into semantic HTML."""
    lines = markdown.splitlines()
    fragments: list[str] = []
    toc: list[tuple[int, str, str]] = []
    paragraph: list[str] = []
    index = 0

    def flush_paragraph() -> None:
        if paragraph:
            content = " ".join(item.strip() for item in paragraph).strip()
            if content:
                fragments.append(f"<p>{inline_markdown(content)}</p>")
            paragraph.clear()

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()

        if not stripped:
            flush_paragraph()
            index += 1
            continue

        if stripped.startswith("```"):
            flush_paragraph()
            language = stripped[3:].strip()
            index += 1
            code_lines: list[str] = []
            while index < len(lines) and not lines[index].strip().startswith("```"):
                code_lines.append(lines[index])
                index += 1
            fragments.append(
                f'<pre class="code-block" data-language="{html.escape(language, quote=True)}"><code>'
                f"{html.escape(chr(10).join(code_lines))}</code></pre>"
            )
            index += 1
            continue

        heading = re.match(r"^(#{1,3})\s+(.+?)\s*$", stripped)
        if heading:
            flush_paragraph()
            level = len(heading.group(1))
            title = heading.group(2).strip()
            anchor = slug(len(toc) + 1)
            toc.append((level, anchor, re.sub(r"[*`_]", "", title)))
            fragments.append(f"<h{level} id=\"{anchor}\">{inline_markdown(title)}</h{level}>")
            index += 1
            continue

        if stripped in {"---", "***", "___"}:
            flush_paragraph()
            fragments.append("<hr>")
            index += 1
            continue

        if stripped.startswith(">"):
            flush_paragraph()
            quote_lines: list[str] = []
            while index < len(lines) and lines[index].strip().startswith(">"):
                quote_lines.append(lines[index].strip()[1:].lstrip())
                index += 1
            fragments.append(f"<blockquote>{inline_markdown(' '.join(quote_lines))}</blockquote>")
            continue

        if stripped.startswith("|") and index + 1 < len(lines) and is_table_divider(lines[index + 1]):
            flush_paragraph()
            headers = table_cells(line)
            index += 2
            rows: list[list[str]] = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                rows.append(table_cells(lines[index]))
                index += 1
            width = len(headers)
            head = "".join(f"<th scope=\"col\">{inline_markdown(cell)}</th>" for cell in headers)
            body: list[str] = []
            for row in rows:
                padded = (row + [""] * width)[:width]
                body.append("<tr>" + "".join(f"<td>{inline_markdown(cell)}</td>" for cell in padded) + "</tr>")
            fragments.append(
                '<div class="table-wrap"><table><thead><tr>' + head + "</tr></thead><tbody>" + "".join(body) + "</tbody></table></div>"
            )
            continue

        unordered = re.match(r"^[-*+]\s+(.+)$", stripped)
        if unordered:
            flush_paragraph()
            items: list[str] = []
            while index < len(lines):
                matched = re.match(r"^[-*+]\s+(.+)$", lines[index].strip())
                if not matched:
                    break
                items.append(f"<li>{inline_markdown(matched.group(1))}</li>")
                index += 1
            fragments.append("<ul>" + "".join(items) + "</ul>")
            continue

        ordered = re.match(r"^\d+[.)]\s+(.+)$", stripped)
        if ordered:
            flush_paragraph()
            items = []
            while index < len(lines):
                matched = re.match(r"^\d+[.)]\s+(.+)$", lines[index].strip())
                if not matched:
                    break
                items.append(f"<li>{inline_markdown(matched.group(1))}</li>")
                index += 1
            fragments.append("<ol>" + "".join(items) + "</ol>")
            continue

        paragraph.append(line)
        index += 1

    flush_paragraph()
    return "\n".join(fragments), toc


def document_html(*, title: str, body: str, toc: list[tuple[int, str, str]], source_name: str, metadata: dict[str, str]) -> str:
    toc_markup = "".join(
        f'<a class="toc-level-{level}" href="#{anchor}">{html.escape(label)}</a>'
        for level, anchor, label in toc
        if level <= 2
    ) or '<span class="toc-empty">报告未使用分级标题</span>'
    updated = metadata.get("updated", dt.date.today().isoformat())
    report_type = metadata.get("type", "analysis-report")
    status = metadata.get("status", "generated")
    css = """
    :root{--ink:#19221f;--muted:#64736a;--canvas:#f3f7f3;--paper:#fff;--line:#dce7dd;--green:#087443;--mint:#e9f7e7;--lime:#c9f46d;--blue:#176bd8;--amber:#b76e00;--rose:#b33a2a;--shadow:0 18px 45px rgba(18,71,42,.09)}
    *{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--canvas);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"SF Pro Display","PingFang SC","Hiragino Sans GB","Microsoft YaHei",Arial,sans-serif;line-height:1.72;font-size:16px}a{color:var(--green);text-decoration:none}a:hover{text-decoration:underline}.topbar{position:sticky;top:0;z-index:20;height:58px;display:flex;align-items:center;border-bottom:1px solid rgba(220,231,221,.9);background:rgba(243,247,243,.93);backdrop-filter:blur(14px)}.topbar-inner{width:min(1240px,calc(100% - 40px));margin:auto;display:flex;align-items:center;justify-content:space-between;gap:20px}.brand{font-size:13px;font-weight:850;letter-spacing:.08em}.brand b{display:inline-grid;place-items:center;width:25px;height:25px;margin-right:8px;border-radius:8px;background:linear-gradient(135deg,#36c677,#087443);color:#fff}.meta{font-size:12px;color:var(--muted)}.shell{width:min(1240px,calc(100% - 40px));margin:0 auto;display:grid;grid-template-columns:230px minmax(0,1fr);gap:34px;padding:44px 0 80px}.toc{position:sticky;top:84px;align-self:start;padding:18px 0}.toc-title{margin-bottom:9px;font-size:11px;letter-spacing:.14em;color:var(--muted);font-weight:850;text-transform:uppercase}.toc a{display:block;padding:5px 10px;border-left:2px solid transparent;font-size:13px;color:var(--muted)}.toc a:hover{border-left-color:var(--green);background:#e9f7e7;color:var(--green);text-decoration:none}.toc-level-2{padding-left:20px!important}.report{min-width:0;background:var(--paper);border:1px solid var(--line);border-radius:24px;padding:clamp(28px,5vw,66px);box-shadow:var(--shadow)}.report h1{font-size:clamp(34px,4.6vw,57px);line-height:1.08;letter-spacing:-.055em;margin:0 0 26px}.report h2{font-size:30px;line-height:1.18;letter-spacing:-.035em;margin:58px 0 18px;padding-top:10px}.report h3{font-size:21px;line-height:1.3;margin:32px 0 12px}.report p{margin:0 0 16px;max-width:860px}.report h1+blockquote,.report h1+p{font-size:19px;color:#415147}.report blockquote{margin:24px 0;padding:18px 20px;border:1px solid #cfebd1;border-left:5px solid var(--green);border-radius:0 15px 15px 0;background:var(--mint);color:#28583c}.report ul,.report ol{padding-left:25px;margin:12px 0 20px}.report li{margin:6px 0}.report hr{height:1px;border:0;background:var(--line);margin:38px 0}.table-wrap{width:100%;margin:18px 0 28px;overflow:auto;border:1px solid var(--line);border-radius:16px}.report table{width:100%;border-collapse:collapse;min-width:610px;font-size:13.5px;background:#fff}.report th,.report td{padding:13px 14px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}.report th{background:#eff7ef;color:#24563a;font-size:12px;letter-spacing:.02em;white-space:nowrap}.report tr:last-child td{border-bottom:0}.report code{padding:2px 6px;border-radius:6px;background:#eef4ef;color:#0b5730;font-family:"SFMono-Regular",Consolas,monospace;font-size:.86em}.code-block{overflow:auto;padding:18px;border-radius:14px;background:#152b37;color:#e8f4ec;line-height:1.55;font-size:12.5px}.code-block code{padding:0;background:transparent;color:inherit}.report img{display:block;max-width:100%;margin:18px auto;border:1px solid var(--line);border-radius:14px;box-shadow:0 9px 25px rgba(20,64,42,.10)}.footer{width:min(1240px,calc(100% - 40px));margin:0 auto 42px;padding-top:18px;border-top:1px solid var(--line);color:var(--muted);font-size:12px}.footer a{margin-left:7px}@media(max-width:900px){.shell{display:block;padding-top:24px}.toc{position:relative;top:auto;margin-bottom:20px;padding:15px;background:rgba(255,255,255,.58);border:1px solid var(--line);border-radius:16px}.toc a{display:inline-block;border:0;padding:5px 7px}.toc-level-2{padding-left:7px!important}.report{padding:28px 22px;border-radius:18px}.topbar-inner,.shell,.footer{width:min(100% - 28px,1240px)}}@media print{body{background:#fff}.topbar,.toc{display:none}.shell{display:block;width:100%;padding:0}.report{box-shadow:none;border:0;border-radius:0;padding:0}.footer{width:100%}.report h2{break-after:avoid}.table-wrap{break-inside:avoid}}
    """
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="report-type" content="{html.escape(report_type, quote=True)}">
  <meta name="report-status" content="{html.escape(status, quote=True)}">
  <title>{html.escape(title)}｜HTML 版</title>
  <style>{css}</style>
</head>
<body>
  <header class="topbar"><div class="topbar-inner"><div class="brand"><b>W</b>WAJE ANALYST</div><div class="meta">HTML 阅读版 · 更新于 {html.escape(updated)}</div></div></header>
  <main class="shell">
    <nav class="toc" aria-label="文档目录"><div class="toc-title">目录</div>{toc_markup}</nav>
    <article class="report">{body}</article>
  </main>
  <footer class="footer">由项目默认 HTML 报告渲染器生成。<a href="{html.escape(source_name, quote=True)}">查看 Markdown 源文件</a></footer>
</body>
</html>
"""


def render_markdown_file(input_path: Path, output_path: Path | None = None, title: str | None = None) -> Path:
    source = input_path.read_text(encoding="utf-8")
    metadata, markdown = split_front_matter(source)
    body, toc = render_body(markdown)
    document_title = title or next((label for level, _anchor, label in toc if level == 1), input_path.stem)
    destination = output_path or input_path.with_suffix(".html")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        document_html(
            title=document_title,
            body=body,
            toc=toc,
            source_name=input_path.name,
            metadata=metadata,
        ),
        encoding="utf-8",
    )
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Markdown report path, relative to project root or absolute")
    parser.add_argument("--output", help="HTML target path, relative to project root or absolute")
    parser.add_argument("--title", help="Optional HTML title")
    args = parser.parse_args()

    def resolve(raw: str | None) -> Path | None:
        if raw is None:
            return None
        path = Path(raw)
        return path if path.is_absolute() else ROOT / path

    target = render_markdown_file(resolve(args.input), resolve(args.output), args.title)
    print(f"html_report={target.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
