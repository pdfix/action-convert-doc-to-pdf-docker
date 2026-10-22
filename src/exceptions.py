EC_ARG_GENERAL: int = 10

EC_FAILED_TO_FIND_INPUT: int = 30
EC_LIBREOFFICE_FAILED_TO_CONVERT: int = 31
EC_LIBREOFFICE_FAILED_TO_LOAD_INPUT: int = 32
EC_FAILED_TO_SAVE_OUTPUT: int = 33

MESSAGE_ARG_GENERAL: str = "Failed to parse arguments. Please check the usage and try again."

MESSAGE_FAILED_TO_FIND_INPUT: str = "Failed to find input document."
MESSAGE_LIBREOFFICE_FAILED_TO_CONVERT: str = "Failed to convert document to PDF."
MESSAGE_LIBREOFFICE_FAILED_TO_LOAD_INPUT: str = (
    "Failed to open input document. The document is damaged, password protected or in unsupported format."
)
MESSAGE_FAILED_TO_SAVE_OUTPUT: str = "Failed to save output PDF. Make sure the output directory exists and is writable."


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


class FailedToFindInputException(ExpectedException):
    """Raised when the input document does not exist."""

    def __init__(self) -> None:
        """Initialize with the missing input error code and message."""
        super().__init__(EC_FAILED_TO_FIND_INPUT)
        self._add_note(MESSAGE_FAILED_TO_FIND_INPUT)


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
