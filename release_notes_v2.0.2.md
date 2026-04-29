# v2.0.2 — Reproducibility package refresh and authorship update

This release provides the refreshed public reproducibility package for the manuscript:

*Event-dependent coupling between extreme rainfall and institutionalized civic response: Evidence from administrative complaints in South Korea*

Zenodo DOI: pending new version publication

## What is new in v2.0.2

- Refreshed the active manuscript figure pipeline so that Figures 1-7 regenerate from the current code path without stale workspace-path dependencies
- Rebuilt `data_processed/` to align the figure-level processed sources with the current manuscript figures
- Updated Figure 7 processed inputs to the manuscript-aligned focal emotions:
  - `Suspicion/Mistrust`
  - `Anger/Rage`
  - `Sadness`
- Removed lossy geometry text export from the Figure 6-7 processed workbooks; geometry is now loaded from the documented province boundary shapefile
- Added reproducibility validation documentation for the manuscript figure pipeline
- Updated repository and package metadata to reflect the current authorship configuration

## Figure-level processed inputs

The following files are included so that each manuscript figure can be regenerated from a single processed input source, without redistributing restricted raw complaint text:

- `data_processed/figure2_source.xlsx`
- `data_processed/figure3_source.xlsx`
- `data_processed/figure4_source.xlsx`
- `data_processed/figure5_source.xlsx`
- `data_processed/figure6_source.xlsx`
- `data_processed/figure7_source.xlsx`

## Access and scope

- Public archive target: Zenodo
- Development mirror: GitHub
- License: MIT
- Raw complaint texts are excluded because they are legally restricted under the ACRC data-use agreement and privacy law
- Reproducibility is provided at the highest shareable analytical level through de-identified aggregates, figure-specific processed inputs, a minimal reproducible subset, synthetic smoke-test inputs, and figure-generation code
