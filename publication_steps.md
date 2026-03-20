# GitHub and Zenodo Publication Steps

## 1. Create the GitHub repository

Recommended repository name:

`sociohydro-flood-complaints`

Upload the contents of:

`/Volumes/Keywest_JetDrive 1/Codex/Academia/Complaint/release_package/`

or upload the archive:

`/Volumes/Keywest_JetDrive 1/Codex/Academia/Complaint/sociohydro_flood_complaints_release_v1.zip`

## 2. Verify the public GitHub URL

Expected URL format:

`https://github.com/<account>/sociohydro-flood-complaints`

Confirm that the following files are visible:

- `README.md`
- `LICENSE`
- `CITATION.cff`
- `.zenodo.json`
- `code/`
- `data/`
- `tables/`
- `figures/`

## 3. Connect the repository to Zenodo

1. Sign in to Zenodo.
2. Enable the GitHub repository in the Zenodo GitHub integration.
3. Create a GitHub release, or upload the release package directly if using Zenodo without GitHub sync.
4. Record the minted DOI.

## 4. Update the manuscript Open Research section

Replace the temporary text in the manuscript with:

### Data Availability Statement

The raw civil complaint data were obtained under a Memorandum of Understanding (MOU) with the Anti-Corruption and Civil Rights Commission (ACRC) of South Korea and cannot be shared publicly because of legal and privacy restrictions under the Personal Information Protection Act. Publicly shareable, de-identified aggregated datasets supporting the analyses and figures are archived at Zenodo: [DOI]. Precipitation data are publicly available from the Korea Meteorological Administration (https://data.kma.go.kr). Internet search trend data were obtained from Naver DataLab (https://datalab.naver.com) and Google Trends (https://trends.google.com). News keyword data were obtained from BigKinds (https://www.bigkinds.or.kr).

### Code Availability Statement

All code required to reproduce the analytical workflow, figures, and summary tables is archived at Zenodo: [DOI] and mirrored on GitHub: [URL]. The repository includes the full analysis pipeline, figure-generation scripts, and documentation for reproducing the shared aggregated outputs.

## 5. Update the references

Add the final software/data citation for the archived repository release once Zenodo issues the DOI.
