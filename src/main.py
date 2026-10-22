import argparse
import sys
import threading
import traceback
from pathlib import Path

from constants import CONFIG_FILE, DEFAULT_PDF_STANDARD, PDF_STANDARDS
from doc_to_pdf import convert_to_pdf
from exceptions import EC_ARG_GENERAL, MESSAGE_ARG_GENERAL, ExpectedException
from image_update import DockerImageContainerUpdateChecker


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


def doc_to_pdf(input_path: str, output_path: str, standard: str) -> None:
    """
    Converts word processing document to PDF document.

    Args:
        input_path (str): Path to input document.
        output_path (str): Path to output PDF document.
        standard (str): PDF standard of the output.
    """
    convert_to_pdf(input_path, output_path, standard)


def main() -> None:
    """Parse CLI arguments and run the selected subcommand."""
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(dest="subparser")

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
        print(e.message, file=sys.stderr)
        sys.exit(e.error_code)
    except SystemExit as e:
        if e.code != 0:
            print(MESSAGE_ARG_GENERAL, file=sys.stderr)
            sys.exit(EC_ARG_GENERAL)
        # This happens when --help is used, exit gracefully
        sys.exit(0)
    except Exception as e:
        print(traceback.format_exc(), file=sys.stderr)
        print(f"Failed to run the program: {e}", file=sys.stderr)
        sys.exit(1)

    if hasattr(args, "func"):
        # Check for updates only when help is not checked
        update_checker = DockerImageContainerUpdateChecker()
        # Check it in separate thread not to be delayed when there is slow or no internet connection
        update_thread = threading.Thread(target=update_checker.check_for_image_updates)
        update_thread.start()

        # Run subcommand
        try:
            args.func(args)
        except ExpectedException as e:
            print(e.message, file=sys.stderr)
            sys.exit(e.error_code)
        except Exception as e:
            print(traceback.format_exc(), file=sys.stderr)
            print(f"Failed to run the program: {e}", file=sys.stderr)
            sys.exit(1)
        finally:
            # Make sure to let update thread finish before exiting
            update_thread.join()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
