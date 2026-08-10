"""Exit codes and exceptions (see docs/spec/01-overview.md, docs/spec/04-cli.md).

`04-cli.md` is the authoritative source for these codes; keep this table in
sync with it.
"""

EXIT_SUCCESS = 0

EXIT_ARG_VALIDATION = 1
EXIT_NOT_GIT_REPO = 2
EXIT_GIT_FAILURE = 3
EXIT_FS_ERROR = 4
EXIT_INVALID_PATTERN = 5
EXIT_UNKNOWN_COMMAND = 6
EXIT_LOCAL_MODIFICATIONS = 7
EXIT_UNEXPECTED_FILTER_OPTION = 8

EXIT_COMPONENT_ALREADY_PRESENT = 11
EXIT_COMPONENT_NOT_FOUND = 12
EXIT_IMPORT_CONFLICT = 13

EXIT_MANIFEST_LOCK_DISAGREE = 15
EXIT_MANIFEST_ALREADY_EXISTS = 16
EXIT_MANIFEST_MISSING = 17
EXIT_MANIFEST_INVALID = 18
EXIT_MANIFEST_UNEDITABLE = 19
EXIT_MANIFEST_UNCREATABLE = 20

EXIT_LOCK_MISSING_OR_INVALID = 21
EXIT_LOCK_UNREADABLE = 22


class GitComponentError(Exception):
    """Base error, carrying the exit code it shall map to."""

    def __init__(self, message: str, exit_code: int):
        super().__init__(message)
        self.exit_code = exit_code


class ArgumentError(GitComponentError):
    def __init__(self, message: str):
        super().__init__(message, EXIT_ARG_VALIDATION)


class NotAGitRepoError(GitComponentError):
    def __init__(self, message: str = "not inside a git repository"):
        super().__init__(message, EXIT_NOT_GIT_REPO)


class GitFailureError(GitComponentError):
    def __init__(self, message: str):
        super().__init__(message, EXIT_GIT_FAILURE)


class FilesystemError(GitComponentError):
    def __init__(self, message: str):
        super().__init__(message, EXIT_FS_ERROR)


class InvalidPatternError(GitComponentError):
    def __init__(self, message: str):
        super().__init__(message, EXIT_INVALID_PATTERN)


class UnknownCommandError(GitComponentError):
    def __init__(self, message: str):
        super().__init__(message, EXIT_UNKNOWN_COMMAND)


class LocalModificationsError(GitComponentError):
    def __init__(self, message: str):
        super().__init__(message, EXIT_LOCAL_MODIFICATIONS)


class UnexpectedFilterOptionError(GitComponentError):
    def __init__(self, message: str):
        super().__init__(message, EXIT_UNEXPECTED_FILTER_OPTION)


class ComponentAlreadyPresentError(GitComponentError):
    def __init__(self, message: str):
        super().__init__(message, EXIT_COMPONENT_ALREADY_PRESENT)


class ComponentNotFoundError(GitComponentError):
    def __init__(self, message: str):
        super().__init__(message, EXIT_COMPONENT_NOT_FOUND)


class ManifestLockDisagreeError(GitComponentError):
    def __init__(self, message: str):
        super().__init__(message, EXIT_MANIFEST_LOCK_DISAGREE)


class ManifestAlreadyExistsError(GitComponentError):
    def __init__(self, message: str):
        super().__init__(message, EXIT_MANIFEST_ALREADY_EXISTS)


class ManifestMissingError(GitComponentError):
    def __init__(self, message: str = "the manifest does not exist or is not initialized"):
        super().__init__(message, EXIT_MANIFEST_MISSING)


class ManifestInvalidError(GitComponentError):
    def __init__(self, message: str):
        super().__init__(message, EXIT_MANIFEST_INVALID)


class ManifestUneditableError(GitComponentError):
    def __init__(self, message: str):
        super().__init__(message, EXIT_MANIFEST_UNEDITABLE)


class ManifestUncreatableError(GitComponentError):
    def __init__(self, message: str):
        super().__init__(message, EXIT_MANIFEST_UNCREATABLE)


class LockMissingOrInvalidError(GitComponentError):
    def __init__(self, message: str):
        super().__init__(message, EXIT_LOCK_MISSING_OR_INVALID)


class LockUnreadableError(GitComponentError):
    def __init__(self, message: str):
        super().__init__(message, EXIT_LOCK_UNREADABLE)
