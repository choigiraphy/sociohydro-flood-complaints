# Figure Processed Sources

Each file in this directory is intended to be a single processed input source for one manuscript figure.
The goal is figure-level analytical reproducibility without exposing raw complaint text.

## Figure 2
- file: `figure2_source.xlsx`
- sheets: metadata, national_weekly, regional_weekly
- rows: {'national_weekly': 156, 'regional_weekly': 1732}
- source files: /Volumes/Keywest_JetDrive 1/데이터저장소/final_final/complaints_with_periods_weekly_aligned.xlsx
- note: Complaint weekly aggregates only; no raw text.

## Figure 3
- file: `figure3_source.xlsx`
- sheets: metadata, national_weekly, regional_weekly
- rows: {'national_weekly': 157, 'regional_weekly': 2669}
- source files: /Volumes/Keywest_JetDrive 1/데이터저장소/강수데이터/pivot_weekly_precipitation_2021_2023.csv
- note: Regional precipitation built from mapped station sums.

## Figure 4
- file: `figure4_source.xlsx`
- sheets: metadata, full_period_weekly, event_window_daily
- rows: {'full_period_weekly': 157, 'event_window_daily': 28}
- source files: /Volumes/Keywest_JetDrive 1/데이터저장소/final_final/complaints_with_periods.xlsx, /Volumes/Keywest_JetDrive 1/데이터저장소/강수데이터/pivot_daily_precipitation_2021_2023.csv, /Volumes/Keywest_JetDrive 1/데이터저장소/datalab_홍수.xlsx, /Volumes/Keywest_JetDrive 1/데이터저장소/google/multiTimeline.csv, /Volumes/Keywest_JetDrive 1/데이터저장소/amCharts_홍수_weekly_bigkinds.csv
- note: Single processed file contains both full-period weekly and flood-window daily inputs.

## Figure 5
- file: `figure5_source.xlsx`
- sheets: metadata, bootstrap_summary
- rows: {'bootstrap_summary': 21}
- source files: /Volumes/Keywest_JetDrive 1/데이터저장소/final_final/bootstrap_results_flood_vs_ordinary.csv
- note: Direct processed bootstrap result table.

## Figure 6
- file: `figure6_source.xlsx`
- sheets: metadata, region_event_intensity
- rows: {'region_event_intensity': 34}
- source files: /Volumes/Keywest_JetDrive 1/데이터저장소/final_final/complaints_with_periods_weekly_aligned.xlsx, /Volumes/Keywest_JetDrive 1/데이터저장소/강수데이터/pivot_daily_precipitation_2021_2023.csv, /Volumes/Keywest_JetDrive 1/Codex/Academia/Complaint/data/region_population_event_months.csv, /Volumes/Keywest_JetDrive 1/데이터저장소/final_final/LX법정구역경계_시도_전국/SIDO.shp
- note: One file includes geometry WKT and all regional attributes needed for the spatial intensity figure.

## Figure 7
- file: `figure7_source.xlsx`
- sheets: metadata, region_emotion_shift
- rows: {'region_emotion_shift': 102}
- source files: /Volumes/Keywest_JetDrive 1/데이터저장소/final_final/complaints_with_periods_weekly_aligned.xlsx, /Volumes/Keywest_JetDrive 1/데이터저장소/final_final/LX법정구역경계_시도_전국/SIDO.shp
- note: One file includes geometry WKT and focal emotion deltas for both flood events.
