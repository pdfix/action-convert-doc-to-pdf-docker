import json
import logging
import shutil
import subprocess
import tempfile
from pathlib import Path

from tqdm import tqdm

from constants import LIBREOFFICE_EXECUTABLE_PATH, PDF_STANDARDS
from exceptions import (
    FailedToConvertException,
    FailedToFindInputException,
    FailedToLoadInputException,
    FailedToSaveOutputException,
)
from logger import get_logger

logger: logging.Logger = get_logger(__name__)


def build_filter_options(standard: str) -> str:
    """
    Builds LibreOffice PDF export filter options in JSON form.

    PDF/UA compliance also forces tagged PDF. The PDF/UA part follows the PDF version
    (PDF 1.7 -> PDF/UA-1, PDF 2.0 -> PDF/UA-2).

    Args:
        standard (str): One of the keys of PDF_STANDARDS.

    Returns:
        JSON string used after "pdf:writer_pdf_Export:" in "--convert-to".
    """
    options: dict[str, dict[str, str]] = {
        "PDFUACompliance": {"type": "boolean", "value": "true"},
        "UseTaggedPDF": {"type": "boolean", "value": "true"},
        "SelectPdfVersion": {"type": "long", "value": f"{PDF_STANDARDS[standard]}"},
    }
    return json.dumps(options, separators=(",", ":"))


def build_command(input_path: Path, output_directory: Path, standard: str) -> list[str]:
    """
    Builds headless LibreOffice command line that converts one document to PDF.

    Args:
        input_path (Path): Document to convert.
        output_directory (Path): Directory where LibreOffice writes "<input stem>.pdf".
        standard (str): One of the keys of PDF_STANDARDS.

    Returns:
        Command line arguments.
    """
    return [
        LIBREOFFICE_EXECUTABLE_PATH.as_posix(),
        "--headless",
        "--convert-to",
        # Export filter options can be passed only together with the export filter name
        f"pdf:writer_pdf_Export:{build_filter_options(standard)}",
        "--outdir",
        output_directory.as_posix(),
        input_path.as_posix(),
    ]


def convert_to_pdf(input: str, output: str, standard: str) -> None:
    """
    Converts a word processing document (DOC, DOCX, ODT, RTF, ...) to PDF/UA using LibreOffice.

    Args:
        input (str): Path to the input document.
        output (str): Path to the output PDF document.
        standard (str): One of the keys of PDF_STANDARDS.

    Raises:
        FailedToFindInputException: If the input document does not exist.
        FailedToLoadInputException: If LibreOffice cannot open the input document.
        FailedToConvertException: If LibreOffice fails for another reason.
        FailedToSaveOutputException: If the PDF cannot be saved to the output path.
    """
    input_path: Path = Path(input).resolve()
    if not input_path.is_file():
        logger.error(f"Input document '{input_path.as_posix()}' was not found.")
        raise FailedToFindInputException()

    output_path: Path = Path(output).resolve()

    with tqdm(total=100) as progress_bar:
        progress_bar.set_description("Converting")
        progress_bar.refresh()

        # LibreOffice names the output after the input, so it is written into own directory first
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_directory: Path = Path(temporary_directory)
            command: list[str] = build_command(input_path, output_directory, standard)
            result: subprocess.CompletedProcess[str] = subprocess.run(
                command, capture_output=True, text=True, check=False
            )
            logger.debug(f"Return code: {result.returncode}\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}")

            if result.returncode != 0:
                # Printed by LibreOffice for damaged, password protected or unsupported documents
                if "source file could not be loaded" in result.stderr:
                    raise FailedToLoadInputException()
                logger.error(f"LibreOffice failed with return code {result.returncode}: {result.stderr}")
                raise FailedToConvertException()

            converted_path: Path = output_directory.joinpath(f"{input_path.stem}.pdf")
            if not converted_path.is_file():
                logger.error(f"LibreOffice finished without creating PDF: {result.stdout}\n{result.stderr}")
                raise FailedToConvertException()

            try:
                shutil.move(converted_path, output_path)
            except OSError as e:
                logger.error(f"{e}")
                raise FailedToSaveOutputException()

        progress_bar.n = 100
        progress_bar.set_description("Done")
        progress_bar.refresh()
