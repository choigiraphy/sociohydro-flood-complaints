"""Plot Supplementary Figure S8: leave-one-region-out sensitivity."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

REGION_LABELS = {
    "강원도": "Gangwon",
    "경기도": "Gyeonggi",
    "경상남도": "Gyeongnam",
    "경상북도": "Gyeongbuk",
    "광주광역시": "Gwangju",
    "대구광역시": "Daegu",
    "대전광역시": "Daejeon",
    "부산광역시": "Busan",
    "서울특별시": "Seoul",
    "세종특별자치시": "Sejong",
    "울산광역시": "Ulsan",
    "인천광역시": "Incheon",
    "전라남도": "Jeonnam",
    "전라북도": "Jeonbuk",
    "제주특별자치도": "Jeju",
    "충청남도": "Chungnam",
    "충청북도": "Chungbuk",
}
EVENT_COLORS = {"Flood 2022": "#e07a10", "Flood 2023": "#4c78a8"}

def plot_leave_one_out_sensitivity(
    loo_df: pd.DataFrame,
    full_df: pd.DataFrame,
    out_path: str,
) -> None:
    """Render the S8 leave-one-out plot."""
    plot_full = full_df.loc[
        (full_df["association_metric"] == "spearman_rho")
        & (full_df["exposure_metric"] == "regional_mean_precip")
        & (full_df["response_metric"] == "raw_complaints")
    ].copy()
    plot_loo = loo_df.loc[
        (loo_df["association_metric"] == "spearman_rho")
        & (loo_df["exposure_metric"] == "regional_mean_precip")
        & (loo_df["response_metric"] == "raw_complaints")
    ].copy()
    plot_loo["region_label"] = plot_loo["excluded_region"].map(REGION_LABELS).fillna(plot_loo["excluded_region"])

    events = ["Flood 2022", "Flood 2023"]
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 7.8), sharey=True, constrained_layout=True)

    for ax, event in zip(axes, events):
        subset = plot_loo.loc[plot_loo["event"] == event].sort_values("estimate")
        baseline = plot_full.loc[plot_full["event"] == event, "estimate"]
        full_estimate = float(baseline.iloc[0]) if not baseline.empty else 0.0
        y_positions = list(range(len(subset)))

        ax.scatter(
            subset["estimate"],
            y_positions,
            color=EVENT_COLORS[event],
            s=42,
            zorder=3,
        )
        ax.axvline(full_estimate, color="#222222", linestyle="--", linewidth=1.4)
        ax.set_title(f"{event}", fontsize=12, fontweight="bold")
        ax.set_xlabel("Spearman rho after excluding one region", fontsize=10)
        ax.set_ylabel("")
        ax.grid(axis="x", color="#dddddd", linewidth=0.8)
        ax.set_axisbelow(True)
        ax.set_yticks(y_positions)
        ax.set_yticklabels(subset["region_label"], fontsize=9)
        ax.invert_yaxis()
        for spine in ["top", "right"]:
            ax.spines[spine].set_visible(False)

    fig.suptitle("Supplementary Figure S8. Leave-one-region-out sensitivity", fontsize=13, fontweight="bold")
    fig.savefig(out_path, dpi=300, bbox_inches="tight")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--loo", required=True, help="Leave-one-out csv/xlsx")
    parser.add_argument("--full", required=True, help="Full-sample association csv/xlsx")
    parser.add_argument("--output", required=True, help="Output png path")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    loo_path = Path(args.loo)
    full_path = Path(args.full)
    if loo_path.suffix.lower() == ".csv":
        loo_df = pd.read_csv(loo_path)
    else:
        loo_df = pd.read_excel(loo_path, sheet_name="leave_one_out")
    if full_path.suffix.lower() == ".csv":
        full_df = pd.read_csv(full_path)
    else:
        full_df = pd.read_excel(full_path, sheet_name="association_metrics")
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    plot_leave_one_out_sensitivity(loo_df, full_df, args.output)
    plt.close("all")


if __name__ == "__main__":
    main()
