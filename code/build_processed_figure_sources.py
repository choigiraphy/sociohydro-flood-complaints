from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import re

import geopandas as gpd
import numpy as np
import pandas as pd


ROOT = Path("/Volumes/Keywest_JetDrive 1/Codex/Academia/Complaint")
DATA_REPO = Path("/Volumes/Keywest_JetDrive 1/데이터저장소")
OUT_DIR = ROOT / "data_processed"

FLOOD_WINDOWS = {
    "Flood 2022": ("2022-08-08", "2022-08-21"),
    "Flood 2023": ("2023-07-10", "2023-07-23"),
}

REGION_FULLNAME_TO_ENG = {
    "서울특별시": "Seoul",
    "부산광역시": "Busan",
    "대구광역시": "Daegu",
    "인천광역시": "Incheon",
    "광주광역시": "Gwangju",
    "대전광역시": "Daejeon",
    "울산광역시": "Ulsan",
    "세종특별자치시": "Sejong",
    "경기도": "Gyeonggi",
    "강원특별자치도": "Gangwon",
    "강원도": "Gangwon",
    "충청북도": "Chungbuk",
    "충청남도": "Chungnam",
    "전북특별자치도": "Jeonbuk",
    "전라북도": "Jeonbuk",
    "전라남도": "Jeonnam",
    "경상북도": "Gyeongbuk",
    "경상남도": "Gyeongnam",
    "제주특별자치도": "Jeju",
}

REGION_ENG_TO_KOR = {
    "Seoul": "서울특별시",
    "Busan": "부산광역시",
    "Daegu": "대구광역시",
    "Incheon": "인천광역시",
    "Gwangju": "광주광역시",
    "Daejeon": "대전광역시",
    "Ulsan": "울산광역시",
    "Sejong": "세종특별자치시",
    "Gyeonggi": "경기도",
    "Gangwon": "강원특별자치도",
    "Chungbuk": "충청북도",
    "Chungnam": "충청남도",
    "Jeonbuk": "전북특별자치도",
    "Jeonnam": "전라남도",
    "Gyeongbuk": "경상북도",
    "Gyeongnam": "경상남도",
    "Jeju": "제주특별자치도",
}

REGION_ORDER = [
    "Gangwon",
    "Seoul",
    "Incheon",
    "Gyeonggi",
    "Chungbuk",
    "Chungnam",
    "Daejeon",
    "Sejong",
    "Gyeongbuk",
    "Daegu",
    "Jeonbuk",
    "Jeonnam",
    "Gwangju",
    "Ulsan",
    "Gyeongnam",
    "Busan",
    "Jeju",
]

STATION_TO_REGION = {
    "서울": "Seoul",
    "부산": "Busan",
    "대구": "Daegu",
    "인천": "Incheon",
    "광주": "Gwangju",
    "대전": "Daejeon",
    "울산": "Ulsan",
    "세종": "Sejong",
    "수원": "Gyeonggi",
    "춘천": "Gangwon",
    "청주": "Chungbuk",
    "홍성": "Chungnam",
    "전주": "Jeonbuk",
    "목포": "Jeonnam",
    "안동": "Gyeongbuk",
    "창원": "Gyeongnam",
    "제주": "Jeju",
}

FOCAL_EMOTIONS = ["Anger/Rage", "Sadness", "Embarrassment/Distress"]
MIN_COUNT_THRESHOLD = 5


@dataclass
class FigureSource:
    figure: str
    output_path: Path
    source_files: list[str]
    sheets: list[str]
    row_counts: dict[str, int]
    notes: str


def _ensure_outdir() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)


def _meta_sheet(entries: dict[str, object]) -> pd.DataFrame:
    return pd.DataFrame({"field": list(entries.keys()), "value": list(entries.values())})


def _normalize_region(series: pd.Series) -> pd.Series:
    return series.astype(str).map(REGION_FULLNAME_TO_ENG)


def _read_google_daily(path: Path) -> pd.Series:
    # File is stored as a 2-column CSV without a true header.
    df = pd.read_csv(path, header=None).iloc[:, :2].copy()
    df.columns = ["date", "value"]
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date")
    return pd.Series(df["value"].values, index=df["date"].dt.normalize(), name="google")


def _read_naver_daily(path: Path) -> pd.Series:
    df = pd.read_excel(path).iloc[:, :2].copy()
    df.columns = ["date", "value"]
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date")
    return pd.Series(df["value"].values, index=df["date"].dt.normalize(), name="naver")


def _read_news_weekly(path: Path) -> pd.Series:
    df = pd.read_csv(path).iloc[:, :2].copy()
    df.columns = ["date", "value"]
    df["date"] = pd.to_datetime(df["date"].astype(str), format="%Y%m%d", errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date")
    return pd.Series(df["value"].values, index=df["date"], name="news")


def _load_shape_with_region() -> gpd.GeoDataFrame:
    shp = DATA_REPO / "final_final/LX법정구역경계_시도_전국/SIDO.shp"
    gdf = gpd.read_file(shp, encoding="utf-8")[["ctpr_cd", "ctpr_nm", "geometry"]].copy()
    gdf["region_eng"] = gdf["ctpr_nm"].map(REGION_FULLNAME_TO_ENG)
    gdf = gdf.dropna(subset=["region_eng"]).copy()
    return gdf


def _write_excel(path: Path, sheets: dict[str, pd.DataFrame]) -> None:
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for sheet_name, df in sheets.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)


def build_figure2_source() -> FigureSource:
    src = DATA_REPO / "final_final/complaints_with_periods_weekly_aligned.xlsx"
    df = pd.read_excel(src)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date", "민원발생지"]).copy()
    df["region_eng"] = _normalize_region(df["민원발생지"])
    df = df.dropna(subset=["region_eng"]).copy()
    parts = df["week"].astype(str).str.split("/", n=1, expand=True)
    df["week_start"] = pd.to_datetime(parts[0], errors="coerce")
    df["week_end"] = pd.to_datetime(parts[1], errors="coerce")

    national = (
        df.groupby(["week", "week_start", "week_end"], as_index=False)
        .size()
        .rename(columns={"size": "complaint_count"})
        .sort_values("week_start")
    )
    regional = (
        df.groupby(["week", "week_start", "week_end", "region_eng"], as_index=False)
        .size()
        .rename(columns={"size": "complaint_count"})
        .sort_values(["week_start", "region_eng"])
    )
    regional["region_order"] = regional["region_eng"].map({r: i for i, r in enumerate(REGION_ORDER, 1)})

    out = OUT_DIR / "figure2_source.xlsx"
    _write_excel(
        out,
        {
            "metadata": _meta_sheet(
                {
                    "figure": "Figure 2",
                    "description": "Weekly national and regional complaint counts for spatiotemporal complaint figure.",
                    "source_file": str(src),
                    "week_definition": "week labels inherited from complaints_with_periods_weekly_aligned.xlsx",
                    "region_mapping": "민원발생지 -> English province names",
                }
            ),
            "national_weekly": national,
            "regional_weekly": regional,
        },
    )
    return FigureSource("Figure 2", out, [str(src)], ["metadata", "national_weekly", "regional_weekly"], {"national_weekly": len(national), "regional_weekly": len(regional)}, "Complaint weekly aggregates only; no raw text.")


def build_figure3_source() -> FigureSource:
    src = DATA_REPO / "강수데이터/pivot_weekly_precipitation_2021_2023.csv"
    df = pd.read_csv(src)
    df["week_start"] = pd.to_datetime(df["week"], errors="coerce")
    station_cols = [c for c in df.columns if c not in {"week", "date", "week_start"}]

    national = df[["week", "date", "week_start"]].copy()
    national["national_precip_sum"] = df[station_cols].sum(axis=1, skipna=True)

    melted = df.melt(id_vars=["week", "date", "week_start"], value_vars=station_cols, var_name="station", value_name="precipitation_mm")
    melted["region_eng"] = melted["station"].map(STATION_TO_REGION)
    melted = melted.dropna(subset=["region_eng"]).copy()
    regional = (
        melted.groupby(["week", "date", "week_start", "region_eng"], as_index=False)["precipitation_mm"]
        .sum()
        .sort_values(["week_start", "region_eng"])
    )
    regional["region_order"] = regional["region_eng"].map({r: i for i, r in enumerate(REGION_ORDER, 1)})

    out = OUT_DIR / "figure3_source.xlsx"
    _write_excel(
        out,
        {
            "metadata": _meta_sheet(
                {
                    "figure": "Figure 3",
                    "description": "Weekly national and regional precipitation aggregates for the spatiotemporal precipitation figure.",
                    "source_file": str(src),
                    "station_to_region_rule": "core province station mapping from manuscript config",
                    "aggregation": "weekly station sums, then sum within region",
                }
            ),
            "national_weekly": national[["week", "date", "week_start", "national_precip_sum"]],
            "regional_weekly": regional,
        },
    )
    return FigureSource("Figure 3", out, [str(src)], ["metadata", "national_weekly", "regional_weekly"], {"national_weekly": len(national), "regional_weekly": len(regional)}, "Regional precipitation built from mapped station sums.")


def build_figure4_source() -> FigureSource:
    complaints_src = DATA_REPO / "final_final/complaints_with_periods.xlsx"
    precip_src = DATA_REPO / "강수데이터/pivot_daily_precipitation_2021_2023.csv"
    naver_src = DATA_REPO / "datalab_홍수.xlsx"
    google_src = DATA_REPO / "google/multiTimeline.csv"
    news_src = DATA_REPO / "amCharts_홍수_weekly_bigkinds.csv"

    complaints = pd.read_excel(complaints_src, usecols=["date"])
    complaints["date"] = pd.to_datetime(complaints["date"], errors="coerce").dt.normalize()
    complaints_daily = complaints.dropna().groupby("date").size().rename("complaints").to_frame()

    precip = pd.read_csv(precip_src)
    precip["date"] = pd.to_datetime(precip.iloc[:, 0], errors="coerce").dt.normalize()
    station_cols = [c for c in precip.columns if c not in {precip.columns[0], "date"}]
    precip_daily = pd.DataFrame({"date": precip["date"], "precipitation": precip[station_cols].sum(axis=1, skipna=True)}).dropna(subset=["date"]).set_index("date")

    naver_daily = _read_naver_daily(naver_src).rename("naver")
    google_daily = _read_google_daily(google_src).rename("google")
    news_weekly = _read_news_weekly(news_src)

    daily = precip_daily.join(complaints_daily, how="outer")
    daily = daily.join(naver_daily, how="left").join(google_daily, how="left")
    daily = daily.sort_index()
    daily["complaints"] = daily["complaints"].fillna(0)
    daily["precipitation"] = daily["precipitation"].fillna(0)

    weekly = pd.DataFrame(index=pd.date_range(daily.index.min(), daily.index.max(), freq="W-SUN"))
    weekly["precipitation"] = daily["precipitation"].resample("W-SUN").sum()
    weekly["complaints"] = daily["complaints"].resample("W-SUN").sum()
    weekly["naver"] = daily["naver"].resample("W-SUN").mean()
    weekly["google"] = daily["google"].resample("W-SUN").mean()
    news_weekly = news_weekly.resample("W-SUN").sum()
    weekly["news_volume"] = news_weekly.reindex(weekly.index)
    weekly = weekly.reset_index().rename(columns={"index": "week_end"})

    event_frames = []
    for event, (start, end) in FLOOD_WINDOWS.items():
        s = pd.Timestamp(start)
        e = pd.Timestamp(end)
        frame = daily.loc[s:e].reset_index().rename(columns={"index": "date"})
        frame["event"] = event
        frame["day"] = frame["date"].dt.strftime("%Y-%m-%d")
        event_frames.append(frame)
    event_daily = pd.concat(event_frames, ignore_index=True)

    out = OUT_DIR / "figure4_source.xlsx"
    _write_excel(
        out,
        {
            "metadata": _meta_sheet(
                {
                    "figure": "Figure 4",
                    "description": "Processed full-period weekly and event-window daily hydro-social inputs for temporal multi-panel figure.",
                    "complaints_source": str(complaints_src),
                    "precip_source": str(precip_src),
                    "naver_source": str(naver_src),
                    "google_source": str(google_src),
                    "news_source": str(news_src),
                    "weekly_rule": "W-SUN; precip/news summed, complaints summed, search series averaged",
                }
            ),
            "full_period_weekly": weekly,
            "event_window_daily": event_daily,
        },
    )
    return FigureSource("Figure 4", out, [str(complaints_src), str(precip_src), str(naver_src), str(google_src), str(news_src)], ["metadata", "full_period_weekly", "event_window_daily"], {"full_period_weekly": len(weekly), "event_window_daily": len(event_daily)}, "Single processed file contains both full-period weekly and flood-window daily inputs.")


def build_figure5_source() -> FigureSource:
    src = DATA_REPO / "final_final/bootstrap_results_flood_vs_ordinary.csv"
    df = pd.read_csv(src)
    df = df.sort_values("Emotion").reset_index(drop=True)
    out = OUT_DIR / "figure5_source.xlsx"
    _write_excel(
        out,
        {
            "metadata": _meta_sheet(
                {
                    "figure": "Figure 5",
                    "description": "Bootstrap forest-plot input for flood-vs-ordinary emotion differences.",
                    "source_file": str(src),
                    "fields": "Delta_2022, CI_Low_2022, CI_High_2022, Sig_2022, Delta_2023, CI_Low_2023, CI_High_2023, Sig_2023",
                }
            ),
            "bootstrap_summary": df,
        },
    )
    return FigureSource("Figure 5", out, [str(src)], ["metadata", "bootstrap_summary"], {"bootstrap_summary": len(df)}, "Direct processed bootstrap result table.")


def build_figure6_source() -> FigureSource:
    complaint_src = DATA_REPO / "final_final/complaints_with_periods_weekly_aligned.xlsx"
    precip_src = DATA_REPO / "강수데이터/pivot_daily_precipitation_2021_2023.csv"
    pop_src = ROOT / "data/region_population_event_months.csv"
    shape_src = DATA_REPO / "final_final/LX법정구역경계_시도_전국/SIDO.shp"

    complaints = pd.read_excel(complaint_src, usecols=["date", "민원발생지"])
    complaints["date"] = pd.to_datetime(complaints["date"], errors="coerce").dt.normalize()
    complaints["region_eng"] = _normalize_region(complaints["민원발생지"])
    complaints = complaints.dropna(subset=["date", "region_eng"]).copy()

    precip = pd.read_csv(precip_src)
    precip["date"] = pd.to_datetime(precip.iloc[:, 0], errors="coerce").dt.normalize()
    station_cols = [c for c in precip.columns if c not in {precip.columns[0], "date"}]
    melted = precip.melt(id_vars=[precip.columns[0], "date"], value_vars=station_cols, var_name="station", value_name="precipitation_mm")
    melted["region_eng"] = melted["station"].map(STATION_TO_REGION)
    melted = melted.dropna(subset=["date", "region_eng"]).copy()
    precip_region = melted.groupby(["date", "region_eng"], as_index=False)["precipitation_mm"].sum()

    population = pd.read_csv(pop_src)
    gdf = _load_shape_with_region()

    rows = []
    for event, (start, end) in FLOOD_WINDOWS.items():
        s = pd.Timestamp(start)
        e = pd.Timestamp(end)
        compl_event = (
            complaints[(complaints["date"] >= s) & (complaints["date"] <= e)]
            .groupby("region_eng")
            .size()
            .rename("complaint_count")
        )
        precip_event = (
            precip_region[(precip_region["date"] >= s) & (precip_region["date"] <= e)]
            .groupby("region_eng")["precipitation_mm"]
            .agg(regional_mean_precip="mean", regional_max_precip="max", event_cumulative_precip="sum")
        )
        merged = gdf[["region_eng", "ctpr_nm", "geometry"]].merge(compl_event, on="region_eng", how="left").merge(precip_event, on="region_eng", how="left")
        merged["event"] = event
        pop_event = population[population["event"] == event][["region", "population"]].rename(columns={"region": "ctpr_nm"})
        merged = merged.merge(pop_event, on="ctpr_nm", how="left")
        merged["complaint_count"] = merged["complaint_count"].fillna(0)
        merged["complaints_per_100k"] = np.where(
            merged["population"].notna() & (merged["population"] > 0),
            merged["complaint_count"] / merged["population"] * 100000.0,
            np.nan,
        )
        merged["geometry_wkt"] = merged.geometry.to_wkt()
        rows.append(merged.drop(columns="geometry"))
    result = pd.concat(rows, ignore_index=True)

    out = OUT_DIR / "figure6_source.xlsx"
    _write_excel(
        out,
        {
            "metadata": _meta_sheet(
                {
                    "figure": "Figure 6",
                    "description": "Regional complaint intensity and precipitation intensity inputs with geometry in WKT.",
                    "complaint_source": str(complaint_src),
                    "precip_source": str(precip_src),
                    "population_source": str(pop_src),
                    "shape_source": str(shape_src),
                    "shape_crs": "EPSG:5186",
                    "event_metrics": "complaint_count, complaints_per_100k, regional_mean_precip, regional_max_precip, event_cumulative_precip",
                }
            ),
            "region_event_intensity": result,
        },
    )
    return FigureSource("Figure 6", out, [str(complaint_src), str(precip_src), str(pop_src), str(shape_src)], ["metadata", "region_event_intensity"], {"region_event_intensity": len(result)}, "One file includes geometry WKT and all regional attributes needed for the spatial intensity figure.")


def build_figure7_source() -> FigureSource:
    complaint_src = DATA_REPO / "final_final/complaints_with_periods_weekly_aligned.xlsx"
    shape_src = DATA_REPO / "final_final/LX법정구역경계_시도_전국/SIDO.shp"
    complaints = pd.read_excel(complaint_src, usecols=["date", "민원발생지", "Top1_Emotion", "period"])
    complaints["date"] = pd.to_datetime(complaints["date"], errors="coerce").dt.normalize()
    complaints["region_eng"] = _normalize_region(complaints["민원발생지"])
    complaints = complaints.dropna(subset=["date", "region_eng", "Top1_Emotion", "period"]).copy()
    complaints["Top1_Emotion"] = complaints["Top1_Emotion"].replace({"Sad/Disappointed": "Sadness"})

    baseline = complaints[complaints["period"] == "ordinary"].copy()
    gdf = _load_shape_with_region()

    rows = []
    for event, period_value in [("Flood 2022", "2022_flood"), ("Flood 2023", "2023_flood")]:
        flood = complaints[complaints["period"] == period_value].copy()
        baseline_prop = (
            baseline.groupby(["region_eng", "Top1_Emotion"]).size().groupby(level=0).apply(lambda s: s / s.sum())
        )
        flood_prop = (
            flood.groupby(["region_eng", "Top1_Emotion"]).size().groupby(level=0).apply(lambda s: s / s.sum())
        )
        for emotion in FOCAL_EMOTIONS:
            base_vals = baseline_prop.xs(emotion, level=1, drop_level=False) if emotion in baseline_prop.index.get_level_values(1) else pd.Series(dtype=float)
            flood_vals = flood_prop.xs(emotion, level=1, drop_level=False) if emotion in flood_prop.index.get_level_values(1) else pd.Series(dtype=float)
            merged = gdf[["region_eng", "ctpr_nm", "geometry"]].copy()
            merged["event"] = event
            merged["emotion"] = emotion
            flood_counts = flood.groupby("region_eng").size().rename("flood_count")
            baseline_counts = baseline.groupby("region_eng").size().rename("baseline_count")
            merged = merged.merge(flood_counts, on="region_eng", how="left").merge(baseline_counts, on="region_eng", how="left")
            merged["flood_count"] = merged["flood_count"].fillna(0)
            merged["baseline_count"] = merged["baseline_count"].fillna(0)
            merged["flood_prop"] = merged["region_eng"].map({k[0]: v for k, v in flood_vals.to_dict().items()})
            merged["baseline_prop"] = merged["region_eng"].map({k[0]: v for k, v in base_vals.to_dict().items()})
            merged["flood_prop"] = merged["flood_prop"].fillna(0)
            merged["baseline_prop"] = merged["baseline_prop"].fillna(0)
            merged["delta_prop"] = merged["flood_prop"] - merged["baseline_prop"]
            merged["meets_min_count"] = (merged["flood_count"] >= MIN_COUNT_THRESHOLD) & (merged["baseline_count"] >= MIN_COUNT_THRESHOLD)
            merged["geometry_wkt"] = merged.geometry.to_wkt()
            rows.append(merged.drop(columns="geometry"))
    result = pd.concat(rows, ignore_index=True)

    out = OUT_DIR / "figure7_source.xlsx"
    _write_excel(
        out,
        {
            "metadata": _meta_sheet(
                {
                    "figure": "Figure 7",
                    "description": "Regional focal-emotion flood-minus-baseline shifts with geometry in WKT.",
                    "complaint_source": str(complaint_src),
                    "shape_source": str(shape_src),
                    "shape_crs": "EPSG:5186",
                    "focal_emotions": ", ".join(FOCAL_EMOTIONS),
                    "minimum_count_rule": f"flood_count >= {MIN_COUNT_THRESHOLD} and baseline_count >= {MIN_COUNT_THRESHOLD}",
                }
            ),
            "region_emotion_shift": result,
        },
    )
    return FigureSource("Figure 7", out, [str(complaint_src), str(shape_src)], ["metadata", "region_emotion_shift"], {"region_emotion_shift": len(result)}, "One file includes geometry WKT and focal emotion deltas for both flood events.")


def write_manifest(sources: list[FigureSource]) -> None:
    manifest = []
    for src in sources:
        manifest.append(
            {
                "figure": src.figure,
                "output_path": str(src.output_path),
                "source_files": src.source_files,
                "sheets": src.sheets,
                "row_counts": src.row_counts,
                "notes": src.notes,
            }
        )
    (OUT_DIR / "figure_processed_sources_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def write_readme(sources: list[FigureSource]) -> None:
    lines = [
        "# Figure Processed Sources",
        "",
        "Each file in this directory is intended to be a single processed input source for one manuscript figure.",
        "The goal is figure-level analytical reproducibility without exposing raw complaint text.",
        "",
    ]
    for src in sources:
        lines.extend(
            [
                f"## {src.figure}",
                f"- file: `{src.output_path.name}`",
                f"- sheets: {', '.join(src.sheets)}",
                f"- rows: {src.row_counts}",
                f"- source files: {', '.join(src.source_files)}",
                f"- note: {src.notes}",
                "",
            ]
        )
    (OUT_DIR / "README.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    _ensure_outdir()
    sources = [
        build_figure2_source(),
        build_figure3_source(),
        build_figure4_source(),
        build_figure5_source(),
        build_figure6_source(),
        build_figure7_source(),
    ]
    write_manifest(sources)
    write_readme(sources)
    print(json.dumps([{s.figure: str(s.output_path)} for s in sources], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
