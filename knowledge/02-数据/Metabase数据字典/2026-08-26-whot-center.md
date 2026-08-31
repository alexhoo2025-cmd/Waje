---
type: metabase_schema_dictionary
date: 2026-08-26
schema: whot_center
status: observed_metadata
source_engine: mysql_style_information_schema_export
---

# Metabase 数据字典｜whot_center

> 证据边界：本分册来自可见 `information_schema` 定义。字段值、默认值、连接参数、敏感字段原文均未保存；字段用途和数据层标记中“命名推断”均需由业务 Owner 或数据开发补证。

## 1. Schema 概览

- 表：**245** 张；字段：**2,597** 个。
- 数据层：业务表（事实/维度待补证）。
- 外键、分区、索引明细、行数、更新时刻、保留周期：本次未导出，不能推断。

## 2. 表清单

| 表 | 类型 | 字段数 | 业务域（命名推断） | 受控字段候选数 | 表说明 |
|---|---|---:|---|---:|---|
| `ad_eagllwin_attribution` | BASE TABLE | 11 | 待分类 | 0 | Eagllwin one-party attribution callback state |
| `ad_eagllwin_attribution_v2` | BASE TABLE | 9 | 待分类 | 0 | Eagllwin attribution callback state v2 |
| `ad_eagllwin_user_attribution_v2` | BASE TABLE | 11 | 用户 / 账号 | 0 | Eagllwin per-user event state v2 |
| `agent_operate_log` | BASE TABLE | 9 | 日志 / 数据质量 | 0 | 代理操作表 |
| `ams_asset` | BASE TABLE | 7 | 资产 / 货币 | 0 | 用户资产表 |
| `ams_bill_000000` | BASE TABLE | 14 | 待分类 | 0 | 账单表 |
| `ams_bill_202510` | BASE TABLE | 14 | 待分类 | 0 | 账单表 |
| `ams_bill_202511` | BASE TABLE | 14 | 待分类 | 0 | 账单表 |
| `ams_bill_202512` | BASE TABLE | 14 | 待分类 | 0 | 账单表 |
| `ams_bill_202601` | BASE TABLE | 14 | 待分类 | 0 | 账单表 |
| `ams_bill_202602` | BASE TABLE | 14 | 待分类 | 0 | 账单表 |
| `ams_bill_202603` | BASE TABLE | 14 | 待分类 | 0 | 账单表 |
| `ams_bill_202604` | BASE TABLE | 14 | 待分类 | 0 | 账单表 |
| `ams_bill_202605` | BASE TABLE | 14 | 待分类 | 0 | 账单表 |
| `ams_bill_202606` | BASE TABLE | 14 | 待分类 | 0 | 账单表 |
| `ams_bill_202607` | BASE TABLE | 14 | 待分类 | 0 | 账单表 |
| `ams_bill_202608` | BASE TABLE | 14 | 待分类 | 0 | 账单表 |
| `ams_bill_extra_000000` | BASE TABLE | 12 | 待分类 | 0 | 账单扩展表 |
| `ams_bill_extra_202510` | BASE TABLE | 12 | 待分类 | 0 | 账单扩展表 |
| `ams_bill_extra_202511` | BASE TABLE | 12 | 待分类 | 0 | 账单扩展表 |
| `ams_bill_extra_202512` | BASE TABLE | 12 | 待分类 | 0 | 账单扩展表 |
| `ams_bill_extra_202601` | BASE TABLE | 12 | 待分类 | 0 | 账单扩展表 |
| `ams_bill_extra_202602` | BASE TABLE | 12 | 待分类 | 0 | 账单扩展表 |
| `ams_bill_extra_202603` | BASE TABLE | 12 | 待分类 | 0 | 账单扩展表 |
| `ams_bill_extra_202604` | BASE TABLE | 12 | 待分类 | 0 | 账单扩展表 |
| `ams_bill_extra_202605` | BASE TABLE | 12 | 待分类 | 0 | 账单扩展表 |
| `ams_bill_extra_202606` | BASE TABLE | 12 | 待分类 | 0 | 账单扩展表 |
| `ams_bill_extra_202607` | BASE TABLE | 12 | 待分类 | 0 | 账单扩展表 |
| `ams_bill_extra_202608` | BASE TABLE | 12 | 待分类 | 0 | 账单扩展表 |
| `ams_charge_000000` | BASE TABLE | 10 | 待分类 | 0 | 资产变化表 |
| `ams_charge_202401` | BASE TABLE | 9 | 待分类 | 0 | 资产变化表 |
| `ams_charge_202402` | BASE TABLE | 9 | 待分类 | 0 | 资产变化表 |
| `ams_charge_202403` | BASE TABLE | 9 | 待分类 | 0 | 资产变化表 |
| `ams_charge_202404` | BASE TABLE | 9 | 待分类 | 0 | 资产变化表 |
| `ams_charge_202405` | BASE TABLE | 9 | 待分类 | 0 | 资产变化表 |
| `ams_charge_202406` | BASE TABLE | 9 | 待分类 | 0 | 资产变化表 |
| `ams_charge_202407` | BASE TABLE | 9 | 待分类 | 0 | 资产变化表 |
| `ams_charge_202408` | BASE TABLE | 9 | 待分类 | 0 | 资产变化表 |
| `ams_charge_202409` | BASE TABLE | 9 | 待分类 | 0 | 资产变化表 |
| `ams_charge_202410` | BASE TABLE | 9 | 待分类 | 0 | 资产变化表 |
| `ams_charge_202411` | BASE TABLE | 9 | 待分类 | 0 | 资产变化表 |
| `ams_charge_202412` | BASE TABLE | 9 | 待分类 | 0 | 资产变化表 |
| `ams_charge_202501` | BASE TABLE | 9 | 待分类 | 0 | 资产变化表 |
| `ams_charge_202502` | BASE TABLE | 9 | 待分类 | 0 | 资产变化表 |
| `ams_charge_202503` | BASE TABLE | 9 | 待分类 | 0 | 资产变化表 |
| `ams_charge_202504` | BASE TABLE | 9 | 待分类 | 0 | 资产变化表 |
| `ams_charge_202505` | BASE TABLE | 9 | 待分类 | 0 | 资产变化表 |
| `ams_charge_202506` | BASE TABLE | 9 | 待分类 | 0 | 资产变化表 |
| `ams_charge_202507` | BASE TABLE | 9 | 待分类 | 0 | 资产变化表 |
| `ams_charge_202508` | BASE TABLE | 10 | 待分类 | 0 | 资产变化表 |
| `ams_charge_202509` | BASE TABLE | 10 | 待分类 | 0 | 资产变化表 |
| `ams_charge_202510` | BASE TABLE | 10 | 待分类 | 0 | 资产变化表 |
| `ams_charge_202511` | BASE TABLE | 10 | 待分类 | 0 | 资产变化表 |
| `ams_charge_202512` | BASE TABLE | 10 | 待分类 | 0 | 资产变化表 |
| `ams_charge_202601` | BASE TABLE | 10 | 待分类 | 0 | 资产变化表 |
| `ams_charge_202602` | BASE TABLE | 10 | 待分类 | 0 | 资产变化表 |
| `ams_charge_202603` | BASE TABLE | 10 | 待分类 | 0 | 资产变化表 |
| `ams_charge_202604` | BASE TABLE | 10 | 待分类 | 0 | 资产变化表 |
| `ams_charge_202605` | BASE TABLE | 10 | 待分类 | 0 | 资产变化表 |
| `ams_charge_202606` | BASE TABLE | 10 | 待分类 | 0 | 资产变化表 |
| `ams_charge_202607` | BASE TABLE | 10 | 待分类 | 0 | 资产变化表 |
| `ams_charge_202608` | BASE TABLE | 10 | 待分类 | 0 | 资产变化表 |
| `ams_diamond_asset` | BASE TABLE | 7 | 资产 / 货币 | 0 | 用户资产表 |
| `ams_diamond_charge_000000` | BASE TABLE | 10 | 资产 / 货币 | 0 | 资产变化表 |
| `ams_diamond_charge_202512` | BASE TABLE | 10 | 资产 / 货币 | 0 | 资产变化表 |
| `ams_diamond_charge_202601` | BASE TABLE | 10 | 资产 / 货币 | 0 | 资产变化表 |
| `ams_diamond_charge_202602` | BASE TABLE | 10 | 资产 / 货币 | 0 | 资产变化表 |
| `ams_diamond_charge_202603` | BASE TABLE | 10 | 资产 / 货币 | 0 | 资产变化表 |
| `ams_diamond_charge_202604` | BASE TABLE | 10 | 资产 / 货币 | 0 | 资产变化表 |
| `ams_diamond_charge_202605` | BASE TABLE | 10 | 资产 / 货币 | 0 | 资产变化表 |
| `ams_diamond_charge_202606` | BASE TABLE | 10 | 资产 / 货币 | 0 | 资产变化表 |
| `ams_diamond_charge_202607` | BASE TABLE | 10 | 资产 / 货币 | 0 | 资产变化表 |
| `ams_diamond_charge_202608` | BASE TABLE | 10 | 资产 / 货币 | 0 | 资产变化表 |
| `baccarat_record_log` | BASE TABLE | 28 | 游戏 / 对局 / RTP | 0 | 百家乐游戏记录数据 |
| `ball_game_state` | BASE TABLE | 4 | 游戏 / 对局 / RTP | 0 | — |
| `betc_casino_bet_info` | BASE TABLE | 10 | 游戏 / 对局 / RTP | 1 | — |
| `collector_cash_active` | BASE TABLE | 11 | 待分类 | 0 | — |
| `collector_remain_report` | BASE TABLE | 6 | 待分类 | 0 | — |
| `collector_report` | BASE TABLE | 10 | 待分类 | 0 | 数据表 |
| `easy_bet` | BASE TABLE | 23 | 游戏 / 对局 / RTP | 0 | — |
| `easy_win_competition_info` | BASE TABLE | 7 | 待分类 | 0 | — |
| `easy_win_fav_casina` | BASE TABLE | 6 | 待分类 | 0 | — |
| `email_log` | BASE TABLE | 7 | 运营 / 消息 | 0 | [已脱敏：敏感字段说明不进入知识库] |
| `email_stat` | BASE TABLE | 5 | 运营 / 消息 | 0 | [已脱敏：敏感字段说明不进入知识库] |
| `ew_booking_code` | BASE TABLE | 14 | 待分类 | 0 | — |
| `ew_copied_bet` | BASE TABLE | 17 | 游戏 / 对局 / RTP | 0 | — |
| `ew_shared_bet` | BASE TABLE | 21 | 游戏 / 对局 / RTP | 0 | — |
| `ew_user_follow` | BASE TABLE | 4 | 用户 / 账号 | 0 | — |
| `extra_remark` | BASE TABLE | 4 | 待分类 | 1 | 额外备注 |
| `finance_transfer_log` | BASE TABLE | 9 | 支付 / 提现 | 0 | 转账记录表 |
| `game_diamond_record_000000` | BASE TABLE | 7 | 资产 / 货币 | 0 | 游戏钻石下注记录 |
| `game_diamond_record_202511` | BASE TABLE | 7 | 资产 / 货币 | 0 | 游戏钻石下注记录 |
| `game_diamond_record_202512` | BASE TABLE | 7 | 资产 / 货币 | 0 | 游戏钻石下注记录 |
| `game_diamond_record_202601` | BASE TABLE | 7 | 资产 / 货币 | 0 | 游戏钻石下注记录 |
| `game_diamond_record_202602` | BASE TABLE | 7 | 资产 / 货币 | 0 | 游戏钻石下注记录 |
| `game_diamond_record_202603` | BASE TABLE | 7 | 资产 / 货币 | 0 | 游戏钻石下注记录 |
| `game_diamond_record_202604` | BASE TABLE | 7 | 资产 / 货币 | 0 | 游戏钻石下注记录 |
| `game_diamond_record_202605` | BASE TABLE | 7 | 资产 / 货币 | 0 | 游戏钻石下注记录 |
| `game_diamond_record_202606` | BASE TABLE | 7 | 资产 / 货币 | 0 | 游戏钻石下注记录 |
| `game_diamond_record_202607` | BASE TABLE | 7 | 资产 / 货币 | 0 | 游戏钻石下注记录 |
| `game_diamond_record_202608` | BASE TABLE | 7 | 资产 / 货币 | 0 | 游戏钻石下注记录 |
| `game_record` | BASE TABLE | 7 | 游戏 / 对局 / RTP | 0 | — |
| `invite_bind_bank_record` | BASE TABLE | 4 | 待分类 | 0 | — |
| `invite_rebate_detail` | BASE TABLE | 9 | 待分类 | 0 | — |
| `invite_reward` | BASE TABLE | 14 | 待分类 | 0 | 邀请用户表 |
| `invite_stat_tree_info` | BASE TABLE | 3 | 待分类 | 0 | — |
| `invite_tree_node` | BASE TABLE | 10 | 待分类 | 0 | — |
| `invite_user` | BASE TABLE | 18 | 用户 / 账号 | 0 | 邀请用户表 |
| `invite_user_reward_data` | BASE TABLE | 6 | 用户 / 账号 | 0 | — |
| `kfc_info` | BASE TABLE | 7 | 待分类 | 3 | — |
| `kyc_bank_info` | BASE TABLE | 10 | KYC / 风控 | 4 | — |
| `kyc_bvn_info` | BASE TABLE | 9 | KYC / 风控 | 2 | — |
| `kyc_event_log` | BASE TABLE | 16 | KYC / 风控 | 1 | kyc事件统计 |
| `kyc_face_bvn_event_log` | BASE TABLE | 19 | KYC / 风控 | 12 | [已脱敏：敏感字段说明不进入知识库] |
| `kyc_face_info` | BASE TABLE | 15 | KYC / 风控 | 5 | — |
| `kyc_face_phone_event_log` | BASE TABLE | 20 | KYC / 风控 | 13 | [已脱敏：敏感字段说明不进入知识库] |
| `kyc_phone_event_log` | BASE TABLE | 20 | KYC / 风控 | 14 | [已脱敏：敏感字段说明不进入知识库] |
| `mail_mail` | BASE TABLE | 10 | 运营 / 消息 | 0 | 邮件列表 |
| `nima_charge` | BASE TABLE | 9 | 待分类 | 0 | 泥马记录 |
| `nima_charge_backup_1` | BASE TABLE | 9 | 待分类 | 0 | 泥马记录 |
| `nima_charge_history_2023` | BASE TABLE | 9 | 待分类 | 0 | 泥马记录 |
| `order_extra_log` | BASE TABLE | 5 | 支付 / 提现 | 0 | 充值扩展表 |
| `order_log` | BASE TABLE | 13 | 支付 / 提现 | 0 | 充值提现订单 |
| `order_withdraw_info` | BASE TABLE | 9 | 支付 / 提现 | 0 | 提现订单 |
| `order_withdraw_review` | BASE TABLE | 14 | 支付 / 提现 | 0 | 提现审核订单 |
| `profile_task` | BASE TABLE | 5 | 用户 / 账号 | 0 | 个人信息任务表 |
| `recall_log` | BASE TABLE | 8 | 日志 / 数据质量 | 0 | 召回记录 |
| `record_log` | BASE TABLE | 24 | 日志 / 数据质量 | 0 | 录像数据 |
| `record_video` | BASE TABLE | 6 | 待分类 | 0 | 录像数据 |
| `risk_info` | BASE TABLE | 7 | KYC / 风控 | 0 | — |
| `risk_recharge` | BASE TABLE | 7 | KYC / 风控 | 0 | — |
| `risk_rule` | BASE TABLE | 4 | KYC / 风控 | 0 | — |
| `sms_log` | BASE TABLE | 6 | 运营 / 消息 | 0 | sms日志 |
| `sms_otp_stat` | BASE TABLE | 6 | 运营 / 消息 | 0 | sms统计 |
| `sports_bet_info` | BASE TABLE | 9 | 游戏 / 对局 / RTP | 1 | — |
| `stat_action_rate` | BASE TABLE | 7 | 待分类 | 0 | 行为率 |
| `stat_cash_black_report` | BASE TABLE | 23 | 待分类 | 0 | — |
| `stat_cash_data` | BASE TABLE | 17 | 待分类 | 0 | — |
| `stat_game_bet_gain` | BASE TABLE | 7 | 游戏 / 对局 / RTP | 0 | 游戏下注&赢 |
| `stat_jackpot_change` | BASE TABLE | 8 | 待分类 | 0 | 奖池变更 |
| `stat_lifecycle_pool_log` | BASE TABLE | 8 | 日志 / 数据质量 | 0 | 生命周期奖池奖池变更日志 |
| `stat_lifecycle_pool_log_v2` | BASE TABLE | 14 | 日志 / 数据质量 | 0 | 生命周期奖池奖池变更日志第二版 |
| `stat_lifecycle_pool_v2_log` | BASE TABLE | 14 | 日志 / 数据质量 | 0 | 生命周期奖池奖池变更日志第二版 |
| `stat_lifecyclev2_fix_detail` | BASE TABLE | 5 | 待分类 | 0 | 生命周期v2首充有效充值修正 |
| `stat_lifecyclev2_rtp_record` | BASE TABLE | 9 | 游戏 / 对局 / RTP | 0 | 生命周期v2回报比打点 |
| `stat_lifecyclev2_withdraw_detail` | BASE TABLE | 7 | 支付 / 提现 | 0 | 生命周期v2提现详情 |
| `stat_seven_day_reward_detail` | BASE TABLE | 9 | 待分类 | 0 | 七日奖励领取详情表 |
| `stat_user_action` | BASE TABLE | 6 | 用户 / 账号 | 0 | 游戏行为 |
| `stat_user_action_sync` | BASE TABLE | 6 | 用户 / 账号 | 0 | 游戏行为 |
| `stat_user_asset_change_profit_000000` | BASE TABLE | 16 | 资产 / 货币 | 0 | 资产变化时终身盈利记录 |
| `stat_user_asset_change_profit_202407` | BASE TABLE | 16 | 资产 / 货币 | 0 | 资产变化时终身盈利记录 |
| `stat_user_asset_change_profit_202408` | BASE TABLE | 16 | 资产 / 货币 | 0 | 资产变化时终身盈利记录 |
| `stat_user_asset_change_profit_202409` | BASE TABLE | 16 | 资产 / 货币 | 0 | 资产变化时终身盈利记录 |
| `stat_user_asset_change_profit_202410` | BASE TABLE | 16 | 资产 / 货币 | 0 | 资产变化时终身盈利记录 |
| `stat_user_asset_change_profit_202411` | BASE TABLE | 16 | 资产 / 货币 | 0 | 资产变化时终身盈利记录 |
| `stat_user_asset_change_profit_202412` | BASE TABLE | 16 | 资产 / 货币 | 0 | 资产变化时终身盈利记录 |
| `stat_user_asset_change_profit_202501` | BASE TABLE | 16 | 资产 / 货币 | 0 | 资产变化时终身盈利记录 |
| `stat_user_asset_change_profit_202502` | BASE TABLE | 16 | 资产 / 货币 | 0 | 资产变化时终身盈利记录 |
| `stat_user_asset_change_profit_202503` | BASE TABLE | 16 | 资产 / 货币 | 0 | 资产变化时终身盈利记录 |
| `stat_user_asset_change_profit_202504` | BASE TABLE | 16 | 资产 / 货币 | 0 | 资产变化时终身盈利记录 |
| `stat_user_asset_change_profit_202505` | BASE TABLE | 16 | 资产 / 货币 | 0 | 资产变化时终身盈利记录 |
| `stat_user_asset_change_profit_202506` | BASE TABLE | 16 | 资产 / 货币 | 0 | 资产变化时终身盈利记录 |
| `stat_user_asset_change_profit_202507` | BASE TABLE | 16 | 资产 / 货币 | 0 | 资产变化时终身盈利记录 |
| `stat_user_asset_change_profit_202508` | BASE TABLE | 16 | 资产 / 货币 | 0 | 资产变化时终身盈利记录 |
| `stat_user_asset_change_profit_202509` | BASE TABLE | 16 | 资产 / 货币 | 0 | 资产变化时终身盈利记录 |
| `stat_user_asset_change_profit_202510` | BASE TABLE | 16 | 资产 / 货币 | 0 | 资产变化时终身盈利记录 |
| `stat_user_asset_change_profit_202511` | BASE TABLE | 16 | 资产 / 货币 | 0 | 资产变化时终身盈利记录 |
| `stat_user_asset_change_profit_202512` | BASE TABLE | 16 | 资产 / 货币 | 0 | 资产变化时终身盈利记录 |
| `stat_user_asset_change_profit_202601` | BASE TABLE | 16 | 资产 / 货币 | 0 | 资产变化时终身盈利记录 |
| `stat_user_asset_change_profit_202602` | BASE TABLE | 16 | 资产 / 货币 | 0 | 资产变化时终身盈利记录 |
| `stat_user_asset_change_profit_202603` | BASE TABLE | 16 | 资产 / 货币 | 0 | 资产变化时终身盈利记录 |
| `stat_user_asset_change_profit_202604` | BASE TABLE | 16 | 资产 / 货币 | 0 | 资产变化时终身盈利记录 |
| `stat_user_asset_change_profit_202605` | BASE TABLE | 16 | 资产 / 货币 | 0 | 资产变化时终身盈利记录 |
| `stat_user_asset_change_profit_202606` | BASE TABLE | 16 | 资产 / 货币 | 0 | 资产变化时终身盈利记录 |
| `stat_user_asset_change_profit_202607` | BASE TABLE | 16 | 资产 / 货币 | 0 | 资产变化时终身盈利记录 |
| `stat_user_asset_change_profit_202608` | BASE TABLE | 16 | 资产 / 货币 | 0 | 资产变化时终身盈利记录 |
| `stat_user_control_daily` | BASE TABLE | 7 | 用户 / 账号 | 0 | 每日用户属性 |
| `stat_user_control_detail` | BASE TABLE | 8 | 用户 / 账号 | 0 | 用户控制详情 |
| `stat_user_flow` | BASE TABLE | 10 | 用户 / 账号 | 0 | 用户输赢流水表 |
| `stat_user_flow_detail_202410` | BASE TABLE | 7 | 用户 / 账号 | 0 | 用户输赢流水详情 |
| `stat_user_flow_detail_202411` | BASE TABLE | 7 | 用户 / 账号 | 0 | 用户输赢流水详情 |
| `stat_user_flow_detail_202412` | BASE TABLE | 7 | 用户 / 账号 | 0 | 用户输赢流水详情 |
| `stat_user_flow_detail_202501` | BASE TABLE | 7 | 用户 / 账号 | 0 | 用户输赢流水详情 |
| `stat_user_flow_detail_202502` | BASE TABLE | 7 | 用户 / 账号 | 0 | 用户输赢流水详情 |
| `stat_user_flow_detail_202503` | BASE TABLE | 7 | 用户 / 账号 | 0 | 用户输赢流水详情 |
| `stat_user_flow_detail_202504` | BASE TABLE | 7 | 用户 / 账号 | 0 | 用户输赢流水详情 |
| `stat_user_flow_detail_202505` | BASE TABLE | 7 | 用户 / 账号 | 0 | 用户输赢流水详情 |
| `stat_user_flow_detail_202506` | BASE TABLE | 7 | 用户 / 账号 | 0 | 用户输赢流水详情 |
| `stat_user_flow_detail_202507` | BASE TABLE | 7 | 用户 / 账号 | 0 | 用户输赢流水详情 |
| `stat_user_flow_detail_202508` | BASE TABLE | 7 | 用户 / 账号 | 0 | 用户输赢流水详情 |
| `stat_user_flow_detail_202509` | BASE TABLE | 7 | 用户 / 账号 | 0 | 用户输赢流水详情 |
| `stat_user_flow_detail_202510` | BASE TABLE | 7 | 用户 / 账号 | 0 | 用户输赢流水详情 |
| `stat_user_flow_detail_202511` | BASE TABLE | 7 | 用户 / 账号 | 0 | 用户输赢流水详情 |
| `stat_user_flow_detail_202512` | BASE TABLE | 7 | 用户 / 账号 | 0 | 用户输赢流水详情 |
| `stat_user_flow_detail_202601` | BASE TABLE | 7 | 用户 / 账号 | 0 | 用户输赢流水详情 |
| `stat_user_flow_detail_202602` | BASE TABLE | 7 | 用户 / 账号 | 0 | 用户输赢流水详情 |
| `stat_user_flow_detail_202603` | BASE TABLE | 7 | 用户 / 账号 | 0 | 用户输赢流水详情 |
| `stat_user_flow_detail_202604` | BASE TABLE | 7 | 用户 / 账号 | 0 | 用户输赢流水详情 |
| `stat_user_flow_detail_202605` | BASE TABLE | 7 | 用户 / 账号 | 0 | 用户输赢流水详情 |
| `stat_user_flow_detail_202606` | BASE TABLE | 7 | 用户 / 账号 | 0 | 用户输赢流水详情 |
| `stat_user_flow_detail_202607` | BASE TABLE | 7 | 用户 / 账号 | 0 | 用户输赢流水详情 |
| `stat_user_flow_detail_202608` | BASE TABLE | 7 | 用户 / 账号 | 0 | 用户输赢流水详情 |
| `stat_user_flow_protect` | BASE TABLE | 7 | 用户 / 账号 | 0 | 流水破产保护 |
| `stat_user_flow_protect_detail` | BASE TABLE | 9 | 用户 / 账号 | 0 | 触发流水破产保护记录 |
| `stat_user_property` | BASE TABLE | 6 | 用户 / 账号 | 0 | 用户信息 |
| `stat_user_withdraw_profit` | BASE TABLE | 7 | 支付 / 提现 | 0 | 提现时终身盈利记录 |
| `stat_user_wlrecord` | BASE TABLE | 6 | 用户 / 账号 | 0 | — |
| `stat_waterline` | BASE TABLE | 5 | 待分类 | 0 | — |
| `stat_whale_pkg_kill_data` | BASE TABLE | 6 | 待分类 | 0 | — |
| `sys_menu` | BASE TABLE | 5 | 待分类 | 0 | — |
| `sys_oauth_identity` | BASE TABLE | 7 | 用户 / 账号 | 0 | — |
| `sys_opt_log` | BASE TABLE | 6 | 日志 / 数据质量 | 0 | — |
| `sys_permission` | BASE TABLE | 3 | 待分类 | 0 | — |
| `sys_role` | BASE TABLE | 2 | 待分类 | 0 | — |
| `sys_role_permission` | BASE TABLE | 3 | 待分类 | 0 | — |
| `sys_user` | BASE TABLE | 4 | 用户 / 账号 | 1 | — |
| `sys_user_role` | BASE TABLE | 3 | 用户 / 账号 | 0 | — |
| `uc_addevice_adchannel` | BASE TABLE | 6 | 待分类 | 0 | 设备广告来源渠道信息表 |
| `uc_bank_account_users` | BASE TABLE | 6 | 用户 / 账号 | 0 | 银行账号对应的玩家id表 |
| `uc_logic` | BASE TABLE | 3 | 日志 / 数据质量 | 0 | 用户逻辑数据 |
| `uc_login` | BASE TABLE | 6 | 用户 / 账号 | 0 | 用户中心login表 |
| `uc_tourist_v2` | BASE TABLE | 5 | 待分类 | 0 | 游客v2 |
| `uc_user` | BASE TABLE | 23 | 用户 / 账号 | 2 | 用户中心user表 |
| `uc_user_adchannel` | BASE TABLE | 8 | 用户 / 账号 | 0 | 用户广告来源渠道信息表 |
| `uc_user_device` | BASE TABLE | 5 | 用户 / 账号 | 0 | 用户设备注册记录 |
| `uc_user_device_info` | BASE TABLE | 11 | 用户 / 账号 | 0 | 用户各种设备信息表 |
| `uc_user_extra` | BASE TABLE | 14 | 用户 / 账号 | 1 | 用户扩展表 |
| `uc_user_flag` | BASE TABLE | 4 | 用户 / 账号 | 0 | 用户标签表 |
| `user_control_list` | BASE TABLE | 11 | 用户 / 账号 | 0 | 玩家控制名单信息 |
| `user_data` | BASE TABLE | 4 | 用户 / 账号 | 0 | 用户数据表 |
| `user_data_backup` | BASE TABLE | 4 | 用户 / 账号 | 0 | 用户数据表 |
| `wg_coin_flips` | BASE TABLE | 10 | 资产 / 货币 | 0 | — |
| `wg_color_game` | BASE TABLE | 11 | 游戏 / 对局 / RTP | 0 | — |
| `wg_hilo_game_order_v2` | BASE TABLE | 25 | 支付 / 提现 | 0 | — |
| `wg_hilo_round_record` | BASE TABLE | 18 | 待分类 | 0 | — |
| `wg_keno` | BASE TABLE | 46 | 待分类 | 0 | — |
| `wg_limbo` | BASE TABLE | 13 | 待分类 | 0 | — |
| `wg_mines_game_order_v1` | BASE TABLE | 22 | 支付 / 提现 | 0 | — |
| `wg_mines_tile_record_v1` | BASE TABLE | 6 | 待分类 | 0 | — |
| `wg_plinko_ball` | BASE TABLE | 15 | 待分类 | 0 | — |
| `wg_plinko_order` | BASE TABLE | 30 | 支付 / 提现 | 0 | — |
| `wg_tower_game_order_v2` | BASE TABLE | 31 | 支付 / 提现 | 0 | — |
| `wg_tower_level_record` | BASE TABLE | 13 | 待分类 | 0 | — |
| `wg_tower_report_outbox_v2` | BASE TABLE | 11 | 待分类 | 1 | — |
| `wg_twist` | BASE TABLE | 12 | 待分类 | 0 | — |

## 3. 逐表字段定义

### ad_eagllwin_attribution

- 表类型：`BASE TABLE`；字段数：11；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | auto id | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gaid` | `varchar(128)` | NO | `UNI` | 业务属性 | google advertising id | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `callback_url` | `varchar(2048)` | NO | `NONE` | 业务属性 | Eagllwin callback url | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `gid` | `bigint unsigned` | NO | `MUL` | 业务属性 | matched game uid | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `activation_report_status` | `tinyint` | NO | `NONE` | 时间 | 0 pending 1 success 2 failed | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `is_login_gaid` | `tinyint` | NO | `NONE` | 业务属性 | 1 created by login gaid backfill | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `register_report_status` | `tinyint` | NO | `NONE` | 时间 | 0 pending 1 success 2 failed 3 skipped | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `first_recharge_report_status` | `tinyint` | NO | `NONE` | 时间 | 0 pending 1 success 2 failed 3 skipped | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `first_recharge_amount` | `bigint` | NO | `NONE` | 金额 / 资产 | first recharge amount in cents | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `create_at` | `bigint` | NO | `NONE` | 时间 | created unix time | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `update_at` | `bigint` | NO | `NONE` | 时间 | updated unix time | 允许在授权范围内做聚合分析；不输出字段值 |

### ad_eagllwin_attribution_v2

- 表类型：`BASE TABLE`；字段数：9；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | auto id | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gaid` | `varchar(128)` | NO | `UNI` | 业务属性 | google advertising id | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `activate_callback_url` | `varchar(2048)` | NO | `NONE` | 时间 | activation callback url | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `register_callback_url` | `varchar(2048)` | NO | `NONE` | 业务属性 | register callback url | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `first_recharge_callback_url` | `varchar(2048)` | NO | `NONE` | 业务属性 | first recharge callback url | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `activate_at` | `bigint` | NO | `NONE` | 时间 | activation unix time | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `activation_report_status` | `tinyint` | NO | `NONE` | 时间 | 0 pending 1 success 2 failed | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `create_at` | `bigint` | NO | `NONE` | 时间 | created unix time | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `update_at` | `bigint` | NO | `NONE` | 时间 | updated unix time | 允许在授权范围内做聚合分析；不输出字段值 |

### ad_eagllwin_user_attribution_v2

- 表类型：`BASE TABLE`；字段数：11；数据层：业务表（事实/维度待补证）。
- 业务域：用户 / 账号（`inferred_name_only`）；建议：注册、登录与生命周期聚合；禁止导出可识别身份字段。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | auto id | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gaid` | `varchar(128)` | NO | `MUL` | 业务属性 | google advertising id | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `gid` | `bigint unsigned` | NO | `MUL` | 业务属性 | game uid | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `is_login_gaid` | `tinyint` | NO | `NONE` | 业务属性 | 1 created by login gaid backfill | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `register_at` | `bigint` | NO | `NONE` | 时间 | register unix time | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `register_report_status` | `tinyint` | NO | `NONE` | 时间 | 0 pending 1 success 2 failed | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `first_recharge_at` | `bigint` | NO | `NONE` | 时间 | first recharge unix time | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `first_recharge_amount` | `bigint` | NO | `NONE` | 金额 / 资产 | first recharge amount in cents | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `first_recharge_report_status` | `tinyint` | NO | `NONE` | 时间 | 0 pending 1 success 2 failed | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `create_at` | `bigint` | NO | `NONE` | 时间 | created unix time | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `update_at` | `bigint` | NO | `NONE` | 时间 | updated unix time | 允许在授权范围内做聚合分析；不输出字段值 |

### agent_operate_log

- 表类型：`BASE TABLE`；字段数：9；数据层：业务表（事实/维度待补证）。
- 业务域：日志 / 数据质量（`inferred_name_only`）；建议：入库延迟、错误、重试和数据质量排障；需明确日志保留周期。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `agent_id` | `int unsigned` | NO | `MUL` | 标识 / 关联 | 代理id | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `from_id` | `int unsigned` | NO | `MUL` | 标识 / 关联 | 转出ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `to_id` | `int unsigned` | NO | `MUL` | 标识 / 关联 | 转入ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `record_type` | `int` | NO | `MUL` | 状态 / 枚举 | 记录类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `amount` | `bigint` | NO | `NONE` | 金额 / 资产 | 变更数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `chip` | `bigint` | NO | `NONE` | 金额 / 资产 | chip余额 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `cash` | `bigint` | NO | `NONE` | 金额 / 资产 | cash余额 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `time` | `bigint` | NO | `NONE` | 时间 | 创建时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### ams_asset

- 表类型：`BASE TABLE`；字段数：7；数据层：业务表（事实/维度待补证）。
- 业务域：资产 / 货币（`inferred_name_only`）；建议：资产流、奖励成本、余额变化与账本对账；必须区分真金、金币和奖励资产。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int unsigned` | NO | `MUL` | 业务属性 | 用户唯一ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `asset_id` | `int unsigned` | NO | `NONE` | 标识 / 关联 | 资产ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `balance` | `bigint unsigned` | NO | `NONE` | 金额 / 资产 | 结余 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `create_time` | `datetime` | NO | `NONE` | 时间 | 创建时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `update_time` | `datetime` | NO | `NONE` | 时间 | 更新时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `last_update_time` | `int` | NO | `NONE` | 时间 | 最后更新时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### ams_bill_000000

- 表类型：`BASE TABLE`；字段数：14；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int unsigned` | NO | `MUL` | 业务属性 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `asset_id` | `int unsigned` | NO | `NONE` | 标识 / 关联 | 资产ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_count` | `bigint` | NO | `NONE` | 业务属性 | 变更数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_type` | `int unsigned` | NO | `NONE` | 状态 / 枚举 | 变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 结余 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `serial_num` | `varchar(64)` | NO | `MUL` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `remark` | `varchar(64)` | NO | `NONE` | 业务属性 | 备注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `time` | `bigint unsigned` | NO | `NONE` | 时间 | 交易时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `bill_type` | `int unsigned` | NO | `NONE` | 状态 / 枚举 | 账单类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `co_game_id` | `varchar(45)` | NO | `NONE` | 标识 / 关联 | 联运的inner游戏id | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `status` | `tinyint unsigned` | NO | `NONE` | 时间 | 状态-充值tx使用 | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `match_id` | `varchar(64)` | NO | `MUL` | 标识 / 关联 | 牌局id | 允许在授权范围内做聚合分析；不输出字段值 |
| 14 | `round_id` | `varchar(64)` | NO | `NONE` | 标识 / 关联 | 回合id | 允许在授权范围内做聚合分析；不输出字段值 |

### ams_bill_202510

- 表类型：`BASE TABLE`；字段数：14；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int unsigned` | NO | `MUL` | 业务属性 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `asset_id` | `int unsigned` | NO | `NONE` | 标识 / 关联 | 资产ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_count` | `bigint` | NO | `NONE` | 业务属性 | 变更数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_type` | `int unsigned` | NO | `NONE` | 状态 / 枚举 | 变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 结余 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `serial_num` | `varchar(64)` | NO | `MUL` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `remark` | `varchar(64)` | NO | `NONE` | 业务属性 | 备注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `time` | `bigint unsigned` | NO | `NONE` | 时间 | 交易时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `bill_type` | `int unsigned` | NO | `NONE` | 状态 / 枚举 | 账单类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `co_game_id` | `varchar(45)` | NO | `NONE` | 标识 / 关联 | 联运的inner游戏id | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `status` | `tinyint unsigned` | NO | `NONE` | 时间 | 状态-充值tx使用 | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `match_id` | `varchar(64)` | NO | `NONE` | 标识 / 关联 | 牌局id | 允许在授权范围内做聚合分析；不输出字段值 |
| 14 | `round_id` | `varchar(64)` | NO | `NONE` | 标识 / 关联 | 回合id | 允许在授权范围内做聚合分析；不输出字段值 |

### ams_bill_202511

- 表类型：`BASE TABLE`；字段数：14；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int unsigned` | NO | `MUL` | 业务属性 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `asset_id` | `int unsigned` | NO | `NONE` | 标识 / 关联 | 资产ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_count` | `bigint` | NO | `NONE` | 业务属性 | 变更数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_type` | `int unsigned` | NO | `NONE` | 状态 / 枚举 | 变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 结余 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `serial_num` | `varchar(64)` | NO | `MUL` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `remark` | `varchar(64)` | NO | `NONE` | 业务属性 | 备注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `time` | `bigint unsigned` | NO | `NONE` | 时间 | 交易时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `bill_type` | `int unsigned` | NO | `NONE` | 状态 / 枚举 | 账单类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `co_game_id` | `varchar(45)` | NO | `NONE` | 标识 / 关联 | 联运的inner游戏id | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `status` | `tinyint unsigned` | NO | `NONE` | 时间 | 状态-充值tx使用 | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `match_id` | `varchar(64)` | NO | `NONE` | 标识 / 关联 | 牌局id | 允许在授权范围内做聚合分析；不输出字段值 |
| 14 | `round_id` | `varchar(64)` | NO | `NONE` | 标识 / 关联 | 回合id | 允许在授权范围内做聚合分析；不输出字段值 |

### ams_bill_202512

- 表类型：`BASE TABLE`；字段数：14；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int unsigned` | NO | `MUL` | 业务属性 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `asset_id` | `int unsigned` | NO | `NONE` | 标识 / 关联 | 资产ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_count` | `bigint` | NO | `NONE` | 业务属性 | 变更数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_type` | `int unsigned` | NO | `NONE` | 状态 / 枚举 | 变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 结余 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `serial_num` | `varchar(64)` | NO | `MUL` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `remark` | `varchar(64)` | NO | `NONE` | 业务属性 | 备注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `time` | `bigint unsigned` | NO | `NONE` | 时间 | 交易时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `bill_type` | `int unsigned` | NO | `NONE` | 状态 / 枚举 | 账单类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `co_game_id` | `varchar(45)` | NO | `NONE` | 标识 / 关联 | 联运的inner游戏id | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `status` | `tinyint unsigned` | NO | `NONE` | 时间 | 状态-充值tx使用 | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `match_id` | `varchar(64)` | NO | `NONE` | 标识 / 关联 | 牌局id | 允许在授权范围内做聚合分析；不输出字段值 |
| 14 | `round_id` | `varchar(64)` | NO | `NONE` | 标识 / 关联 | 回合id | 允许在授权范围内做聚合分析；不输出字段值 |

### ams_bill_202601

- 表类型：`BASE TABLE`；字段数：14；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int unsigned` | NO | `MUL` | 业务属性 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `asset_id` | `int unsigned` | NO | `NONE` | 标识 / 关联 | 资产ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_count` | `bigint` | NO | `NONE` | 业务属性 | 变更数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_type` | `int unsigned` | NO | `NONE` | 状态 / 枚举 | 变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 结余 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `serial_num` | `varchar(64)` | NO | `MUL` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `remark` | `varchar(64)` | NO | `NONE` | 业务属性 | 备注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `time` | `bigint unsigned` | NO | `NONE` | 时间 | 交易时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `bill_type` | `int unsigned` | NO | `NONE` | 状态 / 枚举 | 账单类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `co_game_id` | `varchar(45)` | NO | `NONE` | 标识 / 关联 | 联运的inner游戏id | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `status` | `tinyint unsigned` | NO | `NONE` | 时间 | 状态-充值tx使用 | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `match_id` | `varchar(64)` | NO | `NONE` | 标识 / 关联 | 牌局id | 允许在授权范围内做聚合分析；不输出字段值 |
| 14 | `round_id` | `varchar(64)` | NO | `NONE` | 标识 / 关联 | 回合id | 允许在授权范围内做聚合分析；不输出字段值 |

### ams_bill_202602

- 表类型：`BASE TABLE`；字段数：14；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int unsigned` | NO | `MUL` | 业务属性 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `asset_id` | `int unsigned` | NO | `NONE` | 标识 / 关联 | 资产ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_count` | `bigint` | NO | `NONE` | 业务属性 | 变更数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_type` | `int unsigned` | NO | `NONE` | 状态 / 枚举 | 变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 结余 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `serial_num` | `varchar(64)` | NO | `MUL` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `remark` | `varchar(64)` | NO | `NONE` | 业务属性 | 备注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `time` | `bigint unsigned` | NO | `NONE` | 时间 | 交易时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `bill_type` | `int unsigned` | NO | `NONE` | 状态 / 枚举 | 账单类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `co_game_id` | `varchar(45)` | NO | `NONE` | 标识 / 关联 | 联运的inner游戏id | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `status` | `tinyint unsigned` | NO | `NONE` | 时间 | 状态-充值tx使用 | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `match_id` | `varchar(64)` | NO | `NONE` | 标识 / 关联 | 牌局id | 允许在授权范围内做聚合分析；不输出字段值 |
| 14 | `round_id` | `varchar(64)` | NO | `NONE` | 标识 / 关联 | 回合id | 允许在授权范围内做聚合分析；不输出字段值 |

### ams_bill_202603

- 表类型：`BASE TABLE`；字段数：14；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int unsigned` | NO | `MUL` | 业务属性 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `asset_id` | `int unsigned` | NO | `NONE` | 标识 / 关联 | 资产ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_count` | `bigint` | NO | `NONE` | 业务属性 | 变更数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_type` | `int unsigned` | NO | `NONE` | 状态 / 枚举 | 变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 结余 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `serial_num` | `varchar(64)` | NO | `MUL` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `remark` | `varchar(64)` | NO | `NONE` | 业务属性 | 备注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `time` | `bigint unsigned` | NO | `NONE` | 时间 | 交易时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `bill_type` | `int unsigned` | NO | `NONE` | 状态 / 枚举 | 账单类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `co_game_id` | `varchar(45)` | NO | `NONE` | 标识 / 关联 | 联运的inner游戏id | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `status` | `tinyint unsigned` | NO | `NONE` | 时间 | 状态-充值tx使用 | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `match_id` | `varchar(64)` | NO | `NONE` | 标识 / 关联 | 牌局id | 允许在授权范围内做聚合分析；不输出字段值 |
| 14 | `round_id` | `varchar(64)` | NO | `NONE` | 标识 / 关联 | 回合id | 允许在授权范围内做聚合分析；不输出字段值 |

### ams_bill_202604

- 表类型：`BASE TABLE`；字段数：14；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int unsigned` | NO | `MUL` | 业务属性 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `asset_id` | `int unsigned` | NO | `NONE` | 标识 / 关联 | 资产ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_count` | `bigint` | NO | `NONE` | 业务属性 | 变更数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_type` | `int unsigned` | NO | `NONE` | 状态 / 枚举 | 变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 结余 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `serial_num` | `varchar(64)` | NO | `MUL` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `remark` | `varchar(64)` | NO | `NONE` | 业务属性 | 备注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `time` | `bigint unsigned` | NO | `NONE` | 时间 | 交易时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `bill_type` | `int unsigned` | NO | `NONE` | 状态 / 枚举 | 账单类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `co_game_id` | `varchar(45)` | NO | `NONE` | 标识 / 关联 | 联运的inner游戏id | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `status` | `tinyint unsigned` | NO | `NONE` | 时间 | 状态-充值tx使用 | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `match_id` | `varchar(64)` | NO | `NONE` | 标识 / 关联 | 牌局id | 允许在授权范围内做聚合分析；不输出字段值 |
| 14 | `round_id` | `varchar(64)` | NO | `NONE` | 标识 / 关联 | 回合id | 允许在授权范围内做聚合分析；不输出字段值 |

### ams_bill_202605

- 表类型：`BASE TABLE`；字段数：14；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int unsigned` | NO | `MUL` | 业务属性 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `asset_id` | `int unsigned` | NO | `NONE` | 标识 / 关联 | 资产ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_count` | `bigint` | NO | `NONE` | 业务属性 | 变更数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_type` | `int unsigned` | NO | `NONE` | 状态 / 枚举 | 变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 结余 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `serial_num` | `varchar(64)` | NO | `MUL` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `remark` | `varchar(64)` | NO | `NONE` | 业务属性 | 备注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `time` | `bigint unsigned` | NO | `NONE` | 时间 | 交易时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `bill_type` | `int unsigned` | NO | `NONE` | 状态 / 枚举 | 账单类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `co_game_id` | `varchar(45)` | NO | `NONE` | 标识 / 关联 | 联运的inner游戏id | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `status` | `tinyint unsigned` | NO | `NONE` | 时间 | 状态-充值tx使用 | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `match_id` | `varchar(64)` | NO | `NONE` | 标识 / 关联 | 牌局id | 允许在授权范围内做聚合分析；不输出字段值 |
| 14 | `round_id` | `varchar(64)` | NO | `NONE` | 标识 / 关联 | 回合id | 允许在授权范围内做聚合分析；不输出字段值 |

### ams_bill_202606

- 表类型：`BASE TABLE`；字段数：14；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int unsigned` | NO | `MUL` | 业务属性 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `asset_id` | `int unsigned` | NO | `NONE` | 标识 / 关联 | 资产ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_count` | `bigint` | NO | `NONE` | 业务属性 | 变更数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_type` | `int unsigned` | NO | `NONE` | 状态 / 枚举 | 变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 结余 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `serial_num` | `varchar(64)` | NO | `MUL` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `remark` | `varchar(64)` | NO | `NONE` | 业务属性 | 备注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `time` | `bigint unsigned` | NO | `NONE` | 时间 | 交易时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `bill_type` | `int unsigned` | NO | `NONE` | 状态 / 枚举 | 账单类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `co_game_id` | `varchar(45)` | NO | `NONE` | 标识 / 关联 | 联运的inner游戏id | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `status` | `tinyint unsigned` | NO | `NONE` | 时间 | 状态-充值tx使用 | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `match_id` | `varchar(64)` | NO | `NONE` | 标识 / 关联 | 牌局id | 允许在授权范围内做聚合分析；不输出字段值 |
| 14 | `round_id` | `varchar(64)` | NO | `NONE` | 标识 / 关联 | 回合id | 允许在授权范围内做聚合分析；不输出字段值 |

### ams_bill_202607

- 表类型：`BASE TABLE`；字段数：14；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int unsigned` | NO | `MUL` | 业务属性 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `asset_id` | `int unsigned` | NO | `NONE` | 标识 / 关联 | 资产ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_count` | `bigint` | NO | `NONE` | 业务属性 | 变更数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_type` | `int unsigned` | NO | `NONE` | 状态 / 枚举 | 变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 结余 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `serial_num` | `varchar(64)` | NO | `MUL` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `remark` | `varchar(64)` | NO | `NONE` | 业务属性 | 备注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `time` | `bigint unsigned` | NO | `NONE` | 时间 | 交易时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `bill_type` | `int unsigned` | NO | `NONE` | 状态 / 枚举 | 账单类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `co_game_id` | `varchar(45)` | NO | `NONE` | 标识 / 关联 | 联运的inner游戏id | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `status` | `tinyint unsigned` | NO | `NONE` | 时间 | 状态-充值tx使用 | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `match_id` | `varchar(64)` | NO | `MUL` | 标识 / 关联 | 牌局id | 允许在授权范围内做聚合分析；不输出字段值 |
| 14 | `round_id` | `varchar(64)` | NO | `NONE` | 标识 / 关联 | 回合id | 允许在授权范围内做聚合分析；不输出字段值 |

### ams_bill_202608

- 表类型：`BASE TABLE`；字段数：14；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int unsigned` | NO | `MUL` | 业务属性 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `asset_id` | `int unsigned` | NO | `NONE` | 标识 / 关联 | 资产ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_count` | `bigint` | NO | `NONE` | 业务属性 | 变更数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_type` | `int unsigned` | NO | `NONE` | 状态 / 枚举 | 变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 结余 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `serial_num` | `varchar(64)` | NO | `MUL` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `remark` | `varchar(64)` | NO | `NONE` | 业务属性 | 备注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `time` | `bigint unsigned` | NO | `NONE` | 时间 | 交易时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `bill_type` | `int unsigned` | NO | `NONE` | 状态 / 枚举 | 账单类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `co_game_id` | `varchar(45)` | NO | `NONE` | 标识 / 关联 | 联运的inner游戏id | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `status` | `tinyint unsigned` | NO | `NONE` | 时间 | 状态-充值tx使用 | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `match_id` | `varchar(64)` | NO | `MUL` | 标识 / 关联 | 牌局id | 允许在授权范围内做聚合分析；不输出字段值 |
| 14 | `round_id` | `varchar(64)` | NO | `NONE` | 标识 / 关联 | 回合id | 允许在授权范围内做聚合分析；不输出字段值 |

### ams_bill_extra_000000

- 表类型：`BASE TABLE`；字段数：12；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint` | NO | `PRI` | 标识 / 关联 | 自增id | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `serial_num` | `varchar(64)` | NO | `MUL` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `change_cash` | `bigint` | NO | `NONE` | 金额 / 资产 | 扣除的cash | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_waje_cash` | `bigint` | NO | `NONE` | 金额 / 资产 | 扣除的wajecash | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_fee` | `bigint` | NO | `NONE` | 金额 / 资产 | 扣除的手续费 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `bank` | `varchar(128)` | NO | `NONE` | 业务属性 | 银行 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `account_number` | `varchar(32)` | NO | `NONE` | 业务属性 | 卡号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `withdraw_process_status` | `tinyint unsigned` | NO | `NONE` | 时间 | 提现中的状态 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `w_start_time` | `bigint` | NO | `NONE` | 时间 | 提现开始时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `w_review_time` | `bigint` | NO | `NONE` | 时间 | 提现审核时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `w_transfer_time` | `bigint` | NO | `NONE` | 时间 | 提现转账时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `w_end_time` | `bigint` | NO | `NONE` | 时间 | 提现结束时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### ams_bill_extra_202510

- 表类型：`BASE TABLE`；字段数：12；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint` | NO | `PRI` | 标识 / 关联 | 自增id | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `serial_num` | `varchar(64)` | NO | `MUL` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `change_cash` | `bigint` | NO | `NONE` | 金额 / 资产 | 扣除的cash | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_waje_cash` | `bigint` | NO | `NONE` | 金额 / 资产 | 扣除的wajecash | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_fee` | `bigint` | NO | `NONE` | 金额 / 资产 | 扣除的手续费 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `bank` | `varchar(128)` | NO | `NONE` | 业务属性 | 银行 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `account_number` | `varchar(32)` | NO | `NONE` | 业务属性 | 卡号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `withdraw_process_status` | `tinyint unsigned` | NO | `NONE` | 时间 | 提现中的状态 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `w_start_time` | `bigint` | NO | `NONE` | 时间 | 提现开始时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `w_review_time` | `bigint` | NO | `NONE` | 时间 | 提现审核时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `w_transfer_time` | `bigint` | NO | `NONE` | 时间 | 提现转账时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `w_end_time` | `bigint` | NO | `NONE` | 时间 | 提现结束时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### ams_bill_extra_202511

- 表类型：`BASE TABLE`；字段数：12；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint` | NO | `PRI` | 标识 / 关联 | 自增id | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `serial_num` | `varchar(64)` | NO | `MUL` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `change_cash` | `bigint` | NO | `NONE` | 金额 / 资产 | 扣除的cash | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_waje_cash` | `bigint` | NO | `NONE` | 金额 / 资产 | 扣除的wajecash | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_fee` | `bigint` | NO | `NONE` | 金额 / 资产 | 扣除的手续费 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `bank` | `varchar(128)` | NO | `NONE` | 业务属性 | 银行 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `account_number` | `varchar(32)` | NO | `NONE` | 业务属性 | 卡号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `withdraw_process_status` | `tinyint unsigned` | NO | `NONE` | 时间 | 提现中的状态 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `w_start_time` | `bigint` | NO | `NONE` | 时间 | 提现开始时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `w_review_time` | `bigint` | NO | `NONE` | 时间 | 提现审核时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `w_transfer_time` | `bigint` | NO | `NONE` | 时间 | 提现转账时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `w_end_time` | `bigint` | NO | `NONE` | 时间 | 提现结束时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### ams_bill_extra_202512

- 表类型：`BASE TABLE`；字段数：12；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint` | NO | `PRI` | 标识 / 关联 | 自增id | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `serial_num` | `varchar(64)` | NO | `MUL` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `change_cash` | `bigint` | NO | `NONE` | 金额 / 资产 | 扣除的cash | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_waje_cash` | `bigint` | NO | `NONE` | 金额 / 资产 | 扣除的wajecash | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_fee` | `bigint` | NO | `NONE` | 金额 / 资产 | 扣除的手续费 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `bank` | `varchar(128)` | NO | `NONE` | 业务属性 | 银行 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `account_number` | `varchar(32)` | NO | `NONE` | 业务属性 | 卡号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `withdraw_process_status` | `tinyint unsigned` | NO | `NONE` | 时间 | 提现中的状态 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `w_start_time` | `bigint` | NO | `NONE` | 时间 | 提现开始时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `w_review_time` | `bigint` | NO | `NONE` | 时间 | 提现审核时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `w_transfer_time` | `bigint` | NO | `NONE` | 时间 | 提现转账时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `w_end_time` | `bigint` | NO | `NONE` | 时间 | 提现结束时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### ams_bill_extra_202601

- 表类型：`BASE TABLE`；字段数：12；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint` | NO | `PRI` | 标识 / 关联 | 自增id | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `serial_num` | `varchar(64)` | NO | `MUL` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `change_cash` | `bigint` | NO | `NONE` | 金额 / 资产 | 扣除的cash | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_waje_cash` | `bigint` | NO | `NONE` | 金额 / 资产 | 扣除的wajecash | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_fee` | `bigint` | NO | `NONE` | 金额 / 资产 | 扣除的手续费 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `bank` | `varchar(128)` | NO | `NONE` | 业务属性 | 银行 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `account_number` | `varchar(32)` | NO | `NONE` | 业务属性 | 卡号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `withdraw_process_status` | `tinyint unsigned` | NO | `NONE` | 时间 | 提现中的状态 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `w_start_time` | `bigint` | NO | `NONE` | 时间 | 提现开始时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `w_review_time` | `bigint` | NO | `NONE` | 时间 | 提现审核时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `w_transfer_time` | `bigint` | NO | `NONE` | 时间 | 提现转账时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `w_end_time` | `bigint` | NO | `NONE` | 时间 | 提现结束时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### ams_bill_extra_202602

- 表类型：`BASE TABLE`；字段数：12；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint` | NO | `PRI` | 标识 / 关联 | 自增id | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `serial_num` | `varchar(64)` | NO | `MUL` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `change_cash` | `bigint` | NO | `NONE` | 金额 / 资产 | 扣除的cash | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_waje_cash` | `bigint` | NO | `NONE` | 金额 / 资产 | 扣除的wajecash | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_fee` | `bigint` | NO | `NONE` | 金额 / 资产 | 扣除的手续费 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `bank` | `varchar(128)` | NO | `NONE` | 业务属性 | 银行 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `account_number` | `varchar(32)` | NO | `NONE` | 业务属性 | 卡号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `withdraw_process_status` | `tinyint unsigned` | NO | `NONE` | 时间 | 提现中的状态 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `w_start_time` | `bigint` | NO | `NONE` | 时间 | 提现开始时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `w_review_time` | `bigint` | NO | `NONE` | 时间 | 提现审核时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `w_transfer_time` | `bigint` | NO | `NONE` | 时间 | 提现转账时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `w_end_time` | `bigint` | NO | `NONE` | 时间 | 提现结束时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### ams_bill_extra_202603

- 表类型：`BASE TABLE`；字段数：12；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint` | NO | `PRI` | 标识 / 关联 | 自增id | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `serial_num` | `varchar(64)` | NO | `MUL` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `change_cash` | `bigint` | NO | `NONE` | 金额 / 资产 | 扣除的cash | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_waje_cash` | `bigint` | NO | `NONE` | 金额 / 资产 | 扣除的wajecash | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_fee` | `bigint` | NO | `NONE` | 金额 / 资产 | 扣除的手续费 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `bank` | `varchar(128)` | NO | `NONE` | 业务属性 | 银行 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `account_number` | `varchar(32)` | NO | `NONE` | 业务属性 | 卡号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `withdraw_process_status` | `tinyint unsigned` | NO | `NONE` | 时间 | 提现中的状态 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `w_start_time` | `bigint` | NO | `NONE` | 时间 | 提现开始时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `w_review_time` | `bigint` | NO | `NONE` | 时间 | 提现审核时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `w_transfer_time` | `bigint` | NO | `NONE` | 时间 | 提现转账时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `w_end_time` | `bigint` | NO | `NONE` | 时间 | 提现结束时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### ams_bill_extra_202604

- 表类型：`BASE TABLE`；字段数：12；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint` | NO | `PRI` | 标识 / 关联 | 自增id | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `serial_num` | `varchar(64)` | NO | `MUL` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `change_cash` | `bigint` | NO | `NONE` | 金额 / 资产 | 扣除的cash | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_waje_cash` | `bigint` | NO | `NONE` | 金额 / 资产 | 扣除的wajecash | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_fee` | `bigint` | NO | `NONE` | 金额 / 资产 | 扣除的手续费 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `bank` | `varchar(128)` | NO | `NONE` | 业务属性 | 银行 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `account_number` | `varchar(32)` | NO | `NONE` | 业务属性 | 卡号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `withdraw_process_status` | `tinyint unsigned` | NO | `NONE` | 时间 | 提现中的状态 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `w_start_time` | `bigint` | NO | `NONE` | 时间 | 提现开始时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `w_review_time` | `bigint` | NO | `NONE` | 时间 | 提现审核时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `w_transfer_time` | `bigint` | NO | `NONE` | 时间 | 提现转账时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `w_end_time` | `bigint` | NO | `NONE` | 时间 | 提现结束时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### ams_bill_extra_202605

- 表类型：`BASE TABLE`；字段数：12；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint` | NO | `PRI` | 标识 / 关联 | 自增id | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `serial_num` | `varchar(64)` | NO | `MUL` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `change_cash` | `bigint` | NO | `NONE` | 金额 / 资产 | 扣除的cash | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_waje_cash` | `bigint` | NO | `NONE` | 金额 / 资产 | 扣除的wajecash | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_fee` | `bigint` | NO | `NONE` | 金额 / 资产 | 扣除的手续费 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `bank` | `varchar(128)` | NO | `NONE` | 业务属性 | 银行 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `account_number` | `varchar(32)` | NO | `NONE` | 业务属性 | 卡号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `withdraw_process_status` | `tinyint unsigned` | NO | `NONE` | 时间 | 提现中的状态 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `w_start_time` | `bigint` | NO | `NONE` | 时间 | 提现开始时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `w_review_time` | `bigint` | NO | `NONE` | 时间 | 提现审核时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `w_transfer_time` | `bigint` | NO | `NONE` | 时间 | 提现转账时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `w_end_time` | `bigint` | NO | `NONE` | 时间 | 提现结束时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### ams_bill_extra_202606

- 表类型：`BASE TABLE`；字段数：12；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint` | NO | `PRI` | 标识 / 关联 | 自增id | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `serial_num` | `varchar(64)` | NO | `MUL` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `change_cash` | `bigint` | NO | `NONE` | 金额 / 资产 | 扣除的cash | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_waje_cash` | `bigint` | NO | `NONE` | 金额 / 资产 | 扣除的wajecash | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_fee` | `bigint` | NO | `NONE` | 金额 / 资产 | 扣除的手续费 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `bank` | `varchar(128)` | NO | `NONE` | 业务属性 | 银行 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `account_number` | `varchar(32)` | NO | `NONE` | 业务属性 | 卡号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `withdraw_process_status` | `tinyint unsigned` | NO | `NONE` | 时间 | 提现中的状态 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `w_start_time` | `bigint` | NO | `NONE` | 时间 | 提现开始时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `w_review_time` | `bigint` | NO | `NONE` | 时间 | 提现审核时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `w_transfer_time` | `bigint` | NO | `NONE` | 时间 | 提现转账时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `w_end_time` | `bigint` | NO | `NONE` | 时间 | 提现结束时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### ams_bill_extra_202607

- 表类型：`BASE TABLE`；字段数：12；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint` | NO | `PRI` | 标识 / 关联 | 自增id | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `serial_num` | `varchar(64)` | NO | `MUL` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `change_cash` | `bigint` | NO | `NONE` | 金额 / 资产 | 扣除的cash | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_waje_cash` | `bigint` | NO | `NONE` | 金额 / 资产 | 扣除的wajecash | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_fee` | `bigint` | NO | `NONE` | 金额 / 资产 | 扣除的手续费 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `bank` | `varchar(128)` | NO | `NONE` | 业务属性 | 银行 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `account_number` | `varchar(32)` | NO | `NONE` | 业务属性 | 卡号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `withdraw_process_status` | `tinyint unsigned` | NO | `NONE` | 时间 | 提现中的状态 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `w_start_time` | `bigint` | NO | `NONE` | 时间 | 提现开始时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `w_review_time` | `bigint` | NO | `NONE` | 时间 | 提现审核时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `w_transfer_time` | `bigint` | NO | `NONE` | 时间 | 提现转账时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `w_end_time` | `bigint` | NO | `NONE` | 时间 | 提现结束时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### ams_bill_extra_202608

- 表类型：`BASE TABLE`；字段数：12；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint` | NO | `PRI` | 标识 / 关联 | 自增id | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `serial_num` | `varchar(64)` | NO | `MUL` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `change_cash` | `bigint` | NO | `NONE` | 金额 / 资产 | 扣除的cash | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_waje_cash` | `bigint` | NO | `NONE` | 金额 / 资产 | 扣除的wajecash | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_fee` | `bigint` | NO | `NONE` | 金额 / 资产 | 扣除的手续费 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `bank` | `varchar(128)` | NO | `NONE` | 业务属性 | 银行 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `account_number` | `varchar(32)` | NO | `NONE` | 业务属性 | 卡号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `withdraw_process_status` | `tinyint unsigned` | NO | `NONE` | 时间 | 提现中的状态 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `w_start_time` | `bigint` | NO | `NONE` | 时间 | 提现开始时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `w_review_time` | `bigint` | NO | `NONE` | 时间 | 提现审核时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `w_transfer_time` | `bigint` | NO | `NONE` | 时间 | 提现转账时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `w_end_time` | `bigint` | NO | `NONE` | 时间 | 提现结束时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### ams_charge_000000

- 表类型：`BASE TABLE`；字段数：10；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int unsigned` | NO | `MUL` | 业务属性 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `asset_id` | `int unsigned` | NO | `NONE` | 标识 / 关联 | 资产ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_count` | `bigint` | NO | `NONE` | 业务属性 | 变更数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_type` | `int unsigned` | NO | `MUL` | 状态 / 枚举 | 变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 结余 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `serial_num` | `varchar(64)` | NO | `NONE` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `remark` | `varchar(64)` | NO | `NONE` | 业务属性 | 备注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `time` | `bigint unsigned` | NO | `MUL` | 时间 | 交易时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `all_balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 余额 | 允许在授权范围内做聚合分析；不输出字段值 |

### ams_charge_202401

- 表类型：`BASE TABLE`；字段数：9；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int unsigned` | NO | `MUL` | 业务属性 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `asset_id` | `int unsigned` | NO | `NONE` | 标识 / 关联 | 资产ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_count` | `bigint` | NO | `NONE` | 业务属性 | 变更数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_type` | `int unsigned` | NO | `NONE` | 状态 / 枚举 | 变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 结余 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `serial_num` | `varchar(64)` | NO | `NONE` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `remark` | `varchar(64)` | NO | `NONE` | 业务属性 | 备注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `time` | `bigint unsigned` | NO | `NONE` | 时间 | 交易时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### ams_charge_202402

- 表类型：`BASE TABLE`；字段数：9；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int unsigned` | NO | `MUL` | 业务属性 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `asset_id` | `int unsigned` | NO | `NONE` | 标识 / 关联 | 资产ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_count` | `bigint` | NO | `NONE` | 业务属性 | 变更数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_type` | `int unsigned` | NO | `NONE` | 状态 / 枚举 | 变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 结余 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `serial_num` | `varchar(64)` | NO | `NONE` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `remark` | `varchar(64)` | NO | `NONE` | 业务属性 | 备注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `time` | `bigint unsigned` | NO | `NONE` | 时间 | 交易时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### ams_charge_202403

- 表类型：`BASE TABLE`；字段数：9；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int unsigned` | NO | `MUL` | 业务属性 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `asset_id` | `int unsigned` | NO | `NONE` | 标识 / 关联 | 资产ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_count` | `bigint` | NO | `NONE` | 业务属性 | 变更数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_type` | `int unsigned` | NO | `NONE` | 状态 / 枚举 | 变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 结余 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `serial_num` | `varchar(64)` | NO | `NONE` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `remark` | `varchar(64)` | NO | `NONE` | 业务属性 | 备注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `time` | `bigint unsigned` | NO | `NONE` | 时间 | 交易时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### ams_charge_202404

- 表类型：`BASE TABLE`；字段数：9；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int unsigned` | NO | `MUL` | 业务属性 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `asset_id` | `int unsigned` | NO | `NONE` | 标识 / 关联 | 资产ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_count` | `bigint` | NO | `NONE` | 业务属性 | 变更数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_type` | `int unsigned` | NO | `NONE` | 状态 / 枚举 | 变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 结余 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `serial_num` | `varchar(64)` | NO | `NONE` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `remark` | `varchar(64)` | NO | `NONE` | 业务属性 | 备注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `time` | `bigint unsigned` | NO | `NONE` | 时间 | 交易时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### ams_charge_202405

- 表类型：`BASE TABLE`；字段数：9；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int unsigned` | NO | `MUL` | 业务属性 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `asset_id` | `int unsigned` | NO | `NONE` | 标识 / 关联 | 资产ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_count` | `bigint` | NO | `NONE` | 业务属性 | 变更数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_type` | `int unsigned` | NO | `NONE` | 状态 / 枚举 | 变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 结余 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `serial_num` | `varchar(64)` | NO | `NONE` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `remark` | `varchar(64)` | NO | `NONE` | 业务属性 | 备注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `time` | `bigint unsigned` | NO | `NONE` | 时间 | 交易时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### ams_charge_202406

- 表类型：`BASE TABLE`；字段数：9；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int unsigned` | NO | `MUL` | 业务属性 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `asset_id` | `int unsigned` | NO | `NONE` | 标识 / 关联 | 资产ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_count` | `bigint` | NO | `NONE` | 业务属性 | 变更数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_type` | `int unsigned` | NO | `NONE` | 状态 / 枚举 | 变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 结余 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `serial_num` | `varchar(64)` | NO | `NONE` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `remark` | `varchar(64)` | NO | `NONE` | 业务属性 | 备注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `time` | `bigint unsigned` | NO | `NONE` | 时间 | 交易时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### ams_charge_202407

- 表类型：`BASE TABLE`；字段数：9；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int unsigned` | NO | `MUL` | 业务属性 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `asset_id` | `int unsigned` | NO | `NONE` | 标识 / 关联 | 资产ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_count` | `bigint` | NO | `NONE` | 业务属性 | 变更数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_type` | `int unsigned` | NO | `NONE` | 状态 / 枚举 | 变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 结余 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `serial_num` | `varchar(64)` | NO | `NONE` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `remark` | `varchar(64)` | NO | `NONE` | 业务属性 | 备注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `time` | `bigint unsigned` | NO | `NONE` | 时间 | 交易时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### ams_charge_202408

- 表类型：`BASE TABLE`；字段数：9；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int unsigned` | NO | `MUL` | 业务属性 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `asset_id` | `int unsigned` | NO | `NONE` | 标识 / 关联 | 资产ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_count` | `bigint` | NO | `NONE` | 业务属性 | 变更数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_type` | `int unsigned` | NO | `NONE` | 状态 / 枚举 | 变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 结余 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `serial_num` | `varchar(64)` | NO | `NONE` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `remark` | `varchar(64)` | NO | `NONE` | 业务属性 | 备注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `time` | `bigint unsigned` | NO | `NONE` | 时间 | 交易时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### ams_charge_202409

- 表类型：`BASE TABLE`；字段数：9；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int unsigned` | NO | `MUL` | 业务属性 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `asset_id` | `int unsigned` | NO | `NONE` | 标识 / 关联 | 资产ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_count` | `bigint` | NO | `NONE` | 业务属性 | 变更数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_type` | `int unsigned` | NO | `NONE` | 状态 / 枚举 | 变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 结余 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `serial_num` | `varchar(64)` | NO | `NONE` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `remark` | `varchar(64)` | NO | `NONE` | 业务属性 | 备注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `time` | `bigint unsigned` | NO | `NONE` | 时间 | 交易时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### ams_charge_202410

- 表类型：`BASE TABLE`；字段数：9；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int unsigned` | NO | `MUL` | 业务属性 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `asset_id` | `int unsigned` | NO | `NONE` | 标识 / 关联 | 资产ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_count` | `bigint` | NO | `NONE` | 业务属性 | 变更数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_type` | `int unsigned` | NO | `NONE` | 状态 / 枚举 | 变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 结余 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `serial_num` | `varchar(64)` | NO | `NONE` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `remark` | `varchar(64)` | NO | `NONE` | 业务属性 | 备注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `time` | `bigint unsigned` | NO | `NONE` | 时间 | 交易时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### ams_charge_202411

- 表类型：`BASE TABLE`；字段数：9；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int unsigned` | NO | `MUL` | 业务属性 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `asset_id` | `int unsigned` | NO | `NONE` | 标识 / 关联 | 资产ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_count` | `bigint` | NO | `NONE` | 业务属性 | 变更数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_type` | `int unsigned` | NO | `NONE` | 状态 / 枚举 | 变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 结余 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `serial_num` | `varchar(64)` | NO | `NONE` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `remark` | `varchar(64)` | NO | `NONE` | 业务属性 | 备注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `time` | `bigint unsigned` | NO | `NONE` | 时间 | 交易时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### ams_charge_202412

- 表类型：`BASE TABLE`；字段数：9；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int unsigned` | NO | `MUL` | 业务属性 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `asset_id` | `int unsigned` | NO | `NONE` | 标识 / 关联 | 资产ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_count` | `bigint` | NO | `NONE` | 业务属性 | 变更数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_type` | `int unsigned` | NO | `NONE` | 状态 / 枚举 | 变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 结余 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `serial_num` | `varchar(64)` | NO | `NONE` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `remark` | `varchar(64)` | NO | `NONE` | 业务属性 | 备注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `time` | `bigint unsigned` | NO | `NONE` | 时间 | 交易时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### ams_charge_202501

- 表类型：`BASE TABLE`；字段数：9；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int unsigned` | NO | `MUL` | 业务属性 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `asset_id` | `int unsigned` | NO | `NONE` | 标识 / 关联 | 资产ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_count` | `bigint` | NO | `NONE` | 业务属性 | 变更数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_type` | `int unsigned` | NO | `NONE` | 状态 / 枚举 | 变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 结余 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `serial_num` | `varchar(64)` | NO | `NONE` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `remark` | `varchar(64)` | NO | `NONE` | 业务属性 | 备注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `time` | `bigint unsigned` | NO | `NONE` | 时间 | 交易时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### ams_charge_202502

- 表类型：`BASE TABLE`；字段数：9；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int unsigned` | NO | `MUL` | 业务属性 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `asset_id` | `int unsigned` | NO | `NONE` | 标识 / 关联 | 资产ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_count` | `bigint` | NO | `NONE` | 业务属性 | 变更数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_type` | `int unsigned` | NO | `NONE` | 状态 / 枚举 | 变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 结余 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `serial_num` | `varchar(64)` | NO | `NONE` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `remark` | `varchar(64)` | NO | `NONE` | 业务属性 | 备注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `time` | `bigint unsigned` | NO | `NONE` | 时间 | 交易时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### ams_charge_202503

- 表类型：`BASE TABLE`；字段数：9；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int unsigned` | NO | `MUL` | 业务属性 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `asset_id` | `int unsigned` | NO | `NONE` | 标识 / 关联 | 资产ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_count` | `bigint` | NO | `NONE` | 业务属性 | 变更数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_type` | `int unsigned` | NO | `NONE` | 状态 / 枚举 | 变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 结余 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `serial_num` | `varchar(64)` | NO | `NONE` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `remark` | `varchar(64)` | NO | `NONE` | 业务属性 | 备注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `time` | `bigint unsigned` | NO | `NONE` | 时间 | 交易时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### ams_charge_202504

- 表类型：`BASE TABLE`；字段数：9；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int unsigned` | NO | `MUL` | 业务属性 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `asset_id` | `int unsigned` | NO | `NONE` | 标识 / 关联 | 资产ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_count` | `bigint` | NO | `NONE` | 业务属性 | 变更数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_type` | `int unsigned` | NO | `NONE` | 状态 / 枚举 | 变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 结余 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `serial_num` | `varchar(64)` | NO | `NONE` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `remark` | `varchar(64)` | NO | `NONE` | 业务属性 | 备注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `time` | `bigint unsigned` | NO | `NONE` | 时间 | 交易时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### ams_charge_202505

- 表类型：`BASE TABLE`；字段数：9；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int unsigned` | NO | `MUL` | 业务属性 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `asset_id` | `int unsigned` | NO | `NONE` | 标识 / 关联 | 资产ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_count` | `bigint` | NO | `NONE` | 业务属性 | 变更数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_type` | `int unsigned` | NO | `NONE` | 状态 / 枚举 | 变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 结余 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `serial_num` | `varchar(64)` | NO | `NONE` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `remark` | `varchar(64)` | NO | `NONE` | 业务属性 | 备注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `time` | `bigint unsigned` | NO | `NONE` | 时间 | 交易时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### ams_charge_202506

- 表类型：`BASE TABLE`；字段数：9；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int unsigned` | NO | `MUL` | 业务属性 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `asset_id` | `int unsigned` | NO | `NONE` | 标识 / 关联 | 资产ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_count` | `bigint` | NO | `NONE` | 业务属性 | 变更数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_type` | `int unsigned` | NO | `NONE` | 状态 / 枚举 | 变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 结余 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `serial_num` | `varchar(64)` | NO | `NONE` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `remark` | `varchar(64)` | NO | `NONE` | 业务属性 | 备注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `time` | `bigint unsigned` | NO | `NONE` | 时间 | 交易时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### ams_charge_202507

- 表类型：`BASE TABLE`；字段数：9；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int unsigned` | NO | `MUL` | 业务属性 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `asset_id` | `int unsigned` | NO | `NONE` | 标识 / 关联 | 资产ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_count` | `bigint` | NO | `NONE` | 业务属性 | 变更数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_type` | `int unsigned` | NO | `NONE` | 状态 / 枚举 | 变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 结余 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `serial_num` | `varchar(64)` | NO | `NONE` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `remark` | `varchar(64)` | NO | `NONE` | 业务属性 | 备注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `time` | `bigint unsigned` | NO | `NONE` | 时间 | 交易时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### ams_charge_202508

- 表类型：`BASE TABLE`；字段数：10；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int unsigned` | NO | `MUL` | 业务属性 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `asset_id` | `int unsigned` | NO | `NONE` | 标识 / 关联 | 资产ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_count` | `bigint` | NO | `NONE` | 业务属性 | 变更数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_type` | `int unsigned` | NO | `NONE` | 状态 / 枚举 | 变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 结余 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `serial_num` | `varchar(64)` | NO | `NONE` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `remark` | `varchar(64)` | NO | `NONE` | 业务属性 | 备注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `time` | `bigint unsigned` | NO | `NONE` | 时间 | 交易时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `all_balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 余额 | 允许在授权范围内做聚合分析；不输出字段值 |

### ams_charge_202509

- 表类型：`BASE TABLE`；字段数：10；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int unsigned` | NO | `MUL` | 业务属性 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `asset_id` | `int unsigned` | NO | `NONE` | 标识 / 关联 | 资产ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_count` | `bigint` | NO | `NONE` | 业务属性 | 变更数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_type` | `int unsigned` | NO | `NONE` | 状态 / 枚举 | 变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 结余 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `serial_num` | `varchar(64)` | NO | `NONE` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `remark` | `varchar(64)` | NO | `NONE` | 业务属性 | 备注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `time` | `bigint unsigned` | NO | `NONE` | 时间 | 交易时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `all_balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 余额 | 允许在授权范围内做聚合分析；不输出字段值 |

### ams_charge_202510

- 表类型：`BASE TABLE`；字段数：10；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int unsigned` | NO | `MUL` | 业务属性 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `asset_id` | `int unsigned` | NO | `NONE` | 标识 / 关联 | 资产ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_count` | `bigint` | NO | `NONE` | 业务属性 | 变更数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_type` | `int unsigned` | NO | `NONE` | 状态 / 枚举 | 变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 结余 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `serial_num` | `varchar(64)` | NO | `NONE` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `remark` | `varchar(64)` | NO | `NONE` | 业务属性 | 备注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `time` | `bigint unsigned` | NO | `NONE` | 时间 | 交易时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `all_balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 余额 | 允许在授权范围内做聚合分析；不输出字段值 |

### ams_charge_202511

- 表类型：`BASE TABLE`；字段数：10；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int unsigned` | NO | `MUL` | 业务属性 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `asset_id` | `int unsigned` | NO | `NONE` | 标识 / 关联 | 资产ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_count` | `bigint` | NO | `NONE` | 业务属性 | 变更数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_type` | `int unsigned` | NO | `NONE` | 状态 / 枚举 | 变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 结余 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `serial_num` | `varchar(64)` | NO | `NONE` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `remark` | `varchar(64)` | NO | `NONE` | 业务属性 | 备注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `time` | `bigint unsigned` | NO | `NONE` | 时间 | 交易时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `all_balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 余额 | 允许在授权范围内做聚合分析；不输出字段值 |

### ams_charge_202512

- 表类型：`BASE TABLE`；字段数：10；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int unsigned` | NO | `MUL` | 业务属性 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `asset_id` | `int unsigned` | NO | `NONE` | 标识 / 关联 | 资产ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_count` | `bigint` | NO | `NONE` | 业务属性 | 变更数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_type` | `int unsigned` | NO | `NONE` | 状态 / 枚举 | 变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 结余 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `serial_num` | `varchar(64)` | NO | `NONE` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `remark` | `varchar(64)` | NO | `NONE` | 业务属性 | 备注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `time` | `bigint unsigned` | NO | `NONE` | 时间 | 交易时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `all_balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 余额 | 允许在授权范围内做聚合分析；不输出字段值 |

### ams_charge_202601

- 表类型：`BASE TABLE`；字段数：10；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int unsigned` | NO | `MUL` | 业务属性 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `asset_id` | `int unsigned` | NO | `NONE` | 标识 / 关联 | 资产ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_count` | `bigint` | NO | `NONE` | 业务属性 | 变更数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_type` | `int unsigned` | NO | `NONE` | 状态 / 枚举 | 变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 结余 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `serial_num` | `varchar(64)` | NO | `NONE` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `remark` | `varchar(64)` | NO | `NONE` | 业务属性 | 备注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `time` | `bigint unsigned` | NO | `NONE` | 时间 | 交易时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `all_balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 余额 | 允许在授权范围内做聚合分析；不输出字段值 |

### ams_charge_202602

- 表类型：`BASE TABLE`；字段数：10；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int unsigned` | NO | `MUL` | 业务属性 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `asset_id` | `int unsigned` | NO | `NONE` | 标识 / 关联 | 资产ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_count` | `bigint` | NO | `NONE` | 业务属性 | 变更数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_type` | `int unsigned` | NO | `NONE` | 状态 / 枚举 | 变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 结余 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `serial_num` | `varchar(64)` | NO | `NONE` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `remark` | `varchar(64)` | NO | `NONE` | 业务属性 | 备注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `time` | `bigint unsigned` | NO | `NONE` | 时间 | 交易时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `all_balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 余额 | 允许在授权范围内做聚合分析；不输出字段值 |

### ams_charge_202603

- 表类型：`BASE TABLE`；字段数：10；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int unsigned` | NO | `MUL` | 业务属性 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `asset_id` | `int unsigned` | NO | `NONE` | 标识 / 关联 | 资产ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_count` | `bigint` | NO | `NONE` | 业务属性 | 变更数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_type` | `int unsigned` | NO | `MUL` | 状态 / 枚举 | 变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 结余 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `serial_num` | `varchar(64)` | NO | `NONE` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `remark` | `varchar(64)` | NO | `NONE` | 业务属性 | 备注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `time` | `bigint unsigned` | NO | `NONE` | 时间 | 交易时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `all_balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 余额 | 允许在授权范围内做聚合分析；不输出字段值 |

### ams_charge_202604

- 表类型：`BASE TABLE`；字段数：10；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int unsigned` | NO | `MUL` | 业务属性 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `asset_id` | `int unsigned` | NO | `NONE` | 标识 / 关联 | 资产ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_count` | `bigint` | NO | `NONE` | 业务属性 | 变更数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_type` | `int unsigned` | NO | `MUL` | 状态 / 枚举 | 变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 结余 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `serial_num` | `varchar(64)` | NO | `NONE` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `remark` | `varchar(64)` | NO | `NONE` | 业务属性 | 备注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `time` | `bigint unsigned` | NO | `NONE` | 时间 | 交易时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `all_balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 余额 | 允许在授权范围内做聚合分析；不输出字段值 |

### ams_charge_202605

- 表类型：`BASE TABLE`；字段数：10；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int unsigned` | NO | `MUL` | 业务属性 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `asset_id` | `int unsigned` | NO | `NONE` | 标识 / 关联 | 资产ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_count` | `bigint` | NO | `NONE` | 业务属性 | 变更数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_type` | `int unsigned` | NO | `MUL` | 状态 / 枚举 | 变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 结余 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `serial_num` | `varchar(64)` | NO | `NONE` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `remark` | `varchar(64)` | NO | `NONE` | 业务属性 | 备注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `time` | `bigint unsigned` | NO | `NONE` | 时间 | 交易时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `all_balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 余额 | 允许在授权范围内做聚合分析；不输出字段值 |

### ams_charge_202606

- 表类型：`BASE TABLE`；字段数：10；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int unsigned` | NO | `MUL` | 业务属性 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `asset_id` | `int unsigned` | NO | `NONE` | 标识 / 关联 | 资产ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_count` | `bigint` | NO | `NONE` | 业务属性 | 变更数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_type` | `int unsigned` | NO | `MUL` | 状态 / 枚举 | 变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 结余 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `serial_num` | `varchar(64)` | NO | `NONE` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `remark` | `varchar(64)` | NO | `NONE` | 业务属性 | 备注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `time` | `bigint unsigned` | NO | `MUL` | 时间 | 交易时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `all_balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 余额 | 允许在授权范围内做聚合分析；不输出字段值 |

### ams_charge_202607

- 表类型：`BASE TABLE`；字段数：10；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int unsigned` | NO | `MUL` | 业务属性 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `asset_id` | `int unsigned` | NO | `NONE` | 标识 / 关联 | 资产ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_count` | `bigint` | NO | `NONE` | 业务属性 | 变更数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_type` | `int unsigned` | NO | `MUL` | 状态 / 枚举 | 变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 结余 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `serial_num` | `varchar(64)` | NO | `NONE` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `remark` | `varchar(64)` | NO | `NONE` | 业务属性 | 备注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `time` | `bigint unsigned` | NO | `MUL` | 时间 | 交易时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `all_balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 余额 | 允许在授权范围内做聚合分析；不输出字段值 |

### ams_charge_202608

- 表类型：`BASE TABLE`；字段数：10；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int unsigned` | NO | `MUL` | 业务属性 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `asset_id` | `int unsigned` | NO | `NONE` | 标识 / 关联 | 资产ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_count` | `bigint` | NO | `NONE` | 业务属性 | 变更数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_type` | `int unsigned` | NO | `MUL` | 状态 / 枚举 | 变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 结余 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `serial_num` | `varchar(64)` | NO | `NONE` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `remark` | `varchar(64)` | NO | `NONE` | 业务属性 | 备注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `time` | `bigint unsigned` | NO | `MUL` | 时间 | 交易时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `all_balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 余额 | 允许在授权范围内做聚合分析；不输出字段值 |

### ams_diamond_asset

- 表类型：`BASE TABLE`；字段数：7；数据层：业务表（事实/维度待补证）。
- 业务域：资产 / 货币（`inferred_name_only`）；建议：资产流、奖励成本、余额变化与账本对账；必须区分真金、金币和奖励资产。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int unsigned` | NO | `MUL` | 业务属性 | 用户唯一ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `asset_id` | `int unsigned` | NO | `NONE` | 标识 / 关联 | 资产ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `balance` | `bigint unsigned` | NO | `NONE` | 金额 / 资产 | 结余 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `create_time` | `datetime` | NO | `NONE` | 时间 | 创建时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `update_time` | `datetime` | NO | `NONE` | 时间 | 更新时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `last_update_time` | `int` | NO | `NONE` | 时间 | 最后更新时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### ams_diamond_charge_000000

- 表类型：`BASE TABLE`；字段数：10；数据层：业务表（事实/维度待补证）。
- 业务域：资产 / 货币（`inferred_name_only`）；建议：资产流、奖励成本、余额变化与账本对账；必须区分真金、金币和奖励资产。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int unsigned` | NO | `MUL` | 业务属性 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `asset_id` | `int unsigned` | NO | `NONE` | 标识 / 关联 | 资产ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_count` | `bigint` | NO | `NONE` | 业务属性 | 变更数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_type` | `int unsigned` | NO | `NONE` | 状态 / 枚举 | 变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 结余 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `serial_num` | `varchar(64)` | NO | `NONE` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `remark` | `varchar(64)` | NO | `NONE` | 业务属性 | 备注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `cash_reward` | `bigint` | NO | `NONE` | 金额 / 资产 | 额外cash奖励 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `time` | `bigint unsigned` | NO | `NONE` | 时间 | 交易时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### ams_diamond_charge_202512

- 表类型：`BASE TABLE`；字段数：10；数据层：业务表（事实/维度待补证）。
- 业务域：资产 / 货币（`inferred_name_only`）；建议：资产流、奖励成本、余额变化与账本对账；必须区分真金、金币和奖励资产。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int unsigned` | NO | `MUL` | 业务属性 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `asset_id` | `int unsigned` | NO | `NONE` | 标识 / 关联 | 资产ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_count` | `bigint` | NO | `NONE` | 业务属性 | 变更数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_type` | `int unsigned` | NO | `NONE` | 状态 / 枚举 | 变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 结余 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `serial_num` | `varchar(64)` | NO | `NONE` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `remark` | `varchar(64)` | NO | `NONE` | 业务属性 | 备注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `cash_reward` | `bigint` | NO | `NONE` | 金额 / 资产 | 额外cash奖励 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `time` | `bigint unsigned` | NO | `NONE` | 时间 | 交易时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### ams_diamond_charge_202601

- 表类型：`BASE TABLE`；字段数：10；数据层：业务表（事实/维度待补证）。
- 业务域：资产 / 货币（`inferred_name_only`）；建议：资产流、奖励成本、余额变化与账本对账；必须区分真金、金币和奖励资产。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int unsigned` | NO | `MUL` | 业务属性 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `asset_id` | `int unsigned` | NO | `NONE` | 标识 / 关联 | 资产ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_count` | `bigint` | NO | `NONE` | 业务属性 | 变更数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_type` | `int unsigned` | NO | `NONE` | 状态 / 枚举 | 变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 结余 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `serial_num` | `varchar(64)` | NO | `NONE` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `remark` | `varchar(64)` | NO | `NONE` | 业务属性 | 备注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `cash_reward` | `bigint` | NO | `NONE` | 金额 / 资产 | 额外cash奖励 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `time` | `bigint unsigned` | NO | `NONE` | 时间 | 交易时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### ams_diamond_charge_202602

- 表类型：`BASE TABLE`；字段数：10；数据层：业务表（事实/维度待补证）。
- 业务域：资产 / 货币（`inferred_name_only`）；建议：资产流、奖励成本、余额变化与账本对账；必须区分真金、金币和奖励资产。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int unsigned` | NO | `MUL` | 业务属性 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `asset_id` | `int unsigned` | NO | `NONE` | 标识 / 关联 | 资产ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_count` | `bigint` | NO | `NONE` | 业务属性 | 变更数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_type` | `int unsigned` | NO | `NONE` | 状态 / 枚举 | 变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 结余 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `serial_num` | `varchar(64)` | NO | `NONE` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `remark` | `varchar(64)` | NO | `NONE` | 业务属性 | 备注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `cash_reward` | `bigint` | NO | `NONE` | 金额 / 资产 | 额外cash奖励 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `time` | `bigint unsigned` | NO | `NONE` | 时间 | 交易时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### ams_diamond_charge_202603

- 表类型：`BASE TABLE`；字段数：10；数据层：业务表（事实/维度待补证）。
- 业务域：资产 / 货币（`inferred_name_only`）；建议：资产流、奖励成本、余额变化与账本对账；必须区分真金、金币和奖励资产。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int unsigned` | NO | `MUL` | 业务属性 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `asset_id` | `int unsigned` | NO | `NONE` | 标识 / 关联 | 资产ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_count` | `bigint` | NO | `NONE` | 业务属性 | 变更数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_type` | `int unsigned` | NO | `NONE` | 状态 / 枚举 | 变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 结余 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `serial_num` | `varchar(64)` | NO | `NONE` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `remark` | `varchar(64)` | NO | `NONE` | 业务属性 | 备注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `cash_reward` | `bigint` | NO | `NONE` | 金额 / 资产 | 额外cash奖励 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `time` | `bigint unsigned` | NO | `NONE` | 时间 | 交易时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### ams_diamond_charge_202604

- 表类型：`BASE TABLE`；字段数：10；数据层：业务表（事实/维度待补证）。
- 业务域：资产 / 货币（`inferred_name_only`）；建议：资产流、奖励成本、余额变化与账本对账；必须区分真金、金币和奖励资产。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int unsigned` | NO | `MUL` | 业务属性 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `asset_id` | `int unsigned` | NO | `NONE` | 标识 / 关联 | 资产ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_count` | `bigint` | NO | `NONE` | 业务属性 | 变更数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_type` | `int unsigned` | NO | `NONE` | 状态 / 枚举 | 变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 结余 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `serial_num` | `varchar(64)` | NO | `NONE` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `remark` | `varchar(64)` | NO | `NONE` | 业务属性 | 备注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `cash_reward` | `bigint` | NO | `NONE` | 金额 / 资产 | 额外cash奖励 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `time` | `bigint unsigned` | NO | `NONE` | 时间 | 交易时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### ams_diamond_charge_202605

- 表类型：`BASE TABLE`；字段数：10；数据层：业务表（事实/维度待补证）。
- 业务域：资产 / 货币（`inferred_name_only`）；建议：资产流、奖励成本、余额变化与账本对账；必须区分真金、金币和奖励资产。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int unsigned` | NO | `MUL` | 业务属性 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `asset_id` | `int unsigned` | NO | `NONE` | 标识 / 关联 | 资产ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_count` | `bigint` | NO | `NONE` | 业务属性 | 变更数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_type` | `int unsigned` | NO | `NONE` | 状态 / 枚举 | 变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 结余 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `serial_num` | `varchar(64)` | NO | `NONE` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `remark` | `varchar(64)` | NO | `NONE` | 业务属性 | 备注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `cash_reward` | `bigint` | NO | `NONE` | 金额 / 资产 | 额外cash奖励 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `time` | `bigint unsigned` | NO | `NONE` | 时间 | 交易时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### ams_diamond_charge_202606

- 表类型：`BASE TABLE`；字段数：10；数据层：业务表（事实/维度待补证）。
- 业务域：资产 / 货币（`inferred_name_only`）；建议：资产流、奖励成本、余额变化与账本对账；必须区分真金、金币和奖励资产。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int unsigned` | NO | `MUL` | 业务属性 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `asset_id` | `int unsigned` | NO | `NONE` | 标识 / 关联 | 资产ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_count` | `bigint` | NO | `NONE` | 业务属性 | 变更数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_type` | `int unsigned` | NO | `NONE` | 状态 / 枚举 | 变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 结余 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `serial_num` | `varchar(64)` | NO | `NONE` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `remark` | `varchar(64)` | NO | `NONE` | 业务属性 | 备注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `cash_reward` | `bigint` | NO | `NONE` | 金额 / 资产 | 额外cash奖励 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `time` | `bigint unsigned` | NO | `NONE` | 时间 | 交易时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### ams_diamond_charge_202607

- 表类型：`BASE TABLE`；字段数：10；数据层：业务表（事实/维度待补证）。
- 业务域：资产 / 货币（`inferred_name_only`）；建议：资产流、奖励成本、余额变化与账本对账；必须区分真金、金币和奖励资产。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int unsigned` | NO | `MUL` | 业务属性 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `asset_id` | `int unsigned` | NO | `NONE` | 标识 / 关联 | 资产ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_count` | `bigint` | NO | `NONE` | 业务属性 | 变更数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_type` | `int unsigned` | NO | `NONE` | 状态 / 枚举 | 变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 结余 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `serial_num` | `varchar(64)` | NO | `NONE` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `remark` | `varchar(64)` | NO | `NONE` | 业务属性 | 备注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `cash_reward` | `bigint` | NO | `NONE` | 金额 / 资产 | 额外cash奖励 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `time` | `bigint unsigned` | NO | `NONE` | 时间 | 交易时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### ams_diamond_charge_202608

- 表类型：`BASE TABLE`；字段数：10；数据层：业务表（事实/维度待补证）。
- 业务域：资产 / 货币（`inferred_name_only`）；建议：资产流、奖励成本、余额变化与账本对账；必须区分真金、金币和奖励资产。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int unsigned` | NO | `MUL` | 业务属性 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `asset_id` | `int unsigned` | NO | `NONE` | 标识 / 关联 | 资产ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_count` | `bigint` | NO | `NONE` | 业务属性 | 变更数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_type` | `int unsigned` | NO | `NONE` | 状态 / 枚举 | 变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 结余 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `serial_num` | `varchar(64)` | NO | `NONE` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `remark` | `varchar(64)` | NO | `NONE` | 业务属性 | 备注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `cash_reward` | `bigint` | NO | `NONE` | 金额 / 资产 | 额外cash奖励 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `time` | `bigint unsigned` | NO | `NONE` | 时间 | 交易时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### baccarat_record_log

- 表类型：`BASE TABLE`；字段数：28；数据层：业务表（事实/维度待补证）。
- 业务域：游戏 / 对局 / RTP（`inferred_name_only`）；建议：游戏局、下注、结算、RTP 和玩法/房间拆分；需与 GAMEEND 链路核验。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `userid` | `int` | NO | `MUL` | 业务属性 | 玩家id | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `videoid` | `varchar(128)` | NO | `MUL` | 业务属性 | 录像id | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `playtype` | `int` | NO | `NONE` | 状态 / 枚举 | 玩法id | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `starttime` | `int` | NO | `NONE` | 时间 | 开始时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `time` | `int` | NO | `MUL` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `result0` | `int` | NO | `NONE` | 状态 / 枚举 | 下注区域0结果 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `result1` | `int` | NO | `NONE` | 状态 / 枚举 | 下注区域1结果 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `result2` | `int` | NO | `NONE` | 状态 / 枚举 | 下注区域2结果 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `result3` | `int` | NO | `NONE` | 状态 / 枚举 | 下注区域3结果 | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `result4` | `int` | NO | `NONE` | 状态 / 枚举 | 下注区域4结果 | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `result5` | `int` | NO | `NONE` | 状态 / 枚举 | 下注区域5结果 | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `result6` | `int` | NO | `NONE` | 状态 / 枚举 | 下注区域6结果 | 允许在授权范围内做聚合分析；不输出字段值 |
| 14 | `result7` | `int` | NO | `NONE` | 状态 / 枚举 | 下注区域7结果 | 允许在授权范围内做聚合分析；不输出字段值 |
| 15 | `result8` | `int` | NO | `NONE` | 状态 / 枚举 | 下注区域8结果 | 允许在授权范围内做聚合分析；不输出字段值 |
| 16 | `result9` | `int` | NO | `NONE` | 状态 / 枚举 | 下注区域9结果 | 允许在授权范围内做聚合分析；不输出字段值 |
| 17 | `result10` | `int` | NO | `NONE` | 状态 / 枚举 | 下注区域10结果 | 允许在授权范围内做聚合分析；不输出字段值 |
| 18 | `bet0` | `bigint` | NO | `NONE` | 游戏 / 玩法 | 下注区域0赌注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 19 | `bet1` | `bigint` | NO | `NONE` | 游戏 / 玩法 | 下注区域1赌注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 20 | `bet2` | `bigint` | NO | `NONE` | 游戏 / 玩法 | 下注区域2赌注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 21 | `bet3` | `bigint` | NO | `NONE` | 游戏 / 玩法 | 下注区域3赌注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 22 | `bet4` | `bigint` | NO | `NONE` | 游戏 / 玩法 | 下注区域4赌注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 23 | `bet5` | `bigint` | NO | `NONE` | 游戏 / 玩法 | 下注区域5赌注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 24 | `bet6` | `bigint` | NO | `NONE` | 游戏 / 玩法 | 下注区域6赌注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 25 | `bet7` | `bigint` | NO | `NONE` | 游戏 / 玩法 | 下注区域7赌注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 26 | `bet8` | `bigint` | NO | `NONE` | 游戏 / 玩法 | 下注区域8赌注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 27 | `bet9` | `bigint` | NO | `NONE` | 游戏 / 玩法 | 下注区域9赌注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 28 | `bet10` | `bigint` | NO | `NONE` | 游戏 / 玩法 | 下注区域10赌注 | 允许在授权范围内做聚合分析；不输出字段值 |

### ball_game_state

- 表类型：`BASE TABLE`；字段数：4；数据层：业务表（事实/维度待补证）。
- 业务域：游戏 / 对局 / RTP（`inferred_name_only`）；建议：游戏局、下注、结算、RTP 和玩法/房间拆分；需与 GAMEEND 链路核验。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint` | NO | `PRI` | 标识 / 关联 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `bigint` | NO | `UNI` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `remain_free_times` | `bigint` | NO | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `update_at` | `bigint` | YES | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |

### betc_casino_bet_info

- 表类型：`BASE TABLE`；字段数：10；数据层：业务表（事实/维度待补证）。
- 业务域：游戏 / 对局 / RTP（`inferred_name_only`）；建议：游戏局、下注、结算、RTP 和玩法/房间拆分；需与 GAMEEND 链路核验。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint` | NO | `PRI` | 标识 / 关联 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `bet_amount` | `int` | YES | `NONE` | 金额 / 资产 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `uid` | `bigint` | NO | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | [REDACTED:THIRD_PARTY_RAW_RESPONSE_CANDIDATE] | `text` | NO | `NONE` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 受限；不得进入普通看板或导出 |
| 5 | `asset` | `text` | NO | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `create_time` | `bigint` | NO | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `update_time` | `bigint` | NO | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `game_id` | `int` | NO | `NONE` | 标识 / 关联 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `status` | `int` | NO | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `commit_log` | `varchar(63)` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |

### collector_cash_active

- 表类型：`BASE TABLE`；字段数：11；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `Id` | `bigint` | NO | `PRI` | 标识 / 关联 | 主键 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `play_type` | `int` | NO | `MUL` | 状态 / 枚举 | appId | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `day` | `int` | NO | `NONE` | 业务属性 | day | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `act_0` | `int` | NO | `NONE` | 业务属性 | 活跃 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `act_50` | `int` | NO | `NONE` | 业务属性 | 50活跃 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `act_100` | `int` | NO | `NONE` | 业务属性 | 活跃 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `act_200` | `int` | NO | `NONE` | 业务属性 | 活跃 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `act_500` | `int` | NO | `NONE` | 业务属性 | 活跃 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `act_1000` | `int` | NO | `NONE` | 业务属性 | 活跃 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `act_2500` | `int` | NO | `NONE` | 业务属性 | 活跃 | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `act_5000` | `int` | NO | `NONE` | 业务属性 | 活跃 | 允许在授权范围内做聚合分析；不输出字段值 |

### collector_remain_report

- 表类型：`BASE TABLE`；字段数：6；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `Id` | `int` | NO | `PRI` | 标识 / 关联 | 主键 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `appid` | `int` | NO | `MUL` | 业务属性 | appId | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `nday` | `int` | NO | `NONE` | 业务属性 | nday | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `remain` | `int` | NO | `NONE` | 业务属性 | 留存 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `remainrate` | `int` | NO | `NONE` | 时间 | 留存率 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `time` | `int` | NO | `NONE` | 时间 | 日期 | 允许在授权范围内做聚合分析；不输出字段值 |

### collector_report

- 表类型：`BASE TABLE`；字段数：10；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增主键 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `appid` | `int unsigned` | NO | `MUL` | 业务属性 | 区服ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `newly` | `int unsigned` | NO | `NONE` | 业务属性 | 新增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `active` | `int unsigned` | NO | `NONE` | 业务属性 | 日活 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `effectactive` | `int unsigned` | NO | `NONE` | 业务属性 | 有效日活 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `effectactive_coin` | `int unsigned` | NO | `NONE` | 金额 / 资产 | 金币场有效日活 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `round` | `int unsigned` | NO | `NONE` | 业务属性 | 完整把数 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `totalscore` | `int unsigned` | NO | `NONE` | 业务属性 | 得分总流水 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `dissolved` | `int unsigned` | NO | `NONE` | 业务属性 | 解散把数 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `time` | `int unsigned` | NO | `NONE` | 时间 | 时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### easy_bet

- 表类型：`BASE TABLE`；字段数：23；数据层：业务表（事实/维度待补证）。
- 业务域：游戏 / 对局 / RTP（`inferred_name_only`）；建议：游戏局、下注、结算、RTP 和玩法/房间拆分；需与 GAMEEND 链路核验。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint` | NO | `PRI` | 标识 / 关联 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `bigint` | NO | `MUL` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `amount` | `decimal(12,3)` | YES | `NONE` | 金额 / 资产 | bet金额 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `win_amount` | `decimal(12,3)` | YES | `NONE` | 金额 / 资产 | 最后结算金额，是累计和 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `total_odds` | `decimal(10,3)` | YES | `NONE` | 业务属性 | 总赔率 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `potential_return` | `decimal(15,3)` | YES | `NONE` | 业务属性 | 潜在可赢金额 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `cash_out` | `decimal(15,3)` | YES | `NONE` | 金额 / 资产 | cash_out | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `bet_mode` | `int` | YES | `NONE` | 状态 / 枚举 | 投注模式 0:普通 1:串关 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `booking_code` | `varchar(64)` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `award_code` | `varchar(64)` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `odds_change` | `text` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `bet_info` | `mediumtext` | YES | `NONE` | 游戏 / 玩法 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `booking_info` | `text` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 14 | `reference` | `varchar(128)` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 15 | `order_id` | `varchar(64)` | NO | `UNI` | 标识 / 关联 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 16 | `create_time` | `bigint` | NO | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 17 | `update_time` | `bigint` | NO | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 18 | `status` | `int` | NO | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 19 | `asset` | `text` | YES | `NONE` | 业务属性 | 资产 | 允许在授权范围内做聚合分析；不输出字段值 |
| 20 | `extra_rebate_amount` | `decimal(12,3)` | YES | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 21 | `extra_rebate_rate` | `int` | YES | `NONE` | 时间 | 额外返利比例，百分比 | 允许在授权范围内做聚合分析；不输出字段值 |
| 22 | `share_bet` | `int` | NO | `NONE` | 游戏 / 玩法 | 是否是跟单 0:不是 1:抽佣订单；2:无佣订单 | 允许在授权范围内做聚合分析；不输出字段值 |
| 23 | `settled_asset` | `text` | YES | `NONE` | 业务属性 | 最近一次正向结算的实际返还分布，用于精确回滚 | 允许在授权范围内做聚合分析；不输出字段值 |

### easy_win_competition_info

- 表类型：`BASE TABLE`；字段数：7；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint` | NO | `PRI` | 标识 / 关联 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `competition_id` | `varchar(64)` | NO | `UNI` | 标识 / 关联 | 比赛id | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `competition_name` | `varchar(64)` | NO | `NONE` | 业务属性 | 赛事名 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `match_count` | `int` | YES | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `region_id` | `varchar(64)` | NO | `MUL` | 标识 / 关联 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `region_name` | `varchar(64)` | NO | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `sport_name` | `varchar(64)` | NO | `NONE` | 业务属性 | 分类 | 允许在授权范围内做聚合分析；不输出字段值 |

### easy_win_fav_casina

- 表类型：`BASE TABLE`；字段数：6；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint` | NO | `PRI` | 标识 / 关联 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `bigint` | NO | `MUL` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `competition_id` | `varchar(63)` | NO | `NONE` | 标识 / 关联 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `sport` | `varchar(31)` | NO | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `create_time` | `bigint` | NO | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `update_time` | `bigint` | NO | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |

### email_log

- 表类型：`BASE TABLE`；字段数：7；数据层：业务表（事实/维度待补证）。
- 业务域：运营 / 消息（`inferred_name_only`）；建议：消息触达、发送结果与运营触发分析；不得输出接收人身份字段。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `address` | `varchar(32)` | YES | `MUL` | 业务属性 | 地址 | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `msg` | `varchar(256)` | YES | `NONE` | 业务属性 | 内容 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `channel` | `varchar(16)` | YES | `NONE` | 业务属性 | 渠道 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `category` | `varchar(16)` | YES | `NONE` | 时间 | 分类 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `status` | `tinyint` | YES | `NONE` | 时间 | 是否成功 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `time` | `int unsigned` | YES | `NONE` | 时间 | 时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### email_stat

- 表类型：`BASE TABLE`；字段数：5；数据层：业务表（事实/维度待补证）。
- 业务域：运营 / 消息（`inferred_name_only`）；建议：消息触达、发送结果与运营触发分析；不得输出接收人身份字段。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `address` | `varchar(32)` | YES | `UNI` | 业务属性 | 地址 | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `create_time` | `int unsigned` | YES | `NONE` | 时间 | 创建时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `success_count` | `int unsigned` | YES | `NONE` | 业务属性 | 成功次数 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `fail_count` | `int unsigned` | YES | `NONE` | 业务属性 | 失败次数 | 允许在授权范围内做聚合分析；不输出字段值 |

### ew_booking_code

- 表类型：`BASE TABLE`；字段数：14；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint` | NO | `PRI` | 标识 / 关联 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `code` | `varchar(6)` | NO | `UNI` | 业务属性 | 6位跟单码 | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `uid` | `bigint` | NO | `MUL` | 业务属性 | 生成者uid，0表示未登录 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `device_id` | `varchar(128)` | NO | `MUL` | 标识 / 关联 | 设备ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `bet_selections` | `mediumtext` | NO | `NONE` | 游戏 / 玩法 | 投注组合JSON | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `selections_hash` | `varchar(64)` | NO | `MUL` | 业务属性 | 投注组合哈希，用于去重 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `earliest_close_at` | `bigint` | NO | `NONE` | 时间 | 最早关盘时间戳ms | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `latest_close_at` | `bigint` | NO | `NONE` | 时间 | 最晚关盘时间戳ms | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `expire_at` | `bigint` | NO | `MUL` | 时间 | 跟单码使用截止时间戳ms | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `recycle_at` | `bigint` | NO | `MUL` | 时间 | 跟单码回收时间戳ms | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `match_count` | `int` | NO | `NONE` | 时间 | 比赛场数 | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `default_bet_mode` | `int` | NO | `NONE` | 状态 / 枚举 | 默认投注模式 0:单关 1:串关 | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `create_time` | `bigint` | NO | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 14 | `update_time` | `bigint` | NO | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |

### ew_copied_bet

- 表类型：`BASE TABLE`；字段数：17；数据层：业务表（事实/维度待补证）。
- 业务域：游戏 / 对局 / RTP（`inferred_name_only`）；建议：游戏局、下注、结算、RTP 和玩法/房间拆分；需与 GAMEEND 链路核验。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint` | NO | `PRI` | 标识 / 关联 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `uid` | `bigint` | NO | `MUL` | 业务属性 | 跟单者uid | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `shared_bet_id` | `bigint` | NO | `MUL` | 标识 / 关联 | 关联的推单ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `sharer_uid` | `bigint` | NO | `MUL` | 业务属性 | 带单者uid | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `sharer_nickname` | `varchar(64)` | NO | `NONE` | 业务属性 | 带单者昵称 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `order_id` | `varchar(64)` | NO | `UNI` | 标识 / 关联 | 跟单者的EasyBet订单ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `commission_rate` | `int` | NO | `NONE` | 时间 | 佣金比例百分比 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `bet_count` | `int` | NO | `NONE` | 游戏 / 玩法 | 投注项数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `stake_amount` | `decimal(12,2)` | NO | `NONE` | 金额 / 资产 | 跟单者下注金额 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `total_odds` | `decimal(12,3)` | NO | `NONE` | 业务属性 | 总赔率 | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `return_amount` | `decimal(12,2)` | NO | `NONE` | 金额 / 资产 | 未扣佣金时返还金额 | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `commission_amount` | `decimal(12,2)` | NO | `NONE` | 金额 / 资产 | 实际佣金金额 | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `actual_return` | `decimal(12,2)` | NO | `NONE` | 业务属性 | 扣除佣金后实际返还 | 允许在授权范围内做聚合分析；不输出字段值 |
| 14 | `status` | `int` | NO | `NONE` | 时间 | 0:待结算 1:中奖 2:未中奖 3:返还 4:CashOut | 允许在授权范围内做聚合分析；不输出字段值 |
| 15 | `commission_settled` | `tinyint(1)` | NO | `NONE` | 业务属性 | 佣金是否已结算 | 允许在授权范围内做聚合分析；不输出字段值 |
| 16 | `create_time` | `bigint` | NO | `MUL` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 17 | `update_time` | `bigint` | NO | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |

### ew_shared_bet

- 表类型：`BASE TABLE`；字段数：21；数据层：业务表（事实/维度待补证）。
- 业务域：游戏 / 对局 / RTP（`inferred_name_only`）；建议：游戏局、下注、结算、RTP 和玩法/房间拆分；需与 GAMEEND 链路核验。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint` | NO | `PRI` | 标识 / 关联 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `uid` | `bigint` | NO | `MUL` | 业务属性 | 带单者uid | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `nickname` | `varchar(64)` | NO | `NONE` | 业务属性 | 带单者昵称 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `order_id` | `varchar(64)` | NO | `UNI` | 标识 / 关联 | 关联的EasyBet订单ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `booking_code` | `varchar(64)` | NO | `MUL` | 业务属性 | 关联的booking code | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `commission_rate` | `int` | NO | `NONE` | 时间 | 佣金比例百分比 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `bet_mode` | `int` | NO | `NONE` | 状态 / 枚举 | 投注模式 0:单关 1:串关 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `bet_count` | `int` | NO | `NONE` | 游戏 / 玩法 | 投注项数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `stake_amount` | `decimal(12,2)` | NO | `NONE` | 金额 / 资产 | 带单者下注金额 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `total_odds` | `decimal(12,3)` | NO | `NONE` | 业务属性 | 总赔率 | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `potential_return` | `decimal(12,2)` | NO | `NONE` | 业务属性 | 预计返还 | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `bet_selections` | `mediumtext` | NO | `NONE` | 游戏 / 玩法 | 投注组合JSON | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `earliest_close_at` | `bigint` | NO | `NONE` | 时间 | 最早关盘时间=截止时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 14 | `latest_close_at` | `bigint` | NO | `NONE` | 时间 | 最晚关盘时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 15 | `copied_count` | `int` | NO | `NONE` | 业务属性 | 被跟单次数,不含自己 | 允许在授权范围内做聚合分析；不输出字段值 |
| 16 | `copied_stake` | `decimal(12,2)` | NO | `NONE` | 业务属性 | 跟单总金额,不含自己 | 允许在授权范围内做聚合分析；不输出字段值 |
| 17 | `win_count` | `int` | NO | `NONE` | 业务属性 | 最近10单中奖数 | 允许在授权范围内做聚合分析；不输出字段值 |
| 18 | `total_shared` | `int` | NO | `NONE` | 业务属性 | 最近公开分享总单数 | 允许在授权范围内做聚合分析；不输出字段值 |
| 19 | `status` | `int` | NO | `NONE` | 时间 | 0:进行中 1:已过期 2:已结算 | 允许在授权范围内做聚合分析；不输出字段值 |
| 20 | `create_time` | `bigint` | NO | `MUL` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 21 | `update_time` | `bigint` | NO | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |

### ew_user_follow

- 表类型：`BASE TABLE`；字段数：4；数据层：业务表（事实/维度待补证）。
- 业务域：用户 / 账号（`inferred_name_only`）；建议：注册、登录与生命周期聚合；禁止导出可识别身份字段。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint` | NO | `PRI` | 标识 / 关联 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `uid` | `bigint` | NO | `MUL` | 业务属性 | 关注者uid | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `follow_uid` | `bigint` | NO | `MUL` | 业务属性 | 被关注者uid | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `create_time` | `bigint` | NO | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |

### extra_remark

- 表类型：`BASE TABLE`；字段数：4；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `group_key` | `varchar(15)` | NO | `MUL` | 业务属性 | 分组key | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | [REDACTED:THIRD_PARTY_RAW_RESPONSE_CANDIDATE] | `text` | NO | `NONE` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 受限；不得进入普通看板或导出 |
| 4 | `time` | `bigint` | NO | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |

### finance_transfer_log

- 表类型：`BASE TABLE`；字段数：9；数据层：业务表（事实/维度待补证）。
- 业务域：支付 / 提现（`inferred_name_only`）；建议：支付/提现漏斗、成功率、时延与失败码；金融金额以服务端事实复核。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `source_id` | `int unsigned` | NO | `NONE` | 标识 / 关联 | 转出ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `dest_id` | `int unsigned` | NO | `MUL` | 标识 / 关联 | 转入ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_count` | `bigint` | NO | `NONE` | 业务属性 | 变更数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `source_nick` | `varchar(64)` | NO | `NONE` | 业务属性 | 转出昵称 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `dest_nick` | `varchar(64)` | NO | `NONE` | 业务属性 | 转入昵称 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `source_header` | `varchar(255)` | NO | `NONE` | 业务属性 | 转出头像 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `dest_header` | `varchar(255)` | NO | `NONE` | 业务属性 | 转入头像 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `create_time` | `datetime` | NO | `NONE` | 时间 | 创建时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### game_diamond_record_000000

- 表类型：`BASE TABLE`；字段数：7；数据层：业务表（事实/维度待补证）。
- 业务域：资产 / 货币（`inferred_name_only`）；建议：资产流、奖励成本、余额变化与账本对账；必须区分真金、金币和奖励资产。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `bigint unsigned` | NO | `MUL` | 业务属性 | uid | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `game_id` | `int` | NO | `NONE` | 标识 / 关联 | 游戏id | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `bet_amount` | `bigint` | NO | `NONE` | 金额 / 资产 | 下注金额 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `win_amount` | `bigint` | NO | `NONE` | 金额 / 资产 | 赢金额 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `extra_reward` | `bigint` | NO | `NONE` | 业务属性 | 额外奖励 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `update_at` | `bigint` | NO | `NONE` | 时间 | 更新时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### game_diamond_record_202511

- 表类型：`BASE TABLE`；字段数：7；数据层：业务表（事实/维度待补证）。
- 业务域：资产 / 货币（`inferred_name_only`）；建议：资产流、奖励成本、余额变化与账本对账；必须区分真金、金币和奖励资产。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `bigint unsigned` | NO | `MUL` | 业务属性 | uid | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `game_id` | `int` | NO | `NONE` | 标识 / 关联 | 游戏id | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `bet_amount` | `bigint` | NO | `NONE` | 金额 / 资产 | 下注金额 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `win_amount` | `bigint` | NO | `NONE` | 金额 / 资产 | 赢金额 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `extra_reward` | `bigint` | NO | `NONE` | 业务属性 | 额外奖励 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `update_at` | `bigint` | NO | `NONE` | 时间 | 更新时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### game_diamond_record_202512

- 表类型：`BASE TABLE`；字段数：7；数据层：业务表（事实/维度待补证）。
- 业务域：资产 / 货币（`inferred_name_only`）；建议：资产流、奖励成本、余额变化与账本对账；必须区分真金、金币和奖励资产。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `bigint unsigned` | NO | `MUL` | 业务属性 | uid | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `game_id` | `int` | NO | `NONE` | 标识 / 关联 | 游戏id | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `bet_amount` | `bigint` | NO | `NONE` | 金额 / 资产 | 下注金额 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `win_amount` | `bigint` | NO | `NONE` | 金额 / 资产 | 赢金额 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `extra_reward` | `bigint` | NO | `NONE` | 业务属性 | 额外奖励 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `update_at` | `bigint` | NO | `NONE` | 时间 | 更新时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### game_diamond_record_202601

- 表类型：`BASE TABLE`；字段数：7；数据层：业务表（事实/维度待补证）。
- 业务域：资产 / 货币（`inferred_name_only`）；建议：资产流、奖励成本、余额变化与账本对账；必须区分真金、金币和奖励资产。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `bigint unsigned` | NO | `MUL` | 业务属性 | uid | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `game_id` | `int` | NO | `NONE` | 标识 / 关联 | 游戏id | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `bet_amount` | `bigint` | NO | `NONE` | 金额 / 资产 | 下注金额 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `win_amount` | `bigint` | NO | `NONE` | 金额 / 资产 | 赢金额 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `extra_reward` | `bigint` | NO | `NONE` | 业务属性 | 额外奖励 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `update_at` | `bigint` | NO | `NONE` | 时间 | 更新时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### game_diamond_record_202602

- 表类型：`BASE TABLE`；字段数：7；数据层：业务表（事实/维度待补证）。
- 业务域：资产 / 货币（`inferred_name_only`）；建议：资产流、奖励成本、余额变化与账本对账；必须区分真金、金币和奖励资产。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `bigint unsigned` | NO | `MUL` | 业务属性 | uid | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `game_id` | `int` | NO | `NONE` | 标识 / 关联 | 游戏id | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `bet_amount` | `bigint` | NO | `NONE` | 金额 / 资产 | 下注金额 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `win_amount` | `bigint` | NO | `NONE` | 金额 / 资产 | 赢金额 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `extra_reward` | `bigint` | NO | `NONE` | 业务属性 | 额外奖励 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `update_at` | `bigint` | NO | `NONE` | 时间 | 更新时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### game_diamond_record_202603

- 表类型：`BASE TABLE`；字段数：7；数据层：业务表（事实/维度待补证）。
- 业务域：资产 / 货币（`inferred_name_only`）；建议：资产流、奖励成本、余额变化与账本对账；必须区分真金、金币和奖励资产。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `bigint unsigned` | NO | `MUL` | 业务属性 | uid | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `game_id` | `int` | NO | `NONE` | 标识 / 关联 | 游戏id | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `bet_amount` | `bigint` | NO | `NONE` | 金额 / 资产 | 下注金额 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `win_amount` | `bigint` | NO | `NONE` | 金额 / 资产 | 赢金额 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `extra_reward` | `bigint` | NO | `NONE` | 业务属性 | 额外奖励 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `update_at` | `bigint` | NO | `NONE` | 时间 | 更新时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### game_diamond_record_202604

- 表类型：`BASE TABLE`；字段数：7；数据层：业务表（事实/维度待补证）。
- 业务域：资产 / 货币（`inferred_name_only`）；建议：资产流、奖励成本、余额变化与账本对账；必须区分真金、金币和奖励资产。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `bigint unsigned` | NO | `MUL` | 业务属性 | uid | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `game_id` | `int` | NO | `NONE` | 标识 / 关联 | 游戏id | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `bet_amount` | `bigint` | NO | `NONE` | 金额 / 资产 | 下注金额 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `win_amount` | `bigint` | NO | `NONE` | 金额 / 资产 | 赢金额 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `extra_reward` | `bigint` | NO | `NONE` | 业务属性 | 额外奖励 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `update_at` | `bigint` | NO | `NONE` | 时间 | 更新时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### game_diamond_record_202605

- 表类型：`BASE TABLE`；字段数：7；数据层：业务表（事实/维度待补证）。
- 业务域：资产 / 货币（`inferred_name_only`）；建议：资产流、奖励成本、余额变化与账本对账；必须区分真金、金币和奖励资产。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `bigint unsigned` | NO | `MUL` | 业务属性 | uid | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `game_id` | `int` | NO | `NONE` | 标识 / 关联 | 游戏id | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `bet_amount` | `bigint` | NO | `NONE` | 金额 / 资产 | 下注金额 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `win_amount` | `bigint` | NO | `NONE` | 金额 / 资产 | 赢金额 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `extra_reward` | `bigint` | NO | `NONE` | 业务属性 | 额外奖励 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `update_at` | `bigint` | NO | `NONE` | 时间 | 更新时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### game_diamond_record_202606

- 表类型：`BASE TABLE`；字段数：7；数据层：业务表（事实/维度待补证）。
- 业务域：资产 / 货币（`inferred_name_only`）；建议：资产流、奖励成本、余额变化与账本对账；必须区分真金、金币和奖励资产。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `bigint unsigned` | NO | `MUL` | 业务属性 | uid | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `game_id` | `int` | NO | `NONE` | 标识 / 关联 | 游戏id | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `bet_amount` | `bigint` | NO | `NONE` | 金额 / 资产 | 下注金额 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `win_amount` | `bigint` | NO | `NONE` | 金额 / 资产 | 赢金额 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `extra_reward` | `bigint` | NO | `NONE` | 业务属性 | 额外奖励 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `update_at` | `bigint` | NO | `NONE` | 时间 | 更新时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### game_diamond_record_202607

- 表类型：`BASE TABLE`；字段数：7；数据层：业务表（事实/维度待补证）。
- 业务域：资产 / 货币（`inferred_name_only`）；建议：资产流、奖励成本、余额变化与账本对账；必须区分真金、金币和奖励资产。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `bigint unsigned` | NO | `MUL` | 业务属性 | uid | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `game_id` | `int` | NO | `NONE` | 标识 / 关联 | 游戏id | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `bet_amount` | `bigint` | NO | `NONE` | 金额 / 资产 | 下注金额 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `win_amount` | `bigint` | NO | `NONE` | 金额 / 资产 | 赢金额 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `extra_reward` | `bigint` | NO | `NONE` | 业务属性 | 额外奖励 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `update_at` | `bigint` | NO | `NONE` | 时间 | 更新时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### game_diamond_record_202608

- 表类型：`BASE TABLE`；字段数：7；数据层：业务表（事实/维度待补证）。
- 业务域：资产 / 货币（`inferred_name_only`）；建议：资产流、奖励成本、余额变化与账本对账；必须区分真金、金币和奖励资产。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `bigint unsigned` | NO | `MUL` | 业务属性 | uid | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `game_id` | `int` | NO | `NONE` | 标识 / 关联 | 游戏id | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `bet_amount` | `bigint` | NO | `NONE` | 金额 / 资产 | 下注金额 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `win_amount` | `bigint` | NO | `NONE` | 金额 / 资产 | 赢金额 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `extra_reward` | `bigint` | NO | `NONE` | 业务属性 | 额外奖励 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `update_at` | `bigint` | NO | `NONE` | 时间 | 更新时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### game_record

- 表类型：`BASE TABLE`；字段数：7；数据层：业务表（事实/维度待补证）。
- 业务域：游戏 / 对局 / RTP（`inferred_name_only`）；建议：游戏局、下注、结算、RTP 和玩法/房间拆分；需与 GAMEEND 链路核验。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `bet` | `int unsigned` | NO | `NONE` | 游戏 / 玩法 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `reward` | `int unsigned` | NO | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `user_id` | `bigint unsigned` | NO | `MUL` | 标识 / 关联 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `time` | `bigint unsigned` | NO | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `game` | `varchar(64)` | NO | `NONE` | 游戏 / 玩法 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `remark` | `varchar(64)` | NO | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |

### invite_bind_bank_record

- 表类型：`BASE TABLE`；字段数：4；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint` | NO | `PRI` | 标识 / 关联 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `bank_info` | `varchar(128)` | NO | `UNI` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `uid` | `bigint` | NO | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `tree_id` | `varchar(100)` | NO | `NONE` | 标识 / 关联 | — | 允许在授权范围内做聚合分析；不输出字段值 |

### invite_rebate_detail

- 表类型：`BASE TABLE`；字段数：9；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint` | NO | `PRI` | 标识 / 关联 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `binder` | `bigint` | NO | `MUL` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `inviter` | `bigint` | NO | `MUL` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `amount` | `bigint` | NO | `NONE` | 金额 / 资产 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `recharge_amount` | `bigint` | NO | `NONE` | 金额 / 资产 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `lv` | `int` | NO | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `tree_id` | `varchar(100)` | NO | `NONE` | 标识 / 关联 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `asset_id` | `int` | NO | `NONE` | 标识 / 关联 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `ts` | `bigint` | NO | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |

### invite_reward

- 表类型：`BASE TABLE`；字段数：14；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `inviter` | `int unsigned` | NO | `MUL` | 业务属性 | 邀请者ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `invitee` | `int unsigned` | NO | `MUL` | 业务属性 | 被邀请者ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `status` | `int unsigned` | NO | `NONE` | 时间 | 奖励状态 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `asset_type` | `int unsigned` | NO | `NONE` | 状态 / 枚举 | 资产类型：1001表示cash，1002表示chip，1003表示coin | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `type` | `int unsigned` | NO | `NONE` | 状态 / 枚举 | 类型：1绑定奖励，2充值奖励，3游戏奖励 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `expire` | `bigint unsigned` | NO | `NONE` | 业务属性 | 过期时间，单位：秒 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `reward` | `bigint unsigned` | NO | `NONE` | 业务属性 | 奖励金额 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `data0` | `bigint unsigned` | NO | `NONE` | 时间 | 根据type定义：type=2充值金额 type=3游戏轮数 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `data1` | `bigint unsigned` | NO | `NONE` | 时间 | 根据type定义：type=2奖励系数 type=3本轮游戏次数 | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `data2` | `bigint unsigned` | NO | `NONE` | 时间 | 预留字段 | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `data3` | `bigint unsigned` | NO | `NONE` | 时间 | 预留字段 | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `time` | `int unsigned` | NO | `NONE` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |
| 14 | `collect_time` | `int unsigned` | NO | `NONE` | 时间 | 领取时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |

### invite_stat_tree_info

- 表类型：`BASE TABLE`；字段数：3；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint` | NO | `PRI` | 标识 / 关联 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `tree_id` | `varchar(100)` | NO | `UNI` | 标识 / 关联 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `total_nodes` | `int` | NO | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |

### invite_tree_node

- 表类型：`BASE TABLE`；字段数：10；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint` | NO | `PRI` | 标识 / 关联 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `uid` | `bigint` | NO | `UNI` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `tree_id` | `varchar(100)` | NO | `MUL` | 标识 / 关联 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `lv` | `int` | NO | `MUL` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `parent_id` | `bigint` | NO | `MUL` | 标识 / 关联 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `device_id` | `varchar(128)` | NO | `MUL` | 标识 / 关联 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `is_tourist` | `tinyint(1)` | NO | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `recharge_after_bind` | `bigint` | NO | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `invite_date` | `bigint` | NO | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `forbid_bind` | `tinyint(1)` | NO | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |

### invite_user

- 表类型：`BASE TABLE`；字段数：18；数据层：业务表（事实/维度待补证）。
- 业务域：用户 / 账号（`inferred_name_only`）；建议：注册、登录与生命周期聚合；禁止导出可识别身份字段。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `inviter` | `int unsigned` | NO | `MUL` | 业务属性 | 邀请者ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `invitee` | `int unsigned` | NO | `NONE` | 业务属性 | 被邀请者ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `can_give` | `int unsigned` | NO | `NONE` | 业务属性 | 是否给奖励，1给，2超限 不给，3任务完成 不给 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `total_collected` | `bigint unsigned` | NO | `NONE` | 业务属性 | 已收取的总奖励 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `total_uncollected` | `bigint unsigned` | NO | `NONE` | 业务属性 | 待收取的总奖励 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `total_in_check` | `bigint unsigned` | NO | `NONE` | 业务属性 | 审核中的总奖励 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `bind_collected` | `bigint unsigned` | NO | `NONE` | 业务属性 | 已收取的绑定奖励 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `bind_uncollected` | `bigint unsigned` | NO | `NONE` | 业务属性 | 待收取的绑定奖励 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `bind_in_check` | `bigint unsigned` | NO | `NONE` | 业务属性 | 审核中的绑定奖励 | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `recharge_collected` | `bigint unsigned` | NO | `NONE` | 业务属性 | 已收取的充值奖励 | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `recharge_uncollected` | `bigint unsigned` | NO | `NONE` | 业务属性 | 待收取的充值奖励 | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `recharge_in_check` | `bigint unsigned` | NO | `NONE` | 业务属性 | 审核中的充值奖励 | 允许在授权范围内做聚合分析；不输出字段值 |
| 14 | `play_count_collected` | `bigint unsigned` | NO | `NONE` | 游戏 / 玩法 | 已收取的游戏奖励 | 允许在授权范围内做聚合分析；不输出字段值 |
| 15 | `play_count_uncollected` | `bigint unsigned` | NO | `NONE` | 游戏 / 玩法 | 待收取的游戏奖励 | 允许在授权范围内做聚合分析；不输出字段值 |
| 16 | `play_count_in_check` | `bigint unsigned` | NO | `NONE` | 游戏 / 玩法 | 审核中的游戏奖励 | 允许在授权范围内做聚合分析；不输出字段值 |
| 17 | `time` | `int unsigned` | NO | `NONE` | 时间 | 绑定时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |
| 18 | `update_time` | `int unsigned` | NO | `NONE` | 时间 | 更新时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |

### invite_user_reward_data

- 表类型：`BASE TABLE`；字段数：6；数据层：业务表（事实/维度待补证）。
- 业务域：用户 / 账号（`inferred_name_only`）；建议：注册、登录与生命周期聚合；禁止导出可识别身份字段。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint` | NO | `PRI` | 标识 / 关联 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `uid` | `bigint` | NO | `UNI` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `remain_rewards_cash` | `bigint` | NO | `NONE` | 金额 / 资产 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `remain_rewards_chip` | `bigint` | NO | `NONE` | 金额 / 资产 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `total_rewards` | `bigint` | NO | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `last_claim_at` | `bigint` | NO | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |

### kfc_info

- 表类型：`BASE TABLE`；字段数：7；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `int` | NO | `PRI` | 标识 / 关联 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `bigint` | NO | `UNI` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | [REDACTED:KYC_PERSONAL_IDENTIFIER_OR_BIOMETRIC] | `varchar(31)` | NO | `MUL` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 受限；仅脱敏聚合或伪标识下钻 |
| 4 | [REDACTED:THIRD_PARTY_RAW_RESPONSE_CANDIDATE] | `varchar(255)` | YES | `NONE` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 受限；不得进入普通看板或导出 |
| 5 | [REDACTED:THIRD_PARTY_RAW_RESPONSE_CANDIDATE] | `varchar(255)` | YES | `NONE` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 受限；不得进入普通看板或导出 |
| 6 | `match_percentage` | `int` | YES | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `create_time` | `timestamp` | NO | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |

### kyc_bank_info

- 表类型：`BASE TABLE`；字段数：10；数据层：业务表（事实/维度待补证）。
- 业务域：KYC / 风控（`inferred_name_only`）；建议：KYC 漏斗、失败原因、认证时延；仅使用脱敏聚合。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `int` | NO | `PRI` | 标识 / 关联 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `bigint` | NO | `UNI` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `bank_code` | `varchar(63)` | NO | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | [REDACTED:PAYMENT_ACCOUNT_IDENTIFIER] | `varchar(63)` | NO | `NONE` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 受限；仅脱敏聚合或伪标识下钻 |
| 5 | [REDACTED:KYC_PERSONAL_IDENTIFIER_OR_BIOMETRIC] | `varchar(31)` | NO | `UNI` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 受限；仅脱敏聚合或伪标识下钻 |
| 6 | `verify_result` | `tinyint` | YES | `NONE` | 状态 / 枚举 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | [REDACTED:PAYMENT_ACCOUNT_IDENTIFIER] | `varchar(63)` | YES | `NONE` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 受限；仅脱敏聚合或伪标识下钻 |
| 8 | `match_percentage` | `tinyint` | YES | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | [REDACTED:KYC_PERSONAL_IDENTIFIER_OR_BIOMETRIC] | `varchar(16)` | YES | `NONE` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 受限；仅脱敏聚合或伪标识下钻 |
| 10 | `create_time` | `timestamp` | NO | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |

### kyc_bvn_info

- 表类型：`BASE TABLE`；字段数：9；数据层：业务表（事实/维度待补证）。
- 业务域：KYC / 风控（`inferred_name_only`）；建议：KYC 漏斗、失败原因、认证时延；仅使用脱敏聚合。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `int` | NO | `PRI` | 标识 / 关联 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `bigint` | NO | `UNI` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | [REDACTED:KYC_PERSONAL_IDENTIFIER_OR_BIOMETRIC] | `varchar(31)` | NO | `UNI` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 受限；仅脱敏聚合或伪标识下钻 |
| 4 | `first_name` | `varchar(63)` | NO | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `last_name` | `varchar(63)` | NO | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | [REDACTED:THIRD_PARTY_RAW_RESPONSE_CANDIDATE] | `varchar(511)` | YES | `NONE` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 受限；不得进入普通看板或导出 |
| 7 | `match_percentage` | `int` | YES | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `verify_num` | `varchar(45)` | NO | `NONE` | 业务属性 | 验证次数 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `create_time` | `timestamp` | NO | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |

### kyc_event_log

- 表类型：`BASE TABLE`；字段数：16；数据层：业务表（事实/维度待补证）。
- 业务域：KYC / 风控（`inferred_name_only`）；建议：KYC 漏斗、失败原因、认证时延；仅使用脱敏聚合。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `int` | NO | `PRI` | 标识 / 关联 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `date` | `int unsigned` | NO | `MUL` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `risk_user_num` | `int unsigned` | NO | `NONE` | 业务属性 | 风险用户数 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `risk_user_req_kyc_num` | `int unsigned` | NO | `NONE` | 业务属性 | 风险用户请求kyc次数 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `risk_user_kyc_pass_num` | `int unsigned` | NO | `NONE` | 业务属性 | 风险用户通过kyc次数 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `req_kyc_fail_num` | `int` | NO | `NONE` | 业务属性 | 用户请求kyc失败次数 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `kyc_not_match_num` | `int` | NO | `NONE` | 时间 | 用户名不匹配 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `bank_ex_num` | `int` | NO | `NONE` | 业务属性 | 银行已存在数 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `bank_pass_num` | `int` | NO | `NONE` | 业务属性 | 银行通过数 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `create_time` | `timestamp` | NO | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `ns` | `varchar(45)` | NO | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `kyc_verify_fail_num` | `int` | NO | `NONE` | 业务属性 | 分数不足 | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `bank_fail_num` | `int` | NO | `NONE` | 业务属性 | 请求银行失败 | 允许在授权范围内做聚合分析；不输出字段值 |
| 14 | `bank_verify_fail_num` | `int` | NO | `NONE` | 业务属性 | 银行验证失败 | 允许在授权范围内做聚合分析；不输出字段值 |
| 15 | `kyc_ex_num` | `int` | NO | `NONE` | 业务属性 | kyc已存在 | 允许在授权范围内做聚合分析；不输出字段值 |
| 16 | [REDACTED:KYC_PERSONAL_IDENTIFIER_OR_BIOMETRIC] | `int` | NO | `NONE` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 受限；仅脱敏聚合或伪标识下钻 |

### kyc_face_bvn_event_log

- 表类型：`BASE TABLE`；字段数：19；数据层：业务表（事实/维度待补证）。
- 业务域：KYC / 风控（`inferred_name_only`）；建议：KYC 漏斗、失败原因、认证时延；仅使用脱敏聚合。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `int` | NO | `PRI` | 标识 / 关联 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `date` | `int unsigned` | NO | `MUL` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `package_name` | `varchar(128)` | NO | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `gid` | `bigint` | NO | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | [REDACTED:KYC_PERSONAL_IDENTIFIER_OR_BIOMETRIC] | `int` | NO | `NONE` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 受限；仅脱敏聚合或伪标识下钻 |
| 6 | [REDACTED:KYC_PERSONAL_IDENTIFIER_OR_BIOMETRIC] | `tinyint` | NO | `NONE` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 受限；仅脱敏聚合或伪标识下钻 |
| 7 | [REDACTED:KYC_PERSONAL_IDENTIFIER_OR_BIOMETRIC] | `int` | NO | `NONE` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 受限；仅脱敏聚合或伪标识下钻 |
| 8 | [REDACTED:KYC_PERSONAL_IDENTIFIER_OR_BIOMETRIC] | `tinyint` | NO | `NONE` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 受限；仅脱敏聚合或伪标识下钻 |
| 9 | [REDACTED:KYC_PERSONAL_IDENTIFIER_OR_BIOMETRIC] | `int` | NO | `NONE` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 受限；仅脱敏聚合或伪标识下钻 |
| 10 | [REDACTED:KYC_PERSONAL_IDENTIFIER_OR_BIOMETRIC] | `int` | NO | `NONE` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 受限；仅脱敏聚合或伪标识下钻 |
| 11 | [REDACTED:KYC_PERSONAL_IDENTIFIER_OR_BIOMETRIC] | `int` | NO | `NONE` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 受限；仅脱敏聚合或伪标识下钻 |
| 12 | [REDACTED:KYC_PERSONAL_IDENTIFIER_OR_BIOMETRIC] | `int` | NO | `NONE` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 受限；仅脱敏聚合或伪标识下钻 |
| 13 | [REDACTED:KYC_PERSONAL_IDENTIFIER_OR_BIOMETRIC] | `int` | NO | `NONE` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 受限；仅脱敏聚合或伪标识下钻 |
| 14 | [REDACTED:KYC_PERSONAL_IDENTIFIER_OR_BIOMETRIC] | `int` | NO | `NONE` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 受限；仅脱敏聚合或伪标识下钻 |
| 15 | [REDACTED:KYC_PERSONAL_IDENTIFIER_OR_BIOMETRIC] | `int` | NO | `NONE` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 受限；仅脱敏聚合或伪标识下钻 |
| 16 | [REDACTED:KYC_PERSONAL_IDENTIFIER_OR_BIOMETRIC] | `int` | NO | `NONE` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 受限；仅脱敏聚合或伪标识下钻 |
| 17 | `minors_limit` | `int` | NO | `NONE` | 业务属性 | 未成年限制次数 | 允许在授权范围内做聚合分析；不输出字段值 |
| 18 | `create_time` | `timestamp` | NO | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 19 | `update_time` | `timestamp` | NO | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |

### kyc_face_info

- 表类型：`BASE TABLE`；字段数：15；数据层：业务表（事实/维度待补证）。
- 业务域：KYC / 风控（`inferred_name_only`）；建议：KYC 漏斗、失败原因、认证时延；仅使用脱敏聚合。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `int` | NO | `PRI` | 标识 / 关联 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `bigint` | NO | `UNI` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | [REDACTED:KYC_PERSONAL_IDENTIFIER_OR_BIOMETRIC] | `varchar(31)` | NO | `MUL` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 受限；仅脱敏聚合或伪标识下钻 |
| 4 | [REDACTED:KYC_PERSONAL_IDENTIFIER_OR_BIOMETRIC] | `varchar(20)` | NO | `MUL` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 受限；仅脱敏聚合或伪标识下钻 |
| 5 | `first_name` | `varchar(63)` | YES | `MUL` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `last_name` | `varchar(63)` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `gender` | `varchar(16)` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `birth_date` | `varchar(32)` | YES | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `photo` | `varchar(512)` | NO | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | [REDACTED:THIRD_PARTY_RAW_RESPONSE_CANDIDATE] | `mediumtext` | YES | `NONE` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 受限；不得进入普通看板或导出 |
| 11 | [REDACTED:KYC_PERSONAL_IDENTIFIER_OR_BIOMETRIC] | `int` | NO | `NONE` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 受限；仅脱敏聚合或伪标识下钻 |
| 12 | `result` | `tinyint` | NO | `NONE` | 状态 / 枚举 | 人脸识别结果 1通过 0未通过 | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | [REDACTED:KYC_PERSONAL_IDENTIFIER_OR_BIOMETRIC] | `varchar(128)` | NO | `MUL` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 受限；仅脱敏聚合或伪标识下钻 |
| 14 | `verify_num` | `int` | NO | `NONE` | 业务属性 | 验证次数 | 允许在授权范围内做聚合分析；不输出字段值 |
| 15 | `create_time` | `timestamp` | NO | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |

### kyc_face_phone_event_log

- 表类型：`BASE TABLE`；字段数：20；数据层：业务表（事实/维度待补证）。
- 业务域：KYC / 风控（`inferred_name_only`）；建议：KYC 漏斗、失败原因、认证时延；仅使用脱敏聚合。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `int` | NO | `PRI` | 标识 / 关联 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `date` | `int unsigned` | NO | `MUL` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `package_name` | `varchar(128)` | NO | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `gid` | `bigint` | NO | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | [REDACTED:KYC_PERSONAL_IDENTIFIER_OR_BIOMETRIC] | `int` | NO | `NONE` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 受限；仅脱敏聚合或伪标识下钻 |
| 6 | [REDACTED:KYC_PERSONAL_IDENTIFIER_OR_BIOMETRIC] | `int` | NO | `NONE` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 受限；仅脱敏聚合或伪标识下钻 |
| 7 | [REDACTED:KYC_PERSONAL_IDENTIFIER_OR_BIOMETRIC] | `tinyint` | NO | `NONE` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 受限；仅脱敏聚合或伪标识下钻 |
| 8 | [REDACTED:KYC_PERSONAL_IDENTIFIER_OR_BIOMETRIC] | `int` | NO | `NONE` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 受限；仅脱敏聚合或伪标识下钻 |
| 9 | [REDACTED:KYC_PERSONAL_IDENTIFIER_OR_BIOMETRIC] | `tinyint` | NO | `NONE` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 受限；仅脱敏聚合或伪标识下钻 |
| 10 | [REDACTED:KYC_PERSONAL_IDENTIFIER_OR_BIOMETRIC] | `int` | NO | `NONE` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 受限；仅脱敏聚合或伪标识下钻 |
| 11 | [REDACTED:KYC_PERSONAL_IDENTIFIER_OR_BIOMETRIC] | `int` | NO | `NONE` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 受限；仅脱敏聚合或伪标识下钻 |
| 12 | [REDACTED:KYC_PERSONAL_IDENTIFIER_OR_BIOMETRIC] | `int` | NO | `NONE` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 受限；仅脱敏聚合或伪标识下钻 |
| 13 | [REDACTED:KYC_PERSONAL_IDENTIFIER_OR_BIOMETRIC] | `int` | NO | `NONE` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 受限；仅脱敏聚合或伪标识下钻 |
| 14 | [REDACTED:KYC_PERSONAL_IDENTIFIER_OR_BIOMETRIC] | `int` | NO | `NONE` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 受限；仅脱敏聚合或伪标识下钻 |
| 15 | [REDACTED:KYC_PERSONAL_IDENTIFIER_OR_BIOMETRIC] | `int` | NO | `NONE` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 受限；仅脱敏聚合或伪标识下钻 |
| 16 | [REDACTED:KYC_PERSONAL_IDENTIFIER_OR_BIOMETRIC] | `int` | NO | `NONE` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 受限；仅脱敏聚合或伪标识下钻 |
| 17 | [REDACTED:KYC_PERSONAL_IDENTIFIER_OR_BIOMETRIC] | `int` | NO | `NONE` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 受限；仅脱敏聚合或伪标识下钻 |
| 18 | `minors_limit` | `int` | NO | `NONE` | 业务属性 | 未成年限制次数 | 允许在授权范围内做聚合分析；不输出字段值 |
| 19 | `create_time` | `timestamp` | NO | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 20 | `update_time` | `timestamp` | NO | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |

### kyc_phone_event_log

- 表类型：`BASE TABLE`；字段数：20；数据层：业务表（事实/维度待补证）。
- 业务域：KYC / 风控（`inferred_name_only`）；建议：KYC 漏斗、失败原因、认证时延；仅使用脱敏聚合。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `int` | NO | `PRI` | 标识 / 关联 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `date` | `int unsigned` | NO | `MUL` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `risk_u_num` | `int` | NO | `NONE` | 业务属性 | 风险用户数 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | [REDACTED:KYC_PERSONAL_IDENTIFIER_OR_BIOMETRIC] | `int` | NO | `NONE` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 受限；仅脱敏聚合或伪标识下钻 |
| 5 | [REDACTED:KYC_PERSONAL_IDENTIFIER_OR_BIOMETRIC] | `int` | NO | `NONE` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 受限；仅脱敏聚合或伪标识下钻 |
| 6 | [REDACTED:KYC_PERSONAL_IDENTIFIER_OR_BIOMETRIC] | `int` | NO | `NONE` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 受限；仅脱敏聚合或伪标识下钻 |
| 7 | [REDACTED:KYC_PERSONAL_IDENTIFIER_OR_BIOMETRIC] | `int` | NO | `NONE` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 受限；仅脱敏聚合或伪标识下钻 |
| 8 | [REDACTED:KYC_PERSONAL_IDENTIFIER_OR_BIOMETRIC] | `int` | NO | `NONE` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 受限；仅脱敏聚合或伪标识下钻 |
| 9 | [REDACTED:KYC_PERSONAL_IDENTIFIER_OR_BIOMETRIC] | `int` | NO | `NONE` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 受限；仅脱敏聚合或伪标识下钻 |
| 10 | `create_time` | `timestamp` | NO | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | [REDACTED:KYC_PERSONAL_IDENTIFIER_OR_BIOMETRIC] | `int` | NO | `NONE` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 受限；仅脱敏聚合或伪标识下钻 |
| 12 | `p_b_fail_num` | `int` | NO | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | [REDACTED:KYC_PERSONAL_IDENTIFIER_OR_BIOMETRIC] | `int` | NO | `NONE` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 受限；仅脱敏聚合或伪标识下钻 |
| 14 | [REDACTED:KYC_PERSONAL_IDENTIFIER_OR_BIOMETRIC] | `int` | NO | `NONE` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 受限；仅脱敏聚合或伪标识下钻 |
| 15 | [REDACTED:KYC_PERSONAL_IDENTIFIER_OR_BIOMETRIC] | `int` | NO | `NONE` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 受限；仅脱敏聚合或伪标识下钻 |
| 16 | [REDACTED:KYC_PERSONAL_IDENTIFIER_OR_BIOMETRIC] | `int` | NO | `NONE` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 受限；仅脱敏聚合或伪标识下钻 |
| 17 | `ns` | `varchar(45)` | NO | `NONE` | 业务属性 | config | 允许在授权范围内做聚合分析；不输出字段值 |
| 18 | [REDACTED:KYC_PERSONAL_IDENTIFIER_OR_BIOMETRIC] | `int` | NO | `NONE` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 受限；仅脱敏聚合或伪标识下钻 |
| 19 | [REDACTED:KYC_PERSONAL_IDENTIFIER_OR_BIOMETRIC] | `int` | NO | `NONE` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 受限；仅脱敏聚合或伪标识下钻 |
| 20 | [REDACTED:KYC_PERSONAL_IDENTIFIER_OR_BIOMETRIC] | `int` | NO | `NONE` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 受限；仅脱敏聚合或伪标识下钻 |

### mail_mail

- 表类型：`BASE TABLE`；字段数：10；数据层：业务表（事实/维度待补证）。
- 业务域：运营 / 消息（`inferred_name_only`）；建议：消息触达、发送结果与运营触发分析；不得输出接收人身份字段。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int unsigned` | NO | `MUL` | 业务属性 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `read_status` | `tinyint` | NO | `NONE` | 时间 | 读取状态 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `collect_status` | `tinyint` | NO | `NONE` | 时间 | 领取附件状态 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `title` | `varchar(32)` | NO | `NONE` | 业务属性 | 标题 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `content` | `varchar(512)` | NO | `NONE` | 业务属性 | 内容 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `attach_info` | `varchar(512)` | NO | `NONE` | 时间 | 附件信息 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `del_status` | `tinyint` | NO | `NONE` | 时间 | 删除状态 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `time` | `int` | NO | `NONE` | 时间 | 时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `expire_at` | `bigint` | NO | `MUL` | 时间 | 在什么时间点过期 | 允许在授权范围内做聚合分析；不输出字段值 |

### nima_charge

- 表类型：`BASE TABLE`；字段数：9；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int unsigned` | NO | `MUL` | 业务属性 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `change_count` | `bigint` | NO | `NONE` | 业务属性 | 变更数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_type` | `int unsigned` | NO | `NONE` | 状态 / 枚举 | 变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 结余 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `serial_num` | `varchar(64)` | NO | `UNI` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `remark` | `varchar(64)` | NO | `NONE` | 业务属性 | 备注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `time` | `int unsigned` | NO | `NONE` | 时间 | 交易时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `expiretime` | `int unsigned` | NO | `NONE` | 时间 | 失效时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### nima_charge_backup_1

- 表类型：`BASE TABLE`；字段数：9；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int unsigned` | NO | `MUL` | 业务属性 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `change_count` | `bigint` | NO | `NONE` | 业务属性 | 变更数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_type` | `int unsigned` | NO | `NONE` | 状态 / 枚举 | 变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 结余 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `serial_num` | `varchar(64)` | NO | `UNI` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `remark` | `varchar(64)` | NO | `NONE` | 业务属性 | 备注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `time` | `int unsigned` | NO | `NONE` | 时间 | 交易时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `expiretime` | `int unsigned` | NO | `NONE` | 时间 | 失效时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### nima_charge_history_2023

- 表类型：`BASE TABLE`；字段数：9；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int unsigned` | NO | `MUL` | 业务属性 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `change_count` | `bigint` | NO | `NONE` | 业务属性 | 变更数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_type` | `int unsigned` | NO | `NONE` | 状态 / 枚举 | 变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 结余 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `serial_num` | `varchar(64)` | NO | `UNI` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `remark` | `varchar(64)` | NO | `NONE` | 业务属性 | 备注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `time` | `int unsigned` | NO | `NONE` | 时间 | 交易时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `expiretime` | `int unsigned` | NO | `NONE` | 时间 | 失效时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### order_extra_log

- 表类型：`BASE TABLE`；字段数：5；数据层：业务表（事实/维度待补证）。
- 业务域：支付 / 提现（`inferred_name_only`）；建议：支付/提现漏斗、成功率、时延与失败码；金融金额以服务端事实复核。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint` | NO | `PRI` | 标识 / 关联 | 自增id | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `oid` | `bigint` | NO | `UNI` | 业务属性 | order id | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `reward_amount` | `int` | NO | `NONE` | 金额 / 资产 | 到账金额 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `reward_bonus` | `int` | NO | `NONE` | 业务属性 | 到账bonus | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `reward_coins` | `int` | NO | `NONE` | 金额 / 资产 | 到账coins | 允许在授权范围内做聚合分析；不输出字段值 |

### order_log

- 表类型：`BASE TABLE`；字段数：13；数据层：业务表（事实/维度待补证）。
- 业务域：支付 / 提现（`inferred_name_only`）；建议：支付/提现漏斗、成功率、时延与失败码；金融金额以服务端事实复核。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int unsigned` | NO | `MUL` | 业务属性 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `type` | `tinyint` | NO | `MUL` | 状态 / 枚举 | 状态 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `status` | `tinyint` | NO | `NONE` | 时间 | 状态 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `amount` | `int` | NO | `NONE` | 金额 / 资产 | 提现数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `fee` | `int` | NO | `NONE` | 金额 / 资产 | 手续费 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `pay_amount` | `int` | NO | `NONE` | 金额 / 资产 | 支付数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `pay_way` | `varchar(32)` | NO | `NONE` | 业务属性 | 渠道 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `serial_num` | `varchar(180)` | NO | `UNI` | 业务属性 | 流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `reference` | `varchar(128)` | NO | `MUL` | 业务属性 | 三方平台流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `remark` | `varchar(256)` | NO | `NONE` | 业务属性 | 备注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `time` | `int` | NO | `MUL` | 时间 | 时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `balance` | `bigint` | NO | `NONE` | 金额 / 资产 | 余额 | 允许在授权范围内做聚合分析；不输出字段值 |

### order_withdraw_info

- 表类型：`BASE TABLE`；字段数：9；数据层：业务表（事实/维度待补证）。
- 业务域：支付 / 提现（`inferred_name_only`）；建议：支付/提现漏斗、成功率、时延与失败码；金融金额以服务端事实复核。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `order_id` | `bigint unsigned` | NO | `UNI` | 标识 / 关联 | order id | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `status` | `tinyint` | NO | `MUL` | 时间 | 状态 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `amount` | `int` | NO | `NONE` | 金额 / 资产 | 提现数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `bank` | `varchar(128)` | NO | `NONE` | 业务属性 | 银行 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `account_number` | `varchar(32)` | NO | `NONE` | 业务属性 | 卡号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `remark` | `varchar(128)` | NO | `NONE` | 业务属性 | 备注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `create_time` | `datetime` | NO | `NONE` | 时间 | 创建时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `update_time` | `datetime` | NO | `NONE` | 时间 | 更新时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### order_withdraw_review

- 表类型：`BASE TABLE`；字段数：14；数据层：业务表（事实/维度待补证）。
- 业务域：支付 / 提现（`inferred_name_only`）；建议：支付/提现漏斗、成功率、时延与失败码；金融金额以服务端事实复核。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `order_id` | `bigint unsigned` | NO | `UNI` | 标识 / 关联 | order id | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `user_id` | `int unsigned` | NO | `MUL` | 标识 / 关联 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `status` | `tinyint` | NO | `MUL` | 时间 | 状态 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `amount` | `int` | NO | `NONE` | 金额 / 资产 | 提现数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `bank` | `varchar(128)` | NO | `NONE` | 业务属性 | 银行 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `account_number` | `varchar(32)` | NO | `NONE` | 业务属性 | 卡号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `review_reason` | `tinyint` | YES | `NONE` | 业务属性 | 审核原因 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `reject_reason` | `tinyint` | YES | `NONE` | 业务属性 | 拒绝原因 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `channel` | `varchar(128)` | YES | `NONE` | 业务属性 | 渠道 | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `reviewer` | `varchar(128)` | YES | `NONE` | 业务属性 | 审核人 | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `reject_opt` | `tinyint` | YES | `NONE` | 业务属性 | 拒绝操作,1封号,2扣这笔钱 | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `create_at` | `bigint` | YES | `NONE` | 时间 | 创建时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |
| 14 | `review_at` | `bigint` | YES | `NONE` | 时间 | 审核时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |

### profile_task

- 表类型：`BASE TABLE`；字段数：5；数据层：业务表（事实/维度待补证）。
- 业务域：用户 / 账号（`inferred_name_only`）；建议：注册、登录与生命周期聚合；禁止导出可识别身份字段。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int` | NO | `MUL` | 业务属性 | 用户id | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `task_id` | `int` | NO | `NONE` | 标识 / 关联 | 任务id 999所有任务完成 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `status` | `tinyint unsigned` | NO | `NONE` | 时间 | 状态 是否完成 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `create_at` | `bigint` | YES | `NONE` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |

### recall_log

- 表类型：`BASE TABLE`；字段数：8；数据层：业务表（事实/维度待补证）。
- 业务域：日志 / 数据质量（`inferred_name_only`）；建议：入库延迟、错误、重试和数据质量排障；需明确日志保留周期。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int unsigned` | NO | `MUL` | 业务属性 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `recallcount` | `int` | NO | `NONE` | 业务属性 | 召回次数 累加 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `sendcount` | `int` | NO | `NONE` | 业务属性 | 短信发送次数 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `latest_sendtime` | `int` | NO | `NONE` | 时间 | 最近一次短信发送时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `login_status` | `tinyint` | NO | `NONE` | 时间 | 召回后登录状态 0:未登录 1:已登录 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `login_time` | `int` | NO | `NONE` | 时间 | 召回后首次登录时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `collect_status` | `tinyint` | NO | `NONE` | 时间 | 奖励领取状态 0:未领取 1:已领取 2:已过期 | 允许在授权范围内做聚合分析；不输出字段值 |

### record_log

- 表类型：`BASE TABLE`；字段数：24；数据层：业务表（事实/维度待补证）。
- 业务域：日志 / 数据质量（`inferred_name_only`）；建议：入库延迟、错误、重试和数据质量排障；需明确日志保留周期。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `deskid` | `int` | NO | `NONE` | 业务属性 | 桌子id | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `pluginid` | `int` | NO | `NONE` | 业务属性 | 场次id | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `playtype` | `int` | NO | `NONE` | 状态 / 枚举 | 玩法id | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `user0` | `int` | NO | `MUL` | 业务属性 | 玩家0ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `user1` | `int` | NO | `MUL` | 业务属性 | 玩家1ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `user2` | `int` | NO | `MUL` | 业务属性 | 玩家2ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `user3` | `int` | NO | `MUL` | 业务属性 | 玩家3ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `property0` | `varchar(128)` | NO | `NONE` | 业务属性 | 玩家0属性 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `property1` | `varchar(128)` | NO | `NONE` | 业务属性 | 玩家1属性 | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `property2` | `varchar(128)` | NO | `NONE` | 业务属性 | 玩家2属性 | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `property3` | `varchar(128)` | NO | `NONE` | 业务属性 | 玩家3属性 | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `chips0` | `bigint` | NO | `NONE` | 金额 / 资产 | 玩家0输的chips | 允许在授权范围内做聚合分析；不输出字段值 |
| 14 | `chips1` | `bigint` | NO | `NONE` | 金额 / 资产 | 玩家1输的chips | 允许在授权范围内做聚合分析；不输出字段值 |
| 15 | `chips2` | `bigint` | NO | `NONE` | 金额 / 资产 | 玩家2输的chips | 允许在授权范围内做聚合分析；不输出字段值 |
| 16 | `chips3` | `bigint` | NO | `NONE` | 金额 / 资产 | 玩家3输的chips | 允许在授权范围内做聚合分析；不输出字段值 |
| 17 | `cash0` | `bigint` | NO | `NONE` | 金额 / 资产 | 玩家0赢的cash | 允许在授权范围内做聚合分析；不输出字段值 |
| 18 | `cash1` | `bigint` | NO | `NONE` | 金额 / 资产 | 玩家1赢的cash | 允许在授权范围内做聚合分析；不输出字段值 |
| 19 | `cash2` | `bigint` | NO | `NONE` | 金额 / 资产 | 玩家2赢的cash | 允许在授权范围内做聚合分析；不输出字段值 |
| 20 | `cash3` | `bigint` | NO | `NONE` | 金额 / 资产 | 玩家3赢的cash | 允许在授权范围内做聚合分析；不输出字段值 |
| 21 | `winner` | `int` | NO | `NONE` | 业务属性 | 大赢家id | 允许在授权范围内做聚合分析；不输出字段值 |
| 22 | `entry` | `int` | NO | `NONE` | 业务属性 | 带入 | 允许在授权范围内做聚合分析；不输出字段值 |
| 23 | `starttime` | `int` | NO | `NONE` | 时间 | 开始时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |
| 24 | `time` | `int` | NO | `MUL` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |

### record_video

- 表类型：`BASE TABLE`；字段数：6；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `playtype` | `int` | NO | `NONE` | 状态 / 枚举 | 玩法id | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `log_id` | `bigint` | NO | `MUL` | 标识 / 关联 | 录像logID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `data` | `varchar(4096)` | NO | `NONE` | 时间 | 录像数据 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `time` | `int` | NO | `MUL` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `short_id` | `int` | NO | `MUL` | 标识 / 关联 | 短ID | 允许在授权范围内做聚合分析；不输出字段值 |

### risk_info

- 表类型：`BASE TABLE`；字段数：7；数据层：业务表（事实/维度待补证）。
- 业务域：KYC / 风控（`inferred_name_only`）；建议：KYC 漏斗、失败原因、认证时延；仅使用脱敏聚合。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint` | NO | `PRI` | 标识 / 关联 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `risk_id` | `bigint` | NO | `MUL` | 标识 / 关联 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `gid` | `int` | NO | `MUL` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `unique_id` | `varchar(64)` | NO | `MUL` | 标识 / 关联 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `sub_type` | `int` | NO | `NONE` | 状态 / 枚举 | 1、设备id；2、银行卡；3、ip | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `extra_info` | `varchar(256)` | YES | `NONE` | 业务属性 | 当时额外信息 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `create_time` | `timestamp` | NO | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |

### risk_recharge

- 表类型：`BASE TABLE`；字段数：7；数据层：业务表（事实/维度待补证）。
- 业务域：KYC / 风控（`inferred_name_only`）；建议：KYC 漏斗、失败原因、认证时延；仅使用脱敏聚合。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `bigint` | NO | `MUL` | 业务属性 | 用户gid | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `firstRechargeIp` | `varchar(32)` | NO | `MUL` | 业务属性 | 首充ip | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `firstRechargeAmount` | `int` | NO | `NONE` | 金额 / 资产 | 首充金额单位分 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `firstRechargeTime` | `bigint unsigned` | NO | `MUL` | 时间 | 首充时候时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `beforeRechargeAssets` | `int` | NO | `NONE` | 业务属性 | 首充代币量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `ns` | `varchar(100)` | NO | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |

### risk_rule

- 表类型：`BASE TABLE`；字段数：4；数据层：业务表（事实/维度待补证）。
- 业务域：KYC / 风控（`inferred_name_only`）；建议：KYC 漏斗、失败原因、认证时延；仅使用脱敏聚合。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint` | NO | `PRI` | 标识 / 关联 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `unique_id` | `varchar(64)` | NO | `MUL` | 标识 / 关联 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `flag` | `int` | NO | `NONE` | 状态 / 枚举 | 1、ip黑名单； | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `create_time` | `timestamp` | NO | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |

### sms_log

- 表类型：`BASE TABLE`；字段数：6；数据层：业务表（事实/维度待补证）。
- 业务域：运营 / 消息（`inferred_name_only`）；建议：消息触达、发送结果与运营触发分析；不得输出接收人身份字段。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `tel` | `varchar(16)` | YES | `MUL` | 业务属性 | 电话号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `code` | `varchar(256)` | YES | `NONE` | 业务属性 | 验证码 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `channel` | `varchar(16)` | YES | `NONE` | 业务属性 | 渠道 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `status` | `tinyint` | YES | `NONE` | 时间 | 是否成功 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `time` | `int unsigned` | YES | `NONE` | 时间 | 时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### sms_otp_stat

- 表类型：`BASE TABLE`；字段数：6；数据层：业务表（事实/维度待补证）。
- 业务域：运营 / 消息（`inferred_name_only`）；建议：消息触达、发送结果与运营触发分析；不得输出接收人身份字段。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `tel` | `varchar(16)` | YES | `UNI` | 业务属性 | 账号(电话号) | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `register` | `tinyint` | YES | `NONE` | 业务属性 | 是否注册 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `time` | `int unsigned` | YES | `NONE` | 时间 | 第一次请求时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `success_count` | `int unsigned` | YES | `NONE` | 业务属性 | 成功次数 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `fail_count` | `int unsigned` | YES | `NONE` | 业务属性 | 失败次数 | 允许在授权范围内做聚合分析；不输出字段值 |

### sports_bet_info

- 表类型：`BASE TABLE`；字段数：9；数据层：业务表（事实/维度待补证）。
- 业务域：游戏 / 对局 / RTP（`inferred_name_only`）；建议：游戏局、下注、结算、RTP 和玩法/房间拆分；需与 GAMEEND 链路核验。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint` | NO | `PRI` | 标识 / 关联 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `uid` | `bigint` | NO | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | [REDACTED:THIRD_PARTY_RAW_RESPONSE_CANDIDATE] | `text` | NO | `NONE` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 受限；不得进入普通看板或导出 |
| 4 | `asset` | `text` | NO | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `create_time` | `bigint` | NO | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `update_time` | `bigint` | NO | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `status` | `int` | NO | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `commit_log` | `varchar(63)` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `cash_out` | `int` | YES | `NONE` | 金额 / 资产 | — | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_action_rate

- 表类型：`BASE TABLE`；字段数：7；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `day` | `int` | NO | `MUL` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `act_base` | `int` | NO | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `act` | `int` | NO | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `nday` | `int` | NO | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `count_base` | `int` | NO | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `count_now` | `int` | NO | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_cash_black_report

- 表类型：`BASE TABLE`；字段数：23；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint` | NO | `PRI` | 标识 / 关联 | 主键 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `day` | `int` | NO | `UNI` | 业务属性 | day | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `robot_50` | `int` | NO | `NONE` | 业务属性 | 50场机器人参与把数 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `robot_win_50` | `int` | NO | `NONE` | 业务属性 | 50场机器人获胜把数 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `robot_score_50` | `bigint` | NO | `NONE` | 业务属性 | 50机器人输赢 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `robot_100` | `int` | NO | `NONE` | 业务属性 | 100场机器人参与把数 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `robot_win_100` | `int` | NO | `NONE` | 业务属性 | 100场机器人获胜把数 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `robot_score_100` | `bigint` | NO | `NONE` | 业务属性 | 100机器人输赢 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `robot_200` | `int` | NO | `NONE` | 业务属性 | 200场机器人参与把数 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `robot_win_200` | `int` | NO | `NONE` | 业务属性 | 200场机器人获胜把数 | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `robot_score_200` | `bigint` | NO | `NONE` | 业务属性 | 200机器人输赢 | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `robot_500` | `int` | NO | `NONE` | 业务属性 | 500场机器人参与把数 | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `robot_win_500` | `int` | NO | `NONE` | 业务属性 | 500场机器人获胜把数 | 允许在授权范围内做聚合分析；不输出字段值 |
| 14 | `robot_score_500` | `bigint` | NO | `NONE` | 业务属性 | 500机器人输赢 | 允许在授权范围内做聚合分析；不输出字段值 |
| 15 | `robot_1000` | `int` | NO | `NONE` | 业务属性 | 1000场机器人参与把数 | 允许在授权范围内做聚合分析；不输出字段值 |
| 16 | `robot_win_1000` | `int` | NO | `NONE` | 业务属性 | 1000场机器人获胜把数 | 允许在授权范围内做聚合分析；不输出字段值 |
| 17 | `robot_score_1000` | `bigint` | NO | `NONE` | 业务属性 | 1000机器人输赢 | 允许在授权范围内做聚合分析；不输出字段值 |
| 18 | `robot_2500` | `int` | NO | `NONE` | 业务属性 | 2500场机器人参与把数 | 允许在授权范围内做聚合分析；不输出字段值 |
| 19 | `robot_win_2500` | `int` | NO | `NONE` | 业务属性 | 2500场机器人获胜把数 | 允许在授权范围内做聚合分析；不输出字段值 |
| 20 | `robot_score_2500` | `bigint` | NO | `NONE` | 业务属性 | 2500机器人输赢 | 允许在授权范围内做聚合分析；不输出字段值 |
| 21 | `robot_5000` | `int` | NO | `NONE` | 业务属性 | 5000场机器人参与把数 | 允许在授权范围内做聚合分析；不输出字段值 |
| 22 | `robot_win_5000` | `int` | NO | `NONE` | 业务属性 | 5000场机器人获胜把数 | 允许在授权范围内做聚合分析；不输出字段值 |
| 23 | `robot_score_5000` | `bigint` | NO | `NONE` | 业务属性 | 5000机器人输赢 | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_cash_data

- 表类型：`BASE TABLE`；字段数：17；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint` | NO | `PRI` | 标识 / 关联 | 主键 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `day` | `int` | NO | `MUL` | 业务属性 | day | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `play_type` | `int` | NO | `NONE` | 状态 / 枚举 | 玩法 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `entry` | `int` | NO | `NONE` | 业务属性 | 场次带入 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `active` | `int` | NO | `NONE` | 业务属性 | 日活 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `with_robot` | `int` | NO | `NONE` | 业务属性 | 机器人参与的把数 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `with_player` | `int` | NO | `NONE` | 游戏 / 玩法 | 真人参与的把数 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `fee` | `bigint` | NO | `NONE` | 金额 / 资产 | 抽水 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `agent_profit` | `bigint` | NO | `NONE` | 业务属性 | 代理分润 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `game_robot_1` | `int` | NO | `NONE` | 游戏 / 玩法 | 机器人1参与把数 | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `game_robot_2` | `int` | NO | `NONE` | 游戏 / 玩法 | 机器人2参与把数 | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `robot_score_1` | `bigint` | NO | `NONE` | 业务属性 | 机器人1输赢 | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `robot_score_2` | `bigint` | NO | `NONE` | 业务属性 | 机器人2输赢 | 允许在授权范围内做聚合分析；不输出字段值 |
| 14 | `robot_win_1` | `int` | NO | `NONE` | 业务属性 | 机器人1获胜把数 | 允许在授权范围内做聚合分析；不输出字段值 |
| 15 | `robot_win_2` | `int` | NO | `NONE` | 业务属性 | 机器人2获胜把数 | 允许在授权范围内做聚合分析；不输出字段值 |
| 16 | `robot_fee_1` | `bigint` | NO | `NONE` | 金额 / 资产 | 机器人1抽水 | 允许在授权范围内做聚合分析；不输出字段值 |
| 17 | `robot_fee_2` | `bigint` | NO | `NONE` | 金额 / 资产 | 机器人2抽水 | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_game_bet_gain

- 表类型：`BASE TABLE`；字段数：7；数据层：业务表（事实/维度待补证）。
- 业务域：游戏 / 对局 / RTP（`inferred_name_only`）；建议：游戏局、下注、结算、RTP 和玩法/房间拆分；需与 GAMEEND 链路核验。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `bigint` | NO | `MUL` | 业务属性 | uid | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `game_id` | `int` | NO | `NONE` | 标识 / 关联 | 游戏id | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `bet_amount` | `bigint` | NO | `NONE` | 金额 / 资产 | 下注金额 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `gain_amount` | `bigint` | NO | `NONE` | 金额 / 资产 | 赢金额 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `round_count` | `bigint` | NO | `NONE` | 业务属性 | 游戏次数 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `update_at` | `bigint` | NO | `NONE` | 时间 | 更新时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_jackpot_change

- 表类型：`BASE TABLE`；字段数：8；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `playtype` | `int` | NO | `MUL` | 状态 / 枚举 | 游戏类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `configid` | `int` | NO | `MUL` | 业务属性 | 场次Id | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `usertype` | `int` | NO | `MUL` | 状态 / 枚举 | 用户类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `changetype` | `int` | NO | `MUL` | 状态 / 枚举 | 变更类型 1:游戏 2:后台 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `old_jackpot` | `bigint` | NO | `NONE` | 业务属性 | 原始奖池 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `new_jackpot` | `bigint` | NO | `NONE` | 业务属性 | 当前奖池 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `time` | `int unsigned` | NO | `MUL` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_lifecycle_pool_log

- 表类型：`BASE TABLE`；字段数：8；数据层：业务表（事实/维度待补证）。
- 业务域：日志 / 数据质量（`inferred_name_only`）；建议：入库延迟、错误、重试和数据质量排障；需明确日志保留周期。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `game_type` | `int` | NO | `MUL` | 状态 / 枚举 | 游戏类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `lifecycle` | `int` | NO | `MUL` | 业务属性 | 生命周期 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `pool_type` | `int` | NO | `MUL` | 状态 / 枚举 | 奖池类型 1:实际盈利 2:期望盈利 3:实际盈利调整值 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_type` | `int` | NO | `MUL` | 状态 / 枚举 | 变更类型 1:批量修改 2:单独修改 3:每日自动调整 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `old_pool` | `bigint` | NO | `NONE` | 业务属性 | 原始奖池 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `new_pool` | `bigint` | NO | `NONE` | 业务属性 | 当前奖池 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `time` | `int unsigned` | NO | `MUL` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_lifecycle_pool_log_v2

- 表类型：`BASE TABLE`；字段数：14；数据层：业务表（事实/维度待补证）。
- 业务域：日志 / 数据质量（`inferred_name_only`）；建议：入库延迟、错误、重试和数据质量排障；需明确日志保留周期。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `game_type` | `int` | NO | `MUL` | 状态 / 枚举 | 游戏类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `lifecycle` | `int` | NO | `MUL` | 业务属性 | 生命周期 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `data_type` | `int` | NO | `NONE` | 时间 | 数据类型 1:修改之前数据 2:修改之后数据等 参看枚举 LifecyclePoolDataType | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `pool_type` | `int` | NO | `MUL` | 状态 / 枚举 | 奖池类型 1:实际盈利 2:期望盈利 3:实际盈利调整值等，参看枚举 LifecyclePoolTypeXXX | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `change_type` | `int` | NO | `MUL` | 状态 / 枚举 | 变更类型 1:批量修改 2:单独修改 3:每日自动调整等，参看枚举 LifecyclePoolChangeTypeXXX | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `data` | `bigint` | NO | `NONE` | 时间 | 数据 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `data0` | `bigint` | NO | `NONE` | 时间 | 预留值 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `data1` | `bigint` | NO | `NONE` | 时间 | 预留值 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `data2` | `bigint` | NO | `NONE` | 时间 | 预留值 | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `data3` | `bigint` | NO | `NONE` | 时间 | 预留值 | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `data4` | `bigint` | NO | `NONE` | 时间 | 预留值 | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `time` | `int unsigned` | NO | `MUL` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |
| 14 | `remark` | `varchar(256)` | NO | `NONE` | 业务属性 | 备注 | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_lifecycle_pool_v2_log

- 表类型：`BASE TABLE`；字段数：14；数据层：业务表（事实/维度待补证）。
- 业务域：日志 / 数据质量（`inferred_name_only`）；建议：入库延迟、错误、重试和数据质量排障；需明确日志保留周期。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `game_type` | `int` | NO | `MUL` | 状态 / 枚举 | 游戏类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `lifecycle` | `int` | NO | `MUL` | 业务属性 | 生命周期 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `data_type` | `int` | NO | `NONE` | 时间 | 数据类型 1:修改之前数据 2:修改之后数据等 参看枚举 LifecyclePoolDataType | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `pool_type` | `int` | NO | `MUL` | 状态 / 枚举 | 奖池类型 1:实际盈利 2:期望盈利 3:实际盈利调整值等，参看枚举 LifecyclePoolTypeXXX | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `change_type` | `int` | NO | `MUL` | 状态 / 枚举 | 变更类型 1:批量修改 2:单独修改 3:每日自动调整等，参看枚举 LifecyclePoolChangeTypeXXX | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `data` | `bigint` | NO | `NONE` | 时间 | 数据 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `data0` | `bigint` | NO | `NONE` | 时间 | 预留值 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `data1` | `bigint` | NO | `NONE` | 时间 | 预留值 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `data2` | `bigint` | NO | `NONE` | 时间 | 预留值 | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `data3` | `bigint` | NO | `NONE` | 时间 | 预留值 | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `data4` | `bigint` | NO | `NONE` | 时间 | 预留值 | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `time` | `int unsigned` | NO | `MUL` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |
| 14 | `remark` | `varchar(256)` | NO | `NONE` | 业务属性 | 备注 | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_lifecyclev2_fix_detail

- 表类型：`BASE TABLE`；字段数：5；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `bigint unsigned` | NO | `UNI` | 业务属性 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `fix` | `int` | NO | `NONE` | 业务属性 | 修正值 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `year_day` | `int` | YES | `MUL` | 业务属性 | 日期格式为：20230616 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `create_at` | `bigint` | YES | `MUL` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_lifecyclev2_rtp_record

- 表类型：`BASE TABLE`；字段数：9；数据层：业务表（事实/维度待补证）。
- 业务域：游戏 / 对局 / RTP（`inferred_name_only`）；建议：游戏局、下注、结算、RTP 和玩法/房间拆分；需与 GAMEEND 链路核验。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `cycle` | `int` | YES | `MUL` | 业务属性 | 生命周期 | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `game_id` | `int` | YES | `MUL` | 标识 / 关联 | 游戏id | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `real_profit` | `bigint` | YES | `NONE` | 业务属性 | 真实收益 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `real_profit_reserved` | `bigint` | YES | `NONE` | 业务属性 | 真实收益保留值 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `bet` | `bigint` | YES | `NONE` | 游戏 / 玩法 | 投注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `entire_real_rtp` | `int` | YES | `NONE` | 游戏 / 玩法 | 全量真实回报比 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `year_day` | `int` | YES | `MUL` | 业务属性 | 日期格式为：20230616 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `create_at` | `bigint` | YES | `NONE` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_lifecyclev2_withdraw_detail

- 表类型：`BASE TABLE`；字段数：7；数据层：业务表（事实/维度待补证）。
- 业务域：支付 / 提现（`inferred_name_only`）；建议：支付/提现漏斗、成功率、时延与失败码；金融金额以服务端事实复核。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `bigint unsigned` | NO | `MUL` | 业务属性 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `cycle` | `bigint` | NO | `NONE` | 业务属性 | 生命周期id | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `amount` | `bigint` | NO | `NONE` | 金额 / 资产 | 提现金额 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `new` | `int` | YES | `NONE` | 业务属性 | 生命周期新增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `year_day` | `int` | YES | `MUL` | 业务属性 | 日期格式为：20230616 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `create_at` | `bigint` | YES | `NONE` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_seven_day_reward_detail

- 表类型：`BASE TABLE`；字段数：9；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int` | NO | `MUL` | 业务属性 | 用户id | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `task_id` | `varchar(100)` | NO | `NONE` | 标识 / 关联 | 任务id | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `task_type` | `int` | YES | `NONE` | 状态 / 枚举 | 任务类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `cur_day_index` | `int` | YES | `NONE` | 业务属性 | 领取是第几天 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `task_day_index` | `int` | YES | `NONE` | 业务属性 | 任务是第几天 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `task_desc` | `varchar(100)` | YES | `NONE` | 业务属性 | 描述 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `rewards` | `text` | YES | `NONE` | 业务属性 | 奖励 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `create_at` | `bigint` | YES | `NONE` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_user_action

- 表类型：`BASE TABLE`；字段数：6；数据层：业务表（事实/维度待补证）。
- 业务域：用户 / 账号（`inferred_name_only`）；建议：注册、登录与生命周期聚合；禁止导出可识别身份字段。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `user_id` | `int` | NO | `MUL` | 标识 / 关联 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `act` | `int` | NO | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `count` | `int` | NO | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `amount` | `bigint` | NO | `NONE` | 金额 / 资产 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `time` | `bigint` | NO | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_user_action_sync

- 表类型：`BASE TABLE`；字段数：6；数据层：业务表（事实/维度待补证）。
- 业务域：用户 / 账号（`inferred_name_only`）；建议：注册、登录与生命周期聚合；禁止导出可识别身份字段。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `user_id` | `int` | NO | `MUL` | 标识 / 关联 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `act` | `int` | NO | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `count` | `int` | NO | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `amount` | `bigint` | NO | `NONE` | 金额 / 资产 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `time` | `bigint` | NO | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_user_asset_change_profit_000000

- 表类型：`BASE TABLE`；字段数：16；数据层：业务表（事实/维度待补证）。
- 业务域：资产 / 货币（`inferred_name_only`）；建议：资产流、奖励成本、余额变化与账本对账；必须区分真金、金币和奖励资产。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `user_id` | `bigint` | NO | `MUL` | 标识 / 关联 | 用户id | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `change_type` | `int` | YES | `NONE` | 状态 / 枚举 | 资产变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_asset` | `int` | YES | `NONE` | 业务属性 | 资产变更id | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_amount` | `bigint` | YES | `NONE` | 金额 / 资产 | 资产变更金额 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `life_profit` | `bigint` | YES | `NONE` | 业务属性 | 终身盈利 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `total_recharge` | `bigint` | YES | `NONE` | 业务属性 | 总充值 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `total_withdraw` | `bigint` | YES | `NONE` | 业务属性 | 总提现 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `total_asset` | `bigint` | YES | `NONE` | 业务属性 | 总资产 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `profit_rate` | `int` | YES | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `win_flow` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `lose_flow` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `free_reward` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 14 | `lose_rate` | `int` | YES | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 15 | `year_day` | `int` | YES | `NONE` | 业务属性 | 日期格式为：20230616 | 允许在授权范围内做聚合分析；不输出字段值 |
| 16 | `create_at` | `bigint` | YES | `NONE` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_user_asset_change_profit_202407

- 表类型：`BASE TABLE`；字段数：16；数据层：业务表（事实/维度待补证）。
- 业务域：资产 / 货币（`inferred_name_only`）；建议：资产流、奖励成本、余额变化与账本对账；必须区分真金、金币和奖励资产。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `user_id` | `bigint` | NO | `MUL` | 标识 / 关联 | 用户id | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `change_type` | `int` | YES | `NONE` | 状态 / 枚举 | 资产变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_asset` | `int` | YES | `NONE` | 业务属性 | 资产变更id | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_amount` | `bigint` | YES | `NONE` | 金额 / 资产 | 资产变更金额 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `life_profit` | `bigint` | YES | `NONE` | 业务属性 | 终身盈利 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `total_recharge` | `bigint` | YES | `NONE` | 业务属性 | 总充值 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `total_withdraw` | `bigint` | YES | `NONE` | 业务属性 | 总提现 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `total_asset` | `bigint` | YES | `NONE` | 业务属性 | 总资产 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `profit_rate` | `int` | YES | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `win_flow` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `lose_flow` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `free_reward` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 14 | `lose_rate` | `int` | YES | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 15 | `year_day` | `int` | YES | `NONE` | 业务属性 | 日期格式为：20230616 | 允许在授权范围内做聚合分析；不输出字段值 |
| 16 | `create_at` | `bigint` | YES | `NONE` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_user_asset_change_profit_202408

- 表类型：`BASE TABLE`；字段数：16；数据层：业务表（事实/维度待补证）。
- 业务域：资产 / 货币（`inferred_name_only`）；建议：资产流、奖励成本、余额变化与账本对账；必须区分真金、金币和奖励资产。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `user_id` | `bigint` | NO | `MUL` | 标识 / 关联 | 用户id | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `change_type` | `int` | YES | `NONE` | 状态 / 枚举 | 资产变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_asset` | `int` | YES | `NONE` | 业务属性 | 资产变更id | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_amount` | `bigint` | YES | `NONE` | 金额 / 资产 | 资产变更金额 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `life_profit` | `bigint` | YES | `NONE` | 业务属性 | 终身盈利 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `total_recharge` | `bigint` | YES | `NONE` | 业务属性 | 总充值 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `total_withdraw` | `bigint` | YES | `NONE` | 业务属性 | 总提现 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `total_asset` | `bigint` | YES | `NONE` | 业务属性 | 总资产 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `profit_rate` | `int` | YES | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `win_flow` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `lose_flow` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `free_reward` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 14 | `lose_rate` | `int` | YES | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 15 | `year_day` | `int` | YES | `NONE` | 业务属性 | 日期格式为：20230616 | 允许在授权范围内做聚合分析；不输出字段值 |
| 16 | `create_at` | `bigint` | YES | `NONE` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_user_asset_change_profit_202409

- 表类型：`BASE TABLE`；字段数：16；数据层：业务表（事实/维度待补证）。
- 业务域：资产 / 货币（`inferred_name_only`）；建议：资产流、奖励成本、余额变化与账本对账；必须区分真金、金币和奖励资产。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `user_id` | `bigint` | NO | `MUL` | 标识 / 关联 | 用户id | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `change_type` | `int` | YES | `NONE` | 状态 / 枚举 | 资产变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_asset` | `int` | YES | `NONE` | 业务属性 | 资产变更id | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_amount` | `bigint` | YES | `NONE` | 金额 / 资产 | 资产变更金额 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `life_profit` | `bigint` | YES | `NONE` | 业务属性 | 终身盈利 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `total_recharge` | `bigint` | YES | `NONE` | 业务属性 | 总充值 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `total_withdraw` | `bigint` | YES | `NONE` | 业务属性 | 总提现 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `total_asset` | `bigint` | YES | `NONE` | 业务属性 | 总资产 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `profit_rate` | `int` | YES | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `win_flow` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `lose_flow` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `free_reward` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 14 | `lose_rate` | `int` | YES | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 15 | `year_day` | `int` | YES | `NONE` | 业务属性 | 日期格式为：20230616 | 允许在授权范围内做聚合分析；不输出字段值 |
| 16 | `create_at` | `bigint` | YES | `NONE` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_user_asset_change_profit_202410

- 表类型：`BASE TABLE`；字段数：16；数据层：业务表（事实/维度待补证）。
- 业务域：资产 / 货币（`inferred_name_only`）；建议：资产流、奖励成本、余额变化与账本对账；必须区分真金、金币和奖励资产。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `user_id` | `bigint` | NO | `MUL` | 标识 / 关联 | 用户id | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `change_type` | `int` | YES | `NONE` | 状态 / 枚举 | 资产变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_asset` | `int` | YES | `NONE` | 业务属性 | 资产变更id | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_amount` | `bigint` | YES | `NONE` | 金额 / 资产 | 资产变更金额 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `life_profit` | `bigint` | YES | `NONE` | 业务属性 | 终身盈利 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `total_recharge` | `bigint` | YES | `NONE` | 业务属性 | 总充值 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `total_withdraw` | `bigint` | YES | `NONE` | 业务属性 | 总提现 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `total_asset` | `bigint` | YES | `NONE` | 业务属性 | 总资产 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `profit_rate` | `int` | YES | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `win_flow` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `lose_flow` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `free_reward` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 14 | `lose_rate` | `int` | YES | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 15 | `year_day` | `int` | YES | `NONE` | 业务属性 | 日期格式为：20230616 | 允许在授权范围内做聚合分析；不输出字段值 |
| 16 | `create_at` | `bigint` | YES | `NONE` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_user_asset_change_profit_202411

- 表类型：`BASE TABLE`；字段数：16；数据层：业务表（事实/维度待补证）。
- 业务域：资产 / 货币（`inferred_name_only`）；建议：资产流、奖励成本、余额变化与账本对账；必须区分真金、金币和奖励资产。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `user_id` | `bigint` | NO | `MUL` | 标识 / 关联 | 用户id | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `change_type` | `int` | YES | `NONE` | 状态 / 枚举 | 资产变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_asset` | `int` | YES | `NONE` | 业务属性 | 资产变更id | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_amount` | `bigint` | YES | `NONE` | 金额 / 资产 | 资产变更金额 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `life_profit` | `bigint` | YES | `NONE` | 业务属性 | 终身盈利 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `total_recharge` | `bigint` | YES | `NONE` | 业务属性 | 总充值 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `total_withdraw` | `bigint` | YES | `NONE` | 业务属性 | 总提现 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `total_asset` | `bigint` | YES | `NONE` | 业务属性 | 总资产 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `profit_rate` | `int` | YES | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `win_flow` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `lose_flow` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `free_reward` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 14 | `lose_rate` | `int` | YES | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 15 | `year_day` | `int` | YES | `NONE` | 业务属性 | 日期格式为：20230616 | 允许在授权范围内做聚合分析；不输出字段值 |
| 16 | `create_at` | `bigint` | YES | `NONE` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_user_asset_change_profit_202412

- 表类型：`BASE TABLE`；字段数：16；数据层：业务表（事实/维度待补证）。
- 业务域：资产 / 货币（`inferred_name_only`）；建议：资产流、奖励成本、余额变化与账本对账；必须区分真金、金币和奖励资产。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `user_id` | `bigint` | NO | `MUL` | 标识 / 关联 | 用户id | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `change_type` | `int` | YES | `NONE` | 状态 / 枚举 | 资产变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_asset` | `int` | YES | `NONE` | 业务属性 | 资产变更id | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_amount` | `bigint` | YES | `NONE` | 金额 / 资产 | 资产变更金额 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `life_profit` | `bigint` | YES | `NONE` | 业务属性 | 终身盈利 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `total_recharge` | `bigint` | YES | `NONE` | 业务属性 | 总充值 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `total_withdraw` | `bigint` | YES | `NONE` | 业务属性 | 总提现 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `total_asset` | `bigint` | YES | `NONE` | 业务属性 | 总资产 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `profit_rate` | `int` | YES | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `win_flow` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `lose_flow` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `free_reward` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 14 | `lose_rate` | `int` | YES | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 15 | `year_day` | `int` | YES | `NONE` | 业务属性 | 日期格式为：20230616 | 允许在授权范围内做聚合分析；不输出字段值 |
| 16 | `create_at` | `bigint` | YES | `NONE` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_user_asset_change_profit_202501

- 表类型：`BASE TABLE`；字段数：16；数据层：业务表（事实/维度待补证）。
- 业务域：资产 / 货币（`inferred_name_only`）；建议：资产流、奖励成本、余额变化与账本对账；必须区分真金、金币和奖励资产。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `user_id` | `bigint` | NO | `MUL` | 标识 / 关联 | 用户id | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `change_type` | `int` | YES | `NONE` | 状态 / 枚举 | 资产变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_asset` | `int` | YES | `NONE` | 业务属性 | 资产变更id | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_amount` | `bigint` | YES | `NONE` | 金额 / 资产 | 资产变更金额 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `life_profit` | `bigint` | YES | `NONE` | 业务属性 | 终身盈利 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `total_recharge` | `bigint` | YES | `NONE` | 业务属性 | 总充值 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `total_withdraw` | `bigint` | YES | `NONE` | 业务属性 | 总提现 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `total_asset` | `bigint` | YES | `NONE` | 业务属性 | 总资产 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `profit_rate` | `int` | YES | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `win_flow` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `lose_flow` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `free_reward` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 14 | `lose_rate` | `int` | YES | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 15 | `year_day` | `int` | YES | `NONE` | 业务属性 | 日期格式为：20230616 | 允许在授权范围内做聚合分析；不输出字段值 |
| 16 | `create_at` | `bigint` | YES | `NONE` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_user_asset_change_profit_202502

- 表类型：`BASE TABLE`；字段数：16；数据层：业务表（事实/维度待补证）。
- 业务域：资产 / 货币（`inferred_name_only`）；建议：资产流、奖励成本、余额变化与账本对账；必须区分真金、金币和奖励资产。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `user_id` | `bigint` | NO | `MUL` | 标识 / 关联 | 用户id | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `change_type` | `int` | YES | `NONE` | 状态 / 枚举 | 资产变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_asset` | `int` | YES | `NONE` | 业务属性 | 资产变更id | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_amount` | `bigint` | YES | `NONE` | 金额 / 资产 | 资产变更金额 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `life_profit` | `bigint` | YES | `NONE` | 业务属性 | 终身盈利 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `total_recharge` | `bigint` | YES | `NONE` | 业务属性 | 总充值 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `total_withdraw` | `bigint` | YES | `NONE` | 业务属性 | 总提现 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `total_asset` | `bigint` | YES | `NONE` | 业务属性 | 总资产 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `profit_rate` | `int` | YES | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `win_flow` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `lose_flow` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `free_reward` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 14 | `lose_rate` | `int` | YES | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 15 | `year_day` | `int` | YES | `NONE` | 业务属性 | 日期格式为：20230616 | 允许在授权范围内做聚合分析；不输出字段值 |
| 16 | `create_at` | `bigint` | YES | `NONE` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_user_asset_change_profit_202503

- 表类型：`BASE TABLE`；字段数：16；数据层：业务表（事实/维度待补证）。
- 业务域：资产 / 货币（`inferred_name_only`）；建议：资产流、奖励成本、余额变化与账本对账；必须区分真金、金币和奖励资产。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `user_id` | `bigint` | NO | `MUL` | 标识 / 关联 | 用户id | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `change_type` | `int` | YES | `NONE` | 状态 / 枚举 | 资产变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_asset` | `int` | YES | `NONE` | 业务属性 | 资产变更id | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_amount` | `bigint` | YES | `NONE` | 金额 / 资产 | 资产变更金额 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `life_profit` | `bigint` | YES | `NONE` | 业务属性 | 终身盈利 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `total_recharge` | `bigint` | YES | `NONE` | 业务属性 | 总充值 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `total_withdraw` | `bigint` | YES | `NONE` | 业务属性 | 总提现 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `total_asset` | `bigint` | YES | `NONE` | 业务属性 | 总资产 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `profit_rate` | `int` | YES | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `win_flow` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `lose_flow` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `free_reward` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 14 | `lose_rate` | `int` | YES | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 15 | `year_day` | `int` | YES | `NONE` | 业务属性 | 日期格式为：20230616 | 允许在授权范围内做聚合分析；不输出字段值 |
| 16 | `create_at` | `bigint` | YES | `NONE` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_user_asset_change_profit_202504

- 表类型：`BASE TABLE`；字段数：16；数据层：业务表（事实/维度待补证）。
- 业务域：资产 / 货币（`inferred_name_only`）；建议：资产流、奖励成本、余额变化与账本对账；必须区分真金、金币和奖励资产。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `user_id` | `bigint` | NO | `MUL` | 标识 / 关联 | 用户id | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `change_type` | `int` | YES | `NONE` | 状态 / 枚举 | 资产变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_asset` | `int` | YES | `NONE` | 业务属性 | 资产变更id | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_amount` | `bigint` | YES | `NONE` | 金额 / 资产 | 资产变更金额 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `life_profit` | `bigint` | YES | `NONE` | 业务属性 | 终身盈利 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `total_recharge` | `bigint` | YES | `NONE` | 业务属性 | 总充值 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `total_withdraw` | `bigint` | YES | `NONE` | 业务属性 | 总提现 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `total_asset` | `bigint` | YES | `NONE` | 业务属性 | 总资产 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `profit_rate` | `int` | YES | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `win_flow` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `lose_flow` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `free_reward` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 14 | `lose_rate` | `int` | YES | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 15 | `year_day` | `int` | YES | `NONE` | 业务属性 | 日期格式为：20230616 | 允许在授权范围内做聚合分析；不输出字段值 |
| 16 | `create_at` | `bigint` | YES | `NONE` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_user_asset_change_profit_202505

- 表类型：`BASE TABLE`；字段数：16；数据层：业务表（事实/维度待补证）。
- 业务域：资产 / 货币（`inferred_name_only`）；建议：资产流、奖励成本、余额变化与账本对账；必须区分真金、金币和奖励资产。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `user_id` | `bigint` | NO | `MUL` | 标识 / 关联 | 用户id | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `change_type` | `int` | YES | `NONE` | 状态 / 枚举 | 资产变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_asset` | `int` | YES | `NONE` | 业务属性 | 资产变更id | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_amount` | `bigint` | YES | `NONE` | 金额 / 资产 | 资产变更金额 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `life_profit` | `bigint` | YES | `NONE` | 业务属性 | 终身盈利 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `total_recharge` | `bigint` | YES | `NONE` | 业务属性 | 总充值 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `total_withdraw` | `bigint` | YES | `NONE` | 业务属性 | 总提现 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `total_asset` | `bigint` | YES | `NONE` | 业务属性 | 总资产 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `profit_rate` | `int` | YES | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `win_flow` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `lose_flow` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `free_reward` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 14 | `lose_rate` | `int` | YES | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 15 | `year_day` | `int` | YES | `NONE` | 业务属性 | 日期格式为：20230616 | 允许在授权范围内做聚合分析；不输出字段值 |
| 16 | `create_at` | `bigint` | YES | `NONE` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_user_asset_change_profit_202506

- 表类型：`BASE TABLE`；字段数：16；数据层：业务表（事实/维度待补证）。
- 业务域：资产 / 货币（`inferred_name_only`）；建议：资产流、奖励成本、余额变化与账本对账；必须区分真金、金币和奖励资产。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `user_id` | `bigint` | NO | `MUL` | 标识 / 关联 | 用户id | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `change_type` | `int` | YES | `NONE` | 状态 / 枚举 | 资产变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_asset` | `int` | YES | `NONE` | 业务属性 | 资产变更id | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_amount` | `bigint` | YES | `NONE` | 金额 / 资产 | 资产变更金额 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `life_profit` | `bigint` | YES | `NONE` | 业务属性 | 终身盈利 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `total_recharge` | `bigint` | YES | `NONE` | 业务属性 | 总充值 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `total_withdraw` | `bigint` | YES | `NONE` | 业务属性 | 总提现 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `total_asset` | `bigint` | YES | `NONE` | 业务属性 | 总资产 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `profit_rate` | `int` | YES | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `win_flow` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `lose_flow` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `free_reward` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 14 | `lose_rate` | `int` | YES | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 15 | `year_day` | `int` | YES | `NONE` | 业务属性 | 日期格式为：20230616 | 允许在授权范围内做聚合分析；不输出字段值 |
| 16 | `create_at` | `bigint` | YES | `NONE` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_user_asset_change_profit_202507

- 表类型：`BASE TABLE`；字段数：16；数据层：业务表（事实/维度待补证）。
- 业务域：资产 / 货币（`inferred_name_only`）；建议：资产流、奖励成本、余额变化与账本对账；必须区分真金、金币和奖励资产。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `user_id` | `bigint` | NO | `MUL` | 标识 / 关联 | 用户id | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `change_type` | `int` | YES | `NONE` | 状态 / 枚举 | 资产变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_asset` | `int` | YES | `NONE` | 业务属性 | 资产变更id | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_amount` | `bigint` | YES | `NONE` | 金额 / 资产 | 资产变更金额 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `life_profit` | `bigint` | YES | `NONE` | 业务属性 | 终身盈利 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `total_recharge` | `bigint` | YES | `NONE` | 业务属性 | 总充值 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `total_withdraw` | `bigint` | YES | `NONE` | 业务属性 | 总提现 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `total_asset` | `bigint` | YES | `NONE` | 业务属性 | 总资产 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `profit_rate` | `int` | YES | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `win_flow` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `lose_flow` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `free_reward` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 14 | `lose_rate` | `int` | YES | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 15 | `year_day` | `int` | YES | `NONE` | 业务属性 | 日期格式为：20230616 | 允许在授权范围内做聚合分析；不输出字段值 |
| 16 | `create_at` | `bigint` | YES | `NONE` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_user_asset_change_profit_202508

- 表类型：`BASE TABLE`；字段数：16；数据层：业务表（事实/维度待补证）。
- 业务域：资产 / 货币（`inferred_name_only`）；建议：资产流、奖励成本、余额变化与账本对账；必须区分真金、金币和奖励资产。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `user_id` | `bigint` | NO | `MUL` | 标识 / 关联 | 用户id | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `change_type` | `int` | YES | `NONE` | 状态 / 枚举 | 资产变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_asset` | `int` | YES | `NONE` | 业务属性 | 资产变更id | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_amount` | `bigint` | YES | `NONE` | 金额 / 资产 | 资产变更金额 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `life_profit` | `bigint` | YES | `NONE` | 业务属性 | 终身盈利 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `total_recharge` | `bigint` | YES | `NONE` | 业务属性 | 总充值 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `total_withdraw` | `bigint` | YES | `NONE` | 业务属性 | 总提现 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `total_asset` | `bigint` | YES | `NONE` | 业务属性 | 总资产 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `profit_rate` | `int` | YES | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `win_flow` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `lose_flow` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `free_reward` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 14 | `lose_rate` | `int` | YES | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 15 | `year_day` | `int` | YES | `NONE` | 业务属性 | 日期格式为：20230616 | 允许在授权范围内做聚合分析；不输出字段值 |
| 16 | `create_at` | `bigint` | YES | `NONE` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_user_asset_change_profit_202509

- 表类型：`BASE TABLE`；字段数：16；数据层：业务表（事实/维度待补证）。
- 业务域：资产 / 货币（`inferred_name_only`）；建议：资产流、奖励成本、余额变化与账本对账；必须区分真金、金币和奖励资产。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `user_id` | `bigint` | NO | `MUL` | 标识 / 关联 | 用户id | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `change_type` | `int` | YES | `NONE` | 状态 / 枚举 | 资产变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_asset` | `int` | YES | `NONE` | 业务属性 | 资产变更id | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_amount` | `bigint` | YES | `NONE` | 金额 / 资产 | 资产变更金额 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `life_profit` | `bigint` | YES | `NONE` | 业务属性 | 终身盈利 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `total_recharge` | `bigint` | YES | `NONE` | 业务属性 | 总充值 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `total_withdraw` | `bigint` | YES | `NONE` | 业务属性 | 总提现 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `total_asset` | `bigint` | YES | `NONE` | 业务属性 | 总资产 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `profit_rate` | `int` | YES | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `win_flow` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `lose_flow` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `free_reward` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 14 | `lose_rate` | `int` | YES | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 15 | `year_day` | `int` | YES | `NONE` | 业务属性 | 日期格式为：20230616 | 允许在授权范围内做聚合分析；不输出字段值 |
| 16 | `create_at` | `bigint` | YES | `NONE` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_user_asset_change_profit_202510

- 表类型：`BASE TABLE`；字段数：16；数据层：业务表（事实/维度待补证）。
- 业务域：资产 / 货币（`inferred_name_only`）；建议：资产流、奖励成本、余额变化与账本对账；必须区分真金、金币和奖励资产。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `user_id` | `bigint` | NO | `MUL` | 标识 / 关联 | 用户id | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `change_type` | `int` | YES | `NONE` | 状态 / 枚举 | 资产变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_asset` | `int` | YES | `NONE` | 业务属性 | 资产变更id | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_amount` | `bigint` | YES | `NONE` | 金额 / 资产 | 资产变更金额 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `life_profit` | `bigint` | YES | `NONE` | 业务属性 | 终身盈利 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `total_recharge` | `bigint` | YES | `NONE` | 业务属性 | 总充值 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `total_withdraw` | `bigint` | YES | `NONE` | 业务属性 | 总提现 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `total_asset` | `bigint` | YES | `NONE` | 业务属性 | 总资产 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `profit_rate` | `int` | YES | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `win_flow` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `lose_flow` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `free_reward` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 14 | `lose_rate` | `int` | YES | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 15 | `year_day` | `int` | YES | `NONE` | 业务属性 | 日期格式为：20230616 | 允许在授权范围内做聚合分析；不输出字段值 |
| 16 | `create_at` | `bigint` | YES | `NONE` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_user_asset_change_profit_202511

- 表类型：`BASE TABLE`；字段数：16；数据层：业务表（事实/维度待补证）。
- 业务域：资产 / 货币（`inferred_name_only`）；建议：资产流、奖励成本、余额变化与账本对账；必须区分真金、金币和奖励资产。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `user_id` | `bigint` | NO | `MUL` | 标识 / 关联 | 用户id | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `change_type` | `int` | YES | `NONE` | 状态 / 枚举 | 资产变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_asset` | `int` | YES | `NONE` | 业务属性 | 资产变更id | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_amount` | `bigint` | YES | `NONE` | 金额 / 资产 | 资产变更金额 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `life_profit` | `bigint` | YES | `NONE` | 业务属性 | 终身盈利 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `total_recharge` | `bigint` | YES | `NONE` | 业务属性 | 总充值 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `total_withdraw` | `bigint` | YES | `NONE` | 业务属性 | 总提现 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `total_asset` | `bigint` | YES | `NONE` | 业务属性 | 总资产 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `profit_rate` | `int` | YES | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `win_flow` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `lose_flow` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `free_reward` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 14 | `lose_rate` | `int` | YES | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 15 | `year_day` | `int` | YES | `NONE` | 业务属性 | 日期格式为：20230616 | 允许在授权范围内做聚合分析；不输出字段值 |
| 16 | `create_at` | `bigint` | YES | `NONE` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_user_asset_change_profit_202512

- 表类型：`BASE TABLE`；字段数：16；数据层：业务表（事实/维度待补证）。
- 业务域：资产 / 货币（`inferred_name_only`）；建议：资产流、奖励成本、余额变化与账本对账；必须区分真金、金币和奖励资产。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `user_id` | `bigint` | NO | `MUL` | 标识 / 关联 | 用户id | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `change_type` | `int` | YES | `NONE` | 状态 / 枚举 | 资产变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_asset` | `int` | YES | `NONE` | 业务属性 | 资产变更id | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_amount` | `bigint` | YES | `NONE` | 金额 / 资产 | 资产变更金额 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `life_profit` | `bigint` | YES | `NONE` | 业务属性 | 终身盈利 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `total_recharge` | `bigint` | YES | `NONE` | 业务属性 | 总充值 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `total_withdraw` | `bigint` | YES | `NONE` | 业务属性 | 总提现 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `total_asset` | `bigint` | YES | `NONE` | 业务属性 | 总资产 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `profit_rate` | `int` | YES | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `win_flow` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `lose_flow` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `free_reward` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 14 | `lose_rate` | `int` | YES | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 15 | `year_day` | `int` | YES | `NONE` | 业务属性 | 日期格式为：20230616 | 允许在授权范围内做聚合分析；不输出字段值 |
| 16 | `create_at` | `bigint` | YES | `NONE` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_user_asset_change_profit_202601

- 表类型：`BASE TABLE`；字段数：16；数据层：业务表（事实/维度待补证）。
- 业务域：资产 / 货币（`inferred_name_only`）；建议：资产流、奖励成本、余额变化与账本对账；必须区分真金、金币和奖励资产。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `user_id` | `bigint` | NO | `MUL` | 标识 / 关联 | 用户id | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `change_type` | `int` | YES | `NONE` | 状态 / 枚举 | 资产变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_asset` | `int` | YES | `NONE` | 业务属性 | 资产变更id | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_amount` | `bigint` | YES | `NONE` | 金额 / 资产 | 资产变更金额 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `life_profit` | `bigint` | YES | `NONE` | 业务属性 | 终身盈利 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `total_recharge` | `bigint` | YES | `NONE` | 业务属性 | 总充值 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `total_withdraw` | `bigint` | YES | `NONE` | 业务属性 | 总提现 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `total_asset` | `bigint` | YES | `NONE` | 业务属性 | 总资产 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `profit_rate` | `int` | YES | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `win_flow` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `lose_flow` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `free_reward` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 14 | `lose_rate` | `int` | YES | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 15 | `year_day` | `int` | YES | `NONE` | 业务属性 | 日期格式为：20230616 | 允许在授权范围内做聚合分析；不输出字段值 |
| 16 | `create_at` | `bigint` | YES | `NONE` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_user_asset_change_profit_202602

- 表类型：`BASE TABLE`；字段数：16；数据层：业务表（事实/维度待补证）。
- 业务域：资产 / 货币（`inferred_name_only`）；建议：资产流、奖励成本、余额变化与账本对账；必须区分真金、金币和奖励资产。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `user_id` | `bigint` | NO | `MUL` | 标识 / 关联 | 用户id | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `change_type` | `int` | YES | `NONE` | 状态 / 枚举 | 资产变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_asset` | `int` | YES | `NONE` | 业务属性 | 资产变更id | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_amount` | `bigint` | YES | `NONE` | 金额 / 资产 | 资产变更金额 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `life_profit` | `bigint` | YES | `NONE` | 业务属性 | 终身盈利 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `total_recharge` | `bigint` | YES | `NONE` | 业务属性 | 总充值 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `total_withdraw` | `bigint` | YES | `NONE` | 业务属性 | 总提现 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `total_asset` | `bigint` | YES | `NONE` | 业务属性 | 总资产 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `profit_rate` | `int` | YES | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `win_flow` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `lose_flow` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `free_reward` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 14 | `lose_rate` | `int` | YES | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 15 | `year_day` | `int` | YES | `NONE` | 业务属性 | 日期格式为：20230616 | 允许在授权范围内做聚合分析；不输出字段值 |
| 16 | `create_at` | `bigint` | YES | `NONE` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_user_asset_change_profit_202603

- 表类型：`BASE TABLE`；字段数：16；数据层：业务表（事实/维度待补证）。
- 业务域：资产 / 货币（`inferred_name_only`）；建议：资产流、奖励成本、余额变化与账本对账；必须区分真金、金币和奖励资产。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `user_id` | `bigint` | NO | `MUL` | 标识 / 关联 | 用户id | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `change_type` | `int` | YES | `NONE` | 状态 / 枚举 | 资产变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_asset` | `int` | YES | `NONE` | 业务属性 | 资产变更id | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_amount` | `bigint` | YES | `NONE` | 金额 / 资产 | 资产变更金额 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `life_profit` | `bigint` | YES | `NONE` | 业务属性 | 终身盈利 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `total_recharge` | `bigint` | YES | `NONE` | 业务属性 | 总充值 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `total_withdraw` | `bigint` | YES | `NONE` | 业务属性 | 总提现 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `total_asset` | `bigint` | YES | `NONE` | 业务属性 | 总资产 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `profit_rate` | `int` | YES | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `win_flow` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `lose_flow` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `free_reward` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 14 | `lose_rate` | `int` | YES | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 15 | `year_day` | `int` | YES | `NONE` | 业务属性 | 日期格式为：20230616 | 允许在授权范围内做聚合分析；不输出字段值 |
| 16 | `create_at` | `bigint` | YES | `NONE` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_user_asset_change_profit_202604

- 表类型：`BASE TABLE`；字段数：16；数据层：业务表（事实/维度待补证）。
- 业务域：资产 / 货币（`inferred_name_only`）；建议：资产流、奖励成本、余额变化与账本对账；必须区分真金、金币和奖励资产。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `user_id` | `bigint` | NO | `MUL` | 标识 / 关联 | 用户id | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `change_type` | `int` | YES | `NONE` | 状态 / 枚举 | 资产变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_asset` | `int` | YES | `NONE` | 业务属性 | 资产变更id | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_amount` | `bigint` | YES | `NONE` | 金额 / 资产 | 资产变更金额 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `life_profit` | `bigint` | YES | `NONE` | 业务属性 | 终身盈利 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `total_recharge` | `bigint` | YES | `NONE` | 业务属性 | 总充值 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `total_withdraw` | `bigint` | YES | `NONE` | 业务属性 | 总提现 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `total_asset` | `bigint` | YES | `NONE` | 业务属性 | 总资产 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `profit_rate` | `int` | YES | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `win_flow` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `lose_flow` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `free_reward` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 14 | `lose_rate` | `int` | YES | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 15 | `year_day` | `int` | YES | `NONE` | 业务属性 | 日期格式为：20230616 | 允许在授权范围内做聚合分析；不输出字段值 |
| 16 | `create_at` | `bigint` | YES | `NONE` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_user_asset_change_profit_202605

- 表类型：`BASE TABLE`；字段数：16；数据层：业务表（事实/维度待补证）。
- 业务域：资产 / 货币（`inferred_name_only`）；建议：资产流、奖励成本、余额变化与账本对账；必须区分真金、金币和奖励资产。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `user_id` | `bigint` | NO | `MUL` | 标识 / 关联 | 用户id | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `change_type` | `int` | YES | `NONE` | 状态 / 枚举 | 资产变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_asset` | `int` | YES | `NONE` | 业务属性 | 资产变更id | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_amount` | `bigint` | YES | `NONE` | 金额 / 资产 | 资产变更金额 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `life_profit` | `bigint` | YES | `NONE` | 业务属性 | 终身盈利 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `total_recharge` | `bigint` | YES | `NONE` | 业务属性 | 总充值 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `total_withdraw` | `bigint` | YES | `NONE` | 业务属性 | 总提现 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `total_asset` | `bigint` | YES | `NONE` | 业务属性 | 总资产 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `profit_rate` | `int` | YES | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `win_flow` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `lose_flow` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `free_reward` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 14 | `lose_rate` | `int` | YES | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 15 | `year_day` | `int` | YES | `NONE` | 业务属性 | 日期格式为：20230616 | 允许在授权范围内做聚合分析；不输出字段值 |
| 16 | `create_at` | `bigint` | YES | `NONE` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_user_asset_change_profit_202606

- 表类型：`BASE TABLE`；字段数：16；数据层：业务表（事实/维度待补证）。
- 业务域：资产 / 货币（`inferred_name_only`）；建议：资产流、奖励成本、余额变化与账本对账；必须区分真金、金币和奖励资产。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `user_id` | `bigint` | NO | `MUL` | 标识 / 关联 | 用户id | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `change_type` | `int` | YES | `NONE` | 状态 / 枚举 | 资产变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_asset` | `int` | YES | `NONE` | 业务属性 | 资产变更id | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_amount` | `bigint` | YES | `NONE` | 金额 / 资产 | 资产变更金额 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `life_profit` | `bigint` | YES | `NONE` | 业务属性 | 终身盈利 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `total_recharge` | `bigint` | YES | `NONE` | 业务属性 | 总充值 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `total_withdraw` | `bigint` | YES | `NONE` | 业务属性 | 总提现 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `total_asset` | `bigint` | YES | `NONE` | 业务属性 | 总资产 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `profit_rate` | `int` | YES | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `win_flow` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `lose_flow` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `free_reward` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 14 | `lose_rate` | `int` | YES | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 15 | `year_day` | `int` | YES | `NONE` | 业务属性 | 日期格式为：20230616 | 允许在授权范围内做聚合分析；不输出字段值 |
| 16 | `create_at` | `bigint` | YES | `NONE` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_user_asset_change_profit_202607

- 表类型：`BASE TABLE`；字段数：16；数据层：业务表（事实/维度待补证）。
- 业务域：资产 / 货币（`inferred_name_only`）；建议：资产流、奖励成本、余额变化与账本对账；必须区分真金、金币和奖励资产。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `user_id` | `bigint` | NO | `MUL` | 标识 / 关联 | 用户id | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `change_type` | `int` | YES | `NONE` | 状态 / 枚举 | 资产变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_asset` | `int` | YES | `NONE` | 业务属性 | 资产变更id | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_amount` | `bigint` | YES | `NONE` | 金额 / 资产 | 资产变更金额 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `life_profit` | `bigint` | YES | `NONE` | 业务属性 | 终身盈利 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `total_recharge` | `bigint` | YES | `NONE` | 业务属性 | 总充值 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `total_withdraw` | `bigint` | YES | `NONE` | 业务属性 | 总提现 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `total_asset` | `bigint` | YES | `NONE` | 业务属性 | 总资产 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `profit_rate` | `int` | YES | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `win_flow` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `lose_flow` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `free_reward` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 14 | `lose_rate` | `int` | YES | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 15 | `year_day` | `int` | YES | `NONE` | 业务属性 | 日期格式为：20230616 | 允许在授权范围内做聚合分析；不输出字段值 |
| 16 | `create_at` | `bigint` | YES | `NONE` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_user_asset_change_profit_202608

- 表类型：`BASE TABLE`；字段数：16；数据层：业务表（事实/维度待补证）。
- 业务域：资产 / 货币（`inferred_name_only`）；建议：资产流、奖励成本、余额变化与账本对账；必须区分真金、金币和奖励资产。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `user_id` | `bigint` | NO | `MUL` | 标识 / 关联 | 用户id | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `change_type` | `int` | YES | `NONE` | 状态 / 枚举 | 资产变更类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `change_asset` | `int` | YES | `NONE` | 业务属性 | 资产变更id | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `change_amount` | `bigint` | YES | `NONE` | 金额 / 资产 | 资产变更金额 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `life_profit` | `bigint` | YES | `NONE` | 业务属性 | 终身盈利 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `total_recharge` | `bigint` | YES | `NONE` | 业务属性 | 总充值 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `total_withdraw` | `bigint` | YES | `NONE` | 业务属性 | 总提现 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `total_asset` | `bigint` | YES | `NONE` | 业务属性 | 总资产 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `profit_rate` | `int` | YES | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `win_flow` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `lose_flow` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `free_reward` | `bigint` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 14 | `lose_rate` | `int` | YES | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 15 | `year_day` | `int` | YES | `NONE` | 业务属性 | 日期格式为：20230616 | 允许在授权范围内做聚合分析；不输出字段值 |
| 16 | `create_at` | `bigint` | YES | `NONE` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_user_control_daily

- 表类型：`BASE TABLE`；字段数：7；数据层：业务表（事实/维度待补证）。
- 业务域：用户 / 账号（`inferred_name_only`）；建议：注册、登录与生命周期聚合；禁止导出可识别身份字段。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `day` | `int` | NO | `MUL` | 业务属性 | 日期格式为：20230616 | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `user_id` | `int` | NO | `NONE` | 标识 / 关联 | 用户id | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `type` | `int` | NO | `NONE` | 状态 / 枚举 | 属性类型，具体看定义的常量值 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `count` | `int` | NO | `NONE` | 业务属性 | 次数 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `amount` | `bigint` | NO | `NONE` | 金额 / 资产 | 数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `time` | `bigint` | NO | `MUL` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_user_control_detail

- 表类型：`BASE TABLE`；字段数：8；数据层：业务表（事实/维度待补证）。
- 业务域：用户 / 账号（`inferred_name_only`）；建议：注册、登录与生命周期聚合；禁止导出可识别身份字段。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `user_id` | `int` | NO | `NONE` | 标识 / 关联 | 用户id | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `game_type` | `int` | NO | `NONE` | 状态 / 枚举 | 游戏类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `control_type` | `int` | NO | `NONE` | 状态 / 枚举 | 控制类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `control_subtype` | `int` | NO | `NONE` | 状态 / 枚举 | 控制子类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `count` | `bigint` | NO | `NONE` | 业务属性 | 次数 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `amount` | `bigint` | NO | `NONE` | 金额 / 资产 | 数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `time` | `bigint` | NO | `MUL` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_user_flow

- 表类型：`BASE TABLE`；字段数：10；数据层：业务表（事实/维度待补证）。
- 业务域：用户 / 账号（`inferred_name_only`）；建议：注册、登录与生命周期聚合；禁止导出可识别身份字段。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `user_id` | `int unsigned` | NO | `UNI` | 标识 / 关联 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `win` | `bigint unsigned` | NO | `NONE` | 业务属性 | 赢的流水 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `lose` | `bigint unsigned` | NO | `NONE` | 业务属性 | 输的流水 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `free_reward` | `bigint unsigned` | NO | `NONE` | 业务属性 | 免费奖励流水 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `flow_protect_amount` | `bigint` | NO | `NONE` | 金额 / 资产 | 流水保护额度 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `flow_protect_charge_amount` | `bigint unsigned` | NO | `NONE` | 金额 / 资产 | 流水保护的充值金额 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `create_at` | `datetime` | NO | `NONE` | 时间 | 创建时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `update_at` | `datetime` | NO | `NONE` | 时间 | 更新时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `withdraw_limit` | `bigint unsigned` | NO | `NONE` | 业务属性 | 流水提现额度 | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_user_flow_detail_202410

- 表类型：`BASE TABLE`；字段数：7；数据层：业务表（事实/维度待补证）。
- 业务域：用户 / 账号（`inferred_name_only`）；建议：注册、登录与生命周期聚合；禁止导出可识别身份字段。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `user_id` | `int unsigned` | NO | `MUL` | 标识 / 关联 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `win` | `bigint unsigned` | NO | `NONE` | 业务属性 | 赢的流水 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `lose` | `bigint unsigned` | NO | `NONE` | 业务属性 | 输的流水 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `game_type` | `int` | NO | `NONE` | 状态 / 枚举 | 游戏类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `year_day` | `int` | NO | `NONE` | 业务属性 | 日期格式为：20230616 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `create_at` | `bigint` | NO | `NONE` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_user_flow_detail_202411

- 表类型：`BASE TABLE`；字段数：7；数据层：业务表（事实/维度待补证）。
- 业务域：用户 / 账号（`inferred_name_only`）；建议：注册、登录与生命周期聚合；禁止导出可识别身份字段。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `user_id` | `int unsigned` | NO | `MUL` | 标识 / 关联 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `win` | `bigint unsigned` | NO | `NONE` | 业务属性 | 赢的流水 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `lose` | `bigint unsigned` | NO | `NONE` | 业务属性 | 输的流水 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `game_type` | `int` | NO | `NONE` | 状态 / 枚举 | 游戏类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `year_day` | `int` | NO | `NONE` | 业务属性 | 日期格式为：20230616 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `create_at` | `bigint` | NO | `NONE` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_user_flow_detail_202412

- 表类型：`BASE TABLE`；字段数：7；数据层：业务表（事实/维度待补证）。
- 业务域：用户 / 账号（`inferred_name_only`）；建议：注册、登录与生命周期聚合；禁止导出可识别身份字段。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `user_id` | `int unsigned` | NO | `MUL` | 标识 / 关联 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `win` | `bigint unsigned` | NO | `NONE` | 业务属性 | 赢的流水 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `lose` | `bigint unsigned` | NO | `NONE` | 业务属性 | 输的流水 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `game_type` | `int` | NO | `NONE` | 状态 / 枚举 | 游戏类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `year_day` | `int` | NO | `NONE` | 业务属性 | 日期格式为：20230616 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `create_at` | `bigint` | NO | `NONE` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_user_flow_detail_202501

- 表类型：`BASE TABLE`；字段数：7；数据层：业务表（事实/维度待补证）。
- 业务域：用户 / 账号（`inferred_name_only`）；建议：注册、登录与生命周期聚合；禁止导出可识别身份字段。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `user_id` | `int unsigned` | NO | `MUL` | 标识 / 关联 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `win` | `bigint unsigned` | NO | `NONE` | 业务属性 | 赢的流水 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `lose` | `bigint unsigned` | NO | `NONE` | 业务属性 | 输的流水 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `game_type` | `int` | NO | `NONE` | 状态 / 枚举 | 游戏类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `year_day` | `int` | NO | `NONE` | 业务属性 | 日期格式为：20230616 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `create_at` | `bigint` | NO | `NONE` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_user_flow_detail_202502

- 表类型：`BASE TABLE`；字段数：7；数据层：业务表（事实/维度待补证）。
- 业务域：用户 / 账号（`inferred_name_only`）；建议：注册、登录与生命周期聚合；禁止导出可识别身份字段。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `user_id` | `int unsigned` | NO | `MUL` | 标识 / 关联 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `win` | `bigint unsigned` | NO | `NONE` | 业务属性 | 赢的流水 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `lose` | `bigint unsigned` | NO | `NONE` | 业务属性 | 输的流水 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `game_type` | `int` | NO | `NONE` | 状态 / 枚举 | 游戏类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `year_day` | `int` | NO | `NONE` | 业务属性 | 日期格式为：20230616 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `create_at` | `bigint` | NO | `NONE` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_user_flow_detail_202503

- 表类型：`BASE TABLE`；字段数：7；数据层：业务表（事实/维度待补证）。
- 业务域：用户 / 账号（`inferred_name_only`）；建议：注册、登录与生命周期聚合；禁止导出可识别身份字段。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `user_id` | `int unsigned` | NO | `MUL` | 标识 / 关联 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `win` | `bigint unsigned` | NO | `NONE` | 业务属性 | 赢的流水 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `lose` | `bigint unsigned` | NO | `NONE` | 业务属性 | 输的流水 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `game_type` | `int` | NO | `NONE` | 状态 / 枚举 | 游戏类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `year_day` | `int` | NO | `NONE` | 业务属性 | 日期格式为：20230616 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `create_at` | `bigint` | NO | `NONE` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_user_flow_detail_202504

- 表类型：`BASE TABLE`；字段数：7；数据层：业务表（事实/维度待补证）。
- 业务域：用户 / 账号（`inferred_name_only`）；建议：注册、登录与生命周期聚合；禁止导出可识别身份字段。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `user_id` | `int unsigned` | NO | `MUL` | 标识 / 关联 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `win` | `bigint unsigned` | NO | `NONE` | 业务属性 | 赢的流水 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `lose` | `bigint unsigned` | NO | `NONE` | 业务属性 | 输的流水 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `game_type` | `int` | NO | `NONE` | 状态 / 枚举 | 游戏类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `year_day` | `int` | NO | `NONE` | 业务属性 | 日期格式为：20230616 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `create_at` | `bigint` | NO | `NONE` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_user_flow_detail_202505

- 表类型：`BASE TABLE`；字段数：7；数据层：业务表（事实/维度待补证）。
- 业务域：用户 / 账号（`inferred_name_only`）；建议：注册、登录与生命周期聚合；禁止导出可识别身份字段。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `user_id` | `int unsigned` | NO | `MUL` | 标识 / 关联 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `win` | `bigint unsigned` | NO | `NONE` | 业务属性 | 赢的流水 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `lose` | `bigint unsigned` | NO | `NONE` | 业务属性 | 输的流水 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `game_type` | `int` | NO | `NONE` | 状态 / 枚举 | 游戏类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `year_day` | `int` | NO | `NONE` | 业务属性 | 日期格式为：20230616 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `create_at` | `bigint` | NO | `NONE` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_user_flow_detail_202506

- 表类型：`BASE TABLE`；字段数：7；数据层：业务表（事实/维度待补证）。
- 业务域：用户 / 账号（`inferred_name_only`）；建议：注册、登录与生命周期聚合；禁止导出可识别身份字段。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `user_id` | `int unsigned` | NO | `MUL` | 标识 / 关联 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `win` | `bigint unsigned` | NO | `NONE` | 业务属性 | 赢的流水 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `lose` | `bigint unsigned` | NO | `NONE` | 业务属性 | 输的流水 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `game_type` | `int` | NO | `NONE` | 状态 / 枚举 | 游戏类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `year_day` | `int` | NO | `NONE` | 业务属性 | 日期格式为：20230616 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `create_at` | `bigint` | NO | `NONE` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_user_flow_detail_202507

- 表类型：`BASE TABLE`；字段数：7；数据层：业务表（事实/维度待补证）。
- 业务域：用户 / 账号（`inferred_name_only`）；建议：注册、登录与生命周期聚合；禁止导出可识别身份字段。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `user_id` | `int unsigned` | NO | `MUL` | 标识 / 关联 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `win` | `bigint unsigned` | NO | `NONE` | 业务属性 | 赢的流水 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `lose` | `bigint unsigned` | NO | `NONE` | 业务属性 | 输的流水 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `game_type` | `int` | NO | `NONE` | 状态 / 枚举 | 游戏类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `year_day` | `int` | NO | `NONE` | 业务属性 | 日期格式为：20230616 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `create_at` | `bigint` | NO | `NONE` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_user_flow_detail_202508

- 表类型：`BASE TABLE`；字段数：7；数据层：业务表（事实/维度待补证）。
- 业务域：用户 / 账号（`inferred_name_only`）；建议：注册、登录与生命周期聚合；禁止导出可识别身份字段。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `user_id` | `int unsigned` | NO | `MUL` | 标识 / 关联 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `win` | `bigint unsigned` | NO | `NONE` | 业务属性 | 赢的流水 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `lose` | `bigint unsigned` | NO | `NONE` | 业务属性 | 输的流水 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `game_type` | `int` | NO | `NONE` | 状态 / 枚举 | 游戏类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `year_day` | `int` | NO | `NONE` | 业务属性 | 日期格式为：20230616 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `create_at` | `bigint` | NO | `NONE` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_user_flow_detail_202509

- 表类型：`BASE TABLE`；字段数：7；数据层：业务表（事实/维度待补证）。
- 业务域：用户 / 账号（`inferred_name_only`）；建议：注册、登录与生命周期聚合；禁止导出可识别身份字段。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `user_id` | `int unsigned` | NO | `MUL` | 标识 / 关联 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `win` | `bigint unsigned` | NO | `NONE` | 业务属性 | 赢的流水 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `lose` | `bigint unsigned` | NO | `NONE` | 业务属性 | 输的流水 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `game_type` | `int` | NO | `NONE` | 状态 / 枚举 | 游戏类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `year_day` | `int` | NO | `NONE` | 业务属性 | 日期格式为：20230616 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `create_at` | `bigint` | NO | `NONE` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_user_flow_detail_202510

- 表类型：`BASE TABLE`；字段数：7；数据层：业务表（事实/维度待补证）。
- 业务域：用户 / 账号（`inferred_name_only`）；建议：注册、登录与生命周期聚合；禁止导出可识别身份字段。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `user_id` | `int unsigned` | NO | `MUL` | 标识 / 关联 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `win` | `bigint unsigned` | NO | `NONE` | 业务属性 | 赢的流水 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `lose` | `bigint unsigned` | NO | `NONE` | 业务属性 | 输的流水 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `game_type` | `int` | NO | `NONE` | 状态 / 枚举 | 游戏类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `year_day` | `int` | NO | `NONE` | 业务属性 | 日期格式为：20230616 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `create_at` | `bigint` | NO | `NONE` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_user_flow_detail_202511

- 表类型：`BASE TABLE`；字段数：7；数据层：业务表（事实/维度待补证）。
- 业务域：用户 / 账号（`inferred_name_only`）；建议：注册、登录与生命周期聚合；禁止导出可识别身份字段。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `user_id` | `int unsigned` | NO | `MUL` | 标识 / 关联 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `win` | `bigint unsigned` | NO | `NONE` | 业务属性 | 赢的流水 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `lose` | `bigint unsigned` | NO | `NONE` | 业务属性 | 输的流水 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `game_type` | `int` | NO | `NONE` | 状态 / 枚举 | 游戏类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `year_day` | `int` | NO | `NONE` | 业务属性 | 日期格式为：20230616 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `create_at` | `bigint` | NO | `NONE` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_user_flow_detail_202512

- 表类型：`BASE TABLE`；字段数：7；数据层：业务表（事实/维度待补证）。
- 业务域：用户 / 账号（`inferred_name_only`）；建议：注册、登录与生命周期聚合；禁止导出可识别身份字段。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `user_id` | `int unsigned` | NO | `MUL` | 标识 / 关联 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `win` | `bigint unsigned` | NO | `NONE` | 业务属性 | 赢的流水 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `lose` | `bigint unsigned` | NO | `NONE` | 业务属性 | 输的流水 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `game_type` | `int` | NO | `NONE` | 状态 / 枚举 | 游戏类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `year_day` | `int` | NO | `NONE` | 业务属性 | 日期格式为：20230616 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `create_at` | `bigint` | NO | `NONE` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_user_flow_detail_202601

- 表类型：`BASE TABLE`；字段数：7；数据层：业务表（事实/维度待补证）。
- 业务域：用户 / 账号（`inferred_name_only`）；建议：注册、登录与生命周期聚合；禁止导出可识别身份字段。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `user_id` | `int unsigned` | NO | `MUL` | 标识 / 关联 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `win` | `bigint unsigned` | NO | `NONE` | 业务属性 | 赢的流水 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `lose` | `bigint unsigned` | NO | `NONE` | 业务属性 | 输的流水 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `game_type` | `int` | NO | `NONE` | 状态 / 枚举 | 游戏类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `year_day` | `int` | NO | `NONE` | 业务属性 | 日期格式为：20230616 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `create_at` | `bigint` | NO | `NONE` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_user_flow_detail_202602

- 表类型：`BASE TABLE`；字段数：7；数据层：业务表（事实/维度待补证）。
- 业务域：用户 / 账号（`inferred_name_only`）；建议：注册、登录与生命周期聚合；禁止导出可识别身份字段。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `user_id` | `int unsigned` | NO | `MUL` | 标识 / 关联 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `win` | `bigint unsigned` | NO | `NONE` | 业务属性 | 赢的流水 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `lose` | `bigint unsigned` | NO | `NONE` | 业务属性 | 输的流水 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `game_type` | `int` | NO | `NONE` | 状态 / 枚举 | 游戏类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `year_day` | `int` | NO | `NONE` | 业务属性 | 日期格式为：20230616 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `create_at` | `bigint` | NO | `NONE` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_user_flow_detail_202603

- 表类型：`BASE TABLE`；字段数：7；数据层：业务表（事实/维度待补证）。
- 业务域：用户 / 账号（`inferred_name_only`）；建议：注册、登录与生命周期聚合；禁止导出可识别身份字段。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `user_id` | `int unsigned` | NO | `MUL` | 标识 / 关联 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `win` | `bigint unsigned` | NO | `NONE` | 业务属性 | 赢的流水 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `lose` | `bigint unsigned` | NO | `NONE` | 业务属性 | 输的流水 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `game_type` | `int` | NO | `NONE` | 状态 / 枚举 | 游戏类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `year_day` | `int` | NO | `NONE` | 业务属性 | 日期格式为：20230616 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `create_at` | `bigint` | NO | `NONE` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_user_flow_detail_202604

- 表类型：`BASE TABLE`；字段数：7；数据层：业务表（事实/维度待补证）。
- 业务域：用户 / 账号（`inferred_name_only`）；建议：注册、登录与生命周期聚合；禁止导出可识别身份字段。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `user_id` | `int unsigned` | NO | `MUL` | 标识 / 关联 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `win` | `bigint unsigned` | NO | `NONE` | 业务属性 | 赢的流水 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `lose` | `bigint unsigned` | NO | `NONE` | 业务属性 | 输的流水 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `game_type` | `int` | NO | `NONE` | 状态 / 枚举 | 游戏类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `year_day` | `int` | NO | `NONE` | 业务属性 | 日期格式为：20230616 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `create_at` | `bigint` | NO | `NONE` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_user_flow_detail_202605

- 表类型：`BASE TABLE`；字段数：7；数据层：业务表（事实/维度待补证）。
- 业务域：用户 / 账号（`inferred_name_only`）；建议：注册、登录与生命周期聚合；禁止导出可识别身份字段。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `user_id` | `int unsigned` | NO | `MUL` | 标识 / 关联 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `win` | `bigint unsigned` | NO | `NONE` | 业务属性 | 赢的流水 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `lose` | `bigint unsigned` | NO | `NONE` | 业务属性 | 输的流水 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `game_type` | `int` | NO | `NONE` | 状态 / 枚举 | 游戏类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `year_day` | `int` | NO | `NONE` | 业务属性 | 日期格式为：20230616 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `create_at` | `bigint` | NO | `NONE` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_user_flow_detail_202606

- 表类型：`BASE TABLE`；字段数：7；数据层：业务表（事实/维度待补证）。
- 业务域：用户 / 账号（`inferred_name_only`）；建议：注册、登录与生命周期聚合；禁止导出可识别身份字段。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `user_id` | `int unsigned` | NO | `MUL` | 标识 / 关联 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `win` | `bigint unsigned` | NO | `NONE` | 业务属性 | 赢的流水 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `lose` | `bigint unsigned` | NO | `NONE` | 业务属性 | 输的流水 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `game_type` | `int` | NO | `NONE` | 状态 / 枚举 | 游戏类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `year_day` | `int` | NO | `NONE` | 业务属性 | 日期格式为：20230616 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `create_at` | `bigint` | NO | `NONE` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_user_flow_detail_202607

- 表类型：`BASE TABLE`；字段数：7；数据层：业务表（事实/维度待补证）。
- 业务域：用户 / 账号（`inferred_name_only`）；建议：注册、登录与生命周期聚合；禁止导出可识别身份字段。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `user_id` | `int unsigned` | NO | `MUL` | 标识 / 关联 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `win` | `bigint unsigned` | NO | `NONE` | 业务属性 | 赢的流水 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `lose` | `bigint unsigned` | NO | `NONE` | 业务属性 | 输的流水 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `game_type` | `int` | NO | `NONE` | 状态 / 枚举 | 游戏类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `year_day` | `int` | NO | `NONE` | 业务属性 | 日期格式为：20230616 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `create_at` | `bigint` | NO | `NONE` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_user_flow_detail_202608

- 表类型：`BASE TABLE`；字段数：7；数据层：业务表（事实/维度待补证）。
- 业务域：用户 / 账号（`inferred_name_only`）；建议：注册、登录与生命周期聚合；禁止导出可识别身份字段。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `user_id` | `int unsigned` | NO | `MUL` | 标识 / 关联 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `win` | `bigint unsigned` | NO | `NONE` | 业务属性 | 赢的流水 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `lose` | `bigint unsigned` | NO | `NONE` | 业务属性 | 输的流水 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `game_type` | `int` | NO | `NONE` | 状态 / 枚举 | 游戏类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `year_day` | `int` | NO | `NONE` | 业务属性 | 日期格式为：20230616 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `create_at` | `bigint` | NO | `NONE` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_user_flow_protect

- 表类型：`BASE TABLE`；字段数：7；数据层：业务表（事实/维度待补证）。
- 业务域：用户 / 账号（`inferred_name_only`）；建议：注册、登录与生命周期聚合；禁止导出可识别身份字段。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `user_id` | `int unsigned` | NO | `UNI` | 标识 / 关联 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `flow_protect_amount` | `bigint` | NO | `NONE` | 金额 / 资产 | 流水保护额度 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `flow_protect_charge_amount` | `bigint unsigned` | NO | `NONE` | 金额 / 资产 | 流水保护的充值金额 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `flow_protect_win_amount` | `bigint` | NO | `NONE` | 金额 / 资产 | 流水保护赢钱额度 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `charge_total_asset` | `bigint` | NO | `NONE` | 业务属性 | 上次充值时的总资产 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `flow_protect_max_win` | `bigint` | NO | `NONE` | 业务属性 | 流水保护最大赢钱额度 | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_user_flow_protect_detail

- 表类型：`BASE TABLE`；字段数：9；数据层：业务表（事实/维度待补证）。
- 业务域：用户 / 账号（`inferred_name_only`）；建议：注册、登录与生命周期聚合；禁止导出可识别身份字段。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `user_id` | `int` | NO | `MUL` | 标识 / 关联 | 用户id | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `game_type` | `int` | NO | `NONE` | 状态 / 枚举 | 游戏类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `trigger_type` | `int` | NO | `NONE` | 状态 / 枚举 | 控制类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `trigger_count` | `int unsigned` | NO | `NONE` | 业务属性 | 控制次数 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `win_amount` | `bigint` | NO | `NONE` | 金额 / 资产 | 赢走的钱数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `year_day` | `int` | NO | `MUL` | 业务属性 | 日期格式为：20230616 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `create_at` | `bigint` | NO | `MUL` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `profit_amount` | `bigint` | YES | `NONE` | 金额 / 资产 | 净赢 | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_user_property

- 表类型：`BASE TABLE`；字段数：6；数据层：业务表（事实/维度待补证）。
- 业务域：用户 / 账号（`inferred_name_only`）；建议：注册、登录与生命周期聚合；禁止导出可识别身份字段。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `user_id` | `int` | NO | `MUL` | 标识 / 关联 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `type` | `int` | NO | `NONE` | 状态 / 枚举 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `count` | `int` | NO | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `amount` | `bigint` | NO | `NONE` | 金额 / 资产 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `time` | `bigint` | NO | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_user_withdraw_profit

- 表类型：`BASE TABLE`；字段数：7；数据层：业务表（事实/维度待补证）。
- 业务域：支付 / 提现（`inferred_name_only`）；建议：支付/提现漏斗、成功率、时延与失败码；金融金额以服务端事实复核。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `user_id` | `bigint` | NO | `MUL` | 标识 / 关联 | 用户id | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `withdraw_amount` | `int` | YES | `NONE` | 金额 / 资产 | 提现金额 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `withdraw_order` | `bigint` | YES | `NONE` | 业务属性 | 订单id | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `life_profit` | `bigint` | YES | `NONE` | 业务属性 | 终身盈利 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `year_day` | `int` | YES | `NONE` | 业务属性 | 日期格式为：20230616 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `create_at` | `bigint` | YES | `MUL` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_user_wlrecord

- 表类型：`BASE TABLE`；字段数：6；数据层：业务表（事实/维度待补证）。
- 业务域：用户 / 账号（`inferred_name_only`）；建议：注册、登录与生命周期聚合；禁止导出可识别身份字段。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint` | NO | `PRI` | 标识 / 关联 | 主键 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `userid` | `int` | NO | `NONE` | 业务属性 | userid | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `bet` | `bigint` | NO | `NONE` | 游戏 / 玩法 | 玩家下注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `gain` | `bigint` | NO | `NONE` | 业务属性 | 玩家获得 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `playtype` | `int` | NO | `NONE` | 状态 / 枚举 | 玩法 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `property` | `int` | NO | `NONE` | 业务属性 | 属性 | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_waterline

- 表类型：`BASE TABLE`；字段数：5；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint` | NO | `PRI` | 标识 / 关联 | 主键 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `userid` | `int` | NO | `MUL` | 业务属性 | userid | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `bet` | `bigint` | NO | `NONE` | 游戏 / 玩法 | 玩家下注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `gain` | `bigint` | NO | `NONE` | 业务属性 | 玩家获得 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `playtype` | `int` | NO | `NONE` | 状态 / 枚举 | 玩法 | 允许在授权范围内做聚合分析；不输出字段值 |

### stat_whale_pkg_kill_data

- 表类型：`BASE TABLE`；字段数：6；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint` | NO | `PRI` | 标识 / 关联 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `uid` | `bigint` | NO | `UNI` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `remain_principal_amount` | `bigint` | NO | `NONE` | 金额 / 资产 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `remain_kill_amount` | `bigint` | NO | `NONE` | 金额 / 资产 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `flow_protect_fix_amount` | `bigint` | NO | `NONE` | 金额 / 资产 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `update_at` | `bigint` | NO | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |

### sys_menu

- 表类型：`BASE TABLE`；字段数：5；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `int` | NO | `PRI` | 标识 / 关联 | 菜单Id | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `parent` | `int` | YES | `NONE` | 业务属性 | 上级Id | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `name` | `varchar(100)` | YES | `NONE` | 业务属性 | 菜单名称 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `icon` | `varchar(30)` | YES | `NONE` | 业务属性 | 菜单图标 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `url` | `varchar(100)` | YES | `NONE` | 业务属性 | 菜单链接 | 允许在授权范围内做聚合分析；不输出字段值 |

### sys_oauth_identity

- 表类型：`BASE TABLE`；字段数：7；数据层：业务表（事实/维度待补证）。
- 业务域：用户 / 账号（`inferred_name_only`）；建议：注册、登录与生命周期聚合；禁止导出可识别身份字段。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint` | NO | `PRI` | 标识 / 关联 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `user_id` | `int` | NO | `MUL` | 标识 / 关联 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `issuer` | `varchar(255)` | NO | `MUL` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `subject` | `varchar(255)` | NO | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `preferred_username` | `varchar(100)` | NO | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `created_at` | `datetime` | NO | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `updated_at` | `datetime` | NO | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |

### sys_opt_log

- 表类型：`BASE TABLE`；字段数：6；数据层：业务表（事实/维度待补证）。
- 业务域：日志 / 数据质量（`inferred_name_only`）；建议：入库延迟、错误、重试和数据质量排障；需明确日志保留周期。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `int` | NO | `PRI` | 标识 / 关联 | Id | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `user_id` | `int` | NO | `NONE` | 标识 / 关联 | 管理员Id | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `type` | `tinyint` | NO | `NONE` | 状态 / 枚举 | 操作类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `opt_user` | `int` | NO | `NONE` | 业务属性 | 操作对方ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `opt_value` | `varchar(128)` | YES | `NONE` | 业务属性 | 值 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `create_time` | `datetime` | NO | `NONE` | 时间 | 创建时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### sys_permission

- 表类型：`BASE TABLE`；字段数：3；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `int` | NO | `PRI` | 标识 / 关联 | 权限Id | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `name` | `varchar(100)` | YES | `NONE` | 业务属性 | 权限名称 | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `menu` | `int` | YES | `NONE` | 业务属性 | 菜单Id | 允许在授权范围内做聚合分析；不输出字段值 |

### sys_role

- 表类型：`BASE TABLE`；字段数：2；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `int` | NO | `PRI` | 标识 / 关联 | 角色Id | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `name` | `varchar(100)` | YES | `NONE` | 业务属性 | 角色名称 | 允许在授权范围内做聚合分析；不输出字段值 |

### sys_role_permission

- 表类型：`BASE TABLE`；字段数：3；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `rpid` | `int` | NO | `PRI` | 业务属性 | 表Id | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `roleid` | `int` | NO | `NONE` | 业务属性 | 角色Id | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `permissionid` | `int` | NO | `NONE` | 业务属性 | 权限Id | 允许在授权范围内做聚合分析；不输出字段值 |

### sys_user

- 表类型：`BASE TABLE`；字段数：4；数据层：业务表（事实/维度待补证）。
- 业务域：用户 / 账号（`inferred_name_only`）；建议：注册、登录与生命周期聚合；禁止导出可识别身份字段。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `int` | NO | `PRI` | 标识 / 关联 | 用户Id | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `accounts` | `varchar(100)` | YES | `UNI` | 业务属性 | 账号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | [REDACTED:CREDENTIAL_OR_SECRET] | `varchar(100)` | YES | `NONE` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 禁止展示、导出或进入分析产物 |
| 4 | `nickname` | `varchar(100)` | YES | `NONE` | 业务属性 | 昵称 | 允许在授权范围内做聚合分析；不输出字段值 |

### sys_user_role

- 表类型：`BASE TABLE`；字段数：3；数据层：业务表（事实/维度待补证）。
- 业务域：用户 / 账号（`inferred_name_only`）；建议：注册、登录与生命周期聚合；禁止导出可识别身份字段。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `urid` | `int` | NO | `PRI` | 业务属性 | 表Id | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `userid` | `int` | NO | `NONE` | 业务属性 | 用户Id | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `roleid` | `int` | NO | `NONE` | 业务属性 | 角色Id | 允许在授权范围内做聚合分析；不输出字段值 |

### uc_addevice_adchannel

- 表类型：`BASE TABLE`；字段数：6；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `device_id` | `varchar(128)` | NO | `UNI` | 标识 / 关联 | 注册设备ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `package_id` | `varchar(128)` | NO | `NONE` | 标识 / 关联 | 注册包名 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `ad_channel` | `varchar(128)` | NO | `NONE` | 业务属性 | 广告渠道 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `update_at` | `bigint` | YES | `NONE` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `ad_group_id` | `varchar(128)` | NO | `NONE` | 标识 / 关联 | 广告组ID | 允许在授权范围内做聚合分析；不输出字段值 |

### uc_bank_account_users

- 表类型：`BASE TABLE`；字段数：6；数据层：业务表（事实/维度待补证）。
- 业务域：用户 / 账号（`inferred_name_only`）；建议：注册、登录与生命周期聚合；禁止导出可识别身份字段。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `bank_name` | `varchar(100)` | NO | `MUL` | 业务属性 | 银行 | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `bank_no` | `varchar(100)` | NO | `NONE` | 业务属性 | 银行卡号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `gid` | `int unsigned` | NO | `MUL` | 业务属性 | gid | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `create_at` | `bigint` | NO | `NONE` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `is_default` | `tinyint unsigned` | NO | `NONE` | 业务属性 | 是否默认 1默认 | 允许在授权范围内做聚合分析；不输出字段值 |

### uc_logic

- 表类型：`BASE TABLE`；字段数：3；数据层：业务表（事实/维度待补证）。
- 业务域：日志 / 数据质量（`inferred_name_only`）；建议：入库延迟、错误、重试和数据质量排障；需明确日志保留周期。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `act_data` | `varchar(1024)` | YES | `NONE` | 时间 | 活动数据 | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `switches` | `bigint unsigned` | NO | `NONE` | 业务属性 | 开关 | 允许在授权范围内做聚合分析；不输出字段值 |

### uc_login

- 表类型：`BASE TABLE`；字段数：6；数据层：业务表（事实/维度待补证）。
- 业务域：用户 / 账号（`inferred_name_only`）；建议：注册、登录与生命周期聚合；禁止导出可识别身份字段。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int unsigned` | NO | `MUL` | 业务属性 | 玩家ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `user_id` | `int unsigned` | NO | `NONE` | 标识 / 关联 | 玩家游戏服ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `union_id` | `varchar(64)` | NO | `UNI` | 标识 / 关联 | UnionId | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `mode` | `tinyint` | NO | `NONE` | 状态 / 枚举 | 注册方式 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `time` | `int unsigned` | YES | `NONE` | 时间 | 绑定时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### uc_tourist_v2

- 表类型：`BASE TABLE`；字段数：5；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int unsigned` | NO | `UNI` | 业务属性 | 用户唯一ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `uuid` | `varchar(128)` | YES | `MUL` | 标识 / 关联 | 游客唯一ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `device_id` | `varchar(128)` | YES | `NONE` | 标识 / 关联 | 注册设备ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `reg_channel` | `varchar(256)` | YES | `NONE` | 业务属性 | 注册渠道 | 允许在授权范围内做聚合分析；不输出字段值 |

### uc_user

- 表类型：`BASE TABLE`；字段数：23；数据层：业务表（事实/维度待补证）。
- 业务域：用户 / 账号（`inferred_name_only`）；建议：注册、登录与生命周期聚合；禁止导出可识别身份字段。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `user_id` | `int unsigned` | NO | `UNI` | 标识 / 关联 | 玩家游戏服ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | [REDACTED:KYC_PERSONAL_IDENTIFIER_OR_BIOMETRIC] | `varchar(16)` | YES | `NONE` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 受限；仅脱敏聚合或伪标识下钻 |
| 4 | [REDACTED:CREDENTIAL_OR_SECRET] | `varchar(32)` | YES | `NONE` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 禁止展示、导出或进入分析产物 |
| 5 | `nick_name` | `varchar(64)` | NO | `NONE` | 业务属性 | 玩家昵称 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `sex` | `tinyint` | YES | `NONE` | 业务属性 | 玩家性别 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `ban` | `tinyint` | YES | `NONE` | 业务属性 | 禁止登录 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `head_image_url` | `varchar(512)` | YES | `NONE` | 业务属性 | 玩家头像URL | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `last_login_time` | `int unsigned` | YES | `NONE` | 时间 | 玩家最后一次登录时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `reg_time` | `int unsigned` | YES | `NONE` | 时间 | 玩家注册时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `ban_time` | `int unsigned` | YES | `NONE` | 时间 | 玩家封禁时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `last_login_ip` | `varchar(16)` | NO | `NONE` | 业务属性 | 上次登录IP | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `last_login_mode` | `tinyint` | NO | `NONE` | 状态 / 枚举 | 上次登录方式 | 允许在授权范围内做聚合分析；不输出字段值 |
| 14 | `last_login_dev_model` | `varchar(64)` | YES | `NONE` | 状态 / 枚举 | 上次登录设备型号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 15 | `last_login_sys_ver` | `varchar(64)` | YES | `NONE` | 业务属性 | 上次登录系统版本号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 16 | `reg_ip` | `varchar(16)` | NO | `NONE` | 业务属性 | 注册IP | 允许在授权范围内做聚合分析；不输出字段值 |
| 17 | `birth` | `varchar(12)` | NO | `NONE` | 业务属性 | 生日 | 允许在授权范围内做聚合分析；不输出字段值 |
| 18 | `inviter` | `int unsigned` | NO | `NONE` | 业务属性 | 邀请者ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 19 | `reg_device` | `varchar(64)` | YES | `MUL` | 业务属性 | 注册设备ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 20 | `reg_package` | `varchar(256)` | YES | `NONE` | 业务属性 | 注册包名 | 允许在授权范围内做聚合分析；不输出字段值 |
| 21 | `reg_channel` | `varchar(32)` | YES | `NONE` | 业务属性 | 注册渠道 | 允许在授权范围内做聚合分析；不输出字段值 |
| 22 | `reg_sub_channel` | `varchar(32)` | YES | `NONE` | 业务属性 | 注册二级渠道 | 允许在授权范围内做聚合分析；不输出字段值 |
| 23 | `reg_gaid` | `varchar(64)` | YES | `NONE` | 业务属性 | gaid | 允许在授权范围内做聚合分析；不输出字段值 |

### uc_user_adchannel

- 表类型：`BASE TABLE`；字段数：8；数据层：业务表（事实/维度待补证）。
- 业务域：用户 / 账号（`inferred_name_only`）；建议：注册、登录与生命周期聚合；禁止导出可识别身份字段。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `bigint unsigned` | NO | `UNI` | 业务属性 | 玩家id | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `reg_af_device` | `varchar(128)` | NO | `MUL` | 业务属性 | af注册设备ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `reg_solar_device` | `varchar(128)` | NO | `MUL` | 业务属性 | solar注册设备ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `reg_package` | `varchar(128)` | NO | `NONE` | 业务属性 | 注册包名 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `ad_channel` | `varchar(128)` | NO | `NONE` | 业务属性 | 广告渠道 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `update_at` | `bigint` | YES | `NONE` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `ad_group_id` | `varchar(128)` | NO | `NONE` | 标识 / 关联 | 广告组ID | 允许在授权范围内做聚合分析；不输出字段值 |

### uc_user_device

- 表类型：`BASE TABLE`；字段数：5；数据层：业务表（事实/维度待补证）。
- 业务域：用户 / 账号（`inferred_name_only`）；建议：注册、登录与生命周期聚合；禁止导出可识别身份字段。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `reg_device` | `varchar(128)` | YES | `UNI` | 业务属性 | 注册设备ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `reg_count` | `int unsigned` | NO | `NONE` | 业务属性 | 用户唯一ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `first_reg_time` | `int unsigned` | YES | `NONE` | 时间 | 首次注册时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `last_reg_time` | `int unsigned` | YES | `NONE` | 时间 | 最后一次注册时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### uc_user_device_info

- 表类型：`BASE TABLE`；字段数：11；数据层：业务表（事实/维度待补证）。
- 业务域：用户 / 账号（`inferred_name_only`）；建议：注册、登录与生命周期聚合；禁止导出可识别身份字段。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `bigint unsigned` | NO | `UNI` | 业务属性 | 玩家id | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `reg_package` | `varchar(128)` | NO | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `reg_ip` | `varchar(128)` | NO | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `reg_ua` | `varchar(512)` | NO | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `reg_adid` | `varchar(128)` | NO | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `reg_idfa` | `varchar(128)` | NO | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `update_at` | `bigint` | YES | `NONE` | 时间 | unix时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `reg_h5url` | `varchar(256)` | YES | `NONE` | 业务属性 | h5url | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `reg_operaid` | `varchar(511)` | NO | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `reg_phoenixid` | `varchar(512)` | NO | `NONE` | 业务属性 | Phoenix Ads click id | 允许在授权范围内做聚合分析；不输出字段值 |

### uc_user_extra

- 表类型：`BASE TABLE`；字段数：14；数据层：业务表（事实/维度待补证）。
- 业务域：用户 / 账号（`inferred_name_only`）；建议：注册、登录与生命周期聚合；禁止导出可识别身份字段。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int unsigned` | NO | `UNI` | 业务属性 | 用户唯一ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `first_name` | `varchar(64)` | YES | `NONE` | 业务属性 | first name | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `last_name` | `varchar(64)` | YES | `NONE` | 业务属性 | last name | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | [REDACTED:KYC_PERSONAL_IDENTIFIER_OR_BIOMETRIC] | `varchar(128)` | YES | `NONE` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 受限；仅脱敏聚合或伪标识下钻 |
| 6 | `bank_no` | `varchar(25)` | YES | `MUL` | 业务属性 | 银行卡号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `bank_name` | `varchar(64)` | YES | `NONE` | 业务属性 | 银行 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `ps_recipient` | `varchar(64)` | YES | `NONE` | 业务属性 | 银行code | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `last_charge` | `int unsigned` | NO | `NONE` | 业务属性 | 上次充值档位 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `last_method` | `varchar(64)` | YES | `NONE` | 业务属性 | 上次选择方式 | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `last_channel` | `varchar(64)` | YES | `NONE` | 业务属性 | 上次选择渠道 | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `create_time` | `datetime` | NO | `NONE` | 时间 | 创建时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `update_time` | `datetime` | NO | `NONE` | 时间 | 更新时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 14 | `withdraw_channel` | `varchar(64)` | YES | `NONE` | 业务属性 | 提现渠道 | 允许在授权范围内做聚合分析；不输出字段值 |

### uc_user_flag

- 表类型：`BASE TABLE`；字段数：4；数据层：业务表（事实/维度待补证）。
- 业务域：用户 / 账号（`inferred_name_only`）；建议：注册、登录与生命周期聚合；禁止导出可识别身份字段。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `bigint unsigned` | NO | `UNI` | 业务属性 | 玩家id | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `flag` | `int` | NO | `NONE` | 状态 / 枚举 | 玩家标签 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `update_at` | `bigint` | YES | `NONE` | 时间 | 时间戳 | 允许在授权范围内做聚合分析；不输出字段值 |

### user_control_list

- 表类型：`BASE TABLE`；字段数：11；数据层：业务表（事实/维度待补证）。
- 业务域：用户 / 账号（`inferred_name_only`）；建议：注册、登录与生命周期聚合；禁止导出可识别身份字段。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int unsigned` | NO | `MUL` | 业务属性 | 用户唯一ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `control_type` | `int unsigned` | NO | `NONE` | 状态 / 枚举 | 控制类型 1-黑名单 2-白名单 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `control_state` | `int unsigned` | NO | `NONE` | 时间 | 控制状态 1-控制中 2-控制完 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `coefficient` | `float(8,2) unsigned` | NO | `NONE` | 业务属性 | 获奖系数 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `target_amount` | `bigint unsigned` | NO | `NONE` | 金额 / 资产 | 目标控制数额 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `complete_amount` | `bigint unsigned` | NO | `NONE` | 金额 / 资产 | 完成控制数额 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `start_time` | `int unsigned` | NO | `NONE` | 时间 | 控制开始时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `end_time` | `int unsigned` | NO | `NONE` | 时间 | 控制结束时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `period_start` | `varchar(32)` | NO | `NONE` | 业务属性 | 每日控制时间段开始 | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `period_end` | `varchar(32)` | NO | `NONE` | 业务属性 | 每日控制时间段结束 | 允许在授权范围内做聚合分析；不输出字段值 |

### user_data

- 表类型：`BASE TABLE`；字段数：4；数据层：业务表（事实/维度待补证）。
- 业务域：用户 / 账号（`inferred_name_only`）；建议：注册、登录与生命周期聚合；禁止导出可识别身份字段。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int unsigned` | NO | `MUL` | 业务属性 | 用户唯一ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `type` | `int unsigned` | NO | `NONE` | 状态 / 枚举 | 数据类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `data` | `bigint` | NO | `NONE` | 时间 | 数据值 | 允许在授权范围内做聚合分析；不输出字段值 |

### user_data_backup

- 表类型：`BASE TABLE`；字段数：4；数据层：业务表（事实/维度待补证）。
- 业务域：用户 / 账号（`inferred_name_only`）；建议：注册、登录与生命周期聚合；禁止导出可识别身份字段。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint unsigned` | NO | `PRI` | 标识 / 关联 | 自增 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int unsigned` | NO | `MUL` | 业务属性 | 用户唯一ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `type` | `int unsigned` | NO | `NONE` | 状态 / 枚举 | 数据类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `data` | `bigint` | NO | `NONE` | 时间 | 数据值 | 允许在授权范围内做聚合分析；不输出字段值 |

### wg_coin_flips

- 表类型：`BASE TABLE`；字段数：10；数据层：业务表（事实/维度待补证）。
- 业务域：资产 / 货币（`inferred_name_only`）；建议：资产流、奖励成本、余额变化与账本对账；必须区分真金、金币和奖励资产。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint` | NO | `PRI` | 标识 / 关联 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `bigint` | NO | `MUL` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `bet_amounts` | `text` | NO | `NONE` | 金额 / 资产 | 每轮投注详情 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `win_amounts` | `text` | NO | `NONE` | 金额 / 资产 | 每次win金额详情 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `series` | `int` | NO | `NONE` | 业务属性 | 连胜次数 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `status` | `int` | NO | `NONE` | 时间 | 状态 0:初始 1:已结算 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `bet_asset` | `text` | YES | `NONE` | 游戏 / 玩法 | 投注时资产 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `create_time` | `bigint` | NO | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `update_time` | `bigint` | NO | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `flip_type` | `int` | NO | `NONE` | 状态 / 枚举 | 本局正反面 | 允许在授权范围内做聚合分析；不输出字段值 |

### wg_color_game

- 表类型：`BASE TABLE`；字段数：11；数据层：业务表（事实/维度待补证）。
- 业务域：游戏 / 对局 / RTP（`inferred_name_only`）；建议：游戏局、下注、结算、RTP 和玩法/房间拆分；需与 GAMEEND 链路核验。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint` | NO | `PRI` | 标识 / 关联 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `bigint` | NO | `MUL` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `status` | `int` | NO | `NONE` | 时间 | 1:初始 2:投注中 9:结束 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `unit_bet` | `bigint` | NO | `NONE` | 游戏 / 玩法 | 单注金额 分 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `bet_colors` | `text` | NO | `NONE` | 游戏 / 玩法 | 各颜色下注详情 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `dice_result` | `text` | NO | `NONE` | 状态 / 枚举 | 3颗骰子结果 0-5 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `total_bet_amount` | `bigint` | NO | `NONE` | 金额 / 资产 | 总下注金额 分 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `total_win_amount` | `bigint` | NO | `NONE` | 金额 / 资产 | 总返还金额 分 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `bet_asset` | `text` | YES | `NONE` | 游戏 / 玩法 | 投注时资产快照 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `create_time` | `bigint` | NO | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `update_time` | `bigint` | NO | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |

### wg_hilo_game_order_v2

- 表类型：`BASE TABLE`；字段数：25；数据层：业务表（事实/维度待补证）。
- 业务域：支付 / 提现（`inferred_name_only`）；建议：支付/提现漏斗、成功率、时延与失败码；金融金额以服务端事实复核。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint` | NO | `PRI` | 标识 / 关联 | 主键ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `game_no` | `varchar(64)` | NO | `UNI` | 游戏 / 玩法 | 游戏局号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `gid` | `bigint` | NO | `MUL` | 业务属性 | 用户GID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `active_gid` | `bigint` | YES | `UNI` | 业务属性 | 活跃局用户GID，同一用户仅允许一局 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `game_id` | `int` | NO | `NONE` | 标识 / 关联 | 游戏ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `status` | `int` | NO | `MUL` | 时间 | 状态 1:进行中 2:已提现 3:已失败 4:结算中 5:结算失败 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `bet_amount` | `bigint` | NO | `NONE` | 金额 / 资产 | 下注金额 分 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `is_recharge` | `tinyint(1)` | NO | `NONE` | 业务属性 | 下注时是否为充值用户 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `current_card_rank` | `int` | NO | `NONE` | 业务属性 | 当前牌点数 1-13 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `current_card_suit` | `int` | NO | `NONE` | 业务属性 | 当前牌花色 1-4 | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `current_multiplier` | `bigint` | NO | `NONE` | 业务属性 | 当前倍率 放大100倍 | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `offered_return_ratio` | `bigint` | NO | `NONE` | 时间 | Apollo固定倍率系数 万分比 | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `cashout_amount` | `bigint` | NO | `NONE` | 金额 / 资产 | 当前可提现金额 分 | 允许在授权范围内做聚合分析；不输出字段值 |
| 14 | `round_count` | `int` | NO | `NONE` | 业务属性 | HI/LO回合数 不含SKIP | 允许在授权范围内做聚合分析；不输出字段值 |
| 15 | `skip_count` | `int` | NO | `NONE` | 业务属性 | SKIP次数 | 允许在授权范围内做聚合分析；不输出字段值 |
| 16 | `cashout_round_no` | `int` | NO | `NONE` | 金额 / 资产 | CASH_OUT操作序号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 17 | `max_win_amount` | `bigint` | NO | `NONE` | 金额 / 资产 | 单局最大赢金 分 | 允许在授权范围内做聚合分析；不输出字段值 |
| 18 | `max_win_capped` | `tinyint(1)` | NO | `NONE` | 业务属性 | 是否触发最大赢金封顶 | 允许在授权范围内做聚合分析；不输出字段值 |
| 19 | `bet_serial` | `varchar(128)` | NO | `NONE` | 游戏 / 玩法 | 下注扣款幂等流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 20 | `payout_serial` | `varchar(128)` | YES | `NONE` | 业务属性 | 提现派奖幂等流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 21 | `bet_asset` | `text` | YES | `NONE` | 游戏 / 玩法 | 下注扣款资产回执 | 允许在授权范围内做聚合分析；不输出字段值 |
| 22 | `settle_error` | `text` | YES | `NONE` | 业务属性 | 结算异常信息 | 允许在授权范围内做聚合分析；不输出字段值 |
| 23 | `created_at` | `bigint` | NO | `NONE` | 时间 | 创建时间 Unix秒 | 允许在授权范围内做聚合分析；不输出字段值 |
| 24 | `updated_at` | `bigint` | NO | `NONE` | 时间 | 更新时间 Unix秒 | 允许在授权范围内做聚合分析；不输出字段值 |
| 25 | `ended_at` | `bigint` | NO | `NONE` | 时间 | 游戏结束时间 Unix秒 | 允许在授权范围内做聚合分析；不输出字段值 |

### wg_hilo_round_record

- 表类型：`BASE TABLE`；字段数：18；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint` | NO | `PRI` | 标识 / 关联 | 主键ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `game_no` | `varchar(64)` | NO | `MUL` | 游戏 / 玩法 | 游戏局号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `gid` | `bigint` | NO | `MUL` | 业务属性 | 用户GID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `round_no` | `int` | NO | `NONE` | 业务属性 | 操作序号 含BET/HI/LO/SKIP/CASH_OUT | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `action` | `int` | NO | `NONE` | 业务属性 | 操作类型 1:BET 2:HI 3:LO 4:SKIP 5:CASH_OUT | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `prev_card_rank` | `int` | NO | `NONE` | 业务属性 | 操作前牌点数 1-13 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `prev_card_suit` | `int` | NO | `NONE` | 业务属性 | 操作前牌花色 1-4 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `next_card_rank` | `int` | NO | `NONE` | 业务属性 | 操作后牌点数 1-13，CASH_OUT为0 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `next_card_suit` | `int` | NO | `NONE` | 业务属性 | 操作后牌花色 1-4，CASH_OUT为0 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `rule_type` | `varchar(32)` | NO | `NONE` | 状态 / 枚举 | 规则类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `compare_result` | `varchar(16)` | NO | `NONE` | 状态 / 枚举 | 点数比较结果 | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `is_win` | `tinyint(1)` | NO | `NONE` | 业务属性 | HI/LO是否命中 | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `multiplier_before` | `bigint` | NO | `NONE` | 业务属性 | 操作前倍率 放大100倍 | 允许在授权范围内做聚合分析；不输出字段值 |
| 14 | `target_multiplier` | `bigint` | NO | `NONE` | 业务属性 | 目标倍率 放大100倍 | 允许在授权范围内做聚合分析；不输出字段值 |
| 15 | `multiplier_after` | `bigint` | NO | `NONE` | 业务属性 | 操作后倍率 放大100倍 | 允许在授权范围内做聚合分析；不输出字段值 |
| 16 | `return_ratio` | `bigint` | NO | `NONE` | 时间 | 本轮兑现ReturnRatio 万分比 | 允许在授权范围内做聚合分析；不输出字段值 |
| 17 | `control_type` | `int` | NO | `NONE` | 状态 / 枚举 | 水位控制类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 18 | `created_at` | `bigint` | NO | `NONE` | 时间 | 创建时间 Unix秒 | 允许在授权范围内做聚合分析；不输出字段值 |

### wg_keno

- 表类型：`BASE TABLE`；字段数：46；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint` | NO | `PRI` | 标识 / 关联 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `bigint` | NO | `MUL` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `status` | `int` | NO | `NONE` | 时间 | 状态 1:初始 2:已扣款/结算中 9:结束 10:失败 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `order_id` | `varchar(128)` | NO | `UNI` | 标识 / 关联 | 注单ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `round_id` | `varchar(128)` | NO | `MUL` | 标识 / 关联 | 局号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `user_id` | `varchar(128)` | NO | `MUL` | 标识 / 关联 | 用户ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `game_code` | `varchar(64)` | NO | `NONE` | 游戏 / 玩法 | 游戏编码 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `difficulty` | `varchar(32)` | NO | `NONE` | 业务属性 | 难度 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `selected_numbers` | `text` | NO | `NONE` | 业务属性 | 玩家选号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `draw_numbers` | `text` | YES | `NONE` | 业务属性 | 开奖号码 | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `hit_numbers` | `text` | YES | `NONE` | 业务属性 | 命中号码 | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `pick_count` | `int` | NO | `NONE` | 业务属性 | 选号数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `hit_count` | `int` | NO | `NONE` | 业务属性 | 命中数量 | 允许在授权范围内做聚合分析；不输出字段值 |
| 14 | `bet_amount` | `bigint` | NO | `NONE` | 金额 / 资产 | 下注金额 分 | 允许在授权范围内做聚合分析；不输出字段值 |
| 15 | `multiplier` | `double` | NO | `NONE` | 业务属性 | 固定倍率 | 允许在授权范围内做聚合分析；不输出字段值 |
| 16 | `raw_payout_amount` | `bigint` | NO | `NONE` | 金额 / 资产 | 理论派彩金额 分 | 允许在授权范围内做聚合分析；不输出字段值 |
| 17 | `max_win_amount` | `bigint` | NO | `NONE` | 金额 / 资产 | 最大赢金 分 | 允许在授权范围内做聚合分析；不输出字段值 |
| 18 | `payout_amount` | `bigint` | NO | `NONE` | 金额 / 资产 | 实际派彩金额 分 | 允许在授权范围内做聚合分析；不输出字段值 |
| 19 | `payout_capped` | `tinyint(1)` | NO | `NONE` | 业务属性 | 是否封顶 | 允许在授权范围内做聚合分析；不输出字段值 |
| 20 | `capped_payout_amount` | `bigint` | NO | `NONE` | 金额 / 资产 | 封顶减少金额 分 | 允许在授权范围内做聚合分析；不输出字段值 |
| 21 | `user_net_amount` | `bigint` | NO | `NONE` | 金额 / 资产 | 用户净输赢 分 | 允许在授权范围内做聚合分析；不输出字段值 |
| 22 | `platform_net_amount` | `bigint` | NO | `NONE` | 时间 | 平台净输赢 分 | 允许在授权范围内做聚合分析；不输出字段值 |
| 23 | `currency` | `varchar(32)` | YES | `NONE` | 业务属性 | 币种 | 允许在授权范围内做聚合分析；不输出字段值 |
| 24 | `odds_version` | `varchar(128)` | YES | `NONE` | 业务属性 | 倍率版本 | 允许在授权范围内做聚合分析；不输出字段值 |
| 25 | `probability_generation_mode` | `varchar(64)` | YES | `NONE` | 时间 | 概率生成模式 | 允许在授权范围内做聚合分析；不输出字段值 |
| 26 | `probability_version` | `varchar(128)` | YES | `NONE` | 业务属性 | 概率版本 | 允许在授权范围内做聚合分析；不输出字段值 |
| 27 | `order_probability_snapshot_id` | `varchar(128)` | YES | `NONE` | 标识 / 关联 | 注单概率快照ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 28 | `probability_strategy_id` | `varchar(128)` | YES | `NONE` | 标识 / 关联 | 概率策略ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 29 | `probability_source` | `varchar(64)` | YES | `NONE` | 业务属性 | 概率来源 | 允许在授权范围内做聚合分析；不输出字段值 |
| 30 | `user_win_loss_state` | `varchar(64)` | YES | `NONE` | 时间 | 用户输赢状态 | 允许在授权范围内做聚合分析；不输出字段值 |
| 31 | `limit_version` | `varchar(128)` | YES | `NONE` | 业务属性 | 限额版本 | 允许在授权范围内做聚合分析；不输出字段值 |
| 32 | `target_rtp` | `double` | NO | `NONE` | 游戏 / 玩法 | 目标RTP | 允许在授权范围内做聚合分析；不输出字段值 |
| 33 | `calculated_rtp` | `double` | NO | `NONE` | 时间 | 理论RTP | 允许在授权范围内做聚合分析；不输出字段值 |
| 34 | `rtp_status` | `varchar(32)` | YES | `NONE` | 时间 | RTP状态 | 允许在授权范围内做聚合分析；不输出字段值 |
| 35 | `random_trace_id` | `varchar(128)` | YES | `NONE` | 标识 / 关联 | 随机追踪ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 36 | `random_value` | `bigint` | NO | `NONE` | 业务属性 | 随机值 | 允许在授权范围内做聚合分析；不输出字段值 |
| 37 | `total_weight` | `bigint` | NO | `NONE` | 业务属性 | 权重总和 | 允许在授权范围内做聚合分析；不输出字段值 |
| 38 | `weight_range` | `text` | YES | `NONE` | 业务属性 | 命中权重区间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 39 | `weight_base` | `bigint` | NO | `NONE` | 业务属性 | 权重基数快照 | 允许在授权范围内做聚合分析；不输出字段值 |
| 40 | `bet_asset` | `text` | YES | `NONE` | 游戏 / 玩法 | 下注扣款资产回执 | 允许在授权范围内做聚合分析；不输出字段值 |
| 41 | `control_type` | `int` | NO | `NONE` | 状态 / 枚举 | 水位控制类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 42 | `error_code` | `int` | NO | `NONE` | 业务属性 | 错误码 | 允许在授权范围内做聚合分析；不输出字段值 |
| 43 | `error_message` | `varchar(512)` | YES | `NONE` | 业务属性 | 错误信息 | 允许在授权范围内做聚合分析；不输出字段值 |
| 44 | `create_time` | `bigint` | NO | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 45 | `update_time` | `bigint` | NO | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 46 | `control_attempts` | `int` | NO | `NONE` | 时间 | 水位控制候选生成次数 | 允许在授权范围内做聚合分析；不输出字段值 |

### wg_limbo

- 表类型：`BASE TABLE`；字段数：13；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint` | NO | `PRI` | 标识 / 关联 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `bigint` | NO | `MUL` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `status` | `int` | NO | `NONE` | 时间 | 状态 1:初始 2:下注 9:结束 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `bet_amount` | `bigint` | NO | `NONE` | 金额 / 资产 | 下注金额 分 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `win_amount` | `bigint` | NO | `NONE` | 金额 / 资产 | 返还金额 分 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `target_multiplier` | `bigint` | NO | `NONE` | 业务属性 | 目标倍率 放大100倍 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `result_multiplier` | `bigint` | NO | `NONE` | 状态 / 枚举 | 开奖结果倍率 放大100倍 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `is_win` | `tinyint(1)` | NO | `NONE` | 业务属性 | 是否中奖 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `is_capped` | `tinyint(1)` | NO | `NONE` | 业务属性 | 是否触发最大赢金封顶 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `bet_asset` | `text` | YES | `NONE` | 游戏 / 玩法 | 投注时资产 | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `create_time` | `bigint` | NO | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `update_time` | `bigint` | NO | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `control` | `int` | NO | `NONE` | 业务属性 | 水位控制类型 | 允许在授权范围内做聚合分析；不输出字段值 |

### wg_mines_game_order_v1

- 表类型：`BASE TABLE`；字段数：22；数据层：业务表（事实/维度待补证）。
- 业务域：支付 / 提现（`inferred_name_only`）；建议：支付/提现漏斗、成功率、时延与失败码；金融金额以服务端事实复核。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint` | NO | `PRI` | 标识 / 关联 | 主键ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `game_no` | `varchar(64)` | NO | `UNI` | 游戏 / 玩法 | 游戏局号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `gid` | `bigint` | NO | `MUL` | 业务属性 | 用户GID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `active_gid` | `bigint` | YES | `UNI` | 业务属性 | 活跃局用户GID | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `client_bet_id` | `varchar(64)` | YES | `NONE` | 标识 / 关联 | Auto单轮幂等号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `auto_tile_indexes` | `text` | YES | `NONE` | 业务属性 | Auto预选格顺序 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `status` | `int` | NO | `MUL` | 时间 | 状态 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `bet_amount` | `bigint` | NO | `NONE` | 金额 / 资产 | 下注金额 分 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `mine_count` | `int` | NO | `NONE` | 业务属性 | 雷数 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `is_recharge` | `tinyint(1)` | NO | `NONE` | 业务属性 | 是否充值用户 | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `multipliers` | `text` | NO | `NONE` | 业务属性 | 倍率快照 放大100倍 | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `target_rtp` | `bigint` | NO | `NONE` | 游戏 / 玩法 | 目标RTP 万分比 | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `revealed_safe_count` | `int` | NO | `NONE` | 业务属性 | 已翻安全格数 | 允许在授权范围内做聚合分析；不输出字段值 |
| 14 | `payout_amount` | `bigint` | NO | `NONE` | 金额 / 资产 | 实际派彩金额 分 | 允许在授权范围内做聚合分析；不输出字段值 |
| 15 | `float_asset_deduct_amount` | `bigint` | NO | `NONE` | 时间 | 悬空资产扣减额 分，仅负数有效 | 允许在授权范围内做聚合分析；不输出字段值 |
| 16 | `max_asset_amount` | `bigint` | NO | `NONE` | 金额 / 资产 | 悬空资产档位 分 | 允许在授权范围内做聚合分析；不输出字段值 |
| 17 | `max_win_amount` | `bigint` | NO | `NONE` | 金额 / 资产 | 最大派彩金额 分 | 允许在授权范围内做聚合分析；不输出字段值 |
| 18 | `reveal_board` | `text` | YES | `NONE` | 业务属性 | 终局棋盘 | 允许在授权范围内做聚合分析；不输出字段值 |
| 19 | `bet_asset` | `text` | YES | `NONE` | 游戏 / 玩法 | 下注资产回执 | 允许在授权范围内做聚合分析；不输出字段值 |
| 20 | `last_control_type` | `int` | NO | `NONE` | 状态 / 枚举 | 最后水位控制类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 21 | `created_at` | `bigint` | NO | `NONE` | 时间 | 创建时间 Unix秒 | 允许在授权范围内做聚合分析；不输出字段值 |
| 22 | `ended_at` | `bigint` | NO | `NONE` | 时间 | 结束时间 Unix秒 | 允许在授权范围内做聚合分析；不输出字段值 |

### wg_mines_tile_record_v1

- 表类型：`BASE TABLE`；字段数：6；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint` | NO | `PRI` | 标识 / 关联 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `game_no` | `varchar(64)` | NO | `MUL` | 游戏 / 玩法 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `sequence` | `int` | NO | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `tile_index` | `int` | NO | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `is_safe` | `tinyint(1)` | NO | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `created_at` | `bigint` | NO | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |

### wg_plinko_ball

- 表类型：`BASE TABLE`；字段数：15；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint` | NO | `PRI` | 标识 / 关联 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `order_id` | `bigint` | NO | `MUL` | 标识 / 关联 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `ball_index` | `int` | NO | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `natural_slot_index` | `int` | NO | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `slot_index` | `int` | NO | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `multiplier` | `double` | NO | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `raw_payout_amount` | `bigint` | NO | `NONE` | 金额 / 资产 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `payout_amount` | `bigint` | NO | `NONE` | 金额 / 资产 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `payout_capped` | `tinyint(1)` | NO | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `capped_payout_amount` | `bigint` | NO | `NONE` | 金额 / 资产 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `random_value` | `bigint` | NO | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `weight_range` | `text` | NO | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `control_type` | `int` | NO | `NONE` | 状态 / 枚举 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 14 | `control_attempts` | `int` | NO | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 15 | `create_time` | `bigint` | NO | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |

### wg_plinko_order

- 表类型：`BASE TABLE`；字段数：30；数据层：业务表（事实/维度待补证）。
- 业务域：支付 / 提现（`inferred_name_only`）；建议：支付/提现漏斗、成功率、时延与失败码；金融金额以服务端事实复核。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint` | NO | `PRI` | 标识 / 关联 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `bigint` | NO | `MUL` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `client_bet_id` | `varchar(128)` | NO | `NONE` | 标识 / 关联 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `request_hash` | `varchar(64)` | NO | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `order_id` | `varchar(128)` | NO | `UNI` | 标识 / 关联 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `round_id` | `varchar(128)` | NO | `MUL` | 标识 / 关联 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `status` | `int` | NO | `MUL` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `difficulty` | `varchar(32)` | NO | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `row_count` | `int` | NO | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `ball_count` | `int` | NO | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `per_ball_bet_amount` | `bigint` | NO | `NONE` | 金额 / 资产 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `total_bet_amount` | `bigint` | NO | `NONE` | 金额 / 资产 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `total_raw_payout_amount` | `bigint` | NO | `NONE` | 金额 / 资产 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 14 | `total_payout_amount` | `bigint` | NO | `NONE` | 金额 / 资产 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 15 | `hyper_mode` | `tinyint(1)` | NO | `NONE` | 状态 / 枚举 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 16 | `max_win_amount` | `bigint` | NO | `NONE` | 金额 / 资产 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 17 | `odds_version` | `varchar(128)` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 18 | `limit_version` | `varchar(128)` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 19 | `probability_version` | `varchar(128)` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 20 | `target_rtp` | `double` | NO | `NONE` | 游戏 / 玩法 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 21 | `calculated_rtp` | `double` | NO | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 22 | `total_weight` | `bigint` | NO | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 23 | `final_weights` | `text` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 24 | `bet_asset` | `text` | YES | `NONE` | 游戏 / 玩法 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 25 | `settle_serial` | `varchar(128)` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 26 | `settle_attempts` | `int` | NO | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 27 | `error_code` | `int` | NO | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 28 | `error_message` | `varchar(512)` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 29 | `create_time` | `bigint` | NO | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 30 | `update_time` | `bigint` | NO | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |

### wg_tower_game_order_v2

- 表类型：`BASE TABLE`；字段数：31；数据层：业务表（事实/维度待补证）。
- 业务域：支付 / 提现（`inferred_name_only`）；建议：支付/提现漏斗、成功率、时延与失败码；金融金额以服务端事实复核。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint` | NO | `PRI` | 标识 / 关联 | 主键ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `game_no` | `varchar(64)` | NO | `UNI` | 游戏 / 玩法 | 游戏局号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `gid` | `bigint` | NO | `MUL` | 业务属性 | 用户GID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `active_gid` | `bigint` | YES | `UNI` | 业务属性 | 活跃局用户GID | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `client_bet_id` | `varchar(64)` | YES | `NONE` | 标识 / 关联 | AUTO单轮幂等号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `auto_cell_indexes` | `text` | YES | `NONE` | 业务属性 | AUTO每层预选格顺序 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `game_id` | `int` | NO | `NONE` | 标识 / 关联 | 游戏ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `status` | `int` | NO | `MUL` | 时间 | Tower状态 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `bet_amount` | `bigint` | NO | `NONE` | 金额 / 资产 | 下注金额 分 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `is_recharge` | `tinyint(1)` | NO | `NONE` | 业务属性 | 下注时是否充值用户 | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `difficulty` | `varchar(32)` | NO | `NONE` | 业务属性 | 难度 | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `difficulty_snapshot` | `text` | NO | `NONE` | 业务属性 | 难度配置快照JSON | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `target_rtp` | `bigint` | NO | `NONE` | 游戏 / 玩法 | 目标RTP 万分比 | 允许在授权范围内做聚合分析；不输出字段值 |
| 14 | `test_rtp` | `tinyint(1)` | NO | `NONE` | 游戏 / 玩法 | 是否为测试RTP局 | 允许在授权范围内做聚合分析；不输出字段值 |
| 15 | `current_level` | `int` | NO | `NONE` | 状态 / 枚举 | 当前或最后处理层 | 允许在授权范围内做聚合分析；不输出字段值 |
| 16 | `last_success_level` | `int` | NO | `NONE` | 状态 / 枚举 | 最后成功层 | 允许在授权范围内做聚合分析；不输出字段值 |
| 17 | `current_multiplier` | `bigint` | NO | `NONE` | 业务属性 | 当前倍率 放大100倍 | 允许在授权范围内做聚合分析；不输出字段值 |
| 18 | `cashout_amount` | `bigint` | NO | `NONE` | 金额 / 资产 | 当前可提现金额 分 | 允许在授权范围内做聚合分析；不输出字段值 |
| 19 | `payout_amount` | `bigint` | NO | `NONE` | 金额 / 资产 | 实际派彩金额 分 | 允许在授权范围内做聚合分析；不输出字段值 |
| 20 | `float_asset_deduct_amount` | `bigint` | NO | `NONE` | 时间 | 悬空资产扣减金额 分，负数有效 | 允许在授权范围内做聚合分析；不输出字段值 |
| 21 | `max_asset_amount` | `bigint` | NO | `NONE` | 金额 / 资产 | 悬空资产结算上限 分 | 允许在授权范围内做聚合分析；不输出字段值 |
| 22 | `max_win_amount` | `bigint` | NO | `NONE` | 金额 / 资产 | 单局最大赢金 分 | 允许在授权范围内做聚合分析；不输出字段值 |
| 23 | `max_win_capped` | `tinyint(1)` | NO | `NONE` | 业务属性 | 是否触发最大赢金封顶 | 允许在授权范围内做聚合分析；不输出字段值 |
| 24 | `reveal_board` | `text` | YES | `NONE` | 业务属性 | 终局揭示JSON | 允许在授权范围内做聚合分析；不输出字段值 |
| 25 | `bet_serial` | `varchar(128)` | NO | `NONE` | 游戏 / 玩法 | 下注扣款幂等流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 26 | `payout_serial` | `varchar(128)` | YES | `NONE` | 业务属性 | 派彩幂等流水号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 27 | `bet_asset` | `text` | YES | `NONE` | 游戏 / 玩法 | 下注扣款资产回执 | 允许在授权范围内做聚合分析；不输出字段值 |
| 28 | `settle_error` | `text` | YES | `NONE` | 业务属性 | 结算异常信息 | 允许在授权范围内做聚合分析；不输出字段值 |
| 29 | `created_at` | `bigint` | NO | `NONE` | 时间 | 创建时间 Unix秒 | 允许在授权范围内做聚合分析；不输出字段值 |
| 30 | `updated_at` | `bigint` | NO | `NONE` | 时间 | 更新时间 Unix秒 | 允许在授权范围内做聚合分析；不输出字段值 |
| 31 | `ended_at` | `bigint` | NO | `NONE` | 时间 | 游戏结束时间 Unix秒 | 允许在授权范围内做聚合分析；不输出字段值 |

### wg_tower_level_record

- 表类型：`BASE TABLE`；字段数：13；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint` | NO | `PRI` | 标识 / 关联 | 主键ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `game_no` | `varchar(64)` | NO | `MUL` | 游戏 / 玩法 | 游戏局号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `gid` | `bigint` | NO | `MUL` | 业务属性 | 用户GID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `level` | `int` | NO | `NONE` | 状态 / 枚举 | 层数 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `cell_index` | `int` | NO | `NONE` | 业务属性 | 所选格子 从1开始 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `is_safe` | `tinyint(1)` | NO | `NONE` | 业务属性 | 是否通过 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `probability_numerator` | `bigint` | NO | `NONE` | 时间 | 条件概率分子 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `probability_denominator` | `bigint` | NO | `NONE` | 时间 | 条件概率分母 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `random_value` | `bigint` | NO | `NONE` | 业务属性 | 安全随机值 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `multiplier` | `bigint` | NO | `NONE` | 业务属性 | 本层倍率 放大100倍 | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `return_ratio` | `bigint` | NO | `NONE` | 时间 | 本局RTP 万分比 | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `control_type` | `int` | NO | `NONE` | 状态 / 枚举 | 水位控制类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `created_at` | `bigint` | NO | `NONE` | 时间 | 创建时间 Unix秒 | 允许在授权范围内做聚合分析；不输出字段值 |

### wg_tower_report_outbox_v2

- 表类型：`BASE TABLE`；字段数：11；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint` | NO | `PRI` | 标识 / 关联 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `game_no` | `varchar(64)` | NO | `MUL` | 游戏 / 玩法 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `report_type` | `varchar(32)` | NO | `NONE` | 状态 / 枚举 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `status` | `int` | NO | `MUL` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `attempts` | `int` | NO | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `next_attempt_at` | `bigint` | NO | `MUL` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `lease_until` | `bigint` | NO | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | [REDACTED:CREDENTIAL_OR_SECRET] | `varchar(64)` | NO | `NONE` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 禁止展示、导出或进入分析产物 |
| 9 | `last_error` | `text` | YES | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `created_at` | `bigint` | NO | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `updated_at` | `bigint` | NO | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |

### wg_twist

- 表类型：`BASE TABLE`；字段数：12；数据层：业务表（事实/维度待补证）。
- 业务域：待分类（`inferred_name_only`）；建议：仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `id` | `bigint` | NO | `PRI` | 标识 / 关联 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `gid` | `int` | NO | `MUL` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `status` | `int` | NO | `NONE` | 时间 | 1:初始 2:已下注 9:已结束 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `green_prog` | `int` | NO | `NONE` | 业务属性 | 绿轨道进度 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `orange_prog` | `int` | NO | `NONE` | 业务属性 | 橙轨道进度 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `purple_prog` | `int` | NO | `NONE` | 业务属性 | 紫轨道进度 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `bet_amounts` | `text` | NO | `NONE` | 金额 / 资产 | 每轮押注额，分 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `win_amounts` | `text` | NO | `NONE` | 金额 / 资产 | 每轮赢取额，分，暗石为负值 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `symbols` | `text` | NO | `NONE` | 业务属性 | 每轮符号序列 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `bet_asset` | `text` | YES | `NONE` | 游戏 / 玩法 | 最近一次押注时资产快照 | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `create_time` | `bigint` | NO | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `update_time` | `bigint` | NO | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
