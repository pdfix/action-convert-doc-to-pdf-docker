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
    # @KA:action pdfix_convert_doc_to_pdf_libreoffice
    # @KA:param standard
    # @KA:desc Standard of the output PDF. **PDF/UA-1** (default) gives the most reliable result.
    # **PDF/UA-2** creates PDF 2.0; LibreOffice support for it is new and some PDF/UA-2 rules may
    # still fail validation. The PDF/A variants also make the PDF suitable for archiving (PDF/A-2b
    # with PDF/UA-1, PDF/A-4 with PDF/UA-2).
    # @KA:problem The PDF/UA-2 output fails some PDF/UA-2 validation rules.
    # @KA:solution Convert with **PDF/UA-1** if PDF/UA-2 is not required, or fix the reported
    # problems in the PDF with PDFix actions.
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
    # @KA:param input_doc
    # @KA:desc Word document to convert. PDFix Desktop offers DOCX files. Only word processing
    # documents are supported; spreadsheets, presentations and PDFs are not. Password-protected
    # documents are not supported.
    # @KA:problem "Failed to find input document." (error 30)
    # @KA:solution The input file does not exist. Check the path.
    # @KA:problem "Failed to open input document." (error 32)
    # @KA:solution The document is damaged, password-protected or not a word processing document.
    # Open it in Word, remove the password or save it again as DOCX, and run the action again.
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
            # @KA:logic Conversion
            # @KA:desc LibreOffice opens the document and exports it as a tagged PDF with PDF/UA
            # compliance switched on. Tags come from the document: heading styles become headings,
            # lists, tables and images become list, table and figure tags, image alternative text
            # and hyperlink ScreenTips are kept, and the document title is used as the PDF title.
            # Problems in the document (no title, images without alternative text, text formatted to
            # look like headings without heading styles) stay in the PDF.
            # @KA:problem PDF/UA validation reports missing title, alternative text or link description.
            # @KA:solution Fix it in the Word document and convert again, or fix the PDF with PDFix
            # actions.
            #
            # @KA:logic Fonts
            # @KA:desc Microsoft fonts are not included. Calibri, Cambria, Arial, Times New Roman and
            # Courier New are replaced by fonts with the same character widths (Carlito, Caladea,
            # Liberation), so the page layout is kept but the font names in the PDF differ. Other
            # missing fonts are replaced by DejaVu fonts, which can change the layout.
            command: list[str] = build_command(input_path, output_directory, standard)
            result: subprocess.CompletedProcess[str] = subprocess.run(
                command, capture_output=True, text=True, check=False
            )
            logger.debug(f"Return code: {result.returncode}\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}")

            # @KA:logic Conversion failed
            # @KA:desc When LibreOffice cannot convert the document, the action stops and no PDF is
            # created. The log shows the LibreOffice output.
            # @KA:problem "Failed to convert document to PDF." (error 31)
            # @KA:solution Open the document in Word, save it again as DOCX and run the action again.
            # @KA:problem "Failed to save output PDF." (error 33)
            # @KA:solution The output file cannot be written, for example it is open in another
            # application or the folder is read-only. Close the file or select another output file.
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
