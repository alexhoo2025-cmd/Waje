# WHOT V3.1 可见状态测试控制器

V3.1 是 V3 的独立派生实现，原 V3 日志和数据库保持只读。目标是让
6001 旧版和 9006 新版都通过同一条“观察—决策—点击—确认—结算”链路，
再进入正式 100 局实验。

## 安全边界

- 只接受 `profiles.json` 中为该版本声明的普通 Chrome 游戏来源；当前 6001 为
  `https://test-h5.wajew.com`，9006 为 `https://test-h5.wajetan.com`。
- `probe`、`dry-run` 和离线回放没有点击能力；只有显式 `run` 才开启输入。
- 识别不到规则、牌面、操作主体、倒计时、动作确认或结算字段时保持未知并停止。
- 自动托管、人工介入、未确认点击和路由/窗口变化会使本局失去正式资格。
- 不保存账号、Cookie、Token、对手名称、隐藏牌、牌堆顺序或完整网络响应。
- 测试余额只用于测试；不提供充值、提现或通过异常机制增加余额的功能。

## 命令

```sh
cd /Users/robin/Documents/wajetan_analyst/analysis/whot_test_experience_2026_09_07/v3_1
swiftc -O native.swift -o /tmp/whot-native-v3_1
python3 -B -m unittest discover -s . -p 'test_*.py' -v
python3 -B controller.py probe --game 9006
python3 -B controller.py dry-run --game 9006
```

`run` 只有在 `profiles.json` 的规则、视觉资料及认证回放回执全部通过后才可用：

```sh
python3 -B controller.py run --game 9006 --match <match-id> --seconds 30
```

当前规则/视觉资料仍未认证，所以 `run` 会故意拒绝，避免把错误点击当成测试进度。

## 数据与分析

- `migrate.py` 从 V3 只读重建 V3.1 派生库，重复执行幂等，不推定结算可见性。
- `record_observation.py` 仅用于保留结算可见但回合证据不完整的观察，自动标记为不合格。
- `accounting.py` 只有余额守恒、单位和字段语义认证后才计算 `SUM(gross_return)/SUM(stake)`。
- `shadow.py` 只生成公开状态下的候选特征，不接入线上动作，不使用隐藏牌。

当前 9006 已验证实际路由 `/game/9006-wajewhot`，并保留 1 条最低档结算观察；
该观察为胜利但 `settlement_only`，不计入正式 100 局或 RTP。
