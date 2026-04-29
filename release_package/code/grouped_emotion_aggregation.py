"""Aggregate fine-grained complaint emotions into grouped categories."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

DEFAULT_GROUP_MAP = {
    "Anxiety/Worried": "anxiety_fear",
    "Anger/Rage": "anger_mistrust",
    "Suspicion/Mistrust": "anger_mistrust",
    "Complaint": "complaint_dissatisfaction",
    "Irritation": "complaint_dissatisfaction",
    "Sad/Disappointed": "sadness_distress",
    "Embarrassment/Distress": "sadness_distress",
    "Expectation": "expectation_other",
    "Other": "expectation_other",
}


def load_emotion_group_map(path: str) -> dict[str, str]:
    """Load a fine-to-grouped emotion mapping."""
    df = pd.read_csv(path)
    return dict(zip(df["fine_emotion"], df["grouped_emotion"]))


def apply_grouping(
    df: pd.DataFrame,
    top1_col: str,
    prob_cols: dict[str, str],
    mapping: dict[str, str],
) -> pd.DataFrame:
    """Apply grouped emotion mapping to top-1 and probability columns."""
    out = df.copy()
    out["grouped_top1_emotion"] = out[top1_col].map(lambda x: mapping.get(x, mapping.get("Other", "other")))

    grouped_prob = {}
    for fine_emotion, prob_col in prob_cols.items():
        grouped_emotion = mapping.get(fine_emotion)
        if grouped_emotion is None or prob_col not in out.columns:
            continue
        grouped_prob.setdefault(grouped_emotion, 0.0)
        grouped_prob[grouped_emotion] = grouped_prob[grouped_emotion] + pd.to_numeric(
            out[prob_col], errors="coerce"
        ).fillna(0.0)

    for grouped_emotion, values in grouped_prob.items():
        out[f"grouped_prob_{grouped_emotion}"] = values
    return out


def compute_grouped_differences(df: pd.DataFrame, group_col: str) -> pd.DataFrame:
    """Compute grouped emotion event-baseline differences."""
    grouped_prob_cols = [col for col in df.columns if col.startswith("grouped_prob_")]
    records = []
    for group_value, subset in df.groupby(group_col):
        top_counts = (
            subset["grouped_top1_emotion"]
            .value_counts(normalize=True)
            .rename_axis("emotion_group")
            .reset_index(name="top1_prop")
        )
        if grouped_prob_cols:
            prob_means = subset[grouped_prob_cols].mean().rename_axis("prob_col").reset_index(name="prob_prop")
            prob_means["emotion_group"] = prob_means["prob_col"].str.replace("grouped_prob_", "", regex=False)
            merged = top_counts.merge(prob_means[["emotion_group", "prob_prop"]], on="emotion_group", how="outer")
        else:
            merged = top_counts.copy()
            merged["prob_prop"] = pd.NA
        merged["group"] = group_value
        records.append(merged)
    return pd.concat(records, ignore_index=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Complaint emotion csv/xlsx")
    parser.add_argument("--mapping", help="Emotion group mapping csv")
    parser.add_argument("--output", required=True, help="Grouped output csv/xlsx")
    parser.add_argument("--group-col", default="event_label")
    parser.add_argument("--top1-col", default="Top1_Emotion_Normalized")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    in_path = Path(args.input)
    if in_path.suffix.lower() == ".csv":
        df = pd.read_csv(in_path)
    else:
        df = pd.read_excel(in_path)
    mapping = load_emotion_group_map(args.mapping) if args.mapping else DEFAULT_GROUP_MAP
    prob_cols = {}
    for col in df.columns:
        if col.startswith("share_"):
            fine_emotion = col.replace("share_", "", 1)
            prob_cols[fine_emotion] = col
    grouped_df = apply_grouping(df, args.top1_col, prob_cols, mapping)
    diff_df = compute_grouped_differences(grouped_df, args.group_col)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.suffix.lower() == ".csv":
        diff_df.to_csv(out, index=False)
    else:
        diff_df.to_excel(out, index=False)


if __name__ == "__main__":
    main()
