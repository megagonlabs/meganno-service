from enum import Enum


class SearchMode(Enum):
    KEYWORD = "KEYWORD"
    REGEX = "REGEX"


class VerificationSearchMode(Enum):
    ALL = "ALL"
    VERIFIED = "VERIFIED"
    UNVERIFIED = "UNVERIFIED"


class VerificationTypeSearchMode(Enum):
    CONFIRMS = "CONFIRMS"
    CORRECTS = "CORRECTS"
    ALL = "ALL"
