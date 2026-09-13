## Claude 协作分析（主 Agent 已验收）

本次仅纠正三处，不重写全篇：①第N自然日成熟条件应为「起点日+(N-1)≤截止日」，此前用+N存在一日偏移；②APP总层(合并Android+iOS)与iOS子端须分层独立判定——iOS起点后仅检测到Android活跃时，APP总层记为同端活跃，iOS子端须记为迁移(非同端)，两层结论不可互相替代或混淆；③LTV只可沿用原认证的生命周期口径，不可从「服务端pay_success为支付成功来源」这一订单口径结论反推或等同为LTV定义，其收入范围、退款、币种换算需另行核验，未核验前不得直接使用。未识别端保护、匹配缺失披露、最小10人保护、支付成功用pay_success而非order_success等既有约束保持不变。以下为5个待执行边界测试，未声称已运行任何SQL或测试。

- [inference] 成熟窗口判定存在偏移：第N自然日成熟条件应为 起点日+(N-1) ≤ 截止日，此前版本用+N会多算一天，导致本应不成熟的批次被误判为成熟并参与跨批次比较。（证据：clarified-contract）
- [inference] APP总层(合并Android+iOS)与iOS子端是两套独立统计口径：iOS起点用户次日仅在Android出现事件时，APP总层(因合并Android+iOS)应记为同端活跃；但在iOS子端拆分统计中，同一天应记为迁移(跨子端/非该子端活跃)，不可用APP层结论覆盖子端层，也不可用子端迁移结论反向判定APP层流失。（证据：confirmed-definition, clarified-contract）
- [inference] LTV必须严格沿用此前已校验的生命周期口径本身作为唯一数据来源；已核验的「服务端pay_success为支付成功来源、order_success仅对应创建订单」这一结论只适用于新增付费/首次付费/留存判定场景，不能被引申为LTV的计算规则或用于替代/校正LTV定义，LTV的收入范围、退款处理、币种换算等细节须另行核验，未核验前不得在报表中直接使用或声明其等价关系。（证据：clarified-contract, known-payment-correction）

待确认：最新独立核验完整业务日期的具体数值尚未提供，成熟窗口判定的实际截止日需由主Agent核实后代入。

任务回执：task-c3a990db61c478de7a70
