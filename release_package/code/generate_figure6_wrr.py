from __future__ import annotations

import argparse
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.patches import Patch
from matplotlib.ticker import FuncFormatter
import pandas as pd

from wrr_figure_support import REPO_ROOT, apply_wrr_style, resolve_first_existing


EVENT_ORDER = ["Flood 2022", "Flood 2023"]
PANEL_LABELS = [["(a)", "(b)"], ["(c)", "(d)"]]
BOUNDARY_PATH = resolve_first_existing(
    Path("/Volumes/Keywest_JetDrive/데이터저장소/final_final/LX법정구역경계_시도_전국/SIDO.shp"),
    Path("/Volumes/Keywest_JetDrive 1/데이터저장소/final_final/LX법정구역경계_시도_전국/SIDO.shp"),
)
XTICKS = [125, 127, 129, 131]
YTICKS = [34, 35, 36, 37, 38]


def load_national_boundaries() -> gpd.GeoDataFrame:
    gdf = gpd.read_file(BOUNDARY_PATH)
    gdf["region_join"] = gdf["ctpr_nm"].replace(
        {
            "강원특별자치도": "강원특별자치도",
            "전북특별자치도": "전북특별자치도",
        }
    )
    return gdf[["ctpr_nm", "geometry"]].to_crs(epsg=4326)


def load_region_intensity(path: Path) -> gpd.GeoDataFrame:
    df = pd.read_excel(path, sheet_name="region_event_intensity")
    shapes = load_national_boundaries()
    return shapes.merge(df, on="ctpr_nm", how="left")


def _plot_map(
    ax: plt.Axes,
    gdf: gpd.GeoDataFrame,
    value_col: str,
    cmap: str,
    norm: mcolors.Normalize,
) -> bool:
    valid = gdf.loc[gdf[value_col].notna()].copy()
    missing = gdf.loc[gdf[value_col].isna()].copy()

    gdf.plot(
        ax=ax,
        facecolor="#F5F7F9",
        edgecolor="#C4CBD3",
        linewidth=0.45,
    )

    if not valid.empty:
        valid.plot(
            column=value_col,
            cmap=cmap,
            norm=norm,
            ax=ax,
            edgecolor="#5F6670",
            linewidth=0.55,
            legend=False,
        )
    if not missing.empty:
        missing.plot(
            ax=ax,
            facecolor="#F5F7F9",
            edgecolor="#8E97A0",
            linewidth=0.55,
            hatch="///",
        )
    return not missing.empty


def _configure_geo_axis(ax: plt.Axes, bounds: tuple[float, float, float, float], show_x: bool, show_y: bool) -> None:
    xmin, ymin, xmax, ymax = bounds
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    ax.set_aspect("equal")
    ax.set_xticks(XTICKS)
    ax.set_yticks(YTICKS)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"{x:.0f}°E"))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda y, pos: f"{y:.0f}°N"))
    ax.tick_params(axis="both", labelsize=9, length=3, color="#6A737D")
    if not show_x:
        ax.tick_params(axis="x", labelbottom=False)
    if not show_y:
        ax.tick_params(axis="y", labelleft=False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#B5BDC6")
    ax.spines["bottom"].set_color("#B5BDC6")
    ax.spines["left"].set_linewidth(0.8)
    ax.spines["bottom"].set_linewidth(0.8)


def build_figure(output_path: Path, table_path: Path) -> None:
    apply_wrr_style()
    gdf = load_region_intensity(table_path)

    complaint_values = gdf["complaints_per_100k"].dropna()
    precip_values = gdf["event_cumulative_precip"].dropna()
    complaint_norm = mcolors.Normalize(vmin=0.0, vmax=float(complaint_values.max()))
    precip_norm = mcolors.Normalize(vmin=0.0, vmax=float(precip_values.max()))

    fig, axes = plt.subplots(2, 2, figsize=(12.6, 12.2))
    has_missing = False
    bounds = tuple(gdf.total_bounds)

    for col_idx, event in enumerate(EVENT_ORDER):
        complaint_subset = gdf.loc[gdf["event"] == event].copy()
        precip_subset = complaint_subset.copy()

        has_missing |= _plot_map(axes[0, col_idx], complaint_subset, "complaints_per_100k", "OrRd", complaint_norm)
        has_missing |= _plot_map(axes[1, col_idx], precip_subset, "event_cumulative_precip", "Blues", precip_norm)
        _configure_geo_axis(axes[0, col_idx], bounds, show_x=False, show_y=(col_idx == 0))
        _configure_geo_axis(axes[1, col_idx], bounds, show_x=True, show_y=(col_idx == 0))

        axes[0, col_idx].set_title("2022" if event == "Flood 2022" else "2023", fontsize=14, fontweight="semibold", pad=8)

    for row_idx in range(2):
        for col_idx in range(2):
            axes[row_idx, col_idx].text(
                0.02,
                0.98,
                PANEL_LABELS[row_idx][col_idx],
                transform=axes[row_idx, col_idx].transAxes,
                va="top",
                fontsize=14,
                fontweight="bold",
                bbox=dict(facecolor="white", edgecolor="none", pad=0.4, alpha=0.85),
            )

    axes[0, 0].text(
        -0.18,
        0.5,
        "Complaints per\n100k population",
        transform=axes[0, 0].transAxes,
        rotation=90,
        va="center",
        ha="center",
        fontsize=14,
        fontweight="semibold",
    )
    axes[1, 0].text(
        -0.18,
        0.5,
        "Event cumulative\nprecipitation [mm]",
        transform=axes[1, 0].transAxes,
        rotation=90,
        va="center",
        ha="center",
        fontsize=14,
        fontweight="semibold",
    )

    complaint_sm = plt.cm.ScalarMappable(cmap="OrRd", norm=complaint_norm)
    precip_sm = plt.cm.ScalarMappable(cmap="Blues", norm=precip_norm)
    cax1 = fig.add_axes([0.90, 0.56, 0.024, 0.30])
    cax2 = fig.add_axes([0.90, 0.16, 0.024, 0.30])
    cbar1 = fig.colorbar(complaint_sm, cax=cax1)
    cbar2 = fig.colorbar(precip_sm, cax=cax2)
    cbar1.ax.tick_params(labelsize=10)
    cbar2.ax.tick_params(labelsize=10)
    cbar1.set_label("Complaints per 100k", rotation=270, labelpad=16, fontweight="semibold")
    cbar2.set_label("Event cumulative precipitation [mm]", rotation=270, labelpad=16, fontweight="semibold")

    if has_missing:
        missing_patch = Patch(facecolor="#F5F7F9", edgecolor="#8E97A0", hatch="///", label="No value")
        fig.legend(handles=[missing_patch], loc="lower right", bbox_to_anchor=(0.93, 0.045), frameon=False, fontsize=10)

    plt.subplots_adjust(left=0.10, right=0.88, top=0.93, bottom=0.06, wspace=0.04, hspace=0.08)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate manuscript-aligned WRR Figure 6")
    parser.add_argument("--output", type=Path, default=REPO_ROOT / "figures" / "Figure6_WRR.png")
    parser.add_argument(
        "--table-path",
        type=Path,
        default=REPO_ROOT / "data_processed" / "figure6_source.xlsx",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    build_figure(args.output, args.table_path)
