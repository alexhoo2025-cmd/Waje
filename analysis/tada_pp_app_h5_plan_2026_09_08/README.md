# Tada／PP跨端分析方案交付包

本次只设计数据获取与分析方案；正式业务结果未取数。

## 阅读入口

- `方案.md`：完整中文方案，与飞书文档同源。
- `metric-dictionary.json`：13组指标的定义、算法、分母、来源接口、粒度及维度。
- `schema.json`：逻辑输入与聚合输出契约；不是已经部署的数据库表。
- `sources.json`：7项历史资料路径、用途与当前文件哈希。
- `sql/00_metadata.sql`：授权恢复后可审核使用的元数据查询设计，尚未执行。
- `sql/01_performance.sql.template`：下注份额与RTP聚合模板。`NORMALIZED_BETS_CTE`未绑定，不能直接执行生产查询。
- `reference_logic.py`、`test_contract.py`：模拟计算规则与17个验收用例。
- `access-receipt.json`：BigQuery元数据访问仍需授权。
- `review-receipt.json`：Sonnet独立审查未取得结果；不计为通过。
- `lark-verification.json`：飞书创建与完整回读结果。

## 复验

```bash
python3 analysis/tada_pp_app_h5_plan_2026_09_08/test_contract.py
```

测试只使用明确构造的模拟记录。测试成功代表规则在这些场景中一致，不代表真实上报、结算语义或本期数据已经认证。

## 正式取数前

1. 恢复原企业BigQuery连接并确认wajenigeria可见和获批数据范围。
2. 通过Q00—Q02确认物理字段、完整日、实际端、游戏身份、币种和最终结算。
3. 将认证只读CTE绑定到模板；固定研究产品／包体版本、时间窗及资产范围。
4. 对同批下注、日UV／期UV、回访状态和共享钱包分别对账，再输出隐私安全聚合。

不自动新建BigQuery表、不变更埋点／推荐／RTP／机器人配置、不输出账号或订单明细。窗口示例不是已验证的最新完整日。
