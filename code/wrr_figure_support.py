from __future__ import annotations

from pathlib import Path
import re

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


BASE_DATA_DIR = Path("/Volumes/Keywest_JetDrive 1/학교/2026-1/AGU_WRR_Choi/Code/wrr_reproducible/data")
BASE_FIG_DIR = Path("/Volumes/Keywest_JetDrive 1/Codex/Academia/Complaint/figures")

DEFAULT_PATHS = {
    "daily_hydro": BASE_DATA_DIR / "daily_hydro_social_metrics.csv",
    "naver_weekly": BASE_DATA_DIR / "naver_search_volume.xlsx",
    "google_weekly": BASE_DATA_DIR / "google_trends_weekly.xlsx",
    "google_daily": BASE_DATA_DIR / "google_trends_daily.csv",
    "complaints_daily": BASE_DATA_DIR / "daily_complaint_counts.xlsx",
    "bootstrap_emotion": BASE_DATA_DIR / "bootstrap_emotion_2021_2023.csv",
    "news_weekly": BASE_DATA_DIR / "news_volume_weekly.csv",
}

FLOOD_PERIODS = {
    "2022 Flood": ("2022-08-08", "2022-08-21"),
    "2023 Flood": ("2023-07-10", "2023-07-23"),
}

FLOOD_SHADE = {
    "2022 Flood": "lightblue",
    "2023 Flood": "lightgreen",
}

COLORS = {
    "Mean Precipitation": "#1f77b4",
    "Flood Complaints": "#d62728",
    "Naver DataLab": "#2ca02c",
    "Google Trends": "#ffbf00",
    "News Volume": "#7f7f7f",
}


def apply_wrr_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
            "font.size": 18,
            "axes.titlesize": 24,
            "axes.labelsize": 20,
            "xtick.labelsize": 18,
            "ytick.labelsize": 18,
            "legend.fontsize": 16,
            "axes.linewidth": 2.2,
            "xtick.major.width": 1.8,
            "ytick.major.width": 1.8,
            "xtick.major.size": 6,
            "ytick.major.size": 6,
            "axes.grid": True,
            "grid.color": "#e3e3e3",
            "grid.linewidth": 0.8,
            "figure.facecolor": "white",
            "savefig.facecolor": "white",
            "savefig.dpi": 300,
            "savefig.bbox": "tight",
        }
    )


def assert_exists(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")


def parse_date_series(series: pd.Series) -> pd.Series:
    text = series.astype(str)
    numeric = text.str.replace(r"\D", "", regex=True)
    dt1 = pd.to_datetime(numeric, format="%Y%m%d", errors="coerce")
    dt2 = pd.to_datetime(text, errors="coerce")
    out = dt1.copy()
    out[out.isna()] = dt2[out.isna()]
    return out


def read_2col_timeseries(path: Path) -> pd.Series:
    assert_exists(path)
    if path.suffix.lower() in {".xlsx", ".xls"}:
        df = pd.read_excel(path)
        c0, c1 = str(df.columns[0]), str(df.columns[1])
        is_dateish = bool(re.match(r"^\d{4}[-/.]?\d{2}[-/.]?\d{2}$", c0))
        is_numish = bool(re.match(r"^[+-]?\d+(\.\d+)?$", c1.replace(",", "")))
        if is_dateish and is_numish:
            df = pd.read_excel(path, header=None)
    else:
        df = pd.read_csv(path)

    df = df.iloc[:, :2].copy()
    df.columns = ["date", "value"]
    df["date"] = parse_date_series(df["date"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date")
    series = pd.Series(df["value"].values, index=df["date"].dt.normalize())
    return series[~series.index.duplicated(keep="last")].sort_index()


def normalize_0_100(series: pd.Series) -> pd.Series:
    series = pd.to_numeric(series, errors="coerce").astype(float)
    if series.dropna().empty:
        return series * np.nan
    minimum = np.nanmin(series.values)
    maximum = np.nanmax(series.values)
    if np.isclose(maximum, minimum):
        return pd.Series(0.0, index=series.index)
    return (series - minimum) / (maximum - minimum) * 100.0


def load_daily_hydro(path: Path) -> tuple[pd.Series, pd.Series]:
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.normalize()
    df = df.dropna(subset=["date"]).sort_values("date").set_index("date")
    precip = pd.to_numeric(df["mean_precip"], errors="coerce").fillna(0.0)
    complaints = pd.to_numeric(df["complaints"], errors="coerce").fillna(0.0)
    return precip, complaints


def load_daily_complaints(path: Path) -> pd.Series:
    df = pd.read_excel(path)
    df = df.iloc[:, :2].copy()
    df.columns = ["date", "count"]
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.normalize()
    df = df.dropna(subset=["date"]).sort_values("date").set_index("date")
    return pd.to_numeric(df["count"], errors="coerce").fillna(0.0)


def load_bootstrap_results(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)


def maybe_load_optional_series(path: Path) -> pd.Series | None:
    if path.exists():
        return read_2col_timeseries(path)
    return None
