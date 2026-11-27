EC_ARG_GENERAL: int = 10
EC_ARG_OUTPUT_PDF: int = 11
EC_ARG_OUTPUT_FOLDER_NOT_EXISTS: int = 12
EC_ARG_INPUT_NOT_EXISTS: int = 13

EC_LIBREOFFICE_FAILED_TO_CONVERT: int = 30
EC_LIBREOFFICE_FAILED_TO_LOAD_INPUT: int = 31
EC_FAILED_TO_SAVE_OUTPUT: int = 32

MESSAGE_ARG_GENERAL: str = "Failed to parse arguments. Please check the usage and try again."
MESSAGE_ARG_OUTPUT_PDF: str = "Output file must be PDF document."
MESSAGE_ARG_OUTPUT_FOLDER_NOT_EXISTS: str = "Output folder does not exist."
MESSAGE_ARG_INPUT_NOT_EXISTS: str = "Input file does not exist."

MESSAGE_LIBREOFFICE_FAILED_TO_CONVERT: str = "Failed to convert document to PDF."
MESSAGE_LIBREOFFICE_FAILED_TO_LOAD_INPUT: str = (
    "Failed to open input document. The document is damaged, password protected or in unsupported format."
)
MESSAGE_FAILED_TO_SAVE_OUTPUT: str = "Failed to save PDF document."


class ExpectedException(BaseException):
    """
    Base exception for expected failures surfaced to the user.

    Carries an application error code and a user-facing message printed to stderr.
    """

    def __init__(self, error_code: int) -> None:
        """
        Args:
            error_code (int): Exit code returned to the caller.
        """
        self.error_code: int = error_code
        self.message: str = ""

    def _add_note(self, note: str) -> None:
        """
        Set the user-facing error message.

        Args:
            note (str): Message shown to the user.
        """
        self.message = note


class ArgGeneralException(ExpectedException):
    """Raised when command-line arguments cannot be parsed."""

    def __init__(self) -> None:
        """Initialize with the argument parsing error code and message."""
        super().__init__(EC_ARG_GENERAL)
        self._add_note(MESSAGE_ARG_GENERAL)


class ArgumentOutputPdfException(ExpectedException):
    """Raised when the output file is not a PDF document."""

    def __init__(self) -> None:
        """Initialize with the output extension error code and message."""
        super().__init__(EC_ARG_OUTPUT_PDF)
        self._add_note(MESSAGE_ARG_OUTPUT_PDF)


class ArgumentOutputFolderNotExistsException(ExpectedException):
    """Raised when the folder of the output file does not exist."""

    def __init__(self, path: str) -> None:
        """
        Args:
            path (str): Missing output folder.
        """
        super().__init__(EC_ARG_OUTPUT_FOLDER_NOT_EXISTS)
        self._add_note(f"{MESSAGE_ARG_OUTPUT_FOLDER_NOT_EXISTS} {path}")


class ArgumentInputNotExistsException(ExpectedException):
    """Raised when the input document does not exist."""

    def __init__(self, path: str) -> None:
        """
        Args:
            path (str): Missing input document.
        """
        super().__init__(EC_ARG_INPUT_NOT_EXISTS)
        self._add_note(f"{MESSAGE_ARG_INPUT_NOT_EXISTS} {path}")


class FailedToConvertException(ExpectedException):
    """Raised when LibreOffice fails for a reason not covered by other exceptions."""

    def __init__(self) -> None:
        """Initialize with the conversion error code and message."""
        super().__init__(EC_LIBREOFFICE_FAILED_TO_CONVERT)
        self._add_note(MESSAGE_LIBREOFFICE_FAILED_TO_CONVERT)


class FailedToLoadInputException(ExpectedException):
    """Raised when LibreOffice cannot open the input document."""

    def __init__(self) -> None:
        """Initialize with the load error code and message."""
        super().__init__(EC_LIBREOFFICE_FAILED_TO_LOAD_INPUT)
        self._add_note(MESSAGE_LIBREOFFICE_FAILED_TO_LOAD_INPUT)


class FailedToSaveOutputException(ExpectedException):
    """Raised when the converted PDF cannot be saved to the output path."""

    def __init__(self) -> None:
        """Initialize with the save error code and message."""
        super().__init__(EC_FAILED_TO_SAVE_OUTPUT)
        self._add_note(MESSAGE_FAILED_TO_SAVE_OUTPUT)
