"""Compute spatial robustness checks for Supplementary Table S8."""

from __future__ import annotations

import argparse
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.stats import kendalltau, spearmanr, theilslopes

FLOOD_WINDOWS = {
    "Flood 2022": (pd.Timestamp("2022-08-08"), pd.Timestamp("2022-08-21")),
    "Flood 2023": (pd.Timestamp("2023-07-10"), pd.Timestamp("2023-07-23")),
}


def load_spatial_inputs(
    complaints_path: str,
    precip_path: str,
    region_path: str,
) -> tuple[pd.DataFrame, pd.DataFrame, gpd.GeoDataFrame]:
    """Load complaint, precipitation, and region geometry inputs."""
    complaints_df = pd.read_csv(complaints_path)
    precip_df = pd.read_csv(precip_path)
    region_gdf = gpd.read_file(region_path)
    if "date" in complaints_df.columns:
        complaints_df["date"] = pd.to_datetime(complaints_df["date"])
    if "date" in precip_df.columns:
        precip_df["date"] = pd.to_datetime(precip_df["date"])
    return complaints_df, precip_df, region_gdf


def build_exposure_metrics(
    precip_df: pd.DataFrame,
    event_windows: dict[str, tuple[str, str]],
) -> pd.DataFrame:
    """Build event-region exposure metrics."""
    if {"date", "region", "precipitation_mm"} - set(precip_df.columns):
        raise ValueError("Precipitation input must include date, region, precipitation_mm.")

    records = []
    for event, (start, end) in event_windows.items():
        subset = precip_df.loc[precip_df["date"].between(start, end)].copy()
        grouped = (
            subset.groupby("region", as_index=False)
            .agg(
                regional_mean_precip=("precipitation_mm", "mean"),
                regional_max_precip=("precipitation_mm", "max"),
                event_cumulative_precip=("precipitation_mm", "sum"),
            )
        )
        grouped["event"] = event
        records.append(grouped)
    return pd.concat(records, ignore_index=True)


def build_response_metrics(
    complaints_df: pd.DataFrame,
    population_df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Build event-region response metrics."""
    if {"date", "region", "complaint_count"} - set(complaints_df.columns):
        raise ValueError("Complaint input must include date, region, complaint_count.")

    records = []
    for event, (start, end) in FLOOD_WINDOWS.items():
        subset = complaints_df.loc[complaints_df["date"].between(start, end)].copy()
        grouped = (
            subset.groupby("region", as_index=False)
            .agg(
                raw_complaints=("complaint_count", "sum"),
                mean_daily_complaints=("complaint_count", "mean"),
            )
        )
        total = float(grouped["raw_complaints"].sum())
        grouped["complaint_share"] = np.where(total > 0, grouped["raw_complaints"] / total, np.nan)

        pop_source = population_df
        if pop_source is None:
            pop_cols = [col for col in complaints_df.columns if col.lower() in {"population", "pop", "region_population"}]
            if pop_cols:
                pop_source = complaints_df[["region", pop_cols[0]]].drop_duplicates().rename(columns={pop_cols[0]: "population"})
        if pop_source is not None and {"region", "population"} <= set(pop_source.columns):
            pop_merge = pop_source.copy()
            if "event" in pop_merge.columns:
                pop_merge = pop_merge.loc[pop_merge["event"] == event, ["region", "population"]]
            else:
                pop_merge = pop_merge[["region", "population"]]
            grouped = grouped.merge(pop_merge, on="region", how="left")
            grouped["complaints_per_100k"] = np.where(
                grouped["population"].gt(0),
                grouped["raw_complaints"] / grouped["population"] * 100000.0,
                np.nan,
            )

        grouped["event"] = event
        records.append(grouped)
    return pd.concat(records, ignore_index=True)


def _safe_metric(values_x: pd.Series, values_y: pd.Series, metric: str) -> tuple[float, float]:
    paired = pd.concat([values_x, values_y], axis=1).dropna()
    if len(paired) < 3:
        return np.nan, np.nan
    x = paired.iloc[:, 0].to_numpy(dtype=float)
    y = paired.iloc[:, 1].to_numpy(dtype=float)
    if metric == "spearman_rho":
        stat, pval = spearmanr(x, y)
        return float(stat), float(pval)
    if metric == "kendall_tau":
        stat, pval = kendalltau(x, y)
        return float(stat), float(pval)
    if metric == "theil_sen_slope":
        slope, _, _, _ = theilslopes(y, x, 0.95)
        return float(slope), np.nan
    raise ValueError(f"Unsupported metric: {metric}")


def compute_association_metrics(
    merged_df: pd.DataFrame,
    exposure_cols: list[str],
    response_cols: list[str],
) -> pd.DataFrame:
    """Compute rank-based and robust association metrics."""
    metrics = ["spearman_rho", "kendall_tau", "theil_sen_slope"]
    records = []
    for event, event_df in merged_df.groupby("event"):
        for exposure_col in exposure_cols:
            for response_col in response_cols:
                for metric in metrics:
                    estimate, p_value = _safe_metric(event_df[exposure_col], event_df[response_col], metric)
                    records.append(
                        {
                            "event": event,
                            "exposure_metric": exposure_col,
                            "response_metric": response_col,
                            "association_metric": metric,
                            "estimate": estimate,
                            "p_value": p_value,
                            "n_regions": int(event_df[[exposure_col, response_col]].dropna().shape[0]),
                        }
                    )
    return pd.DataFrame(records)


def leave_one_region_out(
    merged_df: pd.DataFrame,
    exposure_col: str | None = None,
    response_col: str | None = None,
    metric: str | None = None,
) -> pd.DataFrame:
    """Recompute one association metric while excluding one region at a time."""
    metrics = [metric] if metric else ["spearman_rho", "kendall_tau", "theil_sen_slope"]
    exposure_cols = [exposure_col] if exposure_col else [
        col for col in merged_df.columns if col in {"regional_mean_precip", "regional_max_precip", "event_cumulative_precip"}
    ]
    response_cols = [response_col] if response_col else [
        col for col in merged_df.columns if col in {"raw_complaints", "mean_daily_complaints", "complaint_share", "complaints_per_100k"}
    ]

    records = []
    for event, event_df in merged_df.groupby("event"):
        for exp_col in exposure_cols:
            for resp_col in response_cols:
                for metric_name in metrics:
                    for region in sorted(event_df["region"].dropna().unique()):
                        subset = event_df.loc[event_df["region"] != region].copy()
                        estimate, p_value = _safe_metric(subset[exp_col], subset[resp_col], metric_name)
                        records.append(
                            {
                                "event": event,
                                "exposure_metric": exp_col,
                                "response_metric": resp_col,
                                "association_metric": metric_name,
                                "excluded_region": region,
                                "estimate": estimate,
                                "p_value": p_value,
                                "n_regions": int(subset[[exp_col, resp_col]].dropna().shape[0]),
                            }
                        )
    return pd.DataFrame(records)


def export_s8_table(assoc_df: pd.DataFrame, loo_df: pd.DataFrame, out_path: str) -> None:
    """Write the S8 workbook."""
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    summary = (
        loo_df.groupby(["event", "exposure_metric", "response_metric", "association_metric"], as_index=False)
        .agg(
            leave_one_out_min=("estimate", "min"),
            leave_one_out_max=("estimate", "max"),
        )
    )
    assoc_enriched = assoc_df.merge(
        summary,
        on=["event", "exposure_metric", "response_metric", "association_metric"],
        how="left",
    )
    assoc_enriched["direction"] = np.select(
        [
            assoc_enriched["estimate"] > 0.05,
            assoc_enriched["estimate"] < -0.05,
        ],
        ["positive", "negative"],
        default="weak",
    )
    assoc_enriched["supports_main_claim"] = np.where(
        assoc_enriched["event"].eq("Flood 2022") & assoc_enriched["estimate"].gt(0),
        True,
        np.where(
            assoc_enriched["event"].eq("Flood 2023") & assoc_enriched["estimate"].lt(assoc_enriched.groupby(["exposure_metric", "response_metric", "association_metric"])["estimate"].transform("max")),
            True,
            False,
        ),
    )
    with pd.ExcelWriter(out) as writer:
        assoc_enriched.to_excel(writer, sheet_name="association_metrics", index=False)
        loo_df.to_excel(writer, sheet_name="leave_one_out", index=False)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--complaints", required=True, help="Regional complaint csv")
    parser.add_argument("--precip", required=True, help="Regional precipitation csv")
    parser.add_argument("--regions", required=True, help="Region shapefile path")
    parser.add_argument("--population", help="Optional regional population csv")
    parser.add_argument("--output", required=True, help="S8 workbook path")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    complaints_df, precip_df, _ = load_spatial_inputs(args.complaints, args.precip, args.regions)
    population_df = pd.read_csv(args.population) if args.population else None
    exposure_df = build_exposure_metrics(precip_df, FLOOD_WINDOWS)
    response_df = build_response_metrics(complaints_df, population_df=population_df)
    merged_df = exposure_df.merge(response_df, on=["event", "region"], how="inner")
    exposure_cols = [col for col in exposure_df.columns if col not in {"event", "region"}]
    response_cols = [col for col in response_df.columns if col not in {"event", "region"}]
    response_cols = [col for col in response_cols if col != "population"]
    assoc_df = compute_association_metrics(merged_df, exposure_cols, response_cols)
    loo_df = leave_one_region_out(merged_df)
    export_s8_table(assoc_df, loo_df, args.output)


if __name__ == "__main__":
    main()
