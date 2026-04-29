"""Plot Supplementary Figure S7: spatial robustness heatmap."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


def make_spec_label(df: pd.DataFrame) -> pd.DataFrame:
    """Add a human-readable specification label."""
    out = df.copy()
    out["spec_label"] = (
        out["exposure_metric"].astype(str)
        + " | "
        + out["response_metric"].astype(str)
        + " | "
        + out["association_metric"].astype(str)
    )
    return out


def plot_spatial_robustness_heatmap(assoc_df: pd.DataFrame, out_path: str) -> None:
    """Render the S7 heatmap from association metrics."""
    plot_df = assoc_df.copy()
    plot_df = plot_df.loc[plot_df["association_metric"].isin(["spearman_rho", "kendall_tau"])].copy()
    plot_df = plot_df.sort_values(["association_metric", "exposure_metric", "response_metric"])

    pivot = (
        plot_df.pivot_table(
            index="spec_label",
            columns="event",
            values="estimate",
            aggfunc="first",
        )
        .reindex(columns=["Flood 2022", "Flood 2023"])
        .sort_index()
    )

    fig, ax = plt.subplots(figsize=(8.6, max(6.0, 0.34 * len(pivot.index))))
    sns.heatmap(
        pivot,
        ax=ax,
        cmap="RdBu_r",
        center=0.0,
        annot=True,
        fmt=".2f",
        linewidths=0.5,
        linecolor="#f0f0f0",
        cbar_kws={"label": "Association estimate"},
        annot_kws={"fontsize": 9},
    )
    ax.set_title("Supplementary Figure S7. Spatial robustness across specifications", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.tick_params(axis="x", labelsize=10, rotation=0)
    ax.tick_params(axis="y", labelsize=8)
    plt.tight_layout()
    fig.savefig(out_path, dpi=300, bbox_inches="tight")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Association metrics csv/xlsx")
    parser.add_argument("--output", required=True, help="Output png path")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    input_path = Path(args.input)
    if input_path.suffix.lower() == ".csv":
        assoc_df = pd.read_csv(input_path)
    else:
        assoc_df = pd.read_excel(input_path, sheet_name="association_metrics")
    assoc_df = make_spec_label(assoc_df)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    plot_spatial_robustness_heatmap(assoc_df, args.output)
    plt.close("all")


if __name__ == "__main__":
    main()
