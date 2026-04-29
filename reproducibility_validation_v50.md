# Reproducibility validation for v50

## Scope
- Manuscript author/acknowledgement update in `v50.docx`
- Active manuscript figure-rendering pipeline (`Figure1_WRR` to `Figure7_WRR`)
- Processed figure sources in `data_processed/`
- Synced `release_package/code/` and `release_package/data_processed/` to the active figure pipeline

## What was changed
- Updated manuscript author line to `G. Choi, K. Kim, and J. Kam` and moved Young Bae / Hoon Cheol Shin to acknowledgements.
- Replaced stale `Keywest_JetDrive 1` hardcoded defaults in the active figure pipeline with current-path-first resolution and repo-relative output/style paths.
- Refreshed `data_processed/figure2_source.xlsx` to `figure7_source.xlsx`, `README.md`, and `figure_processed_sources_manifest.json`.
- Rebuilt `figure7_source.xlsx` from the manuscript-aligned regional delta workbook so that Figure 7 now reproduces `Suspicion/Mistrust`, `Anger/Rage`, and `Sadness` from a repo-local processed source.
- Removed lossy `geometry_wkt` export from Figure 6-7 processed sources; geometry is loaded from the documented national province boundary shapefile.
- Synced the refreshed figure pipeline and processed source directory into `release_package/`.

## Verification results
- `python3 code/build_processed_figure_sources.py` completed successfully.
- `python3 code/render_all_wrr_figures.py` completed successfully and regenerated Figures 1-7.
- The regenerated local figure files match the embedded manuscript figures in `v50.docx` for `image1.png` through `image7.png`.
- `v50.pdf` was re-exported from Microsoft Word after the manuscript and figure refresh.

## Validation scope note
- This validation covers the active manuscript figure pipeline and the processed-source package used to regenerate Figures 1-7.
- Legacy/archive scripts outside that active path were not fully normalized in this pass.
