# Whot 埋点评审 HTML 设计说明

- Audience: product stakeholders
- Surface: self-contained portable HTML report
- Reading path: title → 执行摘要 → headline scope → old/new gap → event chain → metrics → comparison design → gameplay tracking → implementation → questions → caveats
- Layout: single-column report flow; all dense tables and the chart use full width
- Visual hierarchy: dark navy text, blue for reusable foundations, orange for new P0 work, red only for unresolved blockers, green for verified/reusable items
- Visual plan: one ordered bar chart shows event-contract footprint by lifecycle stage; exact event/metric/decision mappings use tables
- Non-color distinction: every status is also written as text; P0/P1/reuse labels do not rely on color
- Chart omission: no business-result charts are shown because the evidence is a design contract rather than measured launch data
- QA: canonical artifact validation, packaged HTML delivery, desktop and narrow viewport verification
