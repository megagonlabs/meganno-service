class AuthenticationValidation:
    id_list = {"type": "array", "items": {"type": "string"}, "minLength": 1}
    expiration_duration = {"type": "integer", "minimum": 0}
