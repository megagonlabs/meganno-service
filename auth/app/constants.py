import pydash
from jsonschema import Draft7Validator


class bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


class InvalidRequestJson(Exception):
    status_code = 422

    def __init__(self, errors, status_code=None):
        super().__init__()
        self.errors = errors
        if status_code is not None:
            self.status_code = status_code


def d7validate(validations, payload):
    errors = {}
    for error in sorted(
        Draft7Validator(
            {"type": "object", "additionalProperties": False, **validations}
        ).iter_errors(payload),
        key=str,
    ):
        abs_path = list(error.absolute_path)
        if len(abs_path) == 0:
            abs_path = [""]
        messages = pydash.objects.get(errors, abs_path, [])
        messages.append(error.message)
        pydash.objects.set_(errors, abs_path, messages)
    if len(errors) > 0:
        raise InvalidRequestJson(errors)
