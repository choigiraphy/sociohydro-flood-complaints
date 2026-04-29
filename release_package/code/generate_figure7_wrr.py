from __future__ import annotations

import argparse
from pathlib import Path

import geopandas as gpd
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.ticker import FuncFormatter
import pandas as pd

from wrr_figure_support import REPO_ROOT, apply_wrr_style, resolve_first_existing


EMOTION_ORDER = [
    "Suspicion/Mistrust",
    "Anger/Rage",
    "Sadness",
]
EVENT_ORDER = ["Flood 2022", "Flood 2023"]
PANEL_LABELS = [["(a)", "(b)", "(c)"], ["(d)", "(e)", "(f)"]]
BOUNDARY_PATH = resolve_first_existing(
    Path("/Volumes/Keywest_JetDrive/데이터저장소/final_final/LX법정구역경계_시도_전국/SIDO.shp"),
    Path("/Volumes/Keywest_JetDrive 1/데이터저장소/final_final/LX법정구역경계_시도_전국/SIDO.shp"),
)
XTICKS = [125, 127, 129, 131]
YTICKS = [34, 35, 36, 37, 38]
REGION_NAME_MAP = {
    "서울특별시": "Seoul",
    "부산광역시": "Busan",
    "대구광역시": "Daegu",
    "인천광역시": "Incheon",
    "광주광역시": "Gwangju",
    "대전광역시": "Daejeon",
    "울산광역시": "Ulsan",
    "세종특별자치시": "Sejong",
    "경기도": "Gyeonggi",
    "강원특별자치도": "Gangwon",
    "강원도": "Gangwon",
    "충청북도": "Chungbuk",
    "충청남도": "Chungnam",
    "전북특별자치도": "Jeonbuk",
    "전라북도": "Jeonbuk",
    "전라남도": "Jeonnam",
    "경상북도": "Gyeongbuk",
    "경상남도": "Gyeongnam",
    "제주특별자치도": "Jeju",
}
CANONICAL_CTPR = {
    "강원도": "강원특별자치도",
    "전라북도": "전북특별자치도",
}


def load_national_boundaries() -> gpd.GeoDataFrame:
    gdf = gpd.read_file(BOUNDARY_PATH)
    gdf["region_eng"] = gdf["ctpr_nm"].map(REGION_NAME_MAP)
    return gdf[["ctpr_nm", "region_eng", "geometry"]].to_crs(epsg=4326)


def load_region_shift(path: Path) -> gpd.GeoDataFrame:
    workbook = pd.ExcelFile(path)
    if "region_emotion_shift" in workbook.sheet_names:
        df = pd.read_excel(path, sheet_name="region_emotion_shift").copy()
        df["emotion"] = df["emotion"].replace({"Sad/Disappointed": "Sadness"})
        df["sufficient_data"] = df["meets_min_count"].fillna(False)
        df = df.rename(columns={"delta_prop": "delta_share"})
        shapes = load_national_boundaries()
        return shapes.merge(
            df[["region_eng", "ctpr_nm", "event", "emotion", "delta_share", "sufficient_data"]],
            on=["region_eng", "ctpr_nm"],
            how="left",
        )

    records = []
    sheet_map = {
        "DeltaScore_2022": "Flood 2022",
        "DeltaScore_2023": "Flood 2023",
    }
    for sheet_name, event in sheet_map.items():
        wide = pd.read_excel(path, sheet_name=sheet_name)
        wide = wide.rename(columns={"Region": "ctpr_nm"})
        wide["ctpr_nm"] = wide["ctpr_nm"].replace(CANONICAL_CTPR)
        wide = wide.loc[wide["ctpr_nm"].notna()].copy()
        wide = wide.loc[wide["ctpr_nm"] != "NONE"].copy()
        for emotion in EMOTION_ORDER:
            subset = wide[["ctpr_nm", emotion]].copy()
            subset = subset.rename(columns={emotion: "delta_share"})
            subset["event"] = event
            subset["emotion"] = emotion
            subset["sufficient_data"] = subset["delta_share"].notna()
            records.append(subset)

    df = pd.concat(records, ignore_index=True)
    shapes = load_national_boundaries()
    return shapes.merge(df, on="ctpr_nm", how="left")


def _configure_geo_axis(ax: plt.Axes, bounds: tuple[float, float, float, float], show_x: bool, show_y: bool) -> None:
    xmin, ymin, xmax, ymax = bounds
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    ax.set_aspect("equal")
    ax.set_xticks(XTICKS)
    ax.set_yticks(YTICKS)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"{x:.0f}°E"))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda y, pos: f"{y:.0f}°N"))
    ax.tick_params(axis="both", labelsize=8.5, length=3, color="#6A737D")
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
    shifts = load_region_shift(table_path)

    values = shifts.loc[shifts["sufficient_data"] == True, "delta_share"].dropna()
    vmax = max(0.12, float(values.abs().max())) if not values.empty else 0.12
    norm = mcolors.TwoSlopeNorm(vmin=-vmax, vcenter=0.0, vmax=vmax)
    cmap = plt.get_cmap("RdBu_r")

    fig, axes = plt.subplots(2, 3, figsize=(15.2, 10.6))
    has_invalid = False
    bounds = tuple(shifts.total_bounds)

    for row_idx, event in enumerate(EVENT_ORDER):
        for col_idx, emotion in enumerate(EMOTION_ORDER):
            ax = axes[row_idx, col_idx]
            subset = shifts.loc[
                (shifts["event"] == event) & (shifts["emotion"] == emotion)
            ].copy()
            valid = subset.loc[subset["sufficient_data"] == True].copy()
            invalid = subset.loc[subset["sufficient_data"] != True].copy()

            subset.plot(
                ax=ax,
                facecolor="#F5F7F9",
                edgecolor="#C4CBD3",
                linewidth=0.45,
            )
            if not valid.empty:
                valid.plot(
                    column="delta_share",
                    cmap=cmap,
                    norm=norm,
                    ax=ax,
                    edgecolor="#5F6670",
                    linewidth=0.55,
                    legend=False,
                )
            if not invalid.empty:
                invalid.plot(
                    ax=ax,
                    facecolor="#F3F5F7",
                    edgecolor="#8B939B",
                    linewidth=0.55,
                    hatch="///",
                )
                has_invalid = True

            _configure_geo_axis(ax, bounds, show_x=(row_idx == 1), show_y=(col_idx == 0))
            ax.text(
                0.02,
                0.98,
                PANEL_LABELS[row_idx][col_idx],
                transform=ax.transAxes,
                va="top",
                fontsize=14,
                fontweight="bold",
                bbox=dict(facecolor="white", edgecolor="none", pad=0.4, alpha=0.85),
            )
            if row_idx == 0:
                ax.set_title(emotion, fontsize=13.5, fontweight="semibold", pad=8)
            if col_idx == 0:
                ax.text(
                    -0.12,
                    0.50,
                    "2022" if event == "Flood 2022" else "2023",
                    transform=ax.transAxes,
                    rotation=90,
                    va="center",
                    ha="center",
                    fontsize=14,
                    fontweight="semibold",
                )

    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    cax = fig.add_axes([0.90, 0.22, 0.024, 0.56])
    cbar = fig.colorbar(sm, cax=cax)
    cbar.set_label(r"$\Delta$ Proportion (Flood $-$ baseline)", fontsize=12, fontweight="semibold", rotation=270, labelpad=18)
    cbar.ax.tick_params(labelsize=10)

    if has_invalid:
        invalid_patch = Patch(facecolor="#F3F5F7", edgecolor="#8B939B", hatch="///", label="Insufficient data (N < 5)")
        fig.legend(handles=[invalid_patch], loc="lower right", bbox_to_anchor=(0.94, 0.06), fontsize=10, frameon=False)

    plt.subplots_adjust(left=0.07, right=0.88, top=0.93, bottom=0.06, hspace=0.06, wspace=0.04)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate manuscript-aligned WRR Figure 7")
    parser.add_argument("--output", type=Path, default=REPO_ROOT / "figures" / "Figure7_WRR.png")
    parser.add_argument(
        "--table-path",
        type=Path,
        default=REPO_ROOT / "data_processed" / "figure7_source.xlsx",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    build_figure(args.output, args.table_path)
