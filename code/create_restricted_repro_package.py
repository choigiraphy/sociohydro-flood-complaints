from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


INPUT_PATH = Path(
    "/Volumes/Keywest_JetDrive 1/학교/2026-1/AGU_WRR_Choi/Code/wrr_reproducible/data/emotion_ensemble.xlsx"
)
PUBLIC_DIR = Path("/Volumes/Keywest_JetDrive 1/Codex/Academia/Complaint/data/public")
SYNTHETIC_DIR = Path("/Volumes/Keywest_JetDrive 1/Codex/Academia/Complaint/data/synthetic")
SUBSET_PATH = PUBLIC_DIR / "minimal_reproducible_subset.csv"
SYNTH_PATH = SYNTHETIC_DIR / "synthetic_complaint_pipeline_input.csv"
README_PATH = Path("/Volumes/Keywest_JetDrive 1/Codex/Academia/Complaint/restricted_reproducibility_package.md")


FLOOD_2022 = ("2022-08-08", "2022-08-21")
FLOOD_2023 = ("2023-07-10", "2023-07-23")


def map_group(label: str) -> str:
    s = str(label)
    if any(k in s for k in ["Anxiety", "Worried", "Fear"]):
        return "anxiety_fear"
    if any(k in s for k in ["Anger", "Rage", "Suspicion", "Mistrust"]):
        return "anger_mistrust"
    if any(k in s for k in ["Complaint", "Dissatisfaction"]):
        return "complaint_dissatisfaction"
    if any(k in s for k in ["Sad", "Distress", "Embarrassment", "Disappointed"]):
        return "sadness_distress"
    return "expectation_other"


def assign_event(date: pd.Timestamp) -> str:
    if pd.Timestamp(FLOOD_2022[0]) <= date <= pd.Timestamp(FLOOD_2022[1]):
        return "Flood 2022"
    if pd.Timestamp(FLOOD_2023[0]) <= date <= pd.Timestamp(FLOOD_2023[1]):
        return "Flood 2023"
    return "Ordinary"


def main() -> None:
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    SYNTHETIC_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_excel(INPUT_PATH)
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.normalize()
    df = df.dropna(subset=["Date", "Top1_Emotion", "Region"]).copy()
    df["event_label"] = df["Date"].apply(assign_event)
    df["emotion_group"] = df["Top1_Emotion"].map(map_group)
    df["region"] = df["Region"].astype(str)

    ordinary = df[df["event_label"] == "Ordinary"].sample(n=50, random_state=42)
    flood_2022 = df[df["event_label"] == "Flood 2022"].sample(n=50, random_state=42)
    flood_2023 = df[df["event_label"] == "Flood 2023"].sample(n=50, random_state=42)
    subset = pd.concat([ordinary, flood_2022, flood_2023], ignore_index=True)
    subset = subset.sort_values(["event_label", "Date", "region"]).reset_index(drop=True)
    subset.insert(0, "record_id", [f"SUB_{i:04d}" for i in range(1, len(subset) + 1)])
    subset["is_flood_window"] = subset["event_label"].ne("Ordinary")
    subset = subset[
        [
            "record_id",
            "event_label",
            "Date",
            "region",
            "Top1_Emotion",
            "Top1_Score",
            "emotion_group",
            "is_flood_window",
        ]
    ].rename(columns={"Date": "date", "Top1_Emotion": "top1_emotion", "Top1_Score": "top1_score"})
    subset.to_csv(SUBSET_PATH, index=False, encoding="utf-8-sig")

    rng = np.random.default_rng(42)
    synth_rows = []
    emotions = sorted(subset["top1_emotion"].unique())
    regions = sorted(subset["region"].unique())
    for i in range(1, 201):
        emo = rng.choice(emotions)
        synth_rows.append(
            {
                "record_id": f"SYN_{i:04d}",
                "event_label": rng.choice(["Flood 2022", "Flood 2023", "Ordinary"]),
                "date": str(pd.Timestamp("2022-01-01") + pd.Timedelta(days=int(rng.integers(0, 730)))).split(" ")[0],
                "region": rng.choice(regions),
                "top1_emotion": emo,
                "top1_score": round(float(rng.uniform(0.55, 0.99)), 6),
                "emotion_group": map_group(emo),
                "is_flood_window": bool(rng.integers(0, 2)),
            }
        )
    pd.DataFrame(synth_rows).to_csv(SYNTH_PATH, index=False, encoding="utf-8-sig")

    README_PATH.write_text(
        "\n".join(
            [
                "# Restricted Reproducibility Package",
                "",
                "- `data/public/minimal_reproducible_subset.csv`: de-identified complaint-level subset without raw text. Used for reviewer-facing inspection of event labels, regional labels, and grouped emotion outputs.",
                "- `data/synthetic/synthetic_complaint_pipeline_input.csv`: schema-compatible synthetic input for code smoke tests and pipeline demonstrations.",
                "- Raw complaint texts remain restricted under the ACRC MOU and are not redistributed.",
            ]
        ),
        encoding="utf-8",
    )

    print(SUBSET_PATH)
    print(SYNTH_PATH)
    print(README_PATH)


if __name__ == "__main__":
    main()
