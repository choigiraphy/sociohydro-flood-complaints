from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from bootstrap import (
    BaselineConfig,
    BootstrapConfig,
    build_baseline_date_weights,
    expand_complaints_by_date_weight,
    run_bootstrap_suite,
    sample_baseline_blocks,
)
from main_pipeline import (
    DEFAULT_EMOTION_PATH,
    TARGET_EMOTIONS,
    build_candidate_baseline_blocks,
    build_ordinary_week_table,
    build_period_masks,
    load_complaint_data,
)


def run_sensitivity(thresholds: list[int], n_windows: int, n_resamples: int, seed: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    complaints = load_complaint_data(DEFAULT_EMOTION_PATH)
    period_masks = build_period_masks(complaints)

    counts_rows: list[dict] = []
    bootstrap_rows: list[pd.DataFrame] = []

    for threshold in thresholds:
        ordinary = build_ordinary_week_table(complaints, weekly_threshold=threshold)
        candidates = build_candidate_baseline_blocks(ordinary)
        windows = sample_baseline_blocks(candidates, BaselineConfig(n_windows=n_windows, seed=seed))
        weights = build_baseline_date_weights(windows)
        baseline_pool = expand_complaints_by_date_weight(complaints, weights, date_col="day")
        summary, _ = run_bootstrap_suite(
            complaint_scores=complaints,
            baseline_pool=baseline_pool,
            emotions=TARGET_EMOTIONS,
            period_masks=period_masks,
            config=BootstrapConfig(n_resamples=n_resamples, seed=seed),
        )
        summary["ordinary_threshold"] = threshold
        bootstrap_rows.append(summary)
        counts_rows.append(
            {
                "ordinary_threshold": threshold,
                "ordinary_weeks": int(ordinary["is_ordinary_week"].sum()),
                "candidate_blocks": int(len(candidates)),
                "sampled_blocks": int(len(windows)),
                "baseline_pool_n": int(len(baseline_pool)),
            }
        )

    return pd.DataFrame(counts_rows), pd.concat(bootstrap_rows, ignore_index=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export threshold sensitivity results")
    parser.add_argument("--thresholds", nargs="+", type=int, default=[30, 40, 50])
    parser.add_argument("--baseline-windows", type=int, default=500)
    parser.add_argument("--bootstrap-resamples", type=int, default=500)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-path", type=Path, default=Path("/Volumes/Keywest_JetDrive 1/Codex/Academia/Complaint/tables/threshold_sensitivity.xlsx"))
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    counts, bootstrap = run_sensitivity(args.thresholds, args.baseline_windows, args.bootstrap_resamples, args.seed)
    args.output_path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(args.output_path, engine="openpyxl") as writer:
        counts.to_excel(writer, sheet_name="pool_sizes", index=False)
        bootstrap.to_excel(writer, sheet_name="bootstrap_summary", index=False)
