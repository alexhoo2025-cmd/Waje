# 活跃基数口径核查

- 直接证据：原执行SQL `analysis/tada_pp_app_h5_actual_2026_09_08/sql/16_full_active_base.sql`，active CTE从`wajenigeria.origin_hfyl.realtime_edw_user_version_daily`取统计期账号，最终COUNT(DISTINCT user_id)。无下注条件。
- 可确定：899,442与458,169为相应渠道人群在平台用户日表中的去重账号数，不是厂商下注人数。
- 交叉对照：核心游戏聚合中，同期新用户全部Waje游戏下注人数分别为APP 525,457、H5 210,880，与日表基数不同；不是本次新增线上查询。
- 暂缺：该用户日表的生成逻辑、触发事件及与登录/页面访问的对应关系。不能仅凭表名认证为访问UV。
- 本次仅补充该限制与定义，不修改数据、不推算未下注用户交集；渗透率数值保持日表分母口径。
