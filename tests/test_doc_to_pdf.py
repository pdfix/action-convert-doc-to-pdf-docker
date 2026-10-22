import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

sys.path.insert(0, Path(__file__).resolve().parent.parent.joinpath("src").as_posix())

import doc_to_pdf  # noqa: E402
from constants import LIBREOFFICE_EXECUTABLE_PATH, PDF_STANDARDS  # noqa: E402
from exceptions import (  # noqa: E402
    EC_FAILED_TO_FIND_INPUT,
    EC_FAILED_TO_SAVE_OUTPUT,
    EC_LIBREOFFICE_FAILED_TO_CONVERT,
    EC_LIBREOFFICE_FAILED_TO_LOAD_INPUT,
    ExpectedException,
)

# Real LibreOffice 26.8 output for a damaged, password protected or unsupported document
LOAD_ERROR_STDERR: str = "Error: source file could not be loaded\n"


def finished_process(returncode: int, stderr: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args=[], returncode=returncode, stdout="", stderr=stderr)


def fake_libreoffice(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
    # Behaves like LibreOffice: writes "<input stem>.pdf" into --outdir
    output_directory: Path = Path(command[command.index("--outdir") + 1])
    output_directory.joinpath(f"{Path(command[-1]).stem}.pdf").write_bytes(b"%PDF-1.7")
    return finished_process(0)


class TestBuildFilterOptions(unittest.TestCase):
    def test_every_standard_enables_pdfua_and_tagging(self) -> None:
        for standard in PDF_STANDARDS:
            options: Any = json.loads(doc_to_pdf.build_filter_options(standard))
            self.assertEqual(options["PDFUACompliance"], {"type": "boolean", "value": "true"})
            self.assertEqual(options["UseTaggedPDF"], {"type": "boolean", "value": "true"})

    def test_standard_selects_libreoffice_pdf_version(self) -> None:
        expected: dict[str, str] = {"ua1": "0", "ua2": "20", "ua1-a2b": "2", "ua2-a4": "4"}
        for standard, version in expected.items():
            options: Any = json.loads(doc_to_pdf.build_filter_options(standard))
            self.assertEqual(options["SelectPdfVersion"], {"type": "long", "value": version})


class TestBuildCommand(unittest.TestCase):
    def test_command_is_headless_pdf_conversion(self) -> None:
        command: list[str] = doc_to_pdf.build_command(Path("/data/in.docx"), Path("/tmp/out"), "ua2")
        self.assertEqual(command[0], LIBREOFFICE_EXECUTABLE_PATH.as_posix())
        self.assertIn("--headless", command)
        convert_to: str = command[command.index("--convert-to") + 1]
        self.assertEqual(convert_to, f"pdf:writer_pdf_Export:{doc_to_pdf.build_filter_options('ua2')}")
        self.assertEqual(command[command.index("--outdir") + 1], "/tmp/out")
        self.assertEqual(command[-1], "/data/in.docx")


class TestConvertToPdf(unittest.TestCase):
    def setUp(self) -> None:
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        self.directory: Path = Path(temporary_directory.name)
        self.input_path: Path = self.directory.joinpath("report.docx")
        self.input_path.write_bytes(b"document")
        self.output_path: Path = self.directory.joinpath("converted.pdf")

    def convert(self, output_path: Path) -> None:
        doc_to_pdf.convert_to_pdf(self.input_path.as_posix(), output_path.as_posix(), "ua1")

    def assert_error_code(self, error_code: int, output_path: Path) -> None:
        with self.assertRaises(ExpectedException) as context:
            self.convert(output_path)
        self.assertEqual(context.exception.error_code, error_code)
        self.assertFalse(output_path.exists())

    def test_output_is_saved_to_requested_path(self) -> None:
        with mock.patch("doc_to_pdf.subprocess.run", side_effect=fake_libreoffice):
            self.convert(self.output_path)
        self.assertEqual(self.output_path.read_bytes(), b"%PDF-1.7")

    def test_missing_input(self) -> None:
        self.input_path.unlink()
        self.assert_error_code(EC_FAILED_TO_FIND_INPUT, self.output_path)

    def test_document_that_cannot_be_loaded(self) -> None:
        with mock.patch("doc_to_pdf.subprocess.run", return_value=finished_process(1, LOAD_ERROR_STDERR)):
            self.assert_error_code(EC_LIBREOFFICE_FAILED_TO_LOAD_INPUT, self.output_path)

    def test_other_libreoffice_failure(self) -> None:
        with mock.patch("doc_to_pdf.subprocess.run", return_value=finished_process(1, "Error: unexpected\n")):
            self.assert_error_code(EC_LIBREOFFICE_FAILED_TO_CONVERT, self.output_path)

    def test_success_exit_code_without_output(self) -> None:
        with mock.patch("doc_to_pdf.subprocess.run", return_value=finished_process(0)):
            self.assert_error_code(EC_LIBREOFFICE_FAILED_TO_CONVERT, self.output_path)

    def test_output_directory_is_not_created(self) -> None:
        output_path: Path = self.directory.joinpath("missing", "converted.pdf")
        with mock.patch("doc_to_pdf.subprocess.run", side_effect=fake_libreoffice):
            self.assert_error_code(EC_FAILED_TO_SAVE_OUTPUT, output_path)
        self.assertFalse(output_path.parent.exists())


if __name__ == "__main__":
    unittest.main()
