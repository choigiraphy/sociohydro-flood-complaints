from __future__ import annotations

from pathlib import Path
import argparse

from matplotlib.lines import Line2D
from matplotlib.patches import ConnectionPatch
import matplotlib.dates as mdates
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import pandas as pd
try:
    import seaborn as sns
except ImportError:  # pragma: no cover
    sns = None

from wrr_figure_support import (
    BASE_FIG_DIR,
    DEFAULT_PATHS,
    apply_wrr_style,
    load_daily_complaints,
    load_daily_hydro,
    maybe_load_optional_series,
    normalize_0_100,
    parse_date_series,
    read_2col_timeseries,
)


FLOOD_PERIODS = {
    "2022": ("2022-08-08", "2022-08-21"),
    "2023": ("2023-07-10", "2023-07-23"),
}

COLORS = {
    "precip": "#2E6FBB",
    "complaints": "#C33C54",
    "google": "#E3A008",
    "naver": "#4F7A6A",
    "news": "#8B9097",
}


def _load_news_daily() -> pd.Series | None:
    candidates = [
        Path("/Volumes/Keywest_JetDrive/데이터저장소/Bigkinds_20210101-20231231_flood_nationwide_boradcast.xlsx"),
        Path("/Volumes/Keywest_JetDrive/데이터저장소/NewsResult_20210101-20231231_홍수.xlsx"),
        Path("/Volumes/Keywest_JetDrive 1/데이터저장소/Bigkinds_20210101-20231231_flood_nationwide_boradcast.xlsx"),
        Path("/Volumes/Keywest_JetDrive 1/데이터저장소/NewsResult_20210101-20231231_홍수.xlsx"),
    ]
    for path in candidates:
        if not path.exists():
            continue
        df = pd.read_excel(path, usecols=[1])
        df.columns = ["date"]
        df["date"] = parse_date_series(df["date"]).dt.normalize()
        df = df.dropna(subset=["date"])
        return df.groupby("date").size().astype(float).sort_index()
    return None


def _load_news_weekly_from_csv() -> pd.Series | None:
    candidates = [
        Path("/Volumes/Keywest_JetDrive/데이터저장소/amCharts_홍수_weekly_bigkinds.csv"),
        Path("/Volumes/Keywest_JetDrive 1/데이터저장소/amCharts_홍수_weekly_bigkinds.csv"),
        DEFAULT_PATHS["news_weekly"],
    ]
    for path in candidates:
        if not path.exists():
            continue
        return read_2col_timeseries(path)
    return None


def _load_all_series() -> tuple[pd.DataFrame, pd.DataFrame]:
    precip_daily, _ = load_daily_hydro(DEFAULT_PATHS["daily_hydro"])
    complaint_daily = load_daily_complaints(DEFAULT_PATHS["complaints_daily"])
    naver_daily = read_2col_timeseries(DEFAULT_PATHS["naver_weekly"])
    google_daily = read_2col_timeseries(DEFAULT_PATHS["google_daily"])
    google_weekly = read_2col_timeseries(DEFAULT_PATHS["google_weekly"])
    news_daily = _load_news_daily()

    daily = pd.concat(
        {
            "Precipitation": precip_daily,
            "Complaints": complaint_daily,
            "Google": google_daily,
            "Naver": naver_daily,
        },
        axis=1,
    ).sort_index()
    if news_daily is not None:
        daily["News Volume"] = news_daily.reindex(daily.index).fillna(0.0)

    weekly = pd.DataFrame(index=pd.date_range(daily.index.min(), daily.index.max(), freq="W-SUN"))
    weekly["Precipitation"] = normalize_0_100(daily["Precipitation"].resample("W-SUN").sum()).reindex(weekly.index)
    weekly["Complaints"] = normalize_0_100(daily["Complaints"].resample("W-SUN").sum()).reindex(weekly.index)
    weekly["Google"] = normalize_0_100(google_weekly.resample("W-SUN").mean()).reindex(weekly.index)
    weekly["Naver"] = normalize_0_100(daily["Naver"].resample("W-SUN").mean()).reindex(weekly.index)

    news_weekly = _load_news_weekly_from_csv()
    if news_weekly is not None:
        weekly["News Volume"] = normalize_0_100(news_weekly.resample("W-SUN").sum()).reindex(weekly.index)

    return daily, weekly


def _scaled_window(window: pd.DataFrame) -> pd.DataFrame:
    scaled = pd.DataFrame(index=window.index)
    for column in window.columns:
        scaled[column] = normalize_0_100(window[column]).round(0)
    return scaled


def _date_ticklabels(index: pd.DatetimeIndex, month_label: str) -> list[str]:
    labels = [f"{dt.day:02d}" for dt in index]
    if labels:
        labels[0] = f"{labels[0]}\n{month_label}"
    return labels


def _draw_window_lines(ax: plt.Axes, year: str, start: pd.Timestamp, end: pd.Timestamp) -> None:
    linestyle = "-" if year == "2022" else "--"
    ax.axvline(start, color="black", linestyle=linestyle, linewidth=1.8, alpha=0.9)
    ax.axvline(end, color="black", linestyle=linestyle, linewidth=1.8, alpha=0.9)


def _annotate_heatmap(ax: plt.Axes, data: pd.DataFrame, use_half_offset: bool = True) -> None:
    arr = data.to_numpy(dtype=float)
    for i in range(arr.shape[0]):
        for j in range(arr.shape[1]):
            value = arr[i, j]
            if pd.isna(value):
                continue
            txt_color = "#1F252B" if value <= 55 else "white"
            stroke = "white" if txt_color == "#1F252B" else "#1F252B"
            x = j + 0.5 if use_half_offset else j
            y = i + 0.5 if use_half_offset else i
            ax.text(
                x,
                y,
                f"{value:.0f}",
                ha="center",
                va="center",
                fontsize=9.5,
                color=txt_color,
                path_effects=[pe.withStroke(linewidth=1.2, foreground=stroke, alpha=0.35)],
            )


def _draw_heatmap(ax: plt.Axes, data: pd.DataFrame, cmap, show_cbar: bool, cbar_label: str | None = None) -> None:
    if sns is not None:
        sns.heatmap(
            data,
            ax=ax,
            cmap=cmap,
            annot=False,
            linewidths=0.8,
            linecolor="white",
            vmin=0,
            vmax=100,
            cbar=show_cbar,
            cbar_kws={"label": cbar_label, "fraction": 0.035, "pad": 0.02} if show_cbar and cbar_label else None,
        )
        if show_cbar and ax.collections and cbar_label:
            cbar = ax.collections[0].colorbar
            if cbar is not None:
                cbar.set_label(cbar_label, rotation=270, labelpad=18)
        _annotate_heatmap(ax, data, use_half_offset=True)
        return

    arr = data.to_numpy(dtype=float)
    im = ax.imshow(arr, aspect="auto", cmap=cmap, vmin=0, vmax=100)
    ax.set_xticks(range(arr.shape[1]))
    ax.set_yticks(range(arr.shape[0]))
    _annotate_heatmap(ax, data, use_half_offset=False)
    if show_cbar:
        cbar = plt.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
        if cbar_label:
            cbar.set_label(cbar_label, rotation=270, labelpad=18)


def build_figure(output_path: Path) -> None:
    apply_wrr_style()
    daily, weekly = _load_all_series()

    fig = plt.figure(figsize=(13.2, 14.8))
    outer = gridspec.GridSpec(
        4,
        2,
        figure=fig,
        height_ratios=[3.25, 2.15, 1.55, 2.15],
        width_ratios=[1, 1],
        hspace=0.42,
        wspace=0.32,
    )

    ax_a = fig.add_subplot(outer[0, :])

    for column, color, width in [
        ("Precipitation", COLORS["precip"], 2.5),
        ("Complaints", COLORS["complaints"], 2.8),
        ("Google", COLORS["google"], 2.0),
        ("Naver", COLORS["naver"], 2.0),
        ("News Volume", COLORS["news"], 2.0),
    ]:
        if column in weekly.columns:
            ax_a.plot(weekly.index, weekly[column], color=color, linewidth=width)

    for year, (start_str, end_str) in FLOOD_PERIODS.items():
        _draw_window_lines(ax_a, year, pd.Timestamp(start_str), pd.Timestamp(end_str))

    ax_a.set_ylim(-2, 102)
    ax_a.set_yticks([0, 20, 40, 60, 80, 100])
    ax_a.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 5, 9]))
    ax_a.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))
    ax_a.grid(True, axis="both", color="#edf1f4", linewidth=0.6)
    ax_a.text(-0.13, 1.045, "(a)", transform=ax_a.transAxes, fontsize=14, fontweight="bold", va="top")

    legend_handles = [
        Line2D([0], [0], color="black", linewidth=1.8, linestyle="-", label="Flood window 2022 (solid)"),
        Line2D([0], [0], color="black", linewidth=1.8, linestyle="--", label="Flood window 2023 (dashed)"),
        Line2D([0], [0], color=COLORS["precip"], linewidth=2.5, label="Precipitation (weekly sum, rescaled 0 - 100)"),
        Line2D([0], [0], color=COLORS["complaints"], linewidth=2.8, label="Complaints (weekly sum, rescaled 0 - 100)"),
        Line2D([0], [0], color=COLORS["google"], linewidth=2.0, label="Google Trends (rescaled 0 - 100 within period)"),
        Line2D([0], [0], color=COLORS["naver"], linewidth=2.0, label="Naver Datalab (rescaled 0 - 100 within period)"),
    ]
    if "News Volume" in weekly.columns:
        legend_handles.append(
            Line2D([0], [0], color=COLORS["news"], linewidth=2.0, label="News volume (weekly sum, rescaled 0 - 100)")
        )
    fig.legend(
        handles=legend_handles,
        loc="upper center",
        ncol=3,
        frameon=False,
        bbox_to_anchor=(0.5, 0.992),
        borderaxespad=0.0,
        handlelength=2.8,
        columnspacing=1.5,
        fontsize=9.9,
    )

    top_window_axes: dict[str, plt.Axes] = {}
    heatmap_axes: dict[str, plt.Axes] = {}

    for col_idx, year in enumerate(["2022", "2023"]):
        start_str, end_str = FLOOD_PERIODS[year]
        start = pd.Timestamp(start_str)
        end = pd.Timestamp(end_str)
        window = daily.loc[start:end, [c for c in ["Precipitation", "Complaints", "Google", "Naver", "News Volume"] if c in daily.columns]].copy()
        scaled = _scaled_window(window)

        ax_top = fig.add_subplot(outer[1, col_idx])
        top_window_axes[year] = ax_top
        for column, color in [
            ("Precipitation", COLORS["precip"]),
            ("Complaints", COLORS["complaints"]),
            ("Google", COLORS["google"]),
            ("Naver", COLORS["naver"]),
            ("News Volume", COLORS["news"]),
        ]:
            if column in scaled.columns:
                ax_top.plot(scaled.index, scaled[column], color=color, linewidth=2.0)
        _draw_window_lines(ax_top, year, start, end)
        ax_top.set_ylim(0, 102)
        ax_top.set_yticks([0, 25, 50, 75, 100])
        ax_top.set_xticks([start, end])
        ax_top.set_xticklabels([start.strftime("%d"), end.strftime("%d")], fontsize=12)
        ax_top.text(0.5, -0.21, start.strftime("%b"), transform=ax_top.transAxes, ha="center", va="top", fontsize=16)
        ax_top.text(
            1.07,
            0.5,
            f"{year} window",
            transform=ax_top.transAxes,
            rotation=-90,
            va="center",
            ha="left",
            fontsize=16,
            fontweight="bold",
        )
        ax_top.grid(True, color="#efefef", linewidth=0.8)
        ax_top.text(-0.16, 1.08, f"({'bc'[col_idx]})", transform=ax_top.transAxes, fontsize=14, fontweight="bold", va="top")

        ax_heat = fig.add_subplot(outer[2, col_idx])
        heatmap_axes[year] = ax_heat
        row_order = [c for c in ["Precipitation", "Complaints", "Naver", "Google", "News Volume"] if c in scaled.columns]
        cmap = sns.light_palette("#c91414", as_cmap=True) if sns is not None else plt.get_cmap("Reds")
        _draw_heatmap(
            ax_heat,
            scaled[row_order].T,
            cmap=cmap,
            show_cbar=(year == "2023"),
            cbar_label="% of max intensity" if year == "2023" else None,
        )
        if year == "2022":
            ax_heat.set_yticklabels(row_order, rotation=0, fontsize=10)
        else:
            ax_heat.set_yticklabels([])
        month_label = "Aug" if year == "2022" else "Jul"
        ax_heat.set_xticklabels(_date_ticklabels(window.index, month_label), rotation=0, fontsize=9)
        ax_heat.set_xlabel("")
        ax_heat.set_ylabel("")
        ax_heat.text(-0.16, 1.16, f"({'de'[col_idx]})", transform=ax_heat.transAxes, fontsize=14, fontweight="bold", va="top")
        ax_heat.text(0.0, 1.11, year, transform=ax_heat.transAxes, fontsize=15, fontweight="bold")

        bottom_spec = outer[3, col_idx].subgridspec(2, 1, hspace=0.12)
        ax_precip = fig.add_subplot(bottom_spec[0, 0])
        ax_comp = fig.add_subplot(bottom_spec[1, 0], sharex=ax_precip)

        ax_precip.fill_between(window.index, window["Precipitation"], color=COLORS["precip"], alpha=0.25)
        ax_precip.plot(window.index, window["Precipitation"], color=COLORS["precip"], linewidth=2.1)
        ax_comp.fill_between(window.index, window["Complaints"], color=COLORS["complaints"], alpha=0.20)
        ax_comp.plot(window.index, window["Complaints"], color=COLORS["complaints"], linewidth=2.1)

        for ax in [ax_precip, ax_comp]:
            ax.grid(True, color="#efefef", linewidth=0.8)
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
        ax_precip.tick_params(axis="x", which="both", labelbottom=False, bottom=False)
        ax_comp.set_xticks(window.index)
        ax_comp.set_xticklabels(_date_ticklabels(window.index, month_label), rotation=0, fontsize=9)

        if year == "2022":
            ax_precip.set_ylabel("National Avg.\nPrecipitation", fontsize=10)
            ax_comp.set_ylabel("Complaints", fontsize=10)
            ax_precip.text(-0.18, 1.26, "(f)", transform=ax_precip.transAxes, fontsize=14, fontweight="bold", va="top")
        else:
            ax_precip.set_ylabel("")
            ax_comp.set_ylabel("")
            ax_precip.text(-0.18, 1.26, "(g)", transform=ax_precip.transAxes, fontsize=14, fontweight="bold", va="top")

        total = int(window["Complaints"].sum())
        ax_comp.text(
            0.97,
            0.84,
            f"{total} in total",
            transform=ax_comp.transAxes,
            ha="right",
            va="center",
            color=COLORS["complaints"],
            fontsize=11.2,
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.82, pad=1.0),
        )
        ax_precip.set_yticks([])
        ax_comp.set_yticks([])

    ax_a.add_artist(
        ConnectionPatch(
            xyA=(mdates.date2num(pd.Timestamp("2022-08-08")), 0),
            coordsA=ax_a.transData,
            xyB=(0.50, 1.02),
            coordsB=top_window_axes["2022"].transAxes,
            color="black",
            linewidth=1.0,
        )
    )
    ax_a.add_artist(
        ConnectionPatch(
            xyA=(mdates.date2num(pd.Timestamp("2022-08-21")), 0),
            coordsA=ax_a.transData,
            xyB=(0.62, 1.02),
            coordsB=top_window_axes["2022"].transAxes,
            color="black",
            linewidth=1.0,
        )
    )
    ax_a.add_artist(
        ConnectionPatch(
            xyA=(mdates.date2num(pd.Timestamp("2023-07-10")), 0),
            coordsA=ax_a.transData,
            xyB=(0.38, 1.02),
            coordsB=top_window_axes["2023"].transAxes,
            color="black",
            linewidth=1.0,
            linestyle=":",
        )
    )
    ax_a.add_artist(
        ConnectionPatch(
            xyA=(mdates.date2num(pd.Timestamp("2023-07-23")), 0),
            coordsA=ax_a.transData,
            xyB=(0.62, 1.02),
            coordsB=top_window_axes["2023"].transAxes,
            color="black",
            linewidth=1.0,
            linestyle=":",
        )
    )

    fig.canvas.draw()
    for tick in ax_a.get_xticklabels():
        if tick.get_text() == "May\n2022":
            tick.set_bbox(dict(facecolor="#D7DEE6", edgecolor="none", alpha=0.45, pad=0.9))
            break

    plt.subplots_adjust(top=0.90)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate manuscript-aligned Figure 4")
    parser.add_argument("--output", type=Path, default=BASE_FIG_DIR / "Figure4_WRR.png")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    build_figure(args.output)
