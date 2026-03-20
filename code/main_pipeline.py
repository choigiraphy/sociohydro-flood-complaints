from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from bootstrap import (
    BaselineConfig,
    BootstrapConfig,
    build_baseline_date_weights,
    expand_complaints_by_date_weight,
    run_bootstrap_suite,
    sample_baseline_blocks,
    summarize_block_emotions,
    summarize_baseline_windows,
)
from visualization import (
    apply_lab_style,
    load_province_geometries,
    make_bootstrap_forest_plot,
    make_emotion_distribution_figure,
    make_map_figure,
    make_region_distribution_figure,
    make_time_series_figure,
)


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
FIG_DIR = ROOT / "figures"
TABLE_DIR = ROOT / "tables"

DEFAULT_EMOTION_PATH = Path(
    "/Volumes/Keywest_JetDrive 1/데이터저장소/final/emotion_ensemble_complete_results_results_english_2.xlsx"
)
DEFAULT_PRECIP_PATHS = [
    Path("/Volumes/Keywest_JetDrive 1/학교/2025-2/논문/data/precip_asos_2021.csv"),
    Path("/Volumes/Keywest_JetDrive 1/학교/2025-2/논문/data/precip_asos_2022.csv"),
    Path("/Volumes/Keywest_JetDrive 1/학교/2025-2/논문/data/precip_asos_2023.csv"),
]
DEFAULT_BOUNDARY_PATH = Path(
    "/Volumes/Keywest_JetDrive 1/데이터저장소/skorea-municipalities-2018-geo.json"
)

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

FIGURE6_EMOTIONS = [
    "Anger/Rage",
    "Sad/Disappointed",
    "Embarrassment/Distress",
]

FLOOD_2022_START = pd.Timestamp("2022-08-08")
FLOOD_2022_END = pd.Timestamp("2022-08-21")
FLOOD_2023_START = pd.Timestamp("2023-07-10")
FLOOD_2023_END = pd.Timestamp("2023-07-23")

REGION_ALIASES = {
    "강원특별자치도": "강원도",
    "전북특별자치도": "전라북도",
    "제주특별자치도": "제주특별자치도",
    "NONE": np.nan,
}

EMOTION_ALIASES = {
    "Anxiety/Worried": "Anxiety/Worried",
    "불안/걱정": "Anxiety/Worried",
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
    "Pathetic": "Pathetic",
    "Embarrassment/Distress": "Embarrassment/Distress",
    "당황/난처": "Embarrassment/Distress",
    "Safe/Trust": "Safe/Trust",
    "안전/신뢰": "Safe/Trust",
    "Care": "Care",
    "Compassion/Pity": "Care",
    "Gratitude": "Gratitude",
    "Absurd": "Absurd",
    "Admire": "Admire",
    "Happiness": "Positive",
    "Joy/Excitement": "Positive",
    "Interesting": "Positive",
}

STATION_TO_REGION = {
    "강릉": "강원도",
    "강진군": "전라남도",
    "강화": "인천광역시",
    "거제": "경상남도",
    "거창": "경상남도",
    "경주시": "경상북도",
    "고산": "제주특별자치도",
    "고창": "전라북도",
    "고창군": "전라북도",
    "고흥": "전라남도",
    "광양시": "전라남도",
    "광주": "광주광역시",
    "구미": "경상북도",
    "군산": "전라북도",
    "금산": "충청남도",
    "김해시": "경상남도",
    "남원": "전라북도",
    "남해": "경상남도",
    "대관령": "강원도",
    "대구": "대구광역시",
    "대전": "대전광역시",
    "동두천": "경기도",
    "동해": "강원도",
    "목포": "전라남도",
    "문경": "경상북도",
    "밀양": "경상남도",
    "백령도": "인천광역시",
    "보령": "충청남도",
    "보성군": "전라남도",
    "보은": "충청북도",
    "봉화": "경상북도",
    "부산": "부산광역시",
    "부안": "전라북도",
    "부여": "충청남도",
    "북강릉": "강원도",
    "북부산": "부산광역시",
    "북창원": "경상남도",
    "북춘천": "강원도",
    "산청": "경상남도",
    "상주": "경상북도",
    "서귀포": "제주특별자치도",
    "서산": "충청남도",
    "서울": "서울특별시",
    "서청주": "충청북도",
    "성산": "제주특별자치도",
    "세종": "세종특별자치시",
    "속초": "강원도",
    "수원": "경기도",
    "순창군": "전라북도",
    "순천": "전라남도",
    "안동": "경상북도",
    "양산시": "경상남도",
    "양평": "경기도",
    "여수": "전라남도",
    "영광군": "전라남도",
    "영덕": "경상북도",
    "영월": "강원도",
    "영주": "경상북도",
    "영천": "경상북도",
    "완도": "전라남도",
    "울릉도": "경상북도",
    "울산": "울산광역시",
    "울진": "경상북도",
    "원주": "강원도",
    "의령군": "경상남도",
    "의성": "경상북도",
    "이천": "경기도",
    "인제": "강원도",
    "인천": "인천광역시",
    "임실": "전라북도",
    "장수": "전라북도",
    "장흥": "전라남도",
    "전주": "전라북도",
    "정선군": "강원도",
    "정읍": "전라북도",
    "제주": "제주특별자치도",
    "제천": "충청북도",
    "진도군": "전라남도",
    "진주": "경상남도",
    "창원": "경상남도",
    "천안": "충청남도",
    "철원": "강원도",
    "청송군": "경상북도",
    "청주": "충청북도",
    "추풍령": "충청북도",
    "춘천": "강원도",
    "충주": "충청북도",
    "태백": "강원도",
    "통영": "경상남도",
    "파주": "경기도",
    "포항": "경상북도",
    "함양군": "경상남도",
    "합천": "경상남도",
    "해남": "전라남도",
    "홍성": "충청남도",
    "홍천": "강원도",
    "흑산도": "전라남도",
}


def normalize_region(region: object) -> object:
    if pd.isna(region):
        return np.nan
    region = str(region).strip()
    if region in REGION_ALIASES:
        return REGION_ALIASES[region]
    return region


def normalize_emotion(emotion: object) -> object:
    if pd.isna(emotion):
        return np.nan
    emotion = str(emotion).strip()
    return EMOTION_ALIASES.get(emotion, emotion)


def zscore(series: pd.Series) -> pd.Series:
    std = series.std(ddof=0)
    if pd.isna(std) or std == 0:
        return pd.Series(np.zeros(len(series)), index=series.index)
    return (series - series.mean()) / std


def load_complaint_data(emotion_path: Path) -> pd.DataFrame:
    df = pd.read_excel(emotion_path, sheet_name="Individual_Complaints")
    df["date"] = pd.to_datetime(df["date"])
    df["day"] = df["date"].dt.floor("D")
    df["week"] = df["day"].dt.to_period("W-MON").astype(str)
    df["region"] = df["민원발생지"].map(normalize_region)
    df = df.dropna(subset=["region"]).copy()
    df["Top1_Emotion_Normalized"] = df["Top1_Emotion"].map(normalize_emotion)

    top_emotion_cols = [col for col in df.columns if col.startswith("Top") and col.endswith("_Emotion")]
    for emotion in TARGET_EMOTIONS:
        df[emotion] = 0.0

    for emotion_col in top_emotion_cols:
        score_col = emotion_col.replace("_Emotion", "_Score")
        labels = df[emotion_col].map(normalize_emotion)
        scores = pd.to_numeric(df[score_col], errors="coerce").fillna(0.0)
        for emotion in TARGET_EMOTIONS:
            df.loc[labels == emotion, emotion] = np.maximum(
                df.loc[labels == emotion, emotion].to_numpy(dtype=float),
                scores.loc[labels == emotion].to_numpy(dtype=float),
            )

    df["period"] = "Non-flood"
    df.loc[df["day"].between(FLOOD_2022_START, FLOOD_2022_END), "period"] = "Flood 2022"
    df.loc[df["day"].between(FLOOD_2023_START, FLOOD_2023_END), "period"] = "Flood 2023"
    return df


def load_precipitation_data(precip_paths: list[Path]) -> pd.DataFrame:
    frames = []
    for path in precip_paths:
        frame = pd.read_csv(path, encoding="cp949")
        frame["일시"] = pd.to_datetime(frame["일시"])
        frame["date"] = frame["일시"].dt.floor("D")
        frame["station"] = frame["지점명"].astype(str).str.strip()
        frame["region"] = frame["station"].map(STATION_TO_REGION)
        frame["precipitation_mm"] = pd.to_numeric(frame["강수량(mm)"], errors="coerce").fillna(0.0)
        frames.append(frame[["date", "station", "region", "precipitation_mm"]])

    precip = pd.concat(frames, ignore_index=True).dropna(subset=["region"]).copy()
    station_daily = (
        precip.groupby(["date", "region", "station"], as_index=False)["precipitation_mm"]
        .sum()
    )
    region_daily = (
        station_daily.groupby(["date", "region"], as_index=False)["precipitation_mm"]
        .mean()
    )
    region_daily["week"] = region_daily["date"].dt.to_period("W-MON").astype(str)
    return region_daily


def build_daily_outputs(
    complaints: pd.DataFrame,
    precip_daily: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    complaint_daily = (
        complaints.groupby(["day", "region"], as_index=False)
        .agg(
            complaint_count=("region", "size"),
            **{emotion: (emotion, "mean") for emotion in TARGET_EMOTIONS},
        )
        .rename(columns={"day": "date"})
    )

    merged_daily = (
        complaint_daily.merge(precip_daily, on=["date", "region"], how="outer")
        .sort_values(["date", "region"])
    )
    merged_daily["complaint_count"] = merged_daily["complaint_count"].fillna(0).astype(int)
    merged_daily["precipitation_mm"] = merged_daily["precipitation_mm"].fillna(0.0)
    merged_daily["week"] = merged_daily["date"].dt.to_period("W-MON").astype(str)

    weekly = (
        merged_daily.groupby(["week", "region"], as_index=False)
        .agg(
            complaint_count=("complaint_count", "sum"),
            precipitation_mm=("precipitation_mm", "mean"),
            **{emotion: (emotion, "mean") for emotion in TARGET_EMOTIONS},
        )
    )

    daily_national = (
        merged_daily.groupby("date", as_index=False)
        .agg(
            complaint_count=("complaint_count", "sum"),
            precipitation_mm=("precipitation_mm", "mean"),
        )
    )
    return merged_daily, weekly, daily_national


def build_period_masks(complaints: pd.DataFrame) -> dict[str, pd.Series]:
    in_flood_2022 = complaints["day"].between(FLOOD_2022_START, FLOOD_2022_END)
    in_flood_2023 = complaints["day"].between(FLOOD_2023_START, FLOOD_2023_END)

    return {
        "Flood 2022": in_flood_2022,
        "Flood 2023": in_flood_2023,
    }


def build_ordinary_week_table(complaints: pd.DataFrame, weekly_threshold: int = 40) -> pd.DataFrame:
    week_table = complaints.groupby("week", as_index=False).size().rename(columns={"size": "weekly_complaint_count"})
    week_table["week_start"] = pd.to_datetime(week_table["week"].str.split("/").str[0], errors="coerce")
    week_table["week_end"] = week_table["week_start"] + pd.Timedelta(days=6)
    week_table["overlaps_flood_2022"] = (
        week_table["week_end"].ge(FLOOD_2022_START) & week_table["week_start"].le(FLOOD_2022_END)
    )
    week_table["overlaps_flood_2023"] = (
        week_table["week_end"].ge(FLOOD_2023_START) & week_table["week_start"].le(FLOOD_2023_END)
    )
    week_table["is_flood_week"] = week_table["overlaps_flood_2022"] | week_table["overlaps_flood_2023"]
    week_table["ordinary_threshold"] = weekly_threshold
    week_table["is_ordinary_week"] = (~week_table["is_flood_week"]) & (week_table["weekly_complaint_count"] <= weekly_threshold)
    return week_table.sort_values("week_start").reset_index(drop=True)


def build_candidate_baseline_blocks(ordinary_weeks: pd.DataFrame) -> pd.DataFrame:
    ordinary = ordinary_weeks.loc[ordinary_weeks["is_ordinary_week"]].copy()
    if ordinary.empty:
        return pd.DataFrame(
            columns=[
                "block_id",
                "week_a",
                "week_b",
                "start_date",
                "end_date",
                "week_a_count",
                "week_b_count",
                "block_total_complaints",
            ]
        )

    ordinary["next_week"] = ordinary["week"].shift(-1)
    ordinary["next_week_start"] = ordinary["week_start"].shift(-1)
    ordinary["next_week_end"] = ordinary["week_end"].shift(-1)
    ordinary["next_week_count"] = ordinary["weekly_complaint_count"].shift(-1)
    ordinary["is_consecutive_pair"] = ordinary["next_week_start"].eq(ordinary["week_start"] + pd.Timedelta(days=7))

    blocks = ordinary.loc[ordinary["is_consecutive_pair"]].copy()
    if blocks.empty:
        return pd.DataFrame(
            columns=[
                "block_id",
                "week_a",
                "week_b",
                "start_date",
                "end_date",
                "week_a_count",
                "week_b_count",
                "block_total_complaints",
            ]
        )

    blocks = blocks.rename(
        columns={
            "week": "week_a",
            "next_week": "week_b",
            "week_start": "start_date",
            "next_week_end": "end_date",
            "weekly_complaint_count": "week_a_count",
            "next_week_count": "week_b_count",
        }
    )
    blocks["block_total_complaints"] = blocks["week_a_count"] + blocks["week_b_count"]
    blocks.insert(0, "block_id", np.arange(len(blocks), dtype=int))
    return blocks[
        [
            "block_id",
            "week_a",
            "week_b",
            "start_date",
            "end_date",
            "week_a_count",
            "week_b_count",
            "block_total_complaints",
        ]
    ].reset_index(drop=True)


def build_top1_period_distribution(
    complaints: pd.DataFrame,
    baseline_pool: pd.DataFrame,
    baseline_candidates: pd.DataFrame,
    period_masks: dict[str, pd.Series],
) -> pd.DataFrame:
    records = []

    ordinary_records: list[dict] = []
    for row in baseline_candidates.itertuples(index=False):
        subset = complaints.loc[complaints["day"].between(row.start_date, row.end_date)].copy()
        top1 = subset["Top1_Emotion_Normalized"].fillna("Other")
        top1 = top1.where(top1.isin(TARGET_EMOTIONS), "Other")
        counts = top1.value_counts(normalize=True)
        for emotion in list(TARGET_EMOTIONS) + ["Other"]:
            ordinary_records.append({"block_id": row.block_id, "emotion": emotion, "share": float(counts.get(emotion, 0.0))})

    ordinary_df = pd.DataFrame(ordinary_records)
    ordinary_mean = ordinary_df.groupby("emotion", as_index=False)["share"].mean()
    ordinary_mean["period"] = "Ordinary"
    records.append(ordinary_mean)

    for period in ["Flood 2022", "Flood 2023"]:
        subset = complaints.loc[period_masks[period]].copy()
        top1 = subset["Top1_Emotion_Normalized"].fillna("Other")
        top1 = top1.where(top1.isin(TARGET_EMOTIONS), "Other")
        counts = top1.value_counts(normalize=True).rename_axis("emotion").reset_index(name="share")
        counts["period"] = period
        records.append(counts)

    return pd.concat(records, ignore_index=True)


def build_region_emotion_shift_table(
    complaints: pd.DataFrame,
    baseline_pool: pd.DataFrame,
    min_count: int = 5,
) -> pd.DataFrame:
    records: list[dict] = []
    target_emotions = FIGURE6_EMOTIONS
    period_specs = [
        ("Flood 2022", FLOOD_2022_START, FLOOD_2022_END),
        ("Flood 2023", FLOOD_2023_START, FLOOD_2023_END),
    ]

    baseline_top1 = baseline_pool["Top1_Emotion_Normalized"].fillna("Other")
    baseline_top1 = baseline_top1.where(baseline_top1.isin(target_emotions), "Other")

    for period, start, end in period_specs:
        flood = complaints.loc[complaints["day"].between(start, end)].copy()
        flood_top1 = flood["Top1_Emotion_Normalized"].fillna("Other")
        flood["top1_group"] = flood_top1.where(flood_top1.isin(target_emotions), "Other")

        for region, flood_region in flood.groupby("region"):
            baseline_region = baseline_pool.loc[baseline_pool["region"] == region].copy()
            baseline_region_top1 = baseline_region["Top1_Emotion_Normalized"].fillna("Other")
            baseline_region_top1 = baseline_region_top1.where(baseline_region_top1.isin(target_emotions), "Other")

            flood_n = int(len(flood_region))
            baseline_n = int(len(baseline_region))
            sufficient = (flood_n >= min_count) and (baseline_n >= min_count)

            flood_prop = flood_region["top1_group"].value_counts(normalize=True)
            baseline_prop = baseline_region_top1.value_counts(normalize=True)

            for emotion in target_emotions:
                event_share = float(flood_prop.get(emotion, 0.0))
                baseline_share = float(baseline_prop.get(emotion, 0.0))
                records.append(
                    {
                        "period": period,
                        "region": region,
                        "emotion": emotion,
                        "event_n": flood_n,
                        "baseline_n": baseline_n,
                        "event_share": event_share,
                        "baseline_share": baseline_share,
                        "delta_share": event_share - baseline_share,
                        "sufficient_data": bool(sufficient),
                    }
                )

    return pd.DataFrame(records)


def build_spatial_metrics(merged_daily: pd.DataFrame, baseline_date_weights: pd.DataFrame) -> pd.DataFrame:
    ordinary_source = merged_daily.merge(baseline_date_weights, on="date", how="inner")
    baseline = (
        ordinary_source.groupby("region", as_index=False)
        .apply(
            lambda frame: pd.Series(
                {
                    "baseline_anxiety": np.average(frame["Anxiety/Worried"].fillna(0.0), weights=frame["weight"]),
                    "baseline_precip": np.average(frame["precipitation_mm"].fillna(0.0), weights=frame["weight"]),
                }
            ),
            include_groups=False,
        )
        .reset_index()
    )

    outputs = []
    for period, start, end in [
        ("Flood 2022", FLOOD_2022_START, FLOOD_2022_END),
        ("Flood 2023", FLOOD_2023_START, FLOOD_2023_END),
    ]:
        event = (
            merged_daily.loc[merged_daily["date"].between(start, end)]
            .groupby("region", as_index=False)
            .agg(
                event_anxiety=("Anxiety/Worried", "mean"),
                event_precip=("precipitation_mm", "mean"),
            )
        )
        metrics = event.merge(baseline, on="region", how="left")
        metrics["anxiety_diff"] = metrics["event_anxiety"] - metrics["baseline_anxiety"]
        metrics["precip_diff"] = metrics["event_precip"] - metrics["baseline_precip"]
        metrics["mismatch_index"] = zscore(metrics["anxiety_diff"]) - zscore(metrics["precip_diff"])
        metrics["period"] = period
        outputs.append(metrics)

    return pd.concat(outputs, ignore_index=True)


def export_tables(
    bootstrap_summary: pd.DataFrame,
    bootstrap_distribution: pd.DataFrame,
    spatial_metrics: pd.DataFrame,
    period_top1: pd.DataFrame,
    region_emotion_shift: pd.DataFrame,
    baseline_block_summary: pd.DataFrame,
    ordinary_weeks: pd.DataFrame,
    baseline_candidates: pd.DataFrame,
    baseline_windows: pd.DataFrame,
    baseline_window_summary: pd.DataFrame,
    output_path: Path,
) -> None:
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        bootstrap_summary.to_excel(writer, sheet_name="bootstrap_summary", index=False)
        bootstrap_distribution.to_excel(writer, sheet_name="bootstrap_distribution", index=False)
        spatial_metrics.to_excel(writer, sheet_name="spatial_metrics", index=False)
        period_top1.to_excel(writer, sheet_name="period_top1_distribution", index=False)
        region_emotion_shift.to_excel(writer, sheet_name="region_emotion_shift", index=False)
        baseline_block_summary.to_excel(writer, sheet_name="baseline_block_summary", index=False)
        ordinary_weeks.to_excel(writer, sheet_name="ordinary_weeks", index=False)
        baseline_candidates.to_excel(writer, sheet_name="baseline_candidates", index=False)
        baseline_windows.to_excel(writer, sheet_name="baseline_windows", index=False)
        baseline_window_summary.to_excel(writer, sheet_name="baseline_window_summary", index=False)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Flood complaint emotion analysis pipeline")
    parser.add_argument("--emotion-path", type=Path, default=DEFAULT_EMOTION_PATH)
    parser.add_argument("--boundary-path", type=Path, default=DEFAULT_BOUNDARY_PATH)
    parser.add_argument("--bootstrap-resamples", type=int, default=5000)
    parser.add_argument("--baseline-windows", type=int, default=5000)
    parser.add_argument("--baseline-window-days", type=int, default=14)
    parser.add_argument("--baseline-exclusion-days", type=int, default=30)
    parser.add_argument("--ordinary-week-threshold", type=int, default=40)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    apply_lab_style()

    for directory in [DATA_DIR, FIG_DIR, TABLE_DIR]:
        directory.mkdir(parents=True, exist_ok=True)

    complaints = load_complaint_data(args.emotion_path)
    precip_daily = load_precipitation_data(DEFAULT_PRECIP_PATHS)
    merged_daily, merged_weekly, daily_national = build_daily_outputs(complaints, precip_daily)

    baseline_config = BaselineConfig(
        n_windows=args.baseline_windows,
        seed=args.seed,
        window_days=args.baseline_window_days,
        exclusion_days=args.baseline_exclusion_days,
    )
    ordinary_weeks = build_ordinary_week_table(complaints, weekly_threshold=args.ordinary_week_threshold)
    baseline_candidates = build_candidate_baseline_blocks(ordinary_weeks)
    if baseline_candidates.empty:
        raise ValueError("No ordinary weeks were identified under the weekly complaint count <= 40 rule.")
    baseline_windows = sample_baseline_blocks(
        candidate_blocks=baseline_candidates,
        config=baseline_config,
    )
    baseline_date_weights = build_baseline_date_weights(baseline_windows)
    baseline_complaint_pool = expand_complaints_by_date_weight(complaints, baseline_date_weights, date_col="day")
    baseline_window_summary = summarize_baseline_windows(daily_national, baseline_windows)
    baseline_block_summary = summarize_block_emotions(complaints, baseline_candidates, TARGET_EMOTIONS, date_col="day")

    period_masks = build_period_masks(complaints)
    bootstrap_summary, bootstrap_distribution = run_bootstrap_suite(
        complaint_scores=complaints,
        baseline_block_summary=baseline_block_summary,
        emotions=TARGET_EMOTIONS,
        period_masks=period_masks,
        config=BootstrapConfig(n_resamples=args.bootstrap_resamples, seed=args.seed),
    )

    region_totals = complaints.groupby("region", as_index=False).size().rename(columns={"size": "complaint_count"})
    period_top1 = build_top1_period_distribution(complaints, baseline_complaint_pool, baseline_candidates, period_masks)
    region_emotion_shift = build_region_emotion_shift_table(complaints, baseline_complaint_pool)
    spatial_metrics = build_spatial_metrics(merged_daily, baseline_date_weights)
    province_shapes = load_province_geometries(args.boundary_path)

    merged_daily.to_csv(DATA_DIR / "merged_daily_precip_complaints.csv", index=False)
    merged_weekly.to_csv(DATA_DIR / "merged_weekly_precip_complaints.csv", index=False)

    make_time_series_figure(daily_national, FIG_DIR / "fig1_timeseries.png")
    make_region_distribution_figure(region_totals, FIG_DIR / "fig2_distribution.png")
    make_emotion_distribution_figure(period_top1, FIG_DIR / "fig3_emotion.png")
    make_bootstrap_forest_plot(bootstrap_summary, FIG_DIR / "fig4_bootstrap.png")
    make_map_figure(province_shapes, spatial_metrics, FIG_DIR / "fig5_map.png")

    export_tables(
        bootstrap_summary=bootstrap_summary,
        bootstrap_distribution=bootstrap_distribution,
        spatial_metrics=spatial_metrics,
        period_top1=period_top1,
        region_emotion_shift=region_emotion_shift,
        baseline_block_summary=baseline_block_summary,
        ordinary_weeks=ordinary_weeks,
        baseline_candidates=baseline_candidates,
        baseline_windows=baseline_windows,
        baseline_window_summary=baseline_window_summary,
        output_path=TABLE_DIR / "bootstrap_results.xlsx",
    )

    print(f"Saved figures to {FIG_DIR}")
    print(f"Saved tables to {TABLE_DIR}")
    print(f"Saved merged data to {DATA_DIR}")


if __name__ == "__main__":
    main()
