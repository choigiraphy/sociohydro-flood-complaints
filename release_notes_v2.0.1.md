# v2.0.1 — Processed Figure Sources and Restricted Reproducibility Package

This release provides the updated public reproducibility package for the manuscript:

*Event-dependent coupling between extreme rainfall and institutionalized civic response: Evidence from administrative complaints in South Korea*

Zenodo version DOI: [10.5281/zenodo.19176504](https://doi.org/10.5281/zenodo.19176504)

## What is new in v2.0.1

- Added `data_processed/` with figure-level processed source files for manuscript Figures 2-7
- Added a de-identified minimal reproducible subset:
  - `data/public/minimal_reproducible_subset.csv`
- Added a schema-compatible synthetic smoke-test dataset:
  - `data/synthetic/synthetic_complaint_pipeline_input.csv`
- Added official event-month population data for population-normalized regional analyses:
  - `data/region_population_event_months.csv`
- Added supplemental validation outputs:
  - `tables/supplement/Table_S6_emotion_validation_summary.xlsx`
  - `tables/supplement/Table_S8_spatial_robustness.xlsx`
- Added figure/source packaging utilities and validation scripts in `code/`

## Figure-level processed inputs

The following files are included so that each manuscript figure can be regenerated from a single processed input source, without redistributing restricted raw complaint text:

- `data_processed/figure2_source.xlsx`
- `data_processed/figure3_source.xlsx`
- `data_processed/figure4_source.xlsx`
- `data_processed/figure5_source.xlsx`
- `data_processed/figure6_source.xlsx`
- `data_processed/figure7_source.xlsx`

See:

- `data_processed/README.md`
- `data_processed/figure_processed_sources_manifest.json`

## What is included

- Code used for the public analytical workflow
- De-identified aggregated daily and weekly datasets
- Figure-level processed source files
- Public minimal reproducible subset
- Synthetic smoke-test input
- Supporting tables and manuscript-ready figure exports
- Environment and metadata files for archive submission

## What is not included

- Raw civil complaint texts
- Complaint-level restricted spreadsheets
- Any source records governed by the ACRC data-use agreement

These records are excluded because they contain protected personal or administrative information and cannot be publicly redistributed.

## Reproducibility scope

This release supports reproducibility at the highest shareable analytical level. The package includes the code, processed inputs, aggregated outputs, and figure-specific source files needed to verify the published figures and supporting analyses without exposing restricted raw complaint text.

## Archive file

If you need the packaged archive for Zenodo upload, use:

- `sociohydro_flood_complaints_release_v2.zip`
