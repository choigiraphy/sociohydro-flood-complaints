from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED


OLD_DOI = "10.5281/zenodo.19176560"
NEW_DOI = "10.5281/zenodo.19176504"

SRC = Path("/Volumes/Keywest_JetDrive 1/학교/2026-1/AGU_WRR_Choi/최신_AGU_Manuscript_Choi_수정중_Level2_20260320_v39.docx")
DST = Path("/Volumes/Keywest_JetDrive 1/학교/2026-1/AGU_WRR_Choi/최신_AGU_Manuscript_Choi_수정중_Level2_20260320_v40.docx")


def main() -> None:
    with ZipFile(SRC, "r") as zin, ZipFile(DST, "w", compression=ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "word/document.xml":
                text = data.decode("utf-8")
                if OLD_DOI not in text:
                    raise RuntimeError(f"Old DOI not found in {item.filename}")
                text = text.replace(OLD_DOI, NEW_DOI)
                data = text.encode("utf-8")
            zout.writestr(item, data)
    print(DST)


if __name__ == "__main__":
    main()
