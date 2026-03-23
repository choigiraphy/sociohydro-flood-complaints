from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import pandas as pd

from visualization import load_province_geometries
from wrr_figure_support import apply_wrr_style


EMOTION_ORDER = [
    "Anger/Rage",
    "Sad/Disappointed",
    "Embarrassment/Distress",
]

EMOTION_TITLES = {
    "Anger/Rage": "Anger/Rage",
    "Sad/Disappointed": "Sadness",
    "Embarrassment/Distress": "Embarrassment/Distress",
}

PERIOD_ORDER = ["Flood 2022", "Flood 2023"]
PANEL_LABELS = [["(a)", "(b)", "(c)"], ["(d)", "(e)", "(f)"]]


def load_region_shift(path: Path) -> pd.DataFrame:
    return pd.read_excel(path, sheet_name="region_emotion_shift")


def build_figure(output_path: Path, table_path: Path, boundary_path: Path) -> None:
    apply_wrr_style()
    shifts = load_region_shift(table_path)
    shapes = load_province_geometries(boundary_path)

    values = shifts.loc[shifts["sufficient_data"], "delta_share"].dropna()
    vmax = max(abs(values.min()), abs(values.max())) if not values.empty else 0.25
    vmax = max(0.25, float(vmax))
    norm = mcolors.TwoSlopeNorm(vmin=-vmax, vcenter=0.0, vmax=vmax)
    cmap = plt.get_cmap("RdBu_r")

    fig, axes = plt.subplots(2, 3, figsize=(17.5, 13))

    for row_idx, period in enumerate(PERIOD_ORDER):
        for col_idx, emotion in enumerate(EMOTION_ORDER):
            ax = axes[row_idx, col_idx]
            subset = shifts.loc[
                (shifts["period"] == period) & (shifts["emotion"] == emotion),
                ["region", "delta_share", "sufficient_data"],
            ].copy()
            plot_gdf = shapes.merge(subset, on="region", how="left")

            valid = plot_gdf.loc[plot_gdf["sufficient_data"] == True].copy()
            invalid = plot_gdf.loc[plot_gdf["sufficient_data"] != True].copy()

            if not valid.empty:
                valid.plot(
                    column="delta_share",
                    cmap=cmap,
                    norm=norm,
                    ax=ax,
                    edgecolor="black",
                    linewidth=0.55,
                    legend=False,
                )
            if not invalid.empty:
                invalid.plot(
                    ax=ax,
                    facecolor="white",
                    edgecolor="gray",
                    linewidth=0.55,
                    hatch="////",
                )

            ax.axis("off")
            ax.text(
                0.02,
                0.98,
                PANEL_LABELS[row_idx][col_idx],
                transform=ax.transAxes,
                va="top",
                fontsize=18,
                fontweight="bold",
                bbox=dict(facecolor="white", edgecolor="none", pad=0.4, alpha=0.8),
            )
            if row_idx == 0:
                ax.set_title(EMOTION_TITLES[emotion], fontsize=18, fontweight="bold", pad=10)
            if col_idx == 0:
                ax.text(
                    -0.15,
                    0.5,
                    "2022" if period == "Flood 2022" else "2023",
                    transform=ax.transAxes,
                    rotation=90,
                    va="center",
                    ha="center",
                    fontsize=20,
                    fontweight="bold",
                )

    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    cax = fig.add_axes([0.885, 0.20, 0.020, 0.60])
    cbar = fig.colorbar(sm, cax=cax)
    cbar.set_label(r"$\Delta$ Proportion (Flood $-$ Baseline)", fontsize=17, fontweight="bold", rotation=270, labelpad=24)
    cbar.ax.tick_params(labelsize=13)

    hatch_patch = Patch(facecolor="white", edgecolor="gray", hatch="////", label="Insufficient data (N < 5)")
    fig.legend(handles=[hatch_patch], loc="lower right", bbox_to_anchor=(0.93, 0.03), fontsize=13, frameon=True)

    plt.subplots_adjust(hspace=0.06, wspace=0.03, left=0.04, right=0.86, bottom=0.06, top=0.95)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate manuscript-aligned WRR Figure 6")
    parser.add_argument("--output", type=Path, default=Path("/Volumes/Keywest_JetDrive 1/Codex/Academia/Complaint/figures/Figure6_WRR.png"))
    parser.add_argument("--table-path", type=Path, default=Path("/Volumes/Keywest_JetDrive 1/Codex/Academia/Complaint/tables/bootstrap_results.xlsx"))
    parser.add_argument(
        "--boundary-path",
        type=Path,
        default=Path("/Volumes/Keywest_JetDrive 1/데이터저장소/skorea-municipalities-2018-geo.json"),
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    build_figure(args.output, args.table_path, args.boundary_path)
