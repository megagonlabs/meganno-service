import os

from app.flask_app import app

MEGANNO_FLASK_HOST = os.getenv("MEGANNO_FLASK_HOST", None)
MEGANNO_SERVICE_PORT = os.getenv("MEGANNO_SERVICE_PORT", 5000)
APP_ENVIRONMENT = os.getenv("MEGANNO_FLASK_ENV", "production")
debug = APP_ENVIRONMENT != "production"
if __name__ == "__main__":
    if MEGANNO_FLASK_HOST is None:
        app.run(debug=debug, port=MEGANNO_SERVICE_PORT)
    else:
        app.run(debug=debug, port=MEGANNO_SERVICE_PORT, host=MEGANNO_FLASK_HOST)
