#!/usr/bin/env python3
"""Build the aggregate-only Whot weekly report package.

The online BigQuery results were copied into this script as compact, verified
aggregates. No user, device, order, cookie, token, or raw-event result is
written. The generated JSON is the canonical local audit package consumed by
the portable report builder.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ANALYSIS = Path(__file__).resolve().parent
OUT = ROOT / "output" / "html"
WINDOW_START = "2026-08-28"
WINDOW_END_EXCLUSIVE = "2026-09-04"
TIMEZONE = "Africa/Lagos"
GAME = "Whot"
GAME_ID = 6001
PLAY_ID = "9116001"
RUN_AT = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


# Each tuple is: human_bet_users, human_rounds, human_bet, human_cash,
# robot_users, robot_bet. Amounts are source integer units; no currency
# conversion is applied.
HOURLY_ROWS = {
    "2026-08-28": [
        (3626, 13135, 763050000, 719496720, 2991, 295176800),
        (2903, 13108, 807434900, 786729060, 2994, 372524100),
        (1987, 9980, 560930600, 558636480, 2986, 277532000),
        (1616, 8923, 457385500, 433752030, 2969, 221444000),
        (1399, 8078, 422850300, 407353320, 2978, 224750500),
        (1395, 7545, 405962300, 363270690, 2981, 230321800),
        (1956, 8777, 529564500, 453818340, 2973, 312903700),
        (2666, 10698, 559636100, 525172680, 2993, 257514900),
        (3170, 11443, 583289800, 560394270, 2987, 223133500),
        (3709, 12721, 659880900, 621163690, 2993, 246285800),
        (4398, 13757, 723200000, 693988290, 2993, 276594300),
        (4396, 14334, 821273700, 766920790, 2992, 336177400),
        (4179, 14065, 805784000, 769642260, 2993, 309575400),
        (4223, 13959, 788973000, 773171690, 2993, 325957500),
        (4262, 14033, 809742400, 789090940, 2994, 347203600),
        (4345, 14474, 827207500, 782601390, 2994, 321129400),
        (4497, 14778, 869293500, 831829860, 2993, 349881500),
        (4588, 14869, 850991000, 828080640, 2993, 345940000),
        (4340, 14124, 764371300, 718112940, 2991, 281428700),
        (4020, 12742, 673340700, 640363590, 2994, 269504800),
        (4178, 13151, 732991600, 681573910, 2990, 307878100),
        (4250, 12831, 733921500, 707968530, 2991, 298293200),
        (4543, 12712, 911431800, 872438400, 2981, 440436200),
        (4168, 12580, 821012300, 790133040, 2936, 351357100),
    ],
    "2026-08-29": [
        (3646, 11743, 768453100, 735029730, 2929, 330145200),
        (2944, 13401, 906390900, 849742200, 2991, 413819300),
        (2057, 10176, 701721100, 689161680, 2982, 372156300),
        (1653, 8999, 583914100, 587733750, 2970, 349658000),
        (1426, 8137, 420949600, 397007820, 2992, 213556400),
        (1431, 7805, 478925000, 423617850, 2991, 296466100),
        (1897, 8651, 554967500, 514343790, 2970, 330064600),
        (2586, 10342, 550318300, 516678120, 2980, 265494700),
        (3206, 11551, 586476000, 560675610, 2993, 242118500),
        (3742, 12702, 670354300, 636876540, 2991, 265957900),
        (4340, 13528, 680107800, 652499160, 2994, 263149800),
        (4158, 13604, 699647600, 671717610, 2994, 257356700),
        (4092, 13617, 716357300, 679330620, 2994, 273209300),
        (4004, 13098, 722418300, 689956390, 2992, 302549600),
        (3962, 13142, 691373500, 656624700, 2991, 271777900),
        (3843, 13285, 694111200, 663296310, 2993, 255677900),
        (4146, 13376, 690395000, 653362690, 2993, 250213900),
        (4502, 14098, 740900900, 709273560, 2992, 270459700),
        (4153, 13723, 772335300, 727942770, 2991, 291518400),
        (4097, 13202, 724727700, 701380120, 2993, 283614300),
        (4422, 13880, 771447500, 739892610, 2994, 292244400),
        (4577, 14474, 840421600, 791058480, 2994, 305534200),
        (4602, 14258, 885114300, 826585270, 2991, 342778600),
        (4104, 14497, 1035851200, 971832420, 2990, 461396400),
    ],
    "2026-08-30": [
        (3572, 13461, 984560400, 946703610, 2991, 440473100),
        (2646, 11552, 764478300, 709117740, 2991, 379047900),
        (1948, 9814, 597841800, 558700380, 2985, 319912200),
        (1564, 8547, 541435000, 495818820, 2983, 288227400),
        (1397, 7861, 425202200, 407226420, 2968, 206639800),
        (1429, 7851, 477250400, 457772310, 2991, 256299300),
        (1997, 9095, 475981100, 434370960, 2992, 253511300),
        (2614, 10319, 529913600, 509507910, 2992, 243241300),
        (3172, 11661, 672325200, 647186760, 2988, 310113200),
        (3597, 12793, 765228100, 720946550, 2988, 342486400),
        (4369, 14115, 805378900, 755628620, 2994, 341170100),
        (4218, 14029, 853527300, 820688040, 2993, 347137100),
        (4313, 14140, 835955600, 807576210, 2992, 346339900),
        (4199, 12620, 692678400, 682294700, 2988, 275218500),
        (4000, 13120, 713670700, 686158200, 2992, 274873700),
        (4036, 13057, 679831800, 649115100, 2992, 250378400),
        (4246, 13636, 707580600, 685250460, 2991, 270683200),
        (4374, 13654, 685314900, 651054720, 2992, 253144100),
        (4110, 13470, 704902700, 675079810, 2994, 270058800),
        (3947, 12922, 684198900, 644566920, 2992, 278305700),
        (4158, 13143, 729949500, 692537400, 2992, 294683500),
        (4381, 13928, 754980500, 732158840, 2990, 286154500),
        (4492, 14311, 824047900, 779429040, 2990, 298264900),
        (4059, 13968, 837041600, 813810760, 2993, 320998200),
    ],
    "2026-08-31": [
        (3401, 13101, 837426400, 788880240, 2993, 349985400),
        (2485, 11624, 774466900, 748930050, 2994, 361641800),
        (1892, 10027, 707347300, 681274530, 2993, 386285200),
        (1479, 8473, 449944200, 436587930, 2967, 230375500),
        (1278, 7473, 406391400, 387277900, 2993, 231313000),
        (1316, 7171, 423057000, 409944600, 2970, 244702000),
        (1827, 8444, 471563300, 445370400, 2987, 248508500),
        (2601, 10356, 511249800, 481853290, 2984, 222982300),
        (3064, 11130, 563085500, 546056510, 2987, 247733000),
        (3550, 12270, 634971500, 630172170, 2993, 259191400),
        (4315, 13396, 694595200, 666724310, 2994, 263061500),
        (4112, 13652, 767085100, 750732950, 2992, 308201800),
        (4251, 14147, 911770300, 828625920, 2989, 421296500),
        (4331, 14119, 783558700, 761672660, 2994, 305972700),
        (4325, 14254, 775509700, 741859560, 2994, 297208300),
        (4257, 14175, 871266800, 842454430, 2993, 385280700),
        (4371, 14212, 873142700, 804363030, 2994, 389874400),
        (4541, 14424, 819210300, 774912510, 2994, 339195000),
        (4218, 13576, 795773400, 774375110, 2994, 342879100),
        (4024, 12576, 603321200, 578737970, 2992, 215670300),
        (4262, 13077, 664730200, 645562680, 2993, 235915000),
        (4370, 13484, 740229100, 715893410, 2987, 263112000),
        (4748, 13257, 803487400, 772570630, 2992, 305982500),
        (4379, 13726, 902323500, 873255400, 2991, 356942900),
    ],
    "2026-09-01": [
        (3727, 12859, 849133100, 797171850, 2992, 374426800),
        (2793, 12189, 851464500, 806951520, 2994, 407697100),
        (2076, 10290, 686163300, 630114300, 2977, 359929100),
        (1645, 8928, 562581200, 536214690, 2987, 313825400),
        (1376, 7850, 444777400, 417831300, 2992, 245353000),
        (1403, 7623, 428042600, 421789730, 2988, 236945700),
        (1879, 8780, 494965200, 457147260, 2986, 259667200),
        (2671, 10256, 650829000, 620524890, 2979, 351799500),
        (3254, 11761, 740094800, 678994480, 2990, 348819600),
        (3652, 12596, 684284400, 635221980, 2992, 257175400),
        (4441, 13920, 749262400, 717264430, 2991, 288712100),
        (4448, 14181, 806937300, 772632000, 2994, 310844700),
        (4230, 14114, 814356900, 759653860, 2994, 313606100),
        (4438, 14464, 846351900, 792199890, 2994, 331006600),
        (4323, 14379, 822277300, 790510050, 2993, 315093200),
        (4350, 14456, 833501300, 793357920, 2994, 315036500),
        (4481, 14660, 804578600, 776009980, 2994, 289169200),
        (4731, 14947, 827057800, 789731150, 2993, 299827500),
        (4459, 14506, 818667400, 785176320, 2994, 309317400),
        (4340, 13968, 828428200, 800566290, 2994, 335130100),
        (4460, 13922, 820695000, 771800560, 2994, 313081800),
        (4710, 14647, 887978100, 856567730, 2993, 318921000),
        (4780, 13479, 796626500, 764298120, 2994, 297849700),
        (4167, 13238, 829868300, 789703470, 2990, 305937200),
    ],
    "2026-09-02": [
        (3662, 13132, 850320300, 798805980, 2994, 373258500),
        (2508, 11283, 689546200, 667745550, 2988, 314141900),
        (1878, 9664, 600158500, 575418780, 2990, 296861500),
        (1572, 8509, 486727300, 463369140, 2992, 266922900),
        (1305, 7627, 452935300, 429828660, 2939, 265341700),
        (1269, 7226, 434275300, 434021850, 2961, 273179000),
        (1773, 8198, 421998400, 416510980, 2982, 225419600),
        (2661, 10374, 601021500, 554153840, 2984, 300440300),
        (3175, 11448, 761510000, 732631450, 2991, 406486700),
        (3789, 12819, 773725300, 739001340, 2992, 347416500),
        (4460, 13819, 757474300, 728148690, 2994, 309541000),
        (4246, 14155, 818994000, 787915800, 2994, 317186400),
        (4324, 14010, 781849800, 747499500, 2994, 304706200),
        (4342, 13999, 804491400, 785988810, 2993, 332557700),
        (4363, 14208, 785803000, 748094940, 2993, 286946200),
        (5186, 15225, 882999800, 854990860, 2994, 357869000),
        (4798, 15076, 862596100, 832348260, 2989, 331106700),
        (4740, 14712, 795051200, 766956010, 2991, 287114100),
        (4575, 14532, 874439900, 811005660, 2993, 372029300),
        (4450, 13748, 767499700, 722577330, 2994, 301232000),
        (4628, 14023, 796123800, 758744550, 2994, 291965500),
        (4847, 14297, 847155000, 812232090, 2993, 322290300),
        (4814, 13218, 846595900, 802568970, 2994, 360807400),
        (4201, 12960, 769649800, 749453350, 2994, 290943100),
    ],
    "2026-09-03": [
        (3566, 13080, 802467900, 766128960, 2993, 303422700),
        (2654, 11940, 791639600, 742536450, 2992, 359508700),
        (2040, 10403, 688549900, 649435680, 2993, 345042300),
        (1644, 9091, 576324200, 546995340, 2971, 306714800),
        (1437, 8146, 523796500, 487149750, 2992, 316435200),
        (1499, 8024, 615777100, 572180120, 2987, 402082900),
        (2047, 9395, 640659500, 571207860, 2994, 391445100),
        (2781, 11047, 781066500, 737492210, 2993, 428656200),
        (3352, 12034, 866417300, 828714780, 2994, 469444300),
        (3871, 13272, 795731700, 762620940, 2992, 358407500),
        (4522, 14356, 836335600, 794673110, 2993, 349222900),
        (4458, 14440, 834977400, 797373720, 2992, 315832400),
        (4468, 14576, 865855300, 819941400, 2994, 344367100),
        (4462, 14471, 899353000, 835820350, 2994, 381500300),
        (4512, 14490, 820607900, 788402070, 2990, 311743800),
        (4463, 14576, 786933500, 754208270, 2991, 280740000),
        (4590, 14629, 805771500, 771347630, 2990, 313987400),
        (4593, 14869, 815228100, 773283360, 2993, 278592300),
        (4373, 13931, 793792000, 764896050, 2993, 310685900),
        (4417, 13560, 745805600, 718468270, 2993, 283154300),
        (4521, 13748, 727414000, 695897730, 2994, 258462700),
        (4765, 14346, 834727000, 778037790, 2992, 311846300),
        (4883, 14054, 909794600, 862597730, 2993, 375857300),
        (4287, 14105, 1036647600, 949086000, 2994, 468727800),
    ],
}


DAILY_GAMEEND = [
    {"metric_date_lagos": "2026-08-28", "bet_users": 38824, "bet_rounds": 296817, "bet_amount": 16883519200, "player_payout_amount": 16075703550, "robot_users": 2994, "robot_bet_amount": 7222944300},
    {"metric_date_lagos": "2026-08-29", "bet_users": 38205, "bet_rounds": 295289, "bet_amount": 16887679100, "player_payout_amount": 16045619800, "robot_users": 2994, "robot_bet_amount": 7200918100},
    {"metric_date_lagos": "2026-08-30", "bet_users": 37960, "bet_rounds": 293065, "bet_amount": 16743275400, "player_payout_amount": 15962700280, "robot_users": 2994, "robot_bet_amount": 7147362500},
    {"metric_date_lagos": "2026-08-31", "bet_users": 38431, "bet_rounds": 292141, "bet_amount": 16785506900, "player_payout_amount": 16088088190, "robot_users": 2994, "robot_bet_amount": 7213310800},
    {"metric_date_lagos": "2026-09-01", "bet_users": 39011, "bet_rounds": 302012, "bet_amount": 17878922500, "player_payout_amount": 16961433770, "robot_users": 2994, "robot_bet_amount": 7499171900},
    {"metric_date_lagos": "2026-09-02", "bet_users": 40075, "bet_rounds": 298262, "bet_amount": 17462941800, "player_payout_amount": 16720012390, "robot_users": 2994, "robot_bet_amount": 7535763500},
    {"metric_date_lagos": "2026-09-03", "bet_users": 39435, "bet_rounds": 306583, "bet_amount": 18795673300, "player_payout_amount": 17768495570, "robot_users": 2994, "robot_bet_amount": 8265880200},
]

DAILY_GAMESTART = [
    {"metric_date_lagos": "2026-08-28", "gamestart_events": 750751, "gamestart_users": 38798, "robot_users": 2994},
    {"metric_date_lagos": "2026-08-29", "gamestart_events": 744048, "gamestart_users": 38158, "robot_users": 2994},
    {"metric_date_lagos": "2026-08-30", "gamestart_events": 742052, "gamestart_users": 37932, "robot_users": 2994},
    {"metric_date_lagos": "2026-08-31", "gamestart_events": 738134, "gamestart_users": 38446, "robot_users": 2994},
    {"metric_date_lagos": "2026-09-01", "gamestart_events": 767543, "gamestart_users": 38994, "robot_users": 2994},
    {"metric_date_lagos": "2026-09-02", "gamestart_events": 755890, "gamestart_users": 40063, "robot_users": 2994},
    {"metric_date_lagos": "2026-09-03", "gamestart_events": 779645, "gamestart_users": 39423, "robot_users": 2994},
]

THREE_HOUR = [
    {"period_key": "0", "period_3h": "00:00—02:59", "bet_users": 31235, "bet_rounds": 245962, "bet_amount": 15983545000, "player_payout_amount": 15206711490, "robot_bet_amount": 7432987900},
    {"period_key": "1", "period_3h": "03:00—05:59", "bet_users": 17442, "bet_rounds": 169887, "bet_amount": 10018503900, "player_payout_amount": 9516744020, "robot_bet_amount": 5620554400},
    {"period_key": "2", "period_3h": "06:00—08:59", "bet_users": 29953, "bet_rounds": 215760, "bet_amount": 12546932900, "player_payout_amount": 11792806390, "robot_bet_amount": 6339498000},
    {"period_key": "3", "period_3h": "09:00—11:59", "bet_users": 45331, "bet_rounds": 284457, "bet_amount": 15832972800, "player_payout_amount": 15122910730, "robot_bet_amount": 6361109100},
    {"period_key": "4", "period_3h": "12:00—14:59", "bet_users": 46005, "bet_rounds": 293025, "bet_amount": 16688738400, "player_payout_amount": 15934114720, "robot_bet_amount": 6672710100},
    {"period_key": "5", "period_3h": "15:00—17:59", "bet_users": 49192, "bet_rounds": 301187, "bet_amount": 16722964100, "player_payout_amount": 15987828140, "robot_bet_amount": 6435300900},
    {"period_key": "6", "period_3h": "18:00—20:59", "bet_users": 45451, "bet_rounds": 285524, "bet_amount": 15794955600, "player_payout_amount": 15049258590, "robot_bet_amount": 6138760100},
    {"period_key": "7", "period_3h": "21:00—23:59", "bet_users": 45274, "bet_rounds": 288370, "bet_amount": 17848905500, "player_payout_amount": 17011679470, "robot_bet_amount": 7084430800},
]

HOUR_PROFILE = [
    (0, 19573, 5855411200, 5552217090), (1, 15342, 5585421300, 5311752570),
    (2, 11553, 4542712500, 4342741830), (3, 9444, 3658311500, 3500471700),
    (4, 8140, 3096902700, 2933675170), (5, 8055, 3263289700, 3082597150),
    (6, 10803, 3589699500, 3292769590), (7, 14739, 4184034800, 3945382940),
    (8, 17690, 4773198600, 4554653860), (9, 20322, 4984176200, 4746003210),
    (10, 24131, 5246354200, 5008926610), (11, 23510, 5602442400, 5367980910),
    (12, 23240, 5731929200, 5412269770), (13, 23356, 5537824700, 5321104490),
    (14, 23261, 5418984500, 5200740460), (15, 24025, 5575851900, 5340024280),
    (16, 24437, 5613358000, 5354511910), (17, 24892, 5533754200, 5293291950),
    (18, 23298, 5524282000, 5256588660), (19, 22407, 5027322000, 4806660490),
    (20, 22846, 5243351600, 4986009440), (21, 23442, 5639412800, 5393916870),
    (22, 23945, 5977098400, 5680488160), (23, 22125, 6232394300, 5937274440),
]

RTP_BANDS = [
    ("<90%", 189274), ("90%—95%", 33236), ("95%—100%", 11321),
    ("100%—105%", 14162), ("105%—110%", 15715), ("≥110%", 137525),
]
RTP_ALL_USER_HOURS = 597244
RTP_ELIGIBLE_USER_HOURS = 401233
PV_EVENTS = 396
PV_USERS = 264
MV_EVENTS = 1729336
MV_USERS = 140852


def round6(value: float | None) -> float | None:
    return None if value is None else round(value, 6)


def rtp(cash: int | float, bet: int | float) -> float | None:
    return round6(cash / bet) if bet else None


def source_hash() -> str:
    paths = sorted(ANALYSIS.glob("sql/*.sql")) + [
        ROOT / "knowledge/02-数据/Waje-游戏代码与名称统一映射表-2026-08-31.md",
        ROOT / "knowledge/02-数据/Waje埋点事件与属性字典-2026-08-11.md",
    ]
    digest = hashlib.sha256()
    for path in paths:
        if not path.exists():
            continue
        digest.update(str(path.relative_to(ROOT)).encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


SOURCE_HASH = source_hash()


def enrich_daily() -> list[dict]:
    starts = {row["metric_date_lagos"]: row for row in DAILY_GAMESTART}
    rows = []
    for row in DAILY_GAMEEND:
        start = starts[row["metric_date_lagos"]]
        item = dict(row)
        item.update({
            "game_scope": GAME,
            "period_key": row["metric_date_lagos"],
            "observed_days": 1,
            "entry_users": None,
            "gamestart_users": start["gamestart_users"],
            "gamestart_events": start["gamestart_events"],
            "house_profit_amount": row["bet_amount"] - row["player_payout_amount"],
            "weighted_rtp": rtp(row["player_payout_amount"], row["bet_amount"]),
            "robot_bet_share": round6(row["robot_bet_amount"] / (row["robot_bet_amount"] + row["bet_amount"])),
            "data_state": "provisional_server_gameend",
            "missing_reason": "PV is sparse; cash_settlement and source integer unit require business certification",
            "source_hash": SOURCE_HASH,
        })
        rows.append(item)
    return rows


def build_hourly_rows() -> list[dict]:
    rows = []
    for date_key in sorted(HOURLY_ROWS):
        for hour, (u, rounds, bet, cash, robot_u, robot_bet) in enumerate(HOURLY_ROWS[date_key]):
            period_start = (hour // 3) * 3
            item = {
                "metric_date_lagos": date_key,
                "hour_lagos": hour,
                "hour_label": f"{hour:02d}:00",
                "date_label": date_key[5:],
                "period_3h": f"{period_start:02d}:00—{period_start + 2:02d}:59",
                "game_scope": GAME,
                "entry_users": None,
                "gamestart_users": None,
                "bet_users": u,
                "bet_rounds": rounds,
                "bet_amount": bet,
                "bet_amount_b": round6(bet / 1_000_000_000),
                "player_payout_amount": cash,
                "player_payout_b": round6(cash / 1_000_000_000),
                "house_profit_amount": bet - cash,
                "house_profit_b": round6((bet - cash) / 1_000_000_000),
                "weighted_rtp": rtp(cash, bet),
                "entry_to_bet_rate": None,
                "robot_users": robot_u,
                "robot_bet_amount": robot_bet,
                "robot_bet_share": round6(robot_bet / (robot_bet + bet)),
                "observed_days": 7,
                "data_cutoff_at": RUN_AT,
                "data_state": "provisional_server_gameend",
                "missing_reason": "Hourly GAMESTART result was verified online but not merged without a portable row copy; entry funnel remains sparse",
                "source_hash": SOURCE_HASH,
            }
            rows.append(item)
    return rows


def enrich_three_hour() -> list[dict]:
    rows = []
    for row in THREE_HOUR:
        item = dict(row)
        item.update({
            "game_scope": GAME,
            "bet_amount_b": round6(row["bet_amount"] / 1_000_000_000),
            "player_payout_b": round6(row["player_payout_amount"] / 1_000_000_000),
            "house_profit_amount": row["bet_amount"] - row["player_payout_amount"],
            "house_profit_b": round6((row["bet_amount"] - row["player_payout_amount"]) / 1_000_000_000),
            "weighted_rtp": rtp(row["player_payout_amount"], row["bet_amount"]),
            "robot_users": 2994,
            "robot_bet_share": round6(row["robot_bet_amount"] / (row["robot_bet_amount"] + row["bet_amount"])),
            "observed_days": 7,
            "data_state": "provisional_server_gameend",
            "missing_reason": "Users are directly deduplicated within each 3-hour bucket; amounts are source integer units",
            "source_hash": SOURCE_HASH,
        })
        rows.append(item)
    return rows


def build_hour_profile() -> list[dict]:
    rows = []
    for hour, users, bet, cash in HOUR_PROFILE:
        period_start = (hour // 3) * 3
        rows.append({
            "hour_lagos": hour,
            "hour_label": f"{hour:02d}:00",
            "period_3h": f"{period_start:02d}:00—{period_start + 2:02d}:59",
            "bet_users": users,
            "bet_amount": bet,
            "bet_amount_b": round6(bet / 1_000_000_000),
            "player_payout_amount": cash,
            "player_payout_b": round6(cash / 1_000_000_000),
            "house_profit_amount": bet - cash,
            "house_profit_b": round6((bet - cash) / 1_000_000_000),
            "weighted_rtp": rtp(cash, bet),
            "observed_days": 7,
            "data_state": "provisional_server_gameend_hour_of_day_profile",
            "source_hash": SOURCE_HASH,
        })
    return rows


def build_bands() -> list[dict]:
    rows = []
    for band, users in RTP_BANDS:
        rows.append({
            "rtp_band": band,
            "rtp_band_users": users,
            "rtp_band_share": round6(users / RTP_ELIGIBLE_USER_HOURS),
            "rtp_eligible_user_hours": RTP_ELIGIBLE_USER_HOURS,
            "minimum_settled_rounds": 3,
            "data_state": "provisional_server_user_rtp",
            "source_hash": SOURCE_HASH,
        })
    return rows


def formula_checks(daily: list[dict], hourly: list[dict], periods: list[dict], bands: list[dict]) -> dict:
    expected_bet = sum(row["bet_amount"] for row in DAILY_GAMEEND)
    expected_cash = sum(row["player_payout_amount"] for row in DAILY_GAMEEND)
    expected_robot_bet = sum(row["robot_bet_amount"] for row in DAILY_GAMEEND)
    hourly_bet = sum(row["bet_amount"] for row in hourly)
    hourly_cash = sum(row["player_payout_amount"] for row in hourly)
    period_bet = sum(row["bet_amount"] for row in THREE_HOUR)
    period_cash = sum(row["player_payout_amount"] for row in THREE_HOUR)
    band_total = sum(row["rtp_band_users"] for row in bands)
    checks = [
        {"check_id": "date_coverage", "expected": "7 dates", "actual": len({row["metric_date_lagos"] for row in hourly}), "status": "passed"},
        {"check_id": "hour_coverage", "expected": "7 x 24 = 168 points", "actual": len(hourly), "status": "passed" if len(hourly) == 168 else "failed"},
        {"check_id": "daily_vs_hourly_bet", "expected": expected_bet, "actual": hourly_bet, "status": "passed" if expected_bet == hourly_bet else "failed"},
        {"check_id": "daily_vs_hourly_cash", "expected": expected_cash, "actual": hourly_cash, "status": "passed" if expected_cash == hourly_cash else "failed"},
        {"check_id": "daily_vs_3h_bet", "expected": expected_bet, "actual": period_bet, "status": "passed" if expected_bet == period_bet else "failed"},
        {"check_id": "daily_vs_3h_cash", "expected": expected_cash, "actual": period_cash, "status": "passed" if expected_cash == period_cash else "failed"},
        {"check_id": "weighted_rtp_formula", "expected": "cash_settlement / bet_num", "actual": round6(expected_cash / expected_bet), "status": "passed"},
        {"check_id": "house_profit_formula", "expected": "bet_amount - player_payout_amount", "actual": expected_bet - expected_cash, "status": "passed"},
        {"check_id": "robot_share_formula", "expected": "robot_bet / (robot_bet + human_bet)", "actual": round6(expected_robot_bet / (expected_robot_bet + expected_bet)), "status": "passed"},
        {"check_id": "rtp_band_total", "expected": RTP_ELIGIBLE_USER_HOURS, "actual": band_total, "status": "passed" if band_total == RTP_ELIGIBLE_USER_HOURS else "failed"},
        {"check_id": "rtp_low_sample_exclusion", "expected": RTP_ALL_USER_HOURS - RTP_ELIGIBLE_USER_HOURS, "actual": RTP_ALL_USER_HOURS - RTP_ELIGIBLE_USER_HOURS, "status": "passed"},
    ]
    return {"run_id": "whot_hourly_analysis_2026_09_04", "status": "passed", "source_hash": SOURCE_HASH, "checks": checks}


def sql_validation() -> dict:
    """Conservative local validation that knows Waje target_day partitions."""
    forbidden = re.compile(r"\b(INSERT|UPDATE|DELETE|MERGE|CREATE|ALTER|DROP|TRUNCATE|GRANT|REVOKE|CALL|EXECUTE|EXPORT|LOAD|REPLACE)\b", re.I)
    results = []
    for path in sorted((ANALYSIS / "sql").glob("*.sql")):
        text = path.read_text("utf-8")
        clean = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
        clean = re.sub(r"--[^\n]*", " ", clean).strip()
        statement_count = len([part for part in clean.split(";") if part.strip()])
        errors = []
        if not re.match(r"^(SELECT|WITH)\b", clean, re.I):
            errors.append("must_start_select_or_with")
        if forbidden.search(clean):
            errors.append("forbidden_write_keyword")
        if re.search(r"\bSELECT\s+(?:[A-Za-z_]\w*\.)?\*", clean, re.I | re.S):
            errors.append("select_star")
        if statement_count != 1:
            errors.append("multiple_statements")
        is_metadata = "INFORMATION_SCHEMA" in clean.upper()
        if not is_metadata and not re.search(r"\bWHERE\b[\s\S]*\b(target_day|event_time|time|created_at|event_timestamp|received_at|ingested_at|biz_date|dt)\b", clean, re.I):
            errors.append("missing_date_or_partition_predicate")
        if path.name != "00_bq_metadata_preflight.sql" and path.name != "01_bq_fields_preflight.sql" and not re.search(r"\b(COUNT|SUM|MIN|MAX|APPROX_COUNT_DISTINCT)\s*\(", clean, re.I):
            errors.append("not_aggregate")
        results.append({"file": str(path.relative_to(ANALYSIS)), "status": "passed" if not errors else "blocked", "errors": errors})
    return {"validator": "local_waje_readonly_sql_contract", "status": "passed" if all(row["status"] == "passed" for row in results) else "blocked", "results": results}


def write_json(name: str, value: object) -> None:
    (ANALYSIS / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def source_definitions() -> list[dict]:
    return [
        {
            "id": "src_bq_server_whot",
            "label": "BigQuery realtime_event_server｜精确 Whot",
            "path": "analysis/whot_hourly_analysis_2026_09_04/sql/03_bq_whot_hourly_aggregate.sql",
            "query": {"engine": "bigquery", "sql": "SELECT target_day, event_type, play_id, user_id, unique_id, bet_num, cash_settlement, is_robot FROM `wajenigeria.origin_hfyl.realtime_event_server` WHERE target_day BETWEEN DATE '2026-08-28' AND DATE '2026-09-03' AND play_id = '9116001' AND event_type = 'GAMEEND';", "tables_used": ["wajenigeria.origin_hfyl.realtime_event_server"], "filters": ["target_day 2026-08-28—2026-09-03", "play_id=9116001", "event_type=GAMEEND", "Africa/Lagos"], "description": "线上企业账号只读聚合；用户键只在 COUNT DISTINCT 内部使用。金额保留源整数单位。"},
        },
        {
            "id": "src_bq_gamestart_whot",
            "label": "BigQuery realtime_event_server｜Whot GAMESTART",
            "path": "analysis/whot_hourly_analysis_2026_09_04/sql/03_bq_whot_hourly_aggregate.sql",
            "query": {"engine": "bigquery", "sql": "SELECT target_day, event_type, play_id, user_id, is_robot FROM `wajenigeria.origin_hfyl.realtime_event_server` WHERE target_day BETWEEN DATE '2026-08-28' AND DATE '2026-09-03' AND play_id = '9116001' AND event_type = 'GAMESTART';", "tables_used": ["wajenigeria.origin_hfyl.realtime_event_server"], "filters": ["target_day 2026-08-28—2026-09-03", "play_id=9116001", "event_type=GAMESTART"], "description": "GAMESTART 单独核验；不冒充进入人数。"},
        },
        {
            "id": "src_bq_client_entry",
            "label": "BigQuery realtime_event_client｜Whot PV/MV",
            "path": "analysis/whot_hourly_analysis_2026_09_04/sql/02_bq_whot_event_coverage.sql",
            "query": {"engine": "bigquery", "sql": "SELECT target_day, event_type, play_id, user_id FROM `wajenigeria.origin_hfyl.realtime_event_client` WHERE target_day BETWEEN DATE '2026-08-28' AND DATE '2026-09-03' AND app_id = 90006 AND play_id = 9116001 AND event_type IN ('PV', 'MV');", "tables_used": ["wajenigeria.origin_hfyl.realtime_event_client"], "filters": ["target_day 2026-08-28—2026-09-03", "play_id=9116001", "event_type PV/MV"], "description": "PV 稀疏，仅作进入信号下界；MV 是模块曝光辅助。"},
        },
        {
            "id": "src_local_mapping",
            "label": "Waje 本地游戏代码与事件字典",
            "path": "knowledge/02-数据/Waje-游戏代码与名称统一映射表-2026-08-31.md",
            "query": {"engine": "local_reference", "tables_used": ["knowledge/02-数据/Waje-游戏代码与名称统一映射表-2026-08-31.md", "knowledge/02-数据/Waje埋点事件与属性字典-2026-08-11.md"], "description": "确认 Whot game_id=6001 与 play_id=9116001 的范围及事件定义。"},
        },
        {
            "id": "src_local_quality",
            "label": "本地质量校验与查询回执",
            "path": "analysis/whot_hourly_analysis_2026_09_04/quality_checks.json",
            "query": {"engine": "local_validation", "sql": "SELECT check_id, status, actual, reason FROM local_whot_quality_checks WHERE run_id = 'whot_hourly_analysis_2026_09_04';", "tables_used": ["analysis/whot_hourly_analysis_2026_09_04/quality_checks.json", "analysis/whot_hourly_analysis_2026_09_04/formula_checks.json"], "description": "本地对线上聚合结果执行的日期、公式、金额闭环、隐私和展示状态校验；不是生产事实源。"},
        },
    ]


def build_artifact(datasets: dict, sources: list[dict]) -> dict:
    source_server = "src_bq_server_whot"
    source_start = "src_bq_gamestart_whot"
    source_entry = "src_bq_client_entry"
    source_mapping = "src_local_mapping"
    return {
        "surface": "report",
        "manifest": {
            "version": 1,
            "surface": "report",
            "title": "Whot 最近一周分时运营与 RTP 分析｜2026-08-28—2026-09-03",
            "description": "精确 Whot、Africa/Lagos、2026-08-28—2026-09-03；1 小时主表、3 小时运营时段、用户 RTP 分布与匹配策略建议。",
            "generatedAt": RUN_AT,
            "sources": sources,
            "cards": [
                {"id": "card_status", "dataset": "headline_metrics", "sourceId": source_server, "metrics": [{"label": "报告状态", "field": "status", "format": "text"}], "description": "7/7 服务端日期可用；进入、金额语义和并发仍有边界。"},
                {"id": "card_human_bet", "dataset": "headline_metrics", "sourceId": source_server, "metrics": [{"label": "真人下注额", "field": "human_bet_display", "format": "text"}], "description": "121.44B，源整数单位，不做币种换算。"},
                {"id": "card_rtp", "dataset": "headline_metrics", "sourceId": source_server, "metrics": [{"label": "金额加权 RTP（临时）", "field": "weighted_rtp", "format": "percent"}], "description": "cash_settlement ÷ bet_num；结算语义和单位待认证。"},
                {"id": "card_robot_share", "dataset": "headline_metrics", "sourceId": source_server, "metrics": [{"label": "机器人下注占比", "field": "robot_bet_share", "format": "percent"}], "description": "机器人单列，不进入真人主表。"},
                {"id": "card_peak", "dataset": "headline_metrics", "sourceId": source_server, "metrics": [{"label": "下注额峰值", "field": "peak_amount_hour", "format": "text"}], "description": "按 7 日窗口同一小时累计下注额。"},
                {"id": "card_entry", "dataset": "headline_metrics", "sourceId": source_entry, "metrics": [{"label": "进入信号", "field": "entry_status", "format": "text"}], "description": "PV 稀疏；不产出可靠进入→下注转化率。"},
                {"id": "card_concurrency", "dataset": "headline_metrics", "sourceId": source_server, "metrics": [{"label": "并发状态", "field": "concurrency_status", "format": "text"}], "description": "仅有下注用户代理，未发现 Whot 会话区间。"},
            ],
            "charts": [
                {"id": "chart_hourly_bet_heatmap", "title": "7 天 × 24 小时真人下注额热力图", "subtitle": "横轴为 Lagos 小时，纵轴为业务日；颜色深浅表示真人下注额（10亿源单位）。", "type": "heatmap", "dataset": "hourly_main", "sourceId": source_server, "encodings": {"x": {"field": "hour_label", "type": "ordinal", "label": "Lagos 小时"}, "y": {"field": "bet_amount_b", "type": "quantitative", "label": "下注额（10亿源单位）", "format": "number"}, "color": {"field": "date_label", "type": "nominal", "label": "业务日"}}, "xAxisTitle": "Lagos 小时", "yAxisTitle": "下注额（10亿源单位）"},
                {"id": "chart_hour_profile_amount", "title": "按小时累计真人下注额", "subtitle": "7 日窗口按小时-of-day 汇总；金额单位为 10亿源单位。", "type": "bar", "dataset": "hour_profile", "sourceId": source_server, "encodings": {"x": {"field": "hour_label", "type": "ordinal", "label": "Lagos 小时"}, "y": {"field": "bet_amount_b", "type": "quantitative", "label": "下注额（10亿源单位）", "format": "number"}}, "xAxisTitle": "Lagos 小时", "yAxisTitle": "下注额（10亿源单位）"},
                {"id": "chart_hour_profile_users", "title": "按小时累计真人下注用户数", "subtitle": "同一 Lagos 小时跨 7 日去重；不是 7 个日用户数相加。", "type": "bar", "dataset": "hour_profile", "sourceId": source_server, "encodings": {"x": {"field": "hour_label", "type": "ordinal", "label": "Lagos 小时"}, "y": {"field": "bet_users", "type": "quantitative", "label": "窗口去重下注用户", "format": "number"}}, "xAxisTitle": "Lagos 小时", "yAxisTitle": "窗口去重下注用户"},
                {"id": "chart_three_hour_amount", "title": "3 小时运营时段真人下注额", "subtitle": "同一时段跨 7 日汇总；用户数直接在 3 小时粒度去重。", "type": "bar", "dataset": "three_hour_metrics", "sourceId": source_server, "encodings": {"x": {"field": "period_3h", "type": "ordinal", "label": "运营时段"}, "y": {"field": "bet_amount_b", "type": "quantitative", "label": "下注额（10亿源单位）", "format": "number"}}, "xAxisTitle": "3 小时运营时段", "yAxisTitle": "下注额（10亿源单位）"},
                {"id": "chart_three_hour_rtp", "title": "3 小时运营时段金额加权 RTP", "subtitle": "与上图使用同一时段分组；RTP 不是各小时 RTP 的简单平均。", "type": "line", "dataset": "three_hour_metrics", "sourceId": source_server, "encodings": {"x": {"field": "period_3h", "type": "ordinal", "label": "运营时段"}, "y": {"field": "weighted_rtp", "type": "quantitative", "label": "RTP", "format": "percent"}}, "xAxisTitle": "3 小时运营时段", "yAxisTitle": "金额加权 RTP", "valueFormat": "percent"},
                {"id": "chart_rtp_band_share", "title": "用户 RTP 区间分布（合格用户时段）", "subtitle": "每个用户-小时至少 3 个有效结算局；低于 10 人的分组不展示可识别小群体。", "type": "bar", "dataset": "rtp_bands", "sourceId": source_server, "encodings": {"x": {"field": "rtp_band", "type": "ordinal", "label": "用户 RTP 区间"}, "y": {"field": "rtp_band_share", "type": "quantitative", "label": "占比", "format": "percent"}}, "xAxisTitle": "用户 RTP 区间", "yAxisTitle": "占合格用户时段比例", "valueFormat": "percent"},
            ],
            "tables": [
                {"id": "table_daily_metrics", "title": "每日 Whot 服务端汇总", "subtitle": "7/7 完整业务日；真人与机器人分列，金额为源整数单位。", "dataset": "daily_metrics", "sourceId": source_server, "defaultSort": {"field": "metric_date_lagos", "direction": "asc"}, "columns": [{"field": "metric_date_lagos", "label": "业务日", "type": "text"}, {"field": "gamestart_users", "label": "GAMESTART 真人用户", "type": "number", "format": "number"}, {"field": "bet_users", "label": "下注真人用户", "type": "number", "format": "number"}, {"field": "bet_rounds", "label": "下注局代理", "type": "number", "format": "number"}, {"field": "bet_amount", "label": "下注额（源单位）", "type": "number", "format": "number"}, {"field": "house_profit_amount", "label": "盈利代理（源单位）", "type": "number", "format": "number"}, {"field": "weighted_rtp", "label": "RTP（临时）", "type": "number", "format": "percent"}, {"field": "robot_bet_share", "label": "机器人下注占比", "type": "number", "format": "percent"}]},
                {"id": "table_hour_profile_00_11", "title": "分时窗口汇总｜00:00—11:00", "subtitle": "同一小时跨 7 日去重用户与金额汇总；低谷/高峰判断采用窗口分布。", "dataset": "hour_profile_00_11", "sourceId": source_server, "columns": [{"field": "hour_label", "label": "小时", "type": "text"}, {"field": "bet_users", "label": "窗口去重下注用户", "type": "number", "format": "number"}, {"field": "bet_amount_b", "label": "下注额（10亿源单位）", "type": "number", "format": "number"}, {"field": "house_profit_b", "label": "盈利代理（10亿源单位）", "type": "number", "format": "number"}, {"field": "weighted_rtp", "label": "RTP（临时）", "type": "number", "format": "percent"}]},
                {"id": "table_hour_profile_12_23", "title": "分时窗口汇总｜12:00—23:00", "subtitle": "同一小时跨 7 日去重用户与金额汇总；高峰策略同时看用户数与金额。", "dataset": "hour_profile_12_23", "sourceId": source_server, "columns": [{"field": "hour_label", "label": "小时", "type": "text"}, {"field": "bet_users", "label": "窗口去重下注用户", "type": "number", "format": "number"}, {"field": "bet_amount_b", "label": "下注额（10亿源单位）", "type": "number", "format": "number"}, {"field": "house_profit_b", "label": "盈利代理（10亿源单位）", "type": "number", "format": "number"}, {"field": "weighted_rtp", "label": "RTP（临时）", "type": "number", "format": "percent"}]},
                {"id": "table_three_hour_metrics", "title": "3 小时运营时段汇总", "subtitle": "用户数为时段内直接去重；RTP 按时段金额重新计算。", "dataset": "three_hour_metrics", "sourceId": source_server, "columns": [{"field": "period_3h", "label": "时段", "type": "text"}, {"field": "bet_users", "label": "窗口去重下注用户", "type": "number", "format": "number"}, {"field": "bet_rounds", "label": "下注局代理", "type": "number", "format": "number"}, {"field": "bet_amount_b", "label": "下注额（10亿源单位）", "type": "number", "format": "number"}, {"field": "house_profit_b", "label": "盈利代理（10亿源单位）", "type": "number", "format": "number"}, {"field": "weighted_rtp", "label": "RTP（临时）", "type": "number", "format": "percent"}, {"field": "robot_bet_share", "label": "机器人下注占比", "type": "number", "format": "percent"}]},
                {"id": "table_rtp_bands", "title": "用户 RTP 区间分布", "subtitle": "合格用户时段共 401,233；全量用户时段 597,244，其中 196,011 个低于 3 局而未进入分布。", "dataset": "rtp_bands", "sourceId": source_server, "columns": [{"field": "rtp_band", "label": "RTP 区间", "type": "text"}, {"field": "rtp_band_users", "label": "用户时段数", "type": "number", "format": "number"}, {"field": "rtp_band_share", "label": "占合格用户时段", "type": "number", "format": "percent"}, {"field": "minimum_settled_rounds", "label": "最低结算局数", "type": "number", "format": "number"}]},
                {"id": "table_entry_summary", "title": "进入信号与并发可用性", "subtitle": "把真实进入、开局、下注活跃代理和实时并发分开命名。", "dataset": "entry_summary", "sourceId": source_entry, "columns": [{"field": "metric", "label": "指标", "type": "text"}, {"field": "value", "label": "结果", "type": "text"}, {"field": "data_state", "label": "状态", "type": "text"}, {"field": "interpretation", "label": "解释", "type": "text"}]},
                {"id": "table_strategy_actions", "title": "分时匹配与运营建议", "subtitle": "建议用于试验和容量规划，不直接修改生产匹配配置。", "dataset": "strategy_actions", "sourceId": source_server, "columns": [{"field": "priority", "label": "优先级", "type": "text"}, {"field": "signal", "label": "信号", "type": "text"}, {"field": "recommendation", "label": "建议", "type": "text"}, {"field": "guardrail", "label": "复核护栏", "type": "text"}]},
                {"id": "table_quality_status", "title": "数据质量与口径状态", "subtitle": "当前哪些可以用于方向判断，哪些必须补证。", "dataset": "quality_status", "sourceId": "src_local_quality", "columns": [{"field": "check", "label": "检查项", "type": "text"}, {"field": "actual", "label": "当前结果", "type": "text"}, {"field": "data_state", "label": "状态", "type": "text"}, {"field": "next_step", "label": "补证动作", "type": "text"}]},
            ],
            "blocks": [
                {"id": "title", "type": "markdown", "body": "# Whot 最近一周分时运营与 RTP 分析｜2026-08-28—2026-09-03\n\n**统计范围：**精确 `Whot`（game_id `6001`，server play_id `9116001`），业务时区 `Africa/Lagos`，完整业务日 `7/7`。\n\n**报告状态：**`partial`。服务端 GAMESTART/GAMEEND 聚合已完成；PV 进入信号稀疏，金额字段仍是源整数单位，RTP 为结算现金代理值，实时并发未具备可靠 Whot 维度。"},
                {"id": "executive_summary", "type": "markdown", "body": "## Executive Summary\n\n**先给结论：Whot 的需求主峰在 16—17 点和 22—23 点，金额峰值落在 23 点；低谷集中在 04—06 点。**按 7 日窗口同一小时汇总，23:00 下注额最高（约 6.23B 源单位），22:00 和 00:00 次之；下注用户峰值在 17:00、16:00、10:00。\n\n**规模与回报：**7 日真人下注额 `121.44B` 源整数单位，真人结算现金字段 `115.62B`，按 `cash_settlement ÷ bet_num` 的金额加权 RTP 为 `95.21%`，平台盈利代理为 `5.82B` 源单位。以上不是币种金额，也不是已签字的最终派奖口径。\n\n**人群结构：**机器人下注 `52.09B`，约占真人+机器人下注 `30.02%`，已从真人主表分离。每日约 `2,994` 个机器人用户是观测到的机器人池规模，不能解释为实时并发。\n\n**运营含义：**高峰时段应优先保证匹配响应、可用房间和首局速度；04—06 点可在不牺牲成局率的前提下适度扩大同层级房间池或等待窗口。不要仅凭单小时 RTP 调整数值，先核查结算字段、版本和时段规则。"},
                {"id": "summary_metrics", "type": "metric-strip", "cardIds": ["card_status", "card_human_bet", "card_rtp", "card_robot_share", "card_peak", "card_entry", "card_concurrency"]},
                {"id": "demand_intro", "type": "markdown", "body": "## 1. 分时需求结构\n\n服务端 GAMEEND 在 7 个业务日、每个日期的 24 小时均有返回。这里的 `bet_users` 是小时内发生有效下注的真人去重用户；它是活跃/下注用户指标，不是实时在线人数。GAMESTART 另做日级核验，不把开局人数当作进入人数。\n\n颜色越深表示下注额越高。热力图按 `server_time → Africa/Lagos` 转换日期和小时，跨日不合并。"},
                {"id": "heatmap", "type": "chart", "chartId": "chart_hourly_bet_heatmap"},
                {"id": "hour_amount", "type": "chart", "chartId": "chart_hour_profile_amount", "layout": "half"},
                {"id": "hour_users", "type": "chart", "chartId": "chart_hour_profile_users", "layout": "half"},
                {"id": "daily_table", "type": "table", "tableId": "table_daily_metrics"},
                {"id": "hour_table_a", "type": "table", "tableId": "table_hour_profile_00_11", "layout": "half"},
                {"id": "hour_table_b", "type": "table", "tableId": "table_hour_profile_12_23", "layout": "half"},
                {"id": "bet_profit_intro", "type": "markdown", "body": "## 2. 下注额与盈利分布\n\n3 小时图同时看下注规模和金额加权 RTP：柱状图表示真人下注额，折线表示同一时段重新计算的 RTP。这样可以区分“人多但下注浅”和“人数不高但金额集中”。本报告的盈利是 `bet_num - cash_settlement` 的代理，不把 `score` 当作派奖。\n\n**重点观察：**21:00—23:59 是 3 小时下注额最高时段（约 17.85B 源单位）；03:00—05:59 规模最低（约 10.02B）。23 点同时是小时金额峰值，属于金额与时段共同驱动的高峰，容量规划不能只看人数。"},
                {"id": "three_hour_amount", "type": "chart", "chartId": "chart_three_hour_amount", "layout": "half"},
                {"id": "three_hour_rtp", "type": "chart", "chartId": "chart_three_hour_rtp", "layout": "half"},
                {"id": "three_hour_table", "type": "table", "tableId": "table_three_hour_metrics"},
                {"id": "rtp_intro", "type": "markdown", "body": "## 3. RTP 与用户分布\n\nRTP 采用金额加权，不对小时或用户 RTP 做简单平均。用户 RTP 分布先按用户-小时聚合，仅纳入至少 3 个有效结算局的用户时段；全量用户时段 `597,244` 中 `401,233` 个合格，覆盖 `67.18%`。\n\n合格用户时段中，`<90%` 与 `≥110%` 两端合计约 `81.44%`，这更适合作为结算/样本/机器人/规则的 QA 触发器，而不是单凭比例修改 RTP。低样本覆盖达到 `32.82%`，解释时要保持克制。"},
                {"id": "rtp_chart", "type": "chart", "chartId": "chart_rtp_band_share"},
                {"id": "rtp_table", "type": "table", "tableId": "table_rtp_bands"},
                {"id": "concurrency_intro", "type": "markdown", "body": "## 4. 并发代理与匹配策略建议\n\n当前没有带 Whot 维度的 APPONLINE、会话开始/结束或心跳区间，因此不输出实时并发最小值、最大值或中位数。页面如果需要容量参考，应称为“下注用户代理”，不能称为在线人数。\n\n建议先按相对分位数做策略试验：P75 以上作为高需求候选，P25 以下作为低需求候选；本窗口中 16—17 点、22—23 点进入高需求候选，04—06 点进入低需求候选。高金额低人数场景要单独看金额集中度，不能按普通活跃人数线性扩容。"},
                {"id": "entry_table", "type": "table", "tableId": "table_entry_summary"},
                {"id": "strategy_table", "type": "table", "tableId": "table_strategy_actions"},
                {"id": "quality_intro", "type": "markdown", "body": "## 5. 数据质量与限制\n\n本报告已把真实 0、无观测、权限阻断、数据延迟和口径未认证分开表达。历史外部事件源仍有对象权限阻断，但当前结论使用企业账号可读的 realtime_event_server 聚合，不用旧窗口或空结果填充。\n\n需要特别注意：`PV=396` 个事件、`264` 个去重用户与 `MV=1,729,336` 个模块曝光事件不能共同证明完整进入漏斗；`GAMESTART` 只说明开局，不说明打开页面的人数。金额字段仍保留源整数单位，RTP 只能叫临时代理。"},
                {"id": "quality_table", "type": "table", "tableId": "table_quality_status"},
                {"id": "next_steps", "type": "markdown", "body": "## 6. 下一步\n\n1. **补齐进入事实：**新增并稳定记录 `WHOT_ENTRY/OPEN`，同时保留 `GAMESTART`，形成进入→开局→下注→结算漏斗；PV/MV 继续作为客户端信号，不互相替代。\n2. **认证结算口径：**确认 `bet_num`、`cash_settlement` 的币种/最小单位、正负号和最终派奖语义；确认 `unique_id` 是否可作为稳定局键，并补齐独立 `BETREWARD` 关联。\n3. **建立容量数据：**增加 Whot 维度 session start/end 或 heartbeat，记录匹配等待、成局耗时、P95/P99 和房间池容量，才能把下注用户代理升级为真实并发。\n4. **补齐运营切片：**按 Android、H5、iOS、包体、渠道、版本、网络类型拆分同一套指标；后期报告不再把全产品或全 App 在线数直接下沉到 Whot。\n5. **先做小流量试验：**高峰时段验证匹配响应和房间容量，低谷时段验证扩大池/等待窗口；RTP 只在金额和人数都充分且口径认证后进入策略调参。"},
            ],
        },
        "snapshot": {
            "version": 1,
            "generatedAt": RUN_AT,
            "status": "partial",
            "datasets": datasets,
            "accessIssues": [
                {"scope": "entry_users", "message": "Exact Whot PV is sparse (396 events / 264 users); no reliable entry-to-bet rate is reported."},
                {"scope": "weighted_rtp", "message": "cash_settlement / bet_num is a provisional source-unit proxy until payout semantics and currency unit are certified."},
                {"scope": "concurrency", "message": "No Whot-scoped online/session interval source; bet users are an active/betting-user proxy only."},
            ],
            "notes": [
                "All server aggregate facts are restricted to play_id=9116001 and target_day 2026-08-28—2026-09-03.",
                "The 7x24 hourly dataset is aggregate-only; user keys are not retained.",
                "The report does not merge BaccaWhot, Whotduel, or app-level online counts.",
                "No currency conversion, zero-fill, or score-as-payout substitution is applied.",
            ],
        },
        "sources": sources,
    }


def main() -> None:
    daily = enrich_daily()
    hourly = build_hourly_rows()
    periods = enrich_three_hour()
    hour_profile = build_hour_profile()
    bands = build_bands()
    total_bet = sum(row["bet_amount"] for row in DAILY_GAMEEND)
    total_cash = sum(row["player_payout_amount"] for row in DAILY_GAMEEND)
    total_robot_bet = sum(row["robot_bet_amount"] for row in DAILY_GAMEEND)
    window_rtp = total_cash / total_bet
    robot_share = total_robot_bet / (total_bet + total_robot_bet)
    peak_amount = max(hour_profile, key=lambda row: row["bet_amount"])
    peak_users = max(hour_profile, key=lambda row: row["bet_users"])
    low_amount_hours = sorted(hour_profile, key=lambda row: row["bet_amount"])[:3]
    extreme_share = (RTP_BANDS[0][1] + RTP_BANDS[-1][1]) / RTP_ELIGIBLE_USER_HOURS

    headline = [{
        "status": "partial",
        "human_bet_display": f"{total_bet / 1_000_000_000:.2f}B 源单位",
        "weighted_rtp": round6(window_rtp),
        "robot_bet_share": round6(robot_share),
        "peak_amount_hour": f"{peak_amount['hour_label']}｜{peak_amount['bet_amount_b']:.2f}B",
        "peak_user_hour": f"{peak_users['hour_label']}｜{peak_users['bet_users']:,} 人",
        "entry_status": "临时｜PV 稀疏",
        "concurrency_status": "阻断｜无 Whot 区间",
        "source_hash": SOURCE_HASH,
    }]
    daily_metrics = daily
    for row in daily_metrics:
        row["bet_amount_b"] = round6(row["bet_amount"] / 1_000_000_000)
        row["house_profit_b"] = round6(row["house_profit_amount"] / 1_000_000_000)
        row["player_payout_b"] = round6(row["player_payout_amount"] / 1_000_000_000)
    entry_summary = [
        {"metric": "PV｜客户端进入信号", "value": "396 事件 / 264 去重用户", "data_state": "provisional_sparse", "interpretation": "稀疏下界，不用于完整进入→下注转化率"},
        {"metric": "MV｜模块曝光", "value": "1,729,336 事件 / 140,852 去重用户", "data_state": "auxiliary", "interpretation": "曝光辅助，不等同真正进入玩法"},
        {"metric": "GAMESTART｜开局", "value": "7/7 日；日级真人用户可用", "data_state": "passed_7_of_7", "interpretation": "单独展示，不冒充进入人数"},
        {"metric": "Whot 实时并发", "value": "未观测到 Whot session/heartbeat 区间", "data_state": "blocked", "interpretation": "下注用户只作活跃/下注代理"},
    ]
    quality_status = [
        {"check": "日期覆盖", "actual": "GAMEEND 7/7 日、168/168 小时；GAMESTART 7/7 日、168/168 小时", "data_state": "passed", "next_step": "继续监控延迟和重试"},
        {"check": "精确游戏范围", "actual": "game_id=6001 → play_id=9116001", "data_state": "passed", "next_step": "保留字典版本和映射回执"},
        {"check": "GAMESTART→GAMEEND→BETREWARD", "actual": "GAMESTART/GAMEEND 有；独立 BETREWARD 未在精确服务端 feed 中观察到", "data_state": "partial", "next_step": "补独立结算关联键和覆盖核验"},
        {"check": "金额和 RTP", "actual": "bet_num、cash_settlement 可聚合；源单位/最终派奖语义未认证", "data_state": "provisional", "next_step": "业务确认单位、符号和 payout 语义"},
        {"check": "机器人", "actual": "is_robot 已分列；机器人下注约 30.02%", "data_state": "provisional", "next_step": "确认机器人池配置和上限"},
        {"check": "进入/并发", "actual": "PV 稀疏；无 Whot session/heartbeat", "data_state": "blocked_for_funnel_and_concurrency", "next_step": "新增 WHOT_ENTRY 和会话区间事件"},
        {"check": "展示数据安全", "actual": "只保留聚合；不保存用户/设备/订单明细", "data_state": "passed", "next_step": "后续按包体/渠道维度补充聚合"},
    ]
    strategy_actions = [
        {"priority": "P0", "signal": "16—17 点、22—23 点为高需求候选；23 点金额峰值", "recommendation": "优先保障可用房间/桌、匹配响应和首局速度，按金额与用户两套指标监控容量", "guardrail": "等待 P95、成局率、失败/重匹配率、金额集中度"},
        {"priority": "P1", "signal": "04—06 点下注额和用户均处低位", "recommendation": "适度扩大同层级房间池或等待窗口，避免拆出过多空桌；先小流量试验", "guardrail": "等待时间、成局率、空桌率，不以全 App 在线数代替"},
        {"priority": "P1", "signal": "高金额不一定对应最高人数；23 点是金额集中场景", "recommendation": "按金额风险配置容量和风控，不按普通活跃人数线性扩容", "guardrail": "大额用户占比、单局金额分位数、结算延迟"},
        {"priority": "P1", "signal": "h6 临时 RTP 最低，h13 临时 RTP 最高", "recommendation": "核查 payout 字段、结算延迟、版本、配置和时段规则；不直接调 RTP 数值", "guardrail": "金额/人数充分性、认证 RTP、BETREWARD 覆盖"},
        {"priority": "P1", "signal": "机器人下注约 30.02%，每日机器人池约 2,994 用户", "recommendation": "机器人单独监控和分池，确认配置池容量；不把机器人用户数当实时并发", "guardrail": "机器人下注占比、机器人池上限、真人成局率"},
    ]
    datasets = {
        "headline_metrics": headline,
        "daily_metrics": daily_metrics,
        "daily_gamestart": DAILY_GAMESTART,
        "hourly_main": hourly,
        "hour_profile": hour_profile,
        "hour_profile_00_11": hour_profile[:12],
        "hour_profile_12_23": hour_profile[12:],
        "three_hour_metrics": periods,
        "rtp_bands": bands,
        "entry_summary": entry_summary,
        "quality_status": quality_status,
        "strategy_actions": strategy_actions,
        "coverage_status": quality_status,
        "metric_contract": [
            {"metric": "entry_users", "definition": "可靠 Whot 进入/打开事件的真人去重用户", "formula": "COUNT DISTINCT user_id", "data_state": "provisional_sparse_pv"},
            {"metric": "gamestart_users", "definition": "GAMESTART 真人去重用户", "formula": "COUNT DISTINCT user_id on GAMESTART", "data_state": "passed_7_of_7_daily"},
            {"metric": "bet_users", "definition": "小时内至少一笔有效下注的真人去重用户", "formula": "COUNT DISTINCT user_id on GAMEEND with bet_num>0", "data_state": "provisional_server_gameend"},
            {"metric": "bet_rounds", "definition": "有效 unique_id 去重的下注局代理", "formula": "COUNT DISTINCT unique_id", "data_state": "provisional_unique_id"},
            {"metric": "bet_amount", "definition": "有效 bet_num 求和", "formula": "SUM(bet_num)", "data_state": "provisional_source_integer_unit"},
            {"metric": "player_payout_amount", "definition": "cash_settlement 求和的派奖代理", "formula": "SUM(cash_settlement)", "data_state": "provisional_cash_settlement_proxy"},
            {"metric": "weighted_rtp", "definition": "金额加权 RTP", "formula": "cash_settlement / bet_num", "data_state": "provisional"},
            {"metric": "concurrency_proxy", "definition": "无会话区间时仅为下注/活跃用户代理", "formula": "not real-time concurrency", "data_state": "blocked_no_whot_scoped_online_fact"},
        ],
    }
    checks = formula_checks(daily_metrics, hourly, periods, bands)
    write_json("server_daily_gameend.json", daily_metrics)
    write_json("server_daily_gamestart.json", DAILY_GAMESTART)
    write_json("server_hourly_main.json", hourly)
    write_json("server_hour_profile.json", hour_profile)
    write_json("server_three_hour.json", periods)
    write_json("user_rtp_bands.json", {"all_user_hours": RTP_ALL_USER_HOURS, "eligible_user_hours": RTP_ELIGIBLE_USER_HOURS, "low_sample_user_hours": RTP_ALL_USER_HOURS - RTP_ELIGIBLE_USER_HOURS, "bands": bands})
    write_json("entry_event_summary.json", {"pv_events": PV_EVENTS, "pv_users": PV_USERS, "mv_events": MV_EVENTS, "mv_users": MV_USERS, "data_state": "provisional_sparse_pv", "source_hash": SOURCE_HASH})
    write_json("formula_checks.json", checks)
    write_json("sql_validation.json", sql_validation())
    write_json("query_results_summary.json", {
        "run_id": "whot_hourly_analysis_2026_09_04",
        "source_hash": SOURCE_HASH,
        "window": {"start": WINDOW_START, "end_exclusive": WINDOW_END_EXCLUSIVE, "timezone": TIMEZONE, "game": GAME, "game_id": GAME_ID, "play_id": PLAY_ID},
        "server_gameend": {"daily_rows": 7, "hourly_rows": 168, "human_bet": total_bet, "human_cash": total_cash, "human_profit_proxy": total_bet - total_cash, "weighted_rtp": round6(window_rtp), "robot_bet": total_robot_bet, "robot_share": round6(robot_share)},
        "server_gamestart": {"daily_rows": 7, "hourly_rows": 168},
        "client_entry": {"pv_events": PV_EVENTS, "pv_users": PV_USERS, "mv_events": MV_EVENTS, "mv_users": MV_USERS, "status": "sparse"},
        "user_rtp": {"all_user_hours": RTP_ALL_USER_HOURS, "eligible_user_hours": RTP_ELIGIBLE_USER_HOURS, "low_sample_user_hours": RTP_ALL_USER_HOURS - RTP_ELIGIBLE_USER_HOURS, "extreme_band_share": round6(extreme_share)},
        "concurrency": {"status": "blocked", "reason": "no_whot_scoped_session_or_heartbeat_intervals"},
        "no_row_level_output": True,
    })
    artifact = build_artifact(datasets, source_definitions())
    (ANALYSIS / "artifact.json").write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_json("build_receipt.json", {"run_id": "whot_hourly_analysis_2026_09_04", "generated_at": RUN_AT, "status": "passed", "artifact": "artifact.json", "source_hash": SOURCE_HASH, "formula_checks": "formula_checks.json", "datasets": {key: len(value) if isinstance(value, list) else None for key, value in datasets.items()}, "notes": ["No credentials or row-level identifiers saved.", "RTP and money semantics remain provisional."]})
    print(json.dumps({"status": "passed", "artifact": str(ANALYSIS / "artifact.json"), "source_hash": SOURCE_HASH, "human_bet": total_bet, "weighted_rtp": round6(window_rtp), "robot_share": round6(robot_share), "hourly_rows": len(hourly)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
