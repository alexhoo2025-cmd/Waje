#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent.parent
CLI = "/Users/robin/.local/node-v24.18.1-darwin-arm64/bin/lark-cli"
DOC_ID = "GyZddVm2powgFBxLwH0l18Qzguf"
RECEIPT = ROOT / "top_games_mapping_correction_receipt.json"

if RECEIPT.exists():
    raise SystemExit("receipt exists; refusing duplicate correction")


def call(args: list[str]) -> dict:
    env = os.environ.copy()
    env["LARKSUITE_CLI_NO_UPDATE_NOTIFIER"] = "1"
    env["LARKSUITE_CLI_NO_SKILLS_NOTIFIER"] = "1"
    result = subprocess.run([CLI, *args, "--as", "user"], cwd=PROJECT, env=env, text=True, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr[-2000:])
    payload = json.loads(result.stdout)
    if payload.get("ok") is not True:
        raise RuntimeError(json.dumps(payload, ensure_ascii=False))
    return payload


def replace(block_id: str, content: str) -> None:
    call(["docs", "+update", "--doc", DOC_ID, "--command", "block_replace", "--block-id", block_id, "--content", content])


replace(
    "doxlgPoalXEulDdz0CdGkOoLbDg",
    "<p><b>当前游戏表现：</b>Keno页面触达最大，Plinko重复进入强度最高；Limbo D1回访较高，但D1到D3衰减明显。</p>",
)
replace(
    "doxlg1HqOOIq3zmZsu3PpspH6ae",
    """
<callout emoji="💡" background-color="light-blue" border-color="blue">
  <p><b>核心发现：</b>8月21—27日Keno触达规模最大，Plinko人均页面浏览最高。Limbo D1回访最高，Plinko D3回访相对更稳；当前只能描述页面触达与应用回访关联，不能认定单款游戏提升留存。</p>
</callout>
""",
)

game_table = """
<table>
  <thead><tr><th><p>游戏</p></th><th><p>Game ID</p></th><th><p>进入游戏页的新访客</p></th><th><p>人均页面浏览</p></th><th><p>D1 / D3回访</p></th></tr></thead>
  <tbody>
    <tr><td><p>Keno</p></td><td><p>9010</p></td><td><p>271</p></td><td><p>5.51</p></td><td><p>36.4% / 13.6%</p></td></tr>
    <tr><td><p>Color Dice</p></td><td><p>9003</p></td><td><p>413</p></td><td><p>4.01</p></td><td><p>25.2% / 15.7%</p></td></tr>
    <tr><td><p>Plinko</p></td><td><p>9016</p></td><td><p>365</p></td><td background-color="light-green"><p><b>6.27</b></p></td><td background-color="light-green"><p>31.3% / <b>17.3%</b></p></td></tr>
    <tr><td><p>Limbo</p></td><td><p>9008</p></td><td><p>647</p></td><td><p>5.16</p></td><td background-color="light-green"><p><b>29.0%</b> / 13.9%</p></td></tr>
    <tr><td><p>Hilo</p></td><td><p>9011</p></td><td><p>184</p></td><td><p>4.52</p></td><td><p>34.4% / 16.7%</p></td></tr>
  </tbody>
</table>
"""
replace("doxlg46r1Hpw5aRUHVmFva0VIye", game_table)
replace(
    "doxlgiuR3Up5nHUvsOikniiG7eY",
    '<img path="@./analysis/h5_lightgame_report_reorg_2026_08_31/charts/02_新访客游戏页面触达.png" width="880" caption="8月21—27日首次访问用户的游戏页面触达；Limbo=9008，Keno=9010"/>',
)
replace(
    "doxlgAutphogvrVxuskp8V1jX5d",
    '<img path="@./analysis/h5_lightgame_report_reorg_2026_08_31/charts/03_游戏页新访客D1D3回访.png" width="880" caption="进入游戏页的新访客D1/D3应用回访；技术部GameId映射"/>',
)

replace("doxlg5quWrvTd8HO4PQe5gmGHCu", "<h2>产品定义的Top Games九款对照</h2>")
replace(
    "doxlgoXhEfS10GadZcNRT2S6bbb",
    "<p>Top Games固定为Whot、Limbo、CoinFlip、Keno、ColorDice、Hilo、Plinko、Tower和Bottle spin。下表按产品首页顺序展示，数据为8月21—27日进入对应游戏页的新访客。</p>",
)
replace(
    "doxlgVD9oN78caWkkpKhU6BfbXh",
    '<img path="@./analysis/h5_lightgame_report_reorg_2026_08_31/charts/06_GA4产品TopGames九款.png" width="880" caption="产品Top Games九款：新增访客触达"/>',
)

top_games_table = """
<table>
  <thead><tr><th><p>产品顺序</p></th><th><p>游戏/ID</p></th><th><p>新访客</p></th><th><p>页面浏览</p></th><th><p>人均浏览</p></th></tr></thead>
  <tbody>
    <tr><td><p>1</p></td><td><p>Whot（6001）</p></td><td><p>1,109</p></td><td><p>38,447</p></td><td><p>34.67</p></td></tr>
    <tr><td><p>2</p></td><td background-color="light-purple"><p><b>Limbo（9008）</b></p></td><td><p>647</p></td><td><p>3,341</p></td><td><p>5.16</p></td></tr>
    <tr><td><p>3</p></td><td><p>CoinFlip（9001）</p></td><td><p>425</p></td><td><p>3,732</p></td><td><p>8.78</p></td></tr>
    <tr><td><p>4</p></td><td background-color="light-purple"><p><b>Keno（9010）</b></p></td><td><p>270</p></td><td><p>1,492</p></td><td><p>5.53</p></td></tr>
    <tr><td><p>5</p></td><td background-color="light-purple"><p>ColorDice（9003）</p></td><td><p>413</p></td><td><p>1,658</p></td><td><p>4.01</p></td></tr>
    <tr><td><p>6</p></td><td background-color="light-purple"><p>Hilo（9011）</p></td><td><p>184</p></td><td><p>832</p></td><td><p>4.52</p></td></tr>
    <tr><td><p>7</p></td><td background-color="light-purple"><p>Plinko（9016）</p></td><td><p>365</p></td><td><p>2,287</p></td><td><p>6.27</p></td></tr>
    <tr><td><p>8</p></td><td><p>Tower（9013）</p></td><td><p>122</p></td><td><p>843</p></td><td><p>6.91</p></td></tr>
    <tr><td><p>9</p></td><td><p>Bottle spin（2003）</p></td><td><p>709</p></td><td><p>5,446</p></td><td><p>7.68</p></td></tr>
  </tbody>
</table>
"""
replace("doxlgsBs3228cotferzymc5FlQf", top_games_table)
replace(
    "doxlg29bMjyqUD3MdLg7FXajRjo",
    "<p><b>判断：</b>Top Games是产品配置分组，不是流量排名。Whot触达最大；Bottle spin排名第二；Keno页面触达高于Limbo。Whot人均页面浏览异常高，可能包含重复进入、刷新或游戏内路由，不能直接解释为局数。</p>",
)

readback = call(["docs", "+fetch", "--doc", DOC_ID, "--scope", "keyword", "--keyword", "产品定义的Top Games九款对照|Keno页面触达最大|Limbo（9008）|Keno（9010）", "--detail", "with-ids", "--format", "json"])
receipt = {
    "status": "ok",
    "revision_id": readback["data"]["document"]["revision_id"],
    "technical_source": "https://ksg964l11fam.sg.larksuite.com/wiki/ZTvowT9HOiajFHkpwFbl3RjPgub",
    "canonical_mapping": {"Limbo": "9008", "Keno": "9010"},
    "top_games": ["Whot", "Limbo", "CoinFlip", "Keno", "ColorDice", "Hilo", "Plinko", "Tower", "Bottle spin"],
    "readback": readback["data"]["document"]["content"],
}
RECEIPT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"status": "ok", "revision_id": receipt["revision_id"]}, ensure_ascii=False))
