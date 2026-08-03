# 图谱维护工具

## 生成代码与资产图谱

在项目根目录执行：

```bash
python3 tools/build_graph.py
```

生成：

- `knowledge/_generated/代码与资产图谱.md`：在 Obsidian 中查看 Mermaid 图
- `knowledge/_generated/code-graph.json`：供后续 Agent、脚本或可视化工具读取

当前脚本无第三方依赖，扫描 Markdown 链接、Obsidian 双向链接以及 Python/JavaScript/TypeScript 相对导入。新增跨资产关系时，优先在 `knowledge/00-索引/资产地图.md` 增加链接，再重新生成。
