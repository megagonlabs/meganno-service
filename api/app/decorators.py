from functools import wraps

import pydash
from flask import abort, request


def require_role(*role_conditions):
    # 1 user - 1 role
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            conditions = len(role_conditions)
            while conditions > 0:
                rule = role_conditions[conditions - 1]
                role_code = pydash.objects.get(request, "user.role_code", None)
                if pydash.is_string(rule):
                    if not pydash.is_equal(rule, role_code):
                        abort(401, "Permission denied.")
                elif not pydash.includes(rule, role_code):
                    abort(401, "Permission denied.")
                conditions -= 1
            return f(*args, **kwargs)

        return decorated_function

    return decorator
