from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class BootstrapConfig:
    n_resamples: int = 5000
    seed: int = 42


@dataclass(frozen=True)
class BaselineConfig:
    n_windows: int = 5000
    seed: int = 42
    window_days: int = 14
    exclusion_days: int = 30


def sample_baseline_blocks(
    candidate_blocks: pd.DataFrame,
    config: BaselineConfig,
) -> pd.DataFrame:
    if candidate_blocks.empty:
        raise ValueError("No valid baseline blocks available from consecutive ordinary-week pairs.")
    rng = np.random.default_rng(config.seed)
    sampled_idx = rng.choice(candidate_blocks.index.to_numpy(), size=config.n_windows, replace=True)
    sampled = candidate_blocks.loc[sampled_idx].copy().reset_index(drop=True)
    sampled.insert(0, "window_id", np.arange(config.n_windows, dtype=int))
    return sampled.sort_values(["start_date", "window_id"]).reset_index(drop=True)


def build_baseline_date_weights(windows: pd.DataFrame) -> pd.DataFrame:
    records: list[pd.DataFrame] = []
    for row in windows.itertuples(index=False):
        window_dates = pd.date_range(row.start_date, row.end_date, freq="D")
        records.append(pd.DataFrame({"date": window_dates, "weight": 1}))
    weights = pd.concat(records, ignore_index=True).groupby("date", as_index=False)["weight"].sum()
    return weights


def expand_complaints_by_date_weight(
    complaints: pd.DataFrame,
    date_weights: pd.DataFrame,
    date_col: str = "day",
) -> pd.DataFrame:
    weighted = complaints.merge(date_weights, left_on=date_col, right_on="date", how="inner", suffixes=("", "_baseline"))
    weighted["weight"] = weighted["weight"].fillna(0).astype(int)
    weighted = weighted.loc[weighted["weight"] > 0].copy()
    if weighted.empty:
        raise ValueError("Baseline complaint pool is empty after applying date weights.")

    repeated = weighted.loc[weighted.index.repeat(weighted["weight"])].copy()
    drop_cols = [column for column in ["date", "date_baseline", "weight"] if column in repeated.columns]
    repeated = repeated.drop(columns=drop_cols).reset_index(drop=True)
    return repeated


def summarize_block_emotions(
    complaints: pd.DataFrame,
    blocks: pd.DataFrame,
    emotions: list[str],
    date_col: str = "day",
) -> pd.DataFrame:
    summaries: list[dict] = []
    for row in blocks.itertuples(index=False):
        subset = complaints.loc[complaints[date_col].between(row.start_date, row.end_date)].copy()
        record = {
            "block_id": getattr(row, "block_id", np.nan),
            "start_date": row.start_date,
            "end_date": row.end_date,
            "n_complaints": int(len(subset)),
        }
        for emotion in emotions:
            record[emotion] = float(pd.to_numeric(subset[emotion], errors="coerce").dropna().mean()) if not subset.empty else np.nan
        summaries.append(record)
    return pd.DataFrame(summaries)


def summarize_baseline_windows(
    daily_metrics: pd.DataFrame,
    windows: pd.DataFrame,
) -> pd.DataFrame:
    summaries: list[dict] = []
    for row in windows.itertuples(index=False):
        subset = daily_metrics.loc[daily_metrics["date"].between(row.start_date, row.end_date)]
        summaries.append(
            {
                "window_id": row.window_id,
                "start_date": row.start_date,
                "end_date": row.end_date,
                "mean_daily_complaints": float(subset["complaint_count"].mean()),
                "mean_daily_precipitation": float(subset["precipitation_mm"].mean()),
                "total_complaints": int(subset["complaint_count"].sum()),
            }
        )
    return pd.DataFrame(summaries)


def bootstrap_mean_difference(
    group_a: pd.Series,
    group_b: pd.Series,
    config: BootstrapConfig,
    label_a: str,
    label_b: str,
    emotion: str,
) -> tuple[dict, pd.DataFrame]:
    values_a = pd.to_numeric(group_a, errors="coerce").dropna().to_numpy(dtype=float)
    values_b = pd.to_numeric(group_b, errors="coerce").dropna().to_numpy(dtype=float)

    if len(values_a) == 0 or len(values_b) == 0:
        summary = {
            "emotion": emotion,
            "comparison": f"{label_a} - {label_b}",
            "group_a": label_a,
            "group_b": label_b,
            "n_a": len(values_a),
            "n_b": len(values_b),
            "mean_a": np.nan,
            "mean_b": np.nan,
            "mean_diff": np.nan,
            "ci_lower": np.nan,
            "ci_upper": np.nan,
            "significant": False,
        }
        return summary, pd.DataFrame(columns=["emotion", "comparison", "resample_id", "mean_diff"])

    seed_offset = sum(ord(char) for char in f"{emotion}|{label_a}|{label_b}") % (2**32)
    rng = np.random.default_rng(config.seed + seed_offset)

    sample_a = rng.choice(values_a, size=(config.n_resamples, len(values_a)), replace=True)
    sample_b = rng.choice(values_b, size=(config.n_resamples, len(values_b)), replace=True)
    diff_distribution = sample_a.mean(axis=1) - sample_b.mean(axis=1)

    ci_lower, ci_upper = np.quantile(diff_distribution, [0.025, 0.975])
    mean_a = float(values_a.mean())
    mean_b = float(values_b.mean())
    mean_diff = float(mean_a - mean_b)

    summary = {
        "emotion": emotion,
        "comparison": f"{label_a} - {label_b}",
        "group_a": label_a,
        "group_b": label_b,
        "n_a": len(values_a),
        "n_b": len(values_b),
        "mean_a": mean_a,
        "mean_b": mean_b,
        "mean_diff": mean_diff,
        "ci_lower": float(ci_lower),
        "ci_upper": float(ci_upper),
        "significant": bool((ci_lower > 0) or (ci_upper < 0)),
    }
    distribution = pd.DataFrame(
        {
            "emotion": emotion,
            "comparison": f"{label_a} - {label_b}",
            "resample_id": np.arange(config.n_resamples),
            "mean_diff": diff_distribution,
        }
    )
    return summary, distribution


def bootstrap_mean_difference_event_vs_blocks(
    event_values: pd.Series,
    baseline_block_values: pd.Series,
    config: BootstrapConfig,
    label_a: str,
    label_b: str,
    emotion: str,
) -> tuple[dict, pd.DataFrame]:
    values_a = pd.to_numeric(event_values, errors="coerce").dropna().to_numpy(dtype=float)
    values_b = pd.to_numeric(baseline_block_values, errors="coerce").dropna().to_numpy(dtype=float)

    if len(values_a) == 0 or len(values_b) == 0:
        summary = {
            "emotion": emotion,
            "comparison": f"{label_a} - {label_b}",
            "group_a": label_a,
            "group_b": label_b,
            "n_a": len(values_a),
            "n_b": len(values_b),
            "mean_a": np.nan,
            "mean_b": np.nan,
            "mean_diff": np.nan,
            "ci_lower": np.nan,
            "ci_upper": np.nan,
            "significant": False,
        }
        return summary, pd.DataFrame(columns=["emotion", "comparison", "resample_id", "mean_diff"])

    seed_offset = sum(ord(char) for char in f"BLOCK|{emotion}|{label_a}|{label_b}") % (2**32)
    rng = np.random.default_rng(config.seed + seed_offset)

    sample_a = rng.choice(values_a, size=(config.n_resamples, len(values_a)), replace=True).mean(axis=1)
    sample_b = rng.choice(values_b, size=(config.n_resamples, len(values_b)), replace=True).mean(axis=1)
    diff_distribution = sample_a - sample_b

    ci_lower, ci_upper = np.quantile(diff_distribution, [0.025, 0.975])
    mean_a = float(values_a.mean())
    mean_b = float(values_b.mean())
    mean_diff = float(mean_a - mean_b)

    summary = {
        "emotion": emotion,
        "comparison": f"{label_a} - {label_b}",
        "group_a": label_a,
        "group_b": label_b,
        "n_a": len(values_a),
        "n_b": len(values_b),
        "mean_a": mean_a,
        "mean_b": mean_b,
        "mean_diff": mean_diff,
        "ci_lower": float(ci_lower),
        "ci_upper": float(ci_upper),
        "significant": bool((ci_lower > 0) or (ci_upper < 0)),
    }
    distribution = pd.DataFrame(
        {
            "emotion": emotion,
            "comparison": f"{label_a} - {label_b}",
            "resample_id": np.arange(config.n_resamples),
            "mean_diff": diff_distribution,
        }
    )
    return summary, distribution


def run_bootstrap_suite(
    complaint_scores: pd.DataFrame,
    baseline_block_summary: pd.DataFrame,
    emotions: list[str],
    period_masks: dict[str, pd.Series],
    config: BootstrapConfig,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    summaries: list[dict] = []
    distributions: list[pd.DataFrame] = []

    comparisons = [
        ("Flood 2022", "Ordinary"),
        ("Flood 2023", "Ordinary"),
        ("Flood 2022", "Flood 2023"),
    ]

    for emotion in emotions:
        for label_a, label_b in comparisons:
            if "Ordinary" in (label_a, label_b):
                if label_a == "Ordinary":
                    event_series = complaint_scores.loc[period_masks[label_b], emotion]
                    baseline_series = baseline_block_summary[emotion]
                    baseline_label = label_a
                    event_label = label_b
                    reverse_sign = True
                else:
                    event_series = complaint_scores.loc[period_masks[label_a], emotion]
                    baseline_series = baseline_block_summary[emotion]
                    baseline_label = label_b
                    event_label = label_a
                    reverse_sign = False

                summary, distribution = bootstrap_mean_difference_event_vs_blocks(
                    event_values=event_series,
                    baseline_block_values=baseline_series,
                    config=config,
                    label_a=event_label,
                    label_b=baseline_label,
                    emotion=emotion,
                )
                if reverse_sign:
                    summary["comparison"] = f"{label_a} - {label_b}"
                    summary["group_a"] = label_a
                    summary["group_b"] = label_b
                    summary["mean_diff"] = -float(summary["mean_diff"])
                    ci_lower = -float(summary["ci_upper"])
                    ci_upper = -float(summary["ci_lower"])
                    summary["ci_lower"] = ci_lower
                    summary["ci_upper"] = ci_upper
                    distribution["comparison"] = f"{label_a} - {label_b}"
                    distribution["mean_diff"] = -distribution["mean_diff"]
            else:
                series_a = complaint_scores.loc[period_masks[label_a], emotion]
                series_b = complaint_scores.loc[period_masks[label_b], emotion]
                summary, distribution = bootstrap_mean_difference(
                    group_a=series_a,
                    group_b=series_b,
                    config=config,
                    label_a=label_a,
                    label_b=label_b,
                    emotion=emotion,
                )
            summaries.append(summary)
            distributions.append(distribution)

    summary_df = pd.DataFrame(summaries).sort_values(["comparison", "mean_diff"], ascending=[True, False])
    distribution_df = pd.concat(distributions, ignore_index=True)
    return summary_df, distribution_df
