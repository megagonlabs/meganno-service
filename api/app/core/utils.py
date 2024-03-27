class ValueNotExistsError(Exception):
    def __init__(self, val):
        super().__init__(
            f"ValueNotExistsError: Value {val} does not exist in the database/"
        )
