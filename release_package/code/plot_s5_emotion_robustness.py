"""Plot Supplementary Figure S5: emotion aggregation robustness."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.lines import Line2D

EVENT_ORDER = ["Flood 2022 - Ordinary", "Flood 2023 - Ordinary"]
EVENT_COLORS = {
    "Flood 2022 - Ordinary": "#d55e00",
    "Flood 2023 - Ordinary": "#0072b2",
}
TITLE_MAP = {
    "top1": "(a) Top-1 aggregation",
    "prob": "(b) Probability aggregation",
    "grouped": "(c) Grouped-category aggregation",
}


def plot_emotion_aggregation_robustness(
    top1_df: pd.DataFrame,
    prob_df: pd.DataFrame,
    grouped_df: pd.DataFrame,
    out_path: str,
) -> None:
    """Render the S5 figure from tidy inputs."""
    fig, axes = plt.subplots(1, 3, figsize=(18, 5.8), constrained_layout=True)

    _plot_panel(
        ax=axes[0],
        df=top1_df.loc[top1_df["comparison"].isin(EVENT_ORDER)].copy(),
        value_col="mean_diff_top1",
        title=TITLE_MAP["top1"],
    )
    _plot_panel(
        ax=axes[1],
        df=prob_df.loc[prob_df["comparison"].isin(EVENT_ORDER)].copy(),
        value_col="mean_diff_prob",
        title=TITLE_MAP["prob"],
    )
    _plot_panel(
        ax=axes[2],
        df=grouped_df.loc[grouped_df["comparison"].isin(EVENT_ORDER)].copy(),
        value_col="mean_diff_prob",
        title=TITLE_MAP["grouped"],
    )

    handles = [
        Line2D([0], [0], color=EVENT_COLORS[event], lw=8, label=event.replace(" - Ordinary", ""))
        for event in EVENT_ORDER
    ]
    fig.legend(handles=handles, loc="upper center", ncol=2, frameon=False, bbox_to_anchor=(0.5, 1.03), fontsize=11)
    fig.savefig(out_path, dpi=300, bbox_inches="tight")


def _plot_panel(ax: plt.Axes, df: pd.DataFrame, value_col: str, title: str) -> None:
    plot_df = df.copy()
    plot_df = plot_df.loc[plot_df["emotion"].ne("Other")].copy()
    order = (
        plot_df.groupby("emotion")[value_col]
        .apply(lambda s: s.abs().max())
        .sort_values(ascending=True)
        .index
        .tolist()
    )

    width = 0.36
    y_positions = list(range(len(order)))
    event_offsets = {
        EVENT_ORDER[0]: -width / 2,
        EVENT_ORDER[1]: width / 2,
    }

    for event in EVENT_ORDER:
        subset = (
            plot_df.loc[plot_df["comparison"].eq(event), ["emotion", value_col]]
            .set_index("emotion")
            .reindex(order)
            .reset_index()
        )
        ax.barh(
            [y + event_offsets[event] for y in y_positions],
            subset[value_col].fillna(0.0),
            height=width,
            color=EVENT_COLORS[event],
            alpha=0.9,
        )

    ax.axvline(0.0, color="#444444", linewidth=1.0)
    ax.set_yticks(y_positions)
    ax.set_yticklabels(order, fontsize=10)
    ax.tick_params(axis="x", labelsize=10)
    ax.set_title(title, fontsize=13, fontweight="bold", pad=8)
    ax.set_xlabel("Event - baseline difference", fontsize=11)
    ax.grid(axis="x", color="#d9d9d9", linewidth=0.8, alpha=0.8)
    ax.set_axisbelow(True)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--top1", help="Top-1 tidy csv")
    parser.add_argument("--prob", help="Probability tidy csv")
    parser.add_argument("--grouped", help="Grouped tidy csv")
    parser.add_argument("--workbook", help="S6 workbook path")
    parser.add_argument("--output", required=True, help="Output png path")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.workbook:
        top1_df = pd.read_excel(args.workbook, sheet_name="combined_s6_fine")
        prob_df = top1_df.copy()
        grouped_df = pd.read_excel(args.workbook, sheet_name="combined_s6_grouped")
    else:
        if not (args.top1 and args.prob and args.grouped):
            raise ValueError("Provide --workbook or all of --top1, --prob, and --grouped.")
        top1_df = pd.read_csv(args.top1)
        prob_df = pd.read_csv(args.prob)
        grouped_df = pd.read_csv(args.grouped)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    plot_emotion_aggregation_robustness(top1_df, prob_df, grouped_df, args.output)
    plt.close("all")


if __name__ == "__main__":
    main()
