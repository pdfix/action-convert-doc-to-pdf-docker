import argparse
import logging
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

from constants import CONFIG_FILE, DEFAULT_PDF_STANDARD, PDF_STANDARDS
from doc_to_pdf import convert_to_pdf
from exceptions import (
    EC_ARG_GENERAL,
    MESSAGE_ARG_GENERAL,
    ArgumentOutputFolderNotExistsException,
    ArgumentOutputPdfException,
    ExpectedException,
)
from image_update import DockerImageContainerUpdateChecker
from logger import get_logger

logger: logging.Logger = get_logger("app_logger")


def set_arguments(
    parser: argparse.ArgumentParser,
    names: list[str],
    required_output: bool = True,
    output_help: str = "",
) -> None:
    """
    Set arguments for the parser based on the provided names and options.

    Args:
        parser (argparse.ArgumentParser): The argument parser to set arguments for.
        names (list[str]): List of argument names to set.
        required_output (bool): Whether the output argument is required. Defaults to True.
        output_help (str): Help shown for output argument. Defaults to "".
    """
    for name in names:
        match name:
            case "input":
                parser.add_argument(
                    "--input", "-i", type=str, required=True, help="The input document (DOC, DOCX, ODT, RTF, ...)"
                )
            case "output":
                parser.add_argument("--output", "-o", type=str, required=required_output, help=output_help)
            case "standard":
                parser.add_argument(
                    "--standard",
                    type=str,
                    choices=list(PDF_STANDARDS.keys()),
                    default=DEFAULT_PDF_STANDARD,
                    help=f"PDF standard of the output. Defaults to {DEFAULT_PDF_STANDARD}",
                )


def run_config_subcommand(args) -> None:
    get_pdfix_config(args.output)


def get_pdfix_config(path: str) -> None:
    """
    If Path is not provided, output content of config.
    If Path is provided, copy config to destination path.

    Args:
        path (string): Destination path for config.json file
    """
    config_path: Path = Path(__file__).parent.parent.joinpath(CONFIG_FILE).resolve()

    with open(config_path, "r", encoding="utf-8") as file:
        if path is None:
            print(file.read())
        else:
            with open(path, "w") as out:
                out.write(file.read())


def run_doc_to_pdf_subcommand(args) -> None:
    doc_to_pdf(args.input, args.output, args.standard)


# @KA:action pdfix_convert_doc_to_pdf_libreoffice
# @KA:desc Converts a Word document to an accessible PDF (PDF/UA) using LibreOffice. The PDF is
# tagged from the structure of the document: heading styles, lists, tables, images with alternative
# text, hyperlinks and the document title. The input file is not changed, the PDF is saved as the
# output file.
# @KA:context Run when you have the source Word document and need an accessible PDF from it.
# The result is only as accessible as the document: set the document title, use heading styles,
# add alternative text to images and a ScreenTip to hyperlinks before converting. Runs locally in
# Docker, nothing leaves your computer and no PDFix license is needed; the first run downloads the
# image and takes longer.
# @KA:param input_doc
# @KA:desc Word document to convert. PDFix Desktop offers DOCX files. Only word processing
# documents are supported; spreadsheets, presentations and PDFs are not. Password-protected
# documents are not supported.
# @KA:problem "Failed to find input document." (error 30)
# @KA:solution The input file does not exist. Check the path.
# @KA:problem "Failed to open input document." (error 32)
# @KA:solution The document is damaged, password-protected or not a word processing document.
# Open it in Word, remove the password or save it again as DOCX, and run the action again.
# @KA:param output_pdf
# @KA:desc Where the PDF is saved. It must have the `.pdf` extension and the folder must already
# exist; an existing file with the same name is overwritten.
# @KA:problem "Output file must be PDF document." (error 11)
# @KA:solution Use an output file name with the `.pdf` extension.
# @KA:problem "Output folder does not exist." (error 12)
# @KA:solution Create the folder shown in the message or select another output file.
# @KA:param standard
# @KA:desc Standard of the output PDF. **PDF/UA-1** (default) gives the most reliable result.
# **PDF/UA-2** creates PDF 2.0; LibreOffice support for it is new and some PDF/UA-2 rules may
# still fail validation. The PDF/A variants also make the PDF suitable for archiving (PDF/A-2b
# with PDF/UA-1, PDF/A-4 with PDF/UA-2).
# @KA:problem The PDF/UA-2 output fails some PDF/UA-2 validation rules.
# @KA:solution Convert with **PDF/UA-1** if PDF/UA-2 is not required, or fix the reported
# problems in the PDF with PDFix actions.
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
# @KA:logic Fonts
# @KA:desc Microsoft fonts are not included. Calibri, Cambria, Arial, Times New Roman and
# Courier New are replaced by fonts with the same character widths (Carlito, Caladea,
# Liberation), so the page layout is kept but the font names in the PDF differ. Other
# missing fonts are replaced by DejaVu fonts, which can change the layout.
# @KA:logic Conversion failed
# @KA:desc When LibreOffice cannot convert the document, the action stops and no PDF is
# created. The log shows the LibreOffice output.
# @KA:problem "Failed to convert document to PDF." (error 31)
# @KA:solution Open the document in Word, save it again as DOCX and run the action again.
# @KA:problem "Failed to save output PDF." (error 33)
# @KA:solution The output file cannot be written, for example it is open in another
# application or the folder is read-only. Close the file or select another output file.
def doc_to_pdf(input_path: str, output_path: str, standard: str) -> None:
    """
    Converts word processing document to PDF document.

    Args:
        input_path (str): Path to input document.
        output_path (str): Path to output PDF document.
        standard (str): PDF standard of the output.
    """
    if not output_path.lower().endswith(".pdf"):
        raise ArgumentOutputPdfException()

    output_folder: Path = Path(output_path).resolve().parent
    if not output_folder.is_dir():
        raise ArgumentOutputFolderNotExistsException(output_folder.as_posix())

    convert_to_pdf(input_path, output_path, standard)


def main() -> None:
    """Parse CLI arguments and run the selected subcommand."""
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(title="Commands", dest="command", required=True)

    # Config subcommand
    config_parser = subparsers.add_parser("config", help="Save the default configuration file")
    set_arguments(
        config_parser,
        ["output"],
        False,
        "Output to save the config JSON file. Application output is used if not provided",
    )
    config_parser.set_defaults(func=run_config_subcommand)

    # Doc to pdf subcommand
    doc_to_pdf_parser = subparsers.add_parser(
        "doc-to-pdf",
        help="Convert word processing document to PDF/UA document.",
    )
    set_arguments(doc_to_pdf_parser, ["input", "output", "standard"], True, "Output PDF file")
    doc_to_pdf_parser.set_defaults(func=run_doc_to_pdf_subcommand)

    # Parse arguments
    try:
        args = parser.parse_args()
    except ExpectedException as e:
        logger.error(e.message)
        sys.exit(e.error_code)
    except SystemExit as e:
        if e.code != 0:
            logger.error(MESSAGE_ARG_GENERAL)
            sys.exit(EC_ARG_GENERAL)
        # This happens when --help is used, exit gracefully
        sys.exit(0)
    except Exception as e:
        logger.error("Failed to run the program:")
        logger.exception(e)
        sys.exit(1)

    if hasattr(args, "func"):
        # Check for updates only when help is not checked
        update_checker = DockerImageContainerUpdateChecker()
        # Check it in separate thread not to be delayed when there is slow or no internet connection
        update_thread = threading.Thread(target=update_checker.check_for_image_updates)
        update_thread.start()

        # Measure the time it takes to make all requests
        start_time = time.time()  # Record the start time
        current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logger.info(f"Processing started at: {current_time}")

        # Run subcommand
        try:
            args.func(args)
        except ExpectedException as e:
            logger.error(e.message)
            sys.exit(e.error_code)
        except Exception as e:
            # not expected exception -> print stack trace and what exception happened
            logger.error("Failed to run the program:")
            logger.exception(e)
            sys.exit(1)
        finally:
            end_time = time.time()  # Record the end time
            elapsed_time = end_time - start_time  # Calculate the elapsed time
            current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            logger.info(f"Processing finished at: {current_time}. Elapsed time: {elapsed_time:.2f} seconds")

            # Make sure to let update thread finish before exiting
            update_thread.join()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
