from __future__ import annotations

from pathlib import Path

import matplotlib.colors as mcolors
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.patches import Rectangle
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
STYLE_PATH = ROOT / "code" / "agu_manuscript_figures.mplstyle"
DATA_DIR = ROOT / "data_processed"
FIG_DIR = ROOT / "figures"

FIG2_SOURCE = DATA_DIR / "figure2_source.xlsx"
FIG3_SOURCE = DATA_DIR / "figure3_source.xlsx"

OUT_FIG2 = FIG_DIR / "Figure2_WRR.png"
OUT_FIG3 = FIG_DIR / "Figure3_WRR.png"

FLOOD_WINDOWS = {
    "2022": ("2022-08-08", "2022-08-21"),
    "2023": ("2023-07-10", "2023-07-23"),
}

PAIR_STYLE = {
    "complaint_line": "#C33C54",
    "precip_line": "#2E6FBB",
    "frame": "#4A4A4A",
    "grid": "#EDF1F4",
}


def apply_style() -> None:
    if STYLE_PATH.exists():
        plt.style.use(str(STYLE_PATH))
    plt.rcParams.update(
        {
            "axes.grid": True,
            "grid.color": PAIR_STYLE["grid"],
            "grid.linewidth": 0.6,
            "grid.alpha": 1.0,
        }
    )


def _load_figure2_source() -> tuple[pd.DataFrame, pd.DataFrame]:
    national = pd.read_excel(FIG2_SOURCE, sheet_name="national_weekly")
    regional = pd.read_excel(FIG2_SOURCE, sheet_name="regional_weekly")
    national["week_start"] = pd.to_datetime(national["week_start"])
    regional["week_start"] = pd.to_datetime(regional["week_start"])
    return national, regional


def _load_figure3_source() -> tuple[pd.DataFrame, pd.DataFrame]:
    national = pd.read_excel(FIG3_SOURCE, sheet_name="national_weekly")
    regional = pd.read_excel(FIG3_SOURCE, sheet_name="regional_weekly")
    national["week_start"] = pd.to_datetime(national["week_start"])
    regional["week_start"] = pd.to_datetime(regional["week_start"])
    return national, regional


def _make_heatmap_matrix(df: pd.DataFrame, value_col: str) -> pd.DataFrame:
    region_order = (
        df[["region_eng", "region_order"]]
        .drop_duplicates()
        .sort_values("region_order")
    )
    matrix = (
        df.pivot(index="region_eng", columns="week_start", values=value_col)
        .reindex(region_order["region_eng"].tolist())
    )
    return matrix.fillna(0.0)


def _add_flood_boxes_line(ax: plt.Axes, x_dates: pd.Series, ymax: float) -> None:
    for year, (start_str, end_str) in FLOOD_WINDOWS.items():
        start = pd.Timestamp(start_str)
        end = pd.Timestamp(end_str)
        linestyle = "-" if year == "2022" else "--"
        width = end - start
        rect = Rectangle(
            (mdates.date2num(start), 0),
            width.days,
            ymax,
            fill=False,
            edgecolor="black",
            linewidth=1.4,
            linestyle=linestyle,
            zorder=5,
        )
        ax.add_patch(rect)


def _draw_window_bounds(ax: plt.Axes, year: str, start: pd.Timestamp, end: pd.Timestamp) -> None:
    linestyle = "-" if year == "2022" else "--"
    ax.axvline(start, color="black", linestyle=linestyle, linewidth=1.2, alpha=0.9, zorder=5)
    ax.axvline(end, color="black", linestyle=linestyle, linewidth=1.2, alpha=0.9, zorder=5)


def _configure_month_ticks(ax: plt.Axes, dates: pd.Series) -> None:
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 5, 9]))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))
    ax.set_xlim(dates.min(), dates.max())


def _weekly_edges(dates: pd.DatetimeIndex) -> np.ndarray:
    if len(dates) == 1:
        return mdates.date2num([dates[0] - pd.Timedelta(days=3.5), dates[0] + pd.Timedelta(days=3.5)])

    edges = [dates[0] - (dates[1] - dates[0]) / 2]
    for left, right in zip(dates[:-1], dates[1:]):
        edges.append(left + (right - left) / 2)
    edges.append(dates[-1] + (dates[-1] - dates[-2]) / 2)
    return mdates.date2num(pd.to_datetime(edges))


def _plot_context_pair(
    national: pd.DataFrame,
    regional: pd.DataFrame,
    national_value_col: str,
    regional_value_col: str,
    line_color: str,
    cmap_colors: list[str],
    ylabel_top: str,
    cbar_label: str,
    output_path: Path,
) -> None:
    matrix = _make_heatmap_matrix(regional, regional_value_col)
    dates = pd.to_datetime(matrix.columns)
    xmin = dates.min()
    xmax = dates.max()

    fig = plt.figure(figsize=(12.8, 7.8))
    gs = gridspec.GridSpec(2, 1, height_ratios=[1.0, 2.0], hspace=0.26)
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[1, 0], sharex=ax1)

    top = national.set_index("week_start")[national_value_col].reindex(dates)
    ax1.plot(dates, top.values, color=line_color, linewidth=2.2, zorder=3)
    ymax = float(np.nanmax(top.values) * 1.18) if np.isfinite(top.values).any() else 1.0
    ax1.set_ylim(0, ymax)
    _add_flood_boxes_line(ax1, dates.to_series(), ymax)
    _configure_month_ticks(ax1, dates.to_series())
    ax1.set_xlim(xmin, xmax)
    ax1.set_ylabel(ylabel_top, fontweight="semibold")
    ax1.set_title("(a)", loc="left", fontweight="bold", fontsize=14, pad=8)
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)
    ax1.grid(True, axis="y")
    ax1.tick_params(axis="x", labelbottom=False)

    cmap = mcolors.LinearSegmentedColormap.from_list("context_seq", cmap_colors, N=256)
    vmax = np.nanpercentile(matrix.values[np.isfinite(matrix.values)], 95) if np.isfinite(matrix.values).any() else 1.0
    vmax = max(vmax, 1.0)
    x_edges = _weekly_edges(dates)
    y_edges = np.arange(matrix.shape[0] + 1)
    im = ax2.pcolormesh(x_edges, y_edges, matrix.values, shading="flat", cmap=cmap, vmin=0, vmax=vmax)
    ax2.set_yticks(np.arange(matrix.shape[0]) + 0.5)
    ax2.set_yticklabels(matrix.index)
    ax2.invert_yaxis()
    _configure_month_ticks(ax2, dates.to_series())
    ax2.set_xlim(xmin, xmax)
    ax2.set_title("(b)", loc="left", fontweight="bold", fontsize=14, pad=8)
    ax2.set_xlabel("Time period (weekly)", fontweight="semibold")
    ax2.set_ylabel("Administrative regions", fontweight="semibold")
    ax2.grid(False)
    for year, (start_str, end_str) in FLOOD_WINDOWS.items():
        _draw_window_bounds(ax2, year, pd.Timestamp(start_str), pd.Timestamp(end_str))

    cbar = fig.colorbar(im, ax=ax2, fraction=0.025, pad=0.02)
    cbar.set_label(cbar_label, rotation=270, labelpad=18, fontweight="semibold")

    line_proxy = plt.Line2D([0], [0], color=line_color, lw=2.2, label=ylabel_top)
    box_2022 = Rectangle((0, 0), 1, 1, fill=False, edgecolor="black", linewidth=1.2, linestyle="-", label="2022 flood window")
    box_2023 = Rectangle((0, 0), 1, 1, fill=False, edgecolor="black", linewidth=1.2, linestyle="--", label="2023 flood window")
    fig.legend(
        handles=[line_proxy, box_2022, box_2023],
        loc="upper center",
        ncol=3,
        frameon=False,
        bbox_to_anchor=(0.5, 0.995),
        columnspacing=1.8,
        handlelength=2.8,
    )
    fig.subplots_adjust(top=0.90)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=300, bbox_inches="tight", pad_inches=0.04)
    plt.close(fig)


def generate_figure2() -> Path:
    national, regional = _load_figure2_source()
    _plot_context_pair(
        national=national,
        regional=regional,
        national_value_col="complaint_count",
        regional_value_col="complaint_count",
        line_color=PAIR_STYLE["complaint_line"],
        cmap_colors=["#ffffff", "#F7D5DB", "#E996A7", "#C33C54", "#8E2339"],
        ylabel_top="Complaint count",
        cbar_label="Weekly complaints",
        output_path=OUT_FIG2,
    )
    return OUT_FIG2


def generate_figure3() -> Path:
    national, regional = _load_figure3_source()
    _plot_context_pair(
        national=national,
        regional=regional,
        national_value_col="national_precip_sum",
        regional_value_col="precipitation_mm",
        line_color=PAIR_STYLE["precip_line"],
        cmap_colors=["#ffffff", "#DBE8F6", "#9EC3E6", "#5E96CF", "#2E6FBB"],
        ylabel_top="Precipitation (mm)",
        cbar_label="Weekly precipitation (mm)",
        output_path=OUT_FIG3,
    )
    return OUT_FIG3


def main() -> None:
    apply_style()
    print(generate_figure2())
    print(generate_figure3())


if __name__ == "__main__":
    main()
