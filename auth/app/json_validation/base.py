class BaseValidation:
    string = {"type": "string"}
    integer = {"type": "integer"}
    boolean = {"type": "boolean"}
    string_or_none = {"type": ["string", "null"]}
    boolean_or_none = {"type": ["boolean", "null"]}
