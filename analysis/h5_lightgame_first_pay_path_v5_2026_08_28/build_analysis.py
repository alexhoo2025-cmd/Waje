#!/usr/bin/env python3
"""Build aggregate V5 calculations and charts from reviewed Metabase CSV exports.

The script never accepts or writes user-level identifiers. It fails closed when
required aggregate result files or required columns are missing.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
CHARTS = ROOT / "charts"

FILES = {
    "conversion": RESULTS / "01_new_user_first_pay_conversion.csv",
    "paths": RESULTS / "02_first_pay_path_groups.csv",
    "depth": RESULTS / "03_postpay_game_depth.csv",
    "repeat": RESULTS / "04_repeat_pay.csv",
}

PALETTE = {
    "blue": "#4D8EC9",
    "green": "#55A982",
    "yellow": "#E7B94C",
    "orange": "#E58A55",
    "purple": "#8174C8",
    "red": "#D66B67",
    "ink": "#18324B",
    "grid": "#DCE8F0",
    "paper": "#F7FBFD",
}


def require_files() -> None:
    missing = [str(path) for path in FILES.values() if not path.exists()]
    if missing:
        raise SystemExit("blocked_missing_results:\n" + "\n".join(missing))


def read_inputs() -> dict[str, pd.DataFrame]:
    require_files()
    frames = {name: pd.read_csv(path) for name, path in FILES.items()}
    forbidden = {"gid", "user_id", "user_key", "order_id", "device_id", "round_id"}
    for name, frame in frames.items():
        leaked = forbidden.intersection({c.lower() for c in frame.columns})
        if leaked:
            raise SystemExit(f"blocked_sensitive_columns:{name}:{sorted(leaked)}")
    return frames


def channel_name(package: object, media: object) -> str:
    text = f"{package}|{media}".lower()
    if "facebook" in text or "fb" in text:
        return "H5 Facebook"
    if "google" in text or "adwords" in text:
        return "H5 Google"
    if "pwa" in text or "pww" in text:
        return "PWA自然"
    if "h5" in text or "wajebet" in text:
        return "H5自然"
    return "待映射"


def weighted_rate(frame: pd.DataFrame, rate_col: str, weight_col: str) -> float:
    denom = frame[weight_col].sum()
    return float((frame[rate_col] * frame[weight_col]).sum() / denom) if denom else np.nan


def compute_standardization(conversion: pd.DataFrame) -> dict:
    df = conversion.copy()
    df["channel"] = [channel_name(p, m) for p, m in zip(df["reg_package"], df["media_channel"])]
    if (df["channel"] == "待映射").any():
        raise SystemExit("blocked_channel_mapping: preflight categories remain unmapped")

    channel = (
        df.groupby(["period", "channel"], as_index=False)
        .agg(new_users=("new_users", "sum"), first_pay_users_d15=("first_pay_users_d15", "sum"))
    )
    channel["first_pay_rate_d15"] = channel["first_pay_users_d15"] / channel["new_users"]

    pre = channel[channel.period == "pre"].set_index("channel")
    post = channel[channel.period == "post"].set_index("channel")
    common = sorted(set(pre.index) & set(post.index))
    pre = pre.loc[common]
    post = post.loc[common]
    weights = pre.new_users / pre.new_users.sum()
    pre_actual = float(pre.first_pay_users_d15.sum() / pre.new_users.sum())
    post_actual = float(post.first_pay_users_d15.sum() / post.new_users.sum())
    post_standardized = float((post.first_pay_rate_d15 * weights).sum())
    return {
        "channel_rows": channel.to_dict("records"),
        "pre_actual": pre_actual,
        "post_actual": post_actual,
        "post_standardized": post_standardized,
        "within_channel_quality_effect_pp": (post_standardized - pre_actual) * 100,
        "channel_mix_effect_pp": (post_actual - post_standardized) * 100,
        "total_change_pp": (post_actual - pre_actual) * 100,
    }


def compute_decay(depth: pd.DataFrame) -> pd.DataFrame:
    df = depth.copy()
    df = df.sort_values(["period", "path_group", "day_since_first_pay"])
    df["previous_replay_rate"] = df.groupby(["period", "path_group"])["replay_rate"].shift(1)
    df["decay_rate"] = 1 - df["replay_rate"] / df["previous_replay_rate"]
    return df


def plot_conversion(rows: list[dict]) -> None:
    df = pd.DataFrame(rows)
    pivot = df.pivot(index="channel", columns="period", values="first_pay_rate_d15").reindex(
        ["H5自然", "H5 Facebook", "H5 Google", "PWA自然"]
    )
    ax = pivot.mul(100).plot(kind="bar", color=[PALETTE["blue"], PALETTE["green"]], figsize=(10, 5))
    ax.set_title("上线前后新增用户15日首充转化率")
    ax.set_ylabel("首充转化率（%）")
    ax.set_xlabel("")
    ax.grid(axis="y", color=PALETTE["grid"], linewidth=0.8)
    ax.legend(["上线前", "上线后"], frameon=False)
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(CHARTS / "01_上线前后首充转化率.png", dpi=180, facecolor="white")
    plt.close()


def plot_paths(paths: pd.DataFrame) -> None:
    pivot = paths.pivot(index="period", columns="path_group", values="user_share").fillna(0)
    colors = [PALETTE[k] for k in ["blue", "green", "yellow", "orange", "purple", "red"][: len(pivot.columns)]]
    ax = pivot.mul(100).plot(kind="barh", stacked=True, color=colors, figsize=(11, 4.8))
    ax.set_title("首充用户付费前后游戏路径结构")
    ax.set_xlabel("首充用户占比（%）")
    ax.set_ylabel("")
    ax.legend(frameon=False, bbox_to_anchor=(0.5, -0.18), loc="upper center", ncol=3)
    ax.grid(axis="x", color=PALETTE["grid"], linewidth=0.8)
    plt.tight_layout()
    plt.savefig(CHARTS / "02_首充用户路径结构.png", dpi=180, facecolor="white")
    plt.close()


def plot_replay(decay: pd.DataFrame) -> None:
    post = decay[decay.period == "post"]
    fig, ax = plt.subplots(figsize=(11, 5.5))
    for idx, (group, part) in enumerate(post.groupby("path_group")):
        ax.plot(
            part.day_since_first_pay,
            part.replay_rate * 100,
            marker="o",
            linewidth=2,
            label=group,
            color=list(PALETTE.values())[idx % 6],
        )
    ax.set_title("上线后首充用户T0—D15轻量化游戏复玩率")
    ax.set_xlabel("首充后天数")
    ax.set_ylabel("复玩率（%）")
    ax.grid(color=PALETTE["grid"], linewidth=0.8)
    ax.legend(frameon=False, ncol=3)
    plt.tight_layout()
    plt.savefig(CHARTS / "03_首充后逐日复玩率.png", dpi=180, facecolor="white")
    plt.close()


def plot_decay_heatmap(decay: pd.DataFrame) -> None:
    post = decay[(decay.period == "post") & decay.decay_rate.notna()]
    pivot = post.pivot(index="path_group", columns="day_since_first_pay", values="decay_rate")
    fig, ax = plt.subplots(figsize=(12, 4.8))
    im = ax.imshow(pivot.fillna(0).values * 100, cmap="YlOrRd", aspect="auto", vmin=0, vmax=100)
    ax.set_title("上线后首充用户逐日复玩衰减")
    ax.set_xlabel("后一天（Dk）")
    ax.set_ylabel("")
    ax.set_xticks(range(len(pivot.columns)), [f"D{int(x)}" for x in pivot.columns])
    ax.set_yticks(range(len(pivot.index)), pivot.index)
    fig.colorbar(im, ax=ax, label="相对前一日衰减（%）")
    plt.tight_layout()
    plt.savefig(CHARTS / "04_逐日复玩衰减热力图.png", dpi=180, facecolor="white")
    plt.close()


def main() -> None:
    CHARTS.mkdir(exist_ok=True)
    frames = read_inputs()
    standardization = compute_standardization(frames["conversion"])
    decay = compute_decay(frames["depth"])
    decay.to_csv(RESULTS / "derived_replay_decay.csv", index=False)
    payload = {
        "status": "computed_aggregate_only",
        "standardization": standardization,
        "path_rows": frames["paths"].to_dict("records"),
        "repeat_pay_rows": frames["repeat"].to_dict("records"),
    }
    (RESULTS / "analysis_summary.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    plot_conversion(standardization["channel_rows"])
    plot_paths(frames["paths"])
    plot_replay(decay)
    plot_decay_heatmap(decay)


if __name__ == "__main__":
    main()

