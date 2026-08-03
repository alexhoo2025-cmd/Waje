#!/usr/bin/env python3
"""Build a lightweight knowledge + code/asset graph for the repository.

The script intentionally uses only the Python standard library. It scans:
  - Markdown wikilinks and relative Markdown links
  - Python imports
  - JavaScript/TypeScript imports and require() calls

Outputs are generated under knowledge/_generated and should not be edited by hand.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import unquote


SOURCE_EXTENSIONS = {
    ".md", ".mdx", ".json", ".html", ".htm", ".py", ".js", ".jsx",
    ".ts", ".tsx", ".sql", ".sh", ".yaml", ".yml", ".toml",
}
SKIP_DIRS = {".git", ".obsidian", "node_modules", "dist", "build", "_generated"}


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def collect_files(root: Path) -> list[Path]:
    result = []
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in SOURCE_EXTENSIONS:
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        result.append(path)
    return sorted(result)


def candidate_paths(raw: str, source: Path, root: Path) -> list[Path]:
    raw = unquote(raw.strip().replace("\\", "/"))
    raw = raw.split("#", 1)[0].split("?", 1)[0]
    if not raw or raw.startswith(("http://", "https://", "mailto:", "data:")):
        return []
    raw_path = Path(raw)
    base = (source.parent / raw_path).resolve() if raw.startswith(".") else (root / raw_path).resolve()
    try:
        base.relative_to(root.resolve())
    except ValueError:
        return []
    candidates = [base]
    if not base.suffix:
        candidates.extend(base.with_suffix(ext) for ext in SOURCE_EXTENSIONS)
        candidates.append(base / "index.md")
    return candidates


def resolve_link(raw: str, source: Path, root: Path, known: set[str]) -> str | None:
    for candidate in candidate_paths(raw, source, root):
        if candidate.is_file():
            candidate_rel = rel(candidate, root)
            if candidate_rel in known:
                return candidate_rel
        candidate_rel = candidate.relative_to(root).as_posix()
        if candidate_rel in known:
            return candidate_rel
    # Obsidian links can omit a folder or extension. Resolve by exact stem only.
    target = Path(raw.split("#", 1)[0]).name
    matches = [item for item in known if Path(item).stem == target or item == raw]
    return matches[0] if len(matches) == 1 else None


def markdown_edges(path: Path, text: str, root: Path, known: set[str]) -> list[tuple[str, str, str]]:
    source = rel(path, root)
    edges = []
    wikilinks = re.findall(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]", text)
    for target in wikilinks:
        destination = resolve_link(target.strip(), path, root, known)
        if destination and destination != source:
            edges.append((source, destination, "wikilink"))
    markdown_links = re.findall(r"\]\(<?([^)>\s]+)>?\)", text)
    for target in markdown_links:
        destination = resolve_link(target, path, root, known)
        if destination and destination != source:
            edges.append((source, destination, "link"))
    return edges


def code_edges(path: Path, text: str, root: Path, known: set[str]) -> list[tuple[str, str, str]]:
    source = rel(path, root)
    refs: list[tuple[str, str]] = []
    if path.suffix == ".py":
        refs += [(item, "import") for item in re.findall(r"(?:from|import)\s+([\w./-]+)", text)]
    if path.suffix in {".js", ".jsx", ".ts", ".tsx"}:
        refs += [(item, "import") for item in re.findall(r"(?:from\s*|import\s*\(|require\s*\()['\"]([^'\"]+)", text)]
    edges = []
    for target, kind in refs:
        if not target.startswith("."):
            continue
        destination = resolve_link(target, path, root, known)
        if destination and destination != source:
            edges.append((source, destination, kind))
    return edges


def node_id(path: str) -> str:
    readable = re.sub(r"[^A-Za-z0-9_]", "_", path)
    digest = hashlib.sha1(path.encode("utf-8")).hexdigest()[:8]
    return "n_" + readable[:48] + "_" + digest


def build(root: Path) -> tuple[list[dict], list[dict]]:
    files = collect_files(root)
    known = {rel(path, root) for path in files}
    nodes = [
        {
            "id": path,
            "label": path,
            "kind": "knowledge" if path.startswith("knowledge/") else "asset",
        }
        for path in sorted(known)
    ]
    edges: set[tuple[str, str, str]] = set()
    for path in files:
        text = path.read_text(encoding="utf-8", errors="ignore")
        if path.suffix in {".md", ".mdx"}:
            edges.update(markdown_edges(path, text, root, known))
        edges.update(code_edges(path, text, root, known))
    edge_rows = [{"source": a, "target": b, "type": c} for a, b, c in sorted(edges)]
    return nodes, edge_rows


def render_mermaid(nodes: list[dict], edges: list[dict]) -> str:
    lines = ["```mermaid", "flowchart LR"]
    for node in nodes:
        label = node["label"].replace('"', "'")
        lines.append(f'  {node_id(node["id"])}["{label}"]')
    for edge in edges:
        lines.append(
            f'  {node_id(edge["source"])} -->|{edge["type"]}| {node_id(edge["target"])}'
        )
    lines.append("```")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    root = args.root.resolve()
    out = (args.out or root / "knowledge/_generated").resolve()
    out.mkdir(parents=True, exist_ok=True)

    nodes, edges = build(root)
    payload = {
        "generated_at": __import__("datetime").datetime.now().astimezone().isoformat(timespec="seconds"),
        "root": str(root),
        "nodes": nodes,
        "edges": edges,
    }
    (out / "code-graph.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    mermaid_edges = edges[:250]
    note = (
        "---\n"
        "type: generated-graph\n"
        "status: generated\n"
        "updated: " + payload["generated_at"][:10] + "\n"
        "tags: [generated, code-graph, asset-graph]\n"
        "---\n\n"
        "# 代码与资产图谱\n\n"
        "由 `tools/build_graph.py` 生成。节点来自项目文件；边来自 Markdown 链接、Obsidian 双向链接以及 Python/JS/TS 的相对导入。\n\n"
        f"节点数：{len(nodes)}；关系数：{len(edges)}。\n\n"
        + render_mermaid(nodes, mermaid_edges)
        + "\n\n> Mermaid 关系超过 250 条时仅展示前 250 条，完整数据见 `code-graph.json`。\n"
    )
    (out / "代码与资产图谱.md").write_text(note, encoding="utf-8")
    print(f"generated {len(nodes)} nodes and {len(edges)} edges in {out}")


if __name__ == "__main__":
    main()
