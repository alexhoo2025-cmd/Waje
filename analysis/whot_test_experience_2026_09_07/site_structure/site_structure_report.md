# test-h5.wajew.com 网站结构盘点（WHOT 定向测试）

抓取时间：2026-09-07（本地只读抓取）  
入口：`https://test-h5.wajew.com/`  
抓取文件：[homepage.html](homepage.html)

## 1. 抓取结论

- 首页 HTML 大小约 351 KB，使用 Next.js 静态资源和客户端渲染。
- 页面包含 `data-testid="game-card"` 与稳定的 `data-game-id` 属性，适合做结构定位；不应依赖动态辅助树编号。
- 首页同时预加载多个游戏图标和分类卡片，但本次只把它们作为结构信息读取，没有进入其他游戏。
- WHOT 的稳定标识为 `data-game-id="6001"`，图标为 `NewH5Icon/6001.webp`。

## 2. 页面层级

```text
Waje H5 首页
├─ 顶部品牌/账号区
├─ 广播/中奖滚动条
├─ 游戏搜索框：Tafuta michezo
├─ 游戏分类下拉：AllGames
├─ 分类区
│  ├─ For You
│  ├─ TopGame
│  ├─ Exclusives
│  ├─ WorldCup
│  ├─ CoinGames
│  ├─ New
│  ├─ TopPicks
│  ├─ Slots
│  ├─ Fish
│  ├─ Crash
│  ├─ QuickGames
│  ├─ TaDa
│  ├─ PpGame
│  ├─ STP
│  ├─ BETSOFT
│  └─ BGaming
├─ 底部导航：Michezo / Weka pesa / Mchezo / Toa pesa / Mtumiaji
└─ 页脚：品牌、条款、隐私与责任博彩链接
```

首页静态结构中，`For You` 是混合推荐区；`Exclusives` 明确包含 WHOT，最稳定的定向入口是 `Exclusives → Whot → data-game-id=6001`。

## 3. 分类与数量盘点

| 分类 | 静态卡片数 | 说明 |
|---|---:|---|
| For You | 118 | 推荐混合区，数量高，动态排序，不适合作为自动化定位依据 |
| TopGame | 10 | 快捷游戏 |
| Exclusives | 10 | 包含 Fish、WHOT、WajeSpin 等 |
| WorldCup | 10 | 足球/体育主题 |
| CoinGames | 1 | 单独供应商/币类入口 |
| New | 10 | 新游戏 |
| TopPicks | 10 | 推荐区 |
| Slots | 10 | Slots 类 |
| Fish | 10 | 捕鱼类 |
| Crash | 10 | Crash 类 |
| QuickGames | 10 | 快速游戏 |
| TaDa | 10 | TaDa 供应商 |
| PpGame | 10 | PpGame 供应商 |
| STP | 10 | STP 供应商 |
| BETSOFT | 10 | BETSOFT 供应商 |
| BGaming | 10 | BGaming 供应商 |

## 4. WHOT 定向入口

| 字段 | 值 |
|---|---|
| 游戏名称 | WHOT / Whot Game |
| 游戏 ID | `6001` |
| 首页卡片属性 | `data-testid="game-card" data-game-id="6001"` |
| 图标资源 | `https://test-h5.wajetan.com/internal/img/NewH5Icon/6001.webp` |
| 运行路径 | `https://test-h5.wajew.com/game/6001-whot` |
| 内嵌引擎 | Cocos Creator / `whotClient` |
| 内嵌路径 | `/internal/6001/index.html?gameid=6001&domain=...&api_url=...&lan=sw` |

WHOT 运行页是 Cocos 画布，按钮和牌面文字不完整暴露在辅助树中。因此每回合必须以截图为主、辅助树为辅，并在点击后校验 URL 仍是 `game/6001-whot`。

## 5. 误触原因与修正

之前一次误进入 `game/2002-wajespin` 的原因是：首页客户端重绘后辅助树编号发生偏移，旧编号被解释成相邻游戏卡片。

后续固定流程：

1. 重新读取完整页面结构；
2. 只接受 `data-game-id=6001` 或可见的 `Whot Game` 文本/图像；
3. 点击后校验 URL 必须包含 `/game/6001-whot`；
4. 若 URL 不匹配，立即返回，不读取该游戏页面，不产生对局数据；
5. 不用 `Free` 图标、收藏图标或推荐区的旧编号作为点击目标。

## 6. 后续 WHOT 测试循环

```text
首页结构校验
→ data-game-id=6001 定位
→ URL 校验 /game/6001-whot
→ 截图读取局面
→ 公开规则下立即出牌
→ 记录机器人剩余牌数/特殊牌/回合延迟
→ 结算截图
→ 关闭提现提示（不点击）
→ 写入 round receipt
→ 下一局
```

本结构盘点只抓取首页 HTML 和公开静态资源引用，不保存账号、密码、Cookie、Token 或用户级数据，也没有点击其他游戏。
