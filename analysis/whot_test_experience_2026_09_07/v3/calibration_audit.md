# WHOT 6001 校准尝试审计

- 状态：`provisional`；尝试：14；帧：148；提交动作：7
- 正式样本：0；规则/视觉/无托管认证：均未通过；RTP：settlement_semantics_unverified

| 尝试 | 帧 | 动作 | 动作状态变化 | Lobby DAU1 点击 | 结算 | 停止原因 |
|---|---:|---:|---:|---:|---:|---|
| dau1_local_loop_02 | 19 | 0 | 0 | 0 | 0 | card_recognition_unresolved |
| dau1_local_loop_03 | 14 | 0 | 0 | 0 | 0 | card_recognition_unresolved |
| dau1_local_loop_04 | 0 | 0 | 0 | 0 | 1 | — |
| dau1_local_loop_05 | 4 | 0 | 0 | 0 | 0 | surface_changed |
| dau1_local_loop_06 | 1 | 0 | 0 | 0 | 1 | — |
| dau1_local_loop_07 | 1 | 0 | 0 | 0 | 0 | mixed_auto_play |
| dau1_local_loop_08 | 1 | 0 | 0 | 0 | 0 | mixed_auto_play |
| dau1_local_loop_09 | 2 | 0 | 0 | 0 | 0 | mixed_auto_play |
| dau1_local_loop_10 | 37 | 0 | 0 | 0 | 0 | card_recognition_unresolved |
| dau1_local_loop_11 | 10 | 7 | 0 | 0 | 0 | special_state_requires_calibration |
| dau1_local_loop_12 | 2 | 0 | 0 | 0 | 0 | special_state_requires_calibration |
| dau1_local_loop_13 | 1 | 0 | 0 | 0 | 0 | mixed_auto_play |
| dau1_local_loop_14 | 55 | 0 | 0 | 0 | 0 | card_recognition_unresolved |
| settlement_probe_01 | 1 | 0 | 0 | 0 | 1 | — |

所有结果仅为校准/机器人观察证据，不用于策略胜率或正式 RTP。
