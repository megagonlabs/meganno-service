import os

from app.flask_app import app

MEGANNO_FLASK_HOST = os.getenv("MEGANNO_FLASK_HOST", None)
MEGANNO_AUTH_PORT = os.getenv("MEGANNO_AUTH_PORT", 5001)
APP_ENVIRONMENT = os.getenv("MEGANNO_FLASK_ENV", "production")
debug = APP_ENVIRONMENT != "production"
if __name__ == "__main__":
    if MEGANNO_FLASK_HOST is None:
        app.run(debug=debug, port=MEGANNO_AUTH_PORT)
    else:
        app.run(debug=debug, port=MEGANNO_AUTH_PORT, host=MEGANNO_FLASK_HOST)
