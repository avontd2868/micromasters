"""
Exceptions for exams
"""


class InvalidTsvRow(Exception):
    """
    A row for a tsv is invalid
    """


class InvalidProfileDataException(InvalidTsvRow):
    """
    Profile contains invalid data to sync
    """
