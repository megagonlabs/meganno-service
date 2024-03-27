from functools import wraps

import pydash
from flask import abort, request


def require_id_token():
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not pydash.objects.get(request, "user.id_token", False):
                abort(401, "Invalid ID token.")
            return f(*args, **kwargs)

        return decorated_function

    return decorator


def require_role(*role_conditions):
    # 1 user - 1 role
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            conditions = len(role_conditions)
            while conditions > 0:
                rule = role_conditions[conditions - 1]
                role_code = pydash.objects.get(request, "user.role_code", None)
                if (
                    pydash.is_string(rule) and not pydash.is_equal(rule, role_code)
                ) or (pydash.is_list(rule) and not pydash.includes(rule, role_code)):
                    abort(401, "Permission denied.")
                conditions -= 1
            return f(*args, **kwargs)

        return decorated_function

    return decorator
