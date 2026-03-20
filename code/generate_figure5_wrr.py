from __future__ import annotations

from pathlib import Path
import argparse

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from wrr_figure_support import BASE_FIG_DIR, apply_wrr_style


LABEL_MAP = {
    "Anxiety/Worried": "Anxiety\n/Worried",
    "Complaint": "Complaint",
    "Suspicion/Mistrust": "Suspicious\n/Mistrust",
    "Suspicious/Mistrust": "Suspicious\n/Mistrust",
    "Expectation": "Expectation",
    "Pathetic": "Pathetic",
    "Embarrassment/Distress": "Embarrassment\n/Distress",
    "Sadness": "Sadness",
    "Sad/Disappointed": "Sadness",
}

DISPLAY_ORDER = [
    "Sadness",
    "Embarrassment/Distress",
    "Expectation",
    "Suspicion/Mistrust",
    "Complaint",
    "Anger/Rage",
    "Anxiety/Worried",
]


def load_bootstrap_summary(path: Path) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name="bootstrap_summary")
    rename_map = {
        "Sad/Disappointed": "Sadness",
        "Suspicious/Mistrust": "Suspicion/Mistrust",
    }
    df["emotion"] = df["emotion"].replace(rename_map)
    return df


def build_figure(output_path: Path, bootstrap_path: Path) -> None:
    apply_wrr_style()
    summary = load_bootstrap_summary(bootstrap_path)
    subset_2022 = summary.loc[summary["comparison"] == "Flood 2022 - Ordinary"].copy()
    subset_2023 = summary.loc[summary["comparison"] == "Flood 2023 - Ordinary"].copy()
    df = subset_2022.merge(
        subset_2023,
        on="emotion",
        how="outer",
        suffixes=("_2022", "_2023"),
    )
    df["Sig_2022"] = df["significant_2022"].fillna(False)
    df["Sig_2023"] = df["significant_2023"].fillna(False)
    df = df[(df["Sig_2022"]) | (df["Sig_2023"])].copy()
    df["order"] = df["emotion"].map({emotion: idx for idx, emotion in enumerate(DISPLAY_ORDER)})
    df = df.sort_values("order").reset_index(drop=True)

    n = len(df)
    center_y = np.arange(n) * 2.0
    y_2022 = center_y - 0.35
    y_2023 = center_y + 0.35

    fig, ax = plt.subplots(figsize=(14, 2.5 + n * 1.4))
    ax.axvline(0, color="black", linestyle="--", linewidth=3.0, label="Baseline", zorder=1)

    marker_size = 12
    line_width = 3.2
    cap_size = 9
    used_2022 = False
    used_2023 = False

    for i, row in df.iterrows():
        if bool(row["Sig_2022"]):
            delta = float(row["mean_diff_2022"])
            err = [[delta - float(row["ci_lower_2022"])], [float(row["ci_upper_2022"]) - delta]]
            ax.errorbar(
                delta,
                y_2022[i],
                xerr=err,
                fmt="o",
                markersize=marker_size,
                color="#1f77b4",
                ecolor="#1f77b4",
                elinewidth=line_width,
                capsize=cap_size,
                capthick=line_width - 0.4,
                markeredgecolor="white",
                markeredgewidth=1.5,
                label="2022 Flood" if not used_2022 else None,
                zorder=10,
            )
            used_2022 = True

        if bool(row["Sig_2023"]):
            delta = float(row["mean_diff_2023"])
            err = [[delta - float(row["ci_lower_2023"])], [float(row["ci_upper_2023"]) - delta]]
            ax.errorbar(
                delta,
                y_2023[i],
                xerr=err,
                fmt="s",
                markersize=marker_size,
                color="#d62728",
                ecolor="#d62728",
                elinewidth=line_width,
                capsize=cap_size,
                capthick=line_width - 0.4,
                markeredgecolor="white",
                markeredgewidth=1.5,
                label="2023 Flood" if not used_2023 else None,
                zorder=10,
            )
            used_2023 = True

    labels = [LABEL_MAP.get(emotion, emotion) for emotion in df["emotion"]]
    ax.set_yticks(center_y)
    ax.set_yticklabels(labels, fontweight="medium")
    ax.set_xlabel("Difference in Proportion", fontsize=22, fontweight="bold")
    ax.set_ylabel("Significant Emotion Shifts (p < 0.05)", fontsize=20, fontweight="bold")
    ax.grid(False)

    mid_lines = (center_y[:-1] + center_y[1:]) / 2 if len(center_y) > 1 else []
    xlim = (-0.22, 0.26)
    ax.set_xlim(*xlim)
    for y in mid_lines:
        ax.hlines(y, xlim[0], xlim[1], colors="lightgray", linestyles="-", linewidth=1.2, zorder=0)

    ax.set_ylim(center_y[0] - 1.2, center_y[-1] + 1.2)
    ax.invert_yaxis()
    legend = ax.legend(loc="upper left", bbox_to_anchor=(0.02, 0.99), frameon=True, fancybox=True, fontsize=18, handlelength=3.6)
    legend.get_frame().set_edgecolor("#7c8ea3")
    legend.get_frame().set_linewidth(1.2)

    plt.subplots_adjust(left=0.35, right=0.97, top=0.95, bottom=0.08)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate manuscript-aligned WRR Figure 5")
    parser.add_argument("--output", type=Path, default=BASE_FIG_DIR / "Figure5_WRR.png")
    parser.add_argument(
        "--bootstrap-path",
        type=Path,
        default=Path("/Volumes/Keywest_JetDrive 1/Codex/Academia/Complaint/tables/bootstrap_results.xlsx"),
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    build_figure(args.output, args.bootstrap_path)
