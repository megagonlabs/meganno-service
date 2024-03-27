from app.constants import MAX_QUERY_LIMIT, VALID_SCHEMA_LEVELS
from app.enums.import_type import ImportType
from app.enums.search_mode import VerificationSearchMode, VerificationTypeSearchMode


class BaseValidation:
    string = {"type": "string"}
    integer = {"type": "integer"}
    boolean = {"type": "boolean"}
    object_or_none = {"type": ["object", "null"]}
    array_or_none = {"type": ["array", "null"]}
    string_or_none = {"type": ["string", "null"]}
    boolean_or_none = {"type": ["boolean", "null"]}

    uuid = {"type": "string", "length": 36}
    uuid_list = {"type": "array", "items": uuid}

    limit = {"type": "integer", "maximum": MAX_QUERY_LIMIT, "minimum": 1}
    skip = {"type": "integer", "minimum": 0}
    label_level = {"type": "string", "enum": VALID_SCHEMA_LEVELS}

    label_metadata_list = {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "metadata_name": {"type": "string"},
                "metadata_value": {"type": ["string", "number"]},
            },
        },
    }

    label = {
        "type": "object",
        "properties": {
            "label_level": label_level,
            "label_value": {"type": "array", "items": {"type": "string"}},
            "label_name": string,
            "start_idx": {"type": "integer", "minimum": 0},
            "end_idx": {"type": "integer", "minimum": 0},
            "metadata_list": label_metadata_list,
            "annotator": string_or_none,
        },
        "required": ["label_level", "label_name", "label_value"],
    }

    verified_status = {
        "type": "string",
        "enum": [e.value for e in VerificationSearchMode],
    }
    verified_type = {
        "type": ["string", "null"],
        "enum": [e.value for e in VerificationTypeSearchMode] + [None],
    }

    file_type = {"type": ["string"], "enum": [e.value for e in ImportType]}
    column_mapping = {
        "type": "object",
        "properties": {"id": {"type": "string"}, "content": {"type": "string"}},
        "required": ["id", "content"],
        "additionalProperties": True,
    }

    label_uuid = uuid

    filter_by = {
        **string_or_none,
        "enum": ["agent_uuid", "issued_by", "uuid"],
    }

    model_config = {"type": "object"}

    operator = {
        "type": "string",
        "enum": ["==", ">=", "<=", "<", ">", "exists"],
    }

    label_operator = {
        "type": "string",
        "enum": ["==", "exists", "conflicts"],
    }
