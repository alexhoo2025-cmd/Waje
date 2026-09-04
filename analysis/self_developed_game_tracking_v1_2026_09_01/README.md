# Waje 自研游戏 H5 加载、可玩与可下注埋点上报需求 V1

本目录保留飞书需求文档的可追溯材料。

- `self_developed_game_inventory.json`：17 条自研游戏记录、P0 十款候选、P1 七款候选和 ID 冲突。
- `lark-delivery-receipt.json`：创建、迁移与回读后写入。

架构结论：当前游戏通过 iframe 接入，主框架只能观测入口和 iframe 生命周期，不能通过点击或 `iframe.onload` 推断游戏真正可玩或可下注。每个自研游戏必须接入统一桥接协议，再由主框架统一上报。
