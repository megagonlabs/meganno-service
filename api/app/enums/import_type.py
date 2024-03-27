from enum import Enum


class ImportType(Enum):
    CSV = "CSV"
    DF = "DF"

    @classmethod
    def has(cls, value):
        return value in cls._value2member_map_
