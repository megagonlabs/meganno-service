from app.constants import VALID_SCHEMA_LEVELS


class SchemaValidation:
    label_schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "level": {"type": "string", "enum": VALID_SCHEMA_LEVELS},
            "options": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string"},
                        "value": {"type": ["integer", "string"]},
                    },
                    "required": ["text", "value"],
                    "additionalProperties": False,
                },
                "minItems": 1,
            },
        },
        "required": ["name", "level", "options"],
        "additionalProperties": False,
    }
    task_schema = {
        "type": "object",
        "properties": {"label_schema": {"type": "array", "items": label_schema}},
        "additionalProperties": False,
        "required": ["label_schema"],
    }
