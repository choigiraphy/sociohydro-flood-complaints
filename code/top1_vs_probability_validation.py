"""Build Supplementary Table S6 from complaint-level emotion outputs."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from bootstrap import (
    BootstrapConfig,
    bootstrap_mean_difference,
    bootstrap_mean_difference_event_vs_blocks,
)
from grouped_emotion_aggregation import DEFAULT_GROUP_MAP, apply_grouping

TARGET_EMOTIONS = [
    "Anxiety/Worried",
    "Complaint",
    "Anger/Rage",
    "Sad/Disappointed",
    "Suspicion/Mistrust",
    "Expectation",
    "Irritation",
    "Embarrassment/Distress",
]

EMOTION_ALIASES = {
    "Anxiety/Worried": "Anxiety/Worried",
    "불안/걱정": "Anxiety/Worried",
    "Horror/Fear": "Anxiety/Worried",
    "Complaint": "Complaint",
    "불평/불만": "Complaint",
    "Anger/Rage": "Anger/Rage",
    "화남/분노": "Anger/Rage",
    "Sad/Disappointed": "Sad/Disappointed",
    "Sadness": "Sad/Disappointed",
    "안타까움/실망": "Sad/Disappointed",
    "Suspicion/Mistrust": "Suspicion/Mistrust",
    "의심/불신": "Suspicion/Mistrust",
    "Expectation": "Expectation",
    "기대": "Expectation",
    "Irritation": "Irritation",
    "Pathetic": "Irritation",
    "Embarrassment/Distress": "Embarrassment/Distress",
    "당황/난처": "Embarrassment/Distress",
}

FLOOD_WINDOWS = {
    "Flood 2022": (pd.Timestamp("2022-08-08"), pd.Timestamp("2022-08-21")),
    "Flood 2023": (pd.Timestamp("2023-07-10"), pd.Timestamp("2023-07-23")),
}


def normalize_emotion(emotion: object) -> object:
    if pd.isna(emotion):
        return np.nan
    return EMOTION_ALIASES.get(str(emotion).strip(), str(emotion).strip())


def _build_probability_scores(df: pd.DataFrame) -> pd.DataFrame:
    top_emotion_cols = [col for col in df.columns if col.startswith("Top") and col.endswith("_Emotion")]
    for emotion in TARGET_EMOTIONS:
        df[emotion] = 0.0
    for emotion_col in top_emotion_cols:
        score_col = emotion_col.replace("_Emotion", "_Score")
        labels = df[emotion_col].map(normalize_emotion)
        scores = pd.to_numeric(df[score_col], errors="coerce").fillna(0.0)
        for emotion in TARGET_EMOTIONS:
            mask = labels == emotion
            if mask.any():
                df.loc[mask, emotion] = np.maximum(
                    df.loc[mask, emotion].to_numpy(dtype=float),
                    scores.loc[mask].to_numpy(dtype=float),
                )
    total = df[TARGET_EMOTIONS].sum(axis=1)
    safe_total = total.where(total > 0, 1.0)
    for emotion in TARGET_EMOTIONS:
        df[f"share_{emotion}"] = df[emotion] / safe_total
    return df


def _assign_periods(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["event_label"] = "Non-flood"
    for label, (start, end) in FLOOD_WINDOWS.items():
        out.loc[out["day"].between(start, end), "event_label"] = label
    out["is_baseline"] = out["event_label"].eq("Non-flood")
    return out


def load_baseline_candidates(path: str) -> pd.DataFrame:
    """Load baseline candidate blocks from bootstrap workbook or csv/xlsx."""
    in_path = Path(path)
    if in_path.suffix.lower() == ".csv":
        return pd.read_csv(in_path, parse_dates=["start_date", "end_date"])
    if in_path.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(in_path, sheet_name="baseline_candidates", parse_dates=["start_date", "end_date"])
    raise ValueError(f"Unsupported baseline input format: {in_path}")


def _compute_block_shares(
    complaints: pd.DataFrame,
    blocks: pd.DataFrame,
    value_cols: list[str],
    top1_col: str | None = None,
) -> pd.DataFrame:
    records = []
    for row in blocks.itertuples(index=False):
        subset = complaints.loc[complaints["day"].between(row.start_date, row.end_date)].copy()
        record = {
            "block_id": getattr(row, "block_id", np.nan),
            "start_date": row.start_date,
            "end_date": row.end_date,
            "n_complaints": int(len(subset)),
        }
        if top1_col is not None:
            counts = subset[top1_col].value_counts(normalize=True) if not subset.empty else pd.Series(dtype=float)
            for col in value_cols:
                record[col] = float(counts.get(col, 0.0))
        else:
            means = subset[value_cols].mean() if not subset.empty else pd.Series({col: np.nan for col in value_cols})
            for col in value_cols:
                record[col] = float(means.get(col, np.nan))
        records.append(record)
    return pd.DataFrame(records)


def _summarize_bootstrap(
    event_df: pd.DataFrame,
    baseline_blocks: pd.DataFrame,
    value_cols: list[str],
    label_prefix: str,
    config: BootstrapConfig,
) -> pd.DataFrame:
    comparisons = [("Flood 2022", "Ordinary"), ("Flood 2023", "Ordinary"), ("Flood 2022", "Flood 2023")]
    summaries = []
    for emotion in value_cols:
        for label_a, label_b in comparisons:
            if "Ordinary" in (label_a, label_b):
                event_label = label_a if label_a != "Ordinary" else label_b
                event_values = event_df.loc[event_df["event_label"] == event_label, emotion]
                baseline_values = baseline_blocks[emotion]
                summary, _ = bootstrap_mean_difference_event_vs_blocks(
                    event_values=event_values,
                    baseline_block_values=baseline_values,
                    config=config,
                    label_a=event_label if label_a != "Ordinary" else label_a,
                    label_b=label_b if label_a != "Ordinary" else label_b,
                    emotion=emotion,
                )
                if label_a == "Ordinary":
                    summary["comparison"] = f"{label_a} - {label_b}"
                    summary["group_a"] = label_a
                    summary["group_b"] = label_b
                    summary["mean_diff"] = -float(summary["mean_diff"])
                    ci_lower = -float(summary["ci_upper"])
                    ci_upper = -float(summary["ci_lower"])
                    summary["ci_lower"] = ci_lower
                    summary["ci_upper"] = ci_upper
            else:
                summary, _ = bootstrap_mean_difference(
                    group_a=event_df.loc[event_df["event_label"] == label_a, emotion],
                    group_b=event_df.loc[event_df["event_label"] == label_b, emotion],
                    config=config,
                    label_a=label_a,
                    label_b=label_b,
                    emotion=emotion,
                )
            summary["aggregation_level"] = label_prefix
            summaries.append(summary)
    return pd.DataFrame(summaries)


def load_complaint_emotions(path: str) -> pd.DataFrame:
    """Load complaint-level emotion outputs from csv or xlsx."""
    in_path = Path(path)
    suffix = in_path.suffix.lower()
    if suffix == ".csv":
        df = pd.read_csv(in_path)
    elif suffix in {".xlsx", ".xls"}:
        sheet_name = "Individual_Complaints" if suffix in {".xlsx", ".xls"} else 0
        df = pd.read_excel(in_path, sheet_name=sheet_name)
    else:
        raise ValueError(f"Unsupported input format: {in_path}")

    if "date" not in df.columns:
        raise ValueError("Input must contain a 'date' column.")

    df["date"] = pd.to_datetime(df["date"])
    df["day"] = df["date"].dt.floor("D")
    df["Top1_Emotion_Normalized"] = df["Top1_Emotion"].map(normalize_emotion).fillna("Other")
    df["Top1_Emotion_Normalized"] = df["Top1_Emotion_Normalized"].where(
        df["Top1_Emotion_Normalized"].isin(TARGET_EMOTIONS),
        "Other",
    )
    df = _build_probability_scores(df)
    df = _assign_periods(df)
    return df


def compute_top1_distribution(df: pd.DataFrame, group_col: str) -> pd.DataFrame:
    """Return top-1 emotion proportions by analysis group."""
    counts = (
        df.groupby(group_col)["Top1_Emotion_Normalized"]
        .value_counts(normalize=True)
        .rename("share")
        .reset_index()
        .rename(columns={"Top1_Emotion_Normalized": "emotion"})
    )
    counts["aggregation_level"] = "fine"
    counts["method"] = "top1"
    return counts


def compute_probability_distribution(df: pd.DataFrame, group_col: str) -> pd.DataFrame:
    """Return probability-based emotion proportions by analysis group."""
    share_cols = [f"share_{emotion}" for emotion in TARGET_EMOTIONS]
    grouped = df.groupby(group_col)[share_cols].mean().reset_index()
    out = grouped.melt(id_vars=[group_col], var_name="emotion", value_name="share")
    out["emotion"] = out["emotion"].str.replace("share_", "", regex=False)
    out["aggregation_level"] = "fine"
    out["method"] = "probability"
    return out


def summarize_event_baseline_differences(
    top1_df: pd.DataFrame,
    prob_df: pd.DataFrame,
    baseline_label: str = "baseline",
) -> pd.DataFrame:
    """Create the S6 comparison summary."""
    top1_level = top1_df["aggregation_level"].iloc[0] if not top1_df.empty else "unknown_top1"
    prob_level = prob_df["aggregation_level"].iloc[0] if not prob_df.empty else "unknown_probability"
    merged = top1_df.merge(
        prob_df,
        on=["emotion", "comparison"],
        how="outer",
        suffixes=("_top1", "_prob"),
    )
    merged["aggregation_level"] = top1_level.replace("_top1", "")
    top_sign = np.sign(pd.to_numeric(merged["mean_diff_top1"], errors="coerce"))
    prob_sign = np.sign(pd.to_numeric(merged["mean_diff_prob"], errors="coerce"))
    merged["direction_consistent"] = (
        top_sign.notna() & prob_sign.notna() & top_sign.eq(prob_sign)
    )
    merged["top1_level"] = top1_level
    merged["probability_level"] = prob_level
    merged["baseline_label"] = baseline_label
    if merged["emotion"].isin(["Other", "expectation_other"]).any():
        pass
    return merged.sort_values(["aggregation_level", "comparison", "emotion"]).reset_index(drop=True)


def _make_grouped_bootstrap_tables(
    complaints: pd.DataFrame,
    baseline_candidates: pd.DataFrame,
    config: BootstrapConfig,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    prob_cols = {emotion: f"share_{emotion}" for emotion in TARGET_EMOTIONS}
    grouped = apply_grouping(
        complaints,
        top1_col="Top1_Emotion_Normalized",
        prob_cols=prob_cols,
        mapping=DEFAULT_GROUP_MAP,
    )
    grouped_top_col = "grouped_top1_emotion"
    group_levels = sorted(set(DEFAULT_GROUP_MAP.values()))

    top1_block = _compute_block_shares(grouped, baseline_candidates, group_levels, top1_col=grouped_top_col)
    prob_value_cols = [col for col in grouped.columns if col.startswith("grouped_prob_")]
    prob_block = _compute_block_shares(grouped, baseline_candidates, prob_value_cols, top1_col=None)

    event_top = grouped[["event_label", grouped_top_col]].copy()
    for grp in group_levels:
        event_top[grp] = event_top[grouped_top_col].eq(grp).astype(float)

    event_prob = grouped[["event_label"] + prob_value_cols].copy()
    event_prob = event_prob.rename(columns={f"grouped_prob_{grp}": grp for grp in group_levels if f"grouped_prob_{grp}" in event_prob.columns})
    prob_block = prob_block.rename(columns={f"grouped_prob_{grp}": grp for grp in group_levels if f"grouped_prob_{grp}" in prob_block.columns})

    top_summary = _summarize_bootstrap(event_top, top1_block, group_levels, "grouped_top1", config)
    prob_summary = _summarize_bootstrap(event_prob, prob_block, group_levels, "grouped_probability", config)
    return top_summary, prob_summary


def export_s6_inputs(df: pd.DataFrame, out_path: str) -> None:
    """Write the S6 summary table."""
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.suffix.lower() == ".csv":
        df.to_csv(out, index=False)
    else:
        df.to_excel(out, index=False)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Complaint emotion csv/xlsx")
    parser.add_argument("--output", required=True, help="S6 output path")
    parser.add_argument(
        "--baseline-workbook",
        default="/Volumes/Keywest_JetDrive 1/Codex/Academia/Complaint/tables/bootstrap_results.xlsx",
        help="Workbook containing the baseline_candidates sheet",
    )
    parser.add_argument(
        "--n-resamples",
        type=int,
        default=5000,
        help="Bootstrap resamples for top1/probability/grouped comparisons",
    )
    parser.add_argument("--seed", type=int, default=42, help="Bootstrap seed")
    parser.add_argument(
        "--group-col",
        default="event_label",
        help="Grouping column used for top1/probability distributions",
    )
    parser.add_argument(
        "--baseline-label",
        default="Ordinary",
        help="Label representing the baseline group",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    df = load_complaint_emotions(args.input)
    baseline_candidates = load_baseline_candidates(args.baseline_workbook)
    config = BootstrapConfig(n_resamples=args.n_resamples, seed=args.seed)

    # Distribution sheets
    top1_dist = compute_top1_distribution(df, args.group_col)
    prob_dist = compute_probability_distribution(df, args.group_col)

    # Fine-level bootstrap summaries
    top1_event = df[["event_label", "Top1_Emotion_Normalized"]].copy()
    top1_value_cols = TARGET_EMOTIONS + ["Other"]
    for emotion in top1_value_cols:
        top1_event[emotion] = top1_event["Top1_Emotion_Normalized"].eq(emotion).astype(float)
    top1_block = _compute_block_shares(df, baseline_candidates, top1_value_cols, top1_col="Top1_Emotion_Normalized")
    top1_summary = _summarize_bootstrap(top1_event[["event_label"] + top1_value_cols], top1_block, top1_value_cols, "fine_top1", config)

    prob_value_cols = [f"share_{emotion}" for emotion in TARGET_EMOTIONS]
    prob_event = df[["event_label"] + prob_value_cols].rename(columns={f"share_{emotion}": emotion for emotion in TARGET_EMOTIONS})
    prob_block = _compute_block_shares(df, baseline_candidates, prob_value_cols, top1_col=None)
    prob_block = prob_block.rename(columns={f"share_{emotion}": emotion for emotion in TARGET_EMOTIONS})
    prob_summary = _summarize_bootstrap(prob_event, prob_block, TARGET_EMOTIONS, "fine_probability", config)

    grouped_top_summary, grouped_prob_summary = _make_grouped_bootstrap_tables(df, baseline_candidates, config)

    summary_df = summarize_event_baseline_differences(
        top1_summary,
        prob_summary,
        baseline_label=args.baseline_label,
    )
    grouped_df = summarize_event_baseline_differences(
        grouped_top_summary,
        grouped_prob_summary,
        baseline_label=args.baseline_label,
    )

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.suffix.lower() == ".csv":
        export_s6_inputs(summary_df, args.output)
        return

    with pd.ExcelWriter(out) as writer:
        summary_df.to_excel(writer, sheet_name="combined_s6_fine", index=False)
        grouped_df.to_excel(writer, sheet_name="combined_s6_grouped", index=False)
        top1_summary.to_excel(writer, sheet_name="top1_summary", index=False)
        prob_summary.to_excel(writer, sheet_name="probability_summary", index=False)
        grouped_top_summary.to_excel(writer, sheet_name="grouped_top1_summary", index=False)
        grouped_prob_summary.to_excel(writer, sheet_name="grouped_probability_summary", index=False)
        top1_dist.to_excel(writer, sheet_name="top1_distribution", index=False)
        prob_dist.to_excel(writer, sheet_name="probability_distribution", index=False)


if __name__ == "__main__":
    main()
