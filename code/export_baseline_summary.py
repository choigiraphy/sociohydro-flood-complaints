from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def describe_numeric(series: pd.Series, label: str) -> pd.DataFrame:
    stats = {
        "metric": label,
        "count": int(series.count()),
        "mean": float(series.mean()),
        "std": float(series.std(ddof=1)),
        "min": float(series.min()),
        "p10": float(series.quantile(0.10)),
        "p25": float(series.quantile(0.25)),
        "median": float(series.quantile(0.50)),
        "p75": float(series.quantile(0.75)),
        "p90": float(series.quantile(0.90)),
        "max": float(series.max()),
    }
    return pd.DataFrame([stats])


def export_summary(input_path: Path, output_path: Path) -> None:
    ordinary = pd.read_excel(input_path, sheet_name="ordinary_weeks")
    candidates = pd.read_excel(input_path, sheet_name="baseline_candidates")
    windows = pd.read_excel(input_path, sheet_name="baseline_windows")
    period_top1 = pd.read_excel(input_path, sheet_name="period_top1_distribution")

    ordinary_true = ordinary.loc[ordinary["is_ordinary_week"]].copy()
    diagnostics = pd.concat(
        [
            describe_numeric(ordinary.loc[~ordinary["is_flood_week"], "weekly_complaint_count"], "Non-flood weekly complaints"),
            describe_numeric(ordinary_true["weekly_complaint_count"], "Ordinary weekly complaints (<=40)"),
            describe_numeric(candidates["block_total_complaints"], "Candidate baseline block complaints"),
        ],
        ignore_index=True,
    )

    counts = pd.DataFrame(
        [
            {"item": "Non-flood weeks", "value": int((~ordinary["is_flood_week"]).sum())},
            {"item": "Ordinary weeks", "value": int(ordinary["is_ordinary_week"].sum())},
            {"item": "Candidate baseline blocks", "value": int(len(candidates))},
            {"item": "Sampled baseline blocks", "value": int(len(windows))},
        ]
    )

    ordinary_top1 = period_top1.loc[period_top1["period"] == "Ordinary"].copy()
    flood_top1 = period_top1.loc[period_top1["period"].isin(["Flood 2022", "Flood 2023"])].copy()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        diagnostics.to_excel(writer, sheet_name="diagnostics", index=False)
        counts.to_excel(writer, sheet_name="counts", index=False)
        ordinary_top1.to_excel(writer, sheet_name="ordinary_top1", index=False)
        flood_top1.to_excel(writer, sheet_name="flood_top1", index=False)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export baseline distribution summary workbook")
    parser.add_argument("--input-path", type=Path, default=Path("/Volumes/Keywest_JetDrive 1/Codex/Academia/Complaint/tables/bootstrap_results.xlsx"))
    parser.add_argument("--output-path", type=Path, default=Path("/Volumes/Keywest_JetDrive 1/Codex/Academia/Complaint/tables/baseline_distribution_summary.xlsx"))
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    export_summary(args.input_path, args.output_path)
