# Sociohydro Flood Complaints Reproducibility Package

This repository contains the shareable code, figures, tables, and aggregated datasets used to reproduce the main analytical workflow for the manuscript "Event-dependent coupling between extreme rainfall and institutionalized civic response: Evidence from administrative complaints in South Korea."

## What is included

- `code/`: analysis, validation, and figure-generation scripts
- `data/`: de-identified aggregated datasets, public minimal subset, and synthetic smoke-test input
- `data_processed/`: figure-level processed source files for Figures 2-7
- `tables/`: bootstrap outputs, baseline summaries, and sensitivity tables
- `figures/`: manuscript-ready figure exports

## What is not included

- Raw civil complaint texts
- Complaint-level identifiable records
- Any restricted administrative files provided under the ACRC memorandum of understanding

These source records cannot be shared publicly because access is restricted by legal and privacy requirements.

## Reproducibility workflow

1. Run the main pipeline:

```bash
python3 code/main_pipeline.py --bootstrap-resamples 500 --baseline-windows 500 --ordinary-week-threshold 40
```

2. Regenerate manuscript figures:

```bash
python3 code/generate_figure4_wrr.py
python3 code/generate_figure5_wrr.py
python3 code/generate_figure6_wrr.py
```

3. Build figure-level processed sources:

```bash
python3 code/build_processed_figure_sources.py
```

4. Export supporting tables:

```bash
python3 code/export_baseline_summary.py
python3 code/export_threshold_sensitivity.py --baseline-windows 500 --bootstrap-resamples 500
```

## Baseline definition

- Flood windows:
  - 2022 Seoul flood: `2022-08-08` to `2022-08-21`
  - 2023 Osong flood: `2023-07-10` to `2023-07-23`
- Ordinary weeks: non-flood weeks with weekly complaint counts `<= 40`
- Baseline unit: `14-day block = two consecutive ordinary weeks`

## Environment

- Python 3.9
- PyTorch 1.12
- transformers 4.21
- geopandas 0.11

See `environment.yml` for a reproducible environment specification.

## Data access note

Publicly shareable aggregated outputs are included here. Access to restricted raw complaint records is controlled by the Anti-Corruption and Civil Rights Commission (ACRC) of South Korea and is not managed through this package.

## Figure-level processed sources

`data_processed/` provides a one-file input source for each manuscript figure that depends on restricted data.

- `figure2_source.xlsx`: weekly national and regional complaint aggregates
- `figure3_source.xlsx`: weekly national and regional precipitation aggregates
- `figure4_source.xlsx`: full-period weekly and flood-window daily hydro-social inputs
- `figure5_source.xlsx`: bootstrap forest-plot input table
- `figure6_source.xlsx`: region-event complaint and precipitation intensity with geometry WKT
- `figure7_source.xlsx`: region-event focal-emotion shifts with geometry WKT

These files are the highest-shareable analytical inputs used to support figure reproducibility without redistributing raw complaint text.
