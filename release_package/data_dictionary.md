# Data Dictionary

## `data/merged_daily_precip_complaints.csv`

- `date`: calendar date
- `period`: event or non-event label used in the analysis
- `region`: first-order administrative region
- `complaint_count`: daily flood-related complaint count
- `precipitation`: daily aggregated precipitation matched to region
- emotion-related columns: aggregated emotion proportions or scores used for event and baseline comparisons

## `data/merged_weekly_precip_complaints.csv`

- `week_start`: start date of the weekly interval
- `region`: first-order administrative region
- `weekly_complaint_count`: weekly flood-related complaint count
- `weekly_precipitation`: aggregated weekly precipitation

## `tables/bootstrap_results.xlsx`

- `bootstrap_summary`: mean differences, confidence intervals, and significance flags
- `bootstrap_distribution`: full bootstrap draws
- `spatial_metrics`: regional comparison metrics used in spatial interpretation
- `period_top1_distribution`: dominant-emotion distributions by analysis period
- `region_emotion_shift`: baseline-referenced regional emotion shifts
- `ordinary_weeks`: weekly ordinary-period identification
- `baseline_candidates`: eligible 14-day baseline blocks
- `baseline_windows`: sampled baseline blocks
- `baseline_window_summary`: summary statistics for sampled baseline blocks
- `baseline_block_summary`: block-level emotion summaries used for flood-versus-baseline bootstrap comparison

## `tables/baseline_distribution_summary.xlsx`

- ordinary-week complaint distributions
- baseline block complaint distributions

## `tables/threshold_sensitivity.xlsx`

- sensitivity of flood-versus-baseline results to ordinary-week thresholds of 30, 40, and 50

## Privacy note

No raw complaint text is included in the shared package. All shared datasets are aggregated and de-identified.
