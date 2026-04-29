from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
import numpy as np
import pandas as pd
import seaborn as sns


FIG_DPI = 300
FLOOD_WINDOWS = [
    ("2022-08-08", "2022-08-21", "Flood 2022"),
    ("2023-07-17", "2023-07-30", "Flood 2023"),
]

EMOTION_COLORS = {
    "Anxiety/Worried": "#c74b50",
    "Complaint": "#6b7a8f",
    "Anger/Rage": "#8a2d3b",
    "Sad/Disappointed": "#4f6d8a",
    "Suspicion/Mistrust": "#b06c49",
    "Expectation": "#9f8f43",
    "Irritation": "#935d7f",
    "Embarrassment/Distress": "#5e7d66",
    "Other": "#bdbdbd",
}

COMPARISON_ORDER = [
    "Flood 2022 - Ordinary",
    "Flood 2023 - Ordinary",
    "Flood 2022 - Flood 2023",
]


def apply_lab_style() -> None:
    sns.set_theme(style="whitegrid")
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
            "axes.edgecolor": "#4a4a4a",
            "axes.labelcolor": "#222222",
            "xtick.color": "#222222",
            "ytick.color": "#222222",
            "grid.color": "#d9d9d9",
            "grid.linewidth": 0.8,
            "axes.grid": True,
            "axes.axisbelow": True,
            "font.family": ["AppleGothic", "Arial Unicode MS", "DejaVu Sans"],
            "font.size": 13,
            "axes.titlesize": 16,
            "axes.labelsize": 14,
            "xtick.labelsize": 12,
            "ytick.labelsize": 12,
            "legend.fontsize": 11,
            "axes.unicode_minus": False,
        }
    )


def save_figure(fig: plt.Figure, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=FIG_DPI, bbox_inches="tight")
    plt.close(fig)


def make_time_series_figure(daily_national: pd.DataFrame, output_path: Path) -> None:
    fig, ax1 = plt.subplots(figsize=(16, 6))
    ax2 = ax1.twinx()

    ax2.bar(
        daily_national["date"],
        daily_national["precipitation_mm"],
        width=1.0,
        color="#8fb9d8",
        alpha=0.6,
        label="Mean precipitation",
    )
    ax1.plot(
        daily_national["date"],
        daily_national["complaint_count"],
        color="#b33b44",
        linewidth=2.2,
        label="Complaint count",
    )

    for start, end, label in FLOOD_WINDOWS:
        ax1.axvspan(pd.Timestamp(start), pd.Timestamp(end), color="#d9c27a", alpha=0.25)
        ax1.text(
            pd.Timestamp(start) + (pd.Timestamp(end) - pd.Timestamp(start)) / 2,
            ax1.get_ylim()[1] * 0.95 if ax1.get_ylim()[1] > 0 else 1,
            label,
            ha="center",
            va="top",
            fontsize=11,
        )

    ax1.set_title("Daily civil complaints and precipitation, 2021-2023")
    ax1.set_xlabel("Date")
    ax1.set_ylabel("Complaint count")
    ax2.set_ylabel("Mean precipitation (mm/day)")
    ax1.legend(loc="upper left", frameon=True)
    ax2.legend(loc="upper right", frameon=True)
    fig.autofmt_xdate()
    save_figure(fig, output_path)


def make_region_distribution_figure(region_totals: pd.DataFrame, output_path: Path) -> None:
    plot_df = region_totals.sort_values("complaint_count", ascending=True)
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.barh(plot_df["region"], plot_df["complaint_count"], color="#56748c")
    ax.set_title("Total complaints by province")
    ax.set_xlabel("Complaint count")
    ax.set_ylabel("")
    save_figure(fig, output_path)


def make_emotion_distribution_figure(period_top1: pd.DataFrame, output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(11, 6))
    periods = period_top1["period"].drop_duplicates().tolist()
    bottom = np.zeros(len(periods))

    pivot = period_top1.pivot(index="period", columns="emotion", values="share").fillna(0)
    emotion_order = [emotion for emotion in EMOTION_COLORS if emotion in pivot.columns]

    for emotion in emotion_order:
        values = pivot.loc[periods, emotion].to_numpy()
        ax.bar(
            periods,
            values,
            bottom=bottom,
            color=EMOTION_COLORS.get(emotion, "#bdbdbd"),
            label=emotion,
        )
        bottom = bottom + values

    ax.set_ylim(0, 1.0)
    ax.set_ylabel("Share of dominant emotion")
    ax.set_title("Dominant emotion composition by period")
    ax.yaxis.set_major_formatter(PercentFormatter(1.0))
    ax.legend(loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=True)
    save_figure(fig, output_path)


def make_bootstrap_forest_plot(bootstrap_results: pd.DataFrame, output_path: Path) -> None:
    emotions = (
        bootstrap_results.groupby("emotion")["mean_diff"]
        .mean()
        .sort_values()
        .index.tolist()
    )
    fig, axes = plt.subplots(1, 3, figsize=(18, 8), sharey=True)

    for ax, comparison in zip(axes, COMPARISON_ORDER):
        subset = bootstrap_results.loc[bootstrap_results["comparison"] == comparison].copy()
        subset["emotion"] = pd.Categorical(subset["emotion"], categories=emotions, ordered=True)
        subset = subset.sort_values("emotion")

        color = "#b33b44" if "Ordinary" in comparison else "#56748c"
        ax.errorbar(
            subset["mean_diff"],
            subset["emotion"],
            xerr=[
                subset["mean_diff"] - subset["ci_lower"],
                subset["ci_upper"] - subset["mean_diff"],
            ],
            fmt="o",
            color=color,
            ecolor="#4a4a4a",
            elinewidth=1.4,
            capsize=4,
        )
        ax.axvline(0, color="#333333", linestyle="--", linewidth=1)
        ax.set_title(comparison.replace(" - ", "\nvs\n"))
        ax.set_xlabel("Mean difference")

    axes[0].set_ylabel("")
    fig.suptitle("Bootstrap mean differences with 95% confidence intervals", y=0.98)
    save_figure(fig, output_path)


def load_province_geometries(boundary_path: Path) -> gpd.GeoDataFrame:
    prefix_to_region = {
        "11": "서울특별시",
        "26": "부산광역시",
        "27": "대구광역시",
        "28": "인천광역시",
        "29": "광주광역시",
        "30": "대전광역시",
        "31": "울산광역시",
        "36": "세종특별자치시",
        "41": "경기도",
        "42": "강원도",
        "43": "충청북도",
        "44": "충청남도",
        "45": "전라북도",
        "46": "전라남도",
        "47": "경상북도",
        "48": "경상남도",
        "50": "제주특별자치도",
    }
    gdf = gpd.read_file(boundary_path)
    gdf["province_code"] = gdf["code"].astype(str).str[:2]
    gdf["region"] = gdf["province_code"].map(prefix_to_region)
    province_gdf = gdf.dissolve(by="region", as_index=False)
    return province_gdf[["region", "geometry"]]


def make_map_figure(
    province_shapes: gpd.GeoDataFrame,
    spatial_metrics: pd.DataFrame,
    output_path: Path,
) -> None:
    comparisons = ["Flood 2022", "Flood 2023"]
    fig, axes = plt.subplots(1, 2, figsize=(14, 8))

    for ax, comparison in zip(axes, comparisons):
        subset = spatial_metrics.loc[spatial_metrics["period"] == comparison, ["region", "mismatch_index"]]
        plot_gdf = province_shapes.merge(subset, on="region", how="left")
        plot_gdf.plot(
            column="mismatch_index",
            ax=ax,
            cmap="RdBu_r",
            linewidth=0.6,
            edgecolor="white",
            legend=True,
            missing_kwds={"color": "#efefef", "label": "No data"},
            vmin=-2.5,
            vmax=2.5,
        )
        ax.set_title(f"{comparison} mismatch index")
        ax.axis("off")

    fig.suptitle("Spatial mismatch between anxiety signal and precipitation anomaly", y=0.96)
    save_figure(fig, output_path)
