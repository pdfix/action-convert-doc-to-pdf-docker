from pathlib import Path

CONFIG_FILE: str = "config.json"
DOCKER_NAMESPACE: str = "pdfix"
DOCKER_REPOSITORY: str = "convert-doc-to-pdf"
DOCKER_IMAGE: str = f"{DOCKER_NAMESPACE}/{DOCKER_REPOSITORY}"

LIBREOFFICE_EXECUTABLE_PATH: Path = Path("/usr/bin/soffice")

# PDF standard name -> LibreOffice "SelectPdfVersion" filter value.
# PDF/UA part follows PDF version: PDF 1.7 -> PDF/UA-1, PDF 2.0 -> PDF/UA-2.
PDF_STANDARD_UA1: str = "ua1"
PDF_STANDARD_UA2: str = "ua2"
PDF_STANDARD_UA1_A2B: str = "ua1-a2b"
PDF_STANDARD_UA2_A4: str = "ua2-a4"
PDF_STANDARDS: dict[str, int] = {
    PDF_STANDARD_UA1: 0,  # PDF 1.7 + PDF/UA-1
    PDF_STANDARD_UA2: 20,  # PDF 2.0 + PDF/UA-2
    PDF_STANDARD_UA1_A2B: 2,  # PDF/A-2b + PDF/UA-1
    PDF_STANDARD_UA2_A4: 4,  # PDF/A-4 + PDF/UA-2
}
DEFAULT_PDF_STANDARD: str = PDF_STANDARD_UA1
