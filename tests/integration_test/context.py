import os

from conftest import TEST_TOKEN


class COLORS:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def log_test_case(message):
    print()
    print(f"{COLORS.OKBLUE}{message}{COLORS.ENDC}")


class Service:
    def __init__(self, app):
        self.service = app.test_client()
        self.project = os.getenv("MEGANNO_PROJECT_NAME")

    def get_base_payload(self):
        return {"token": TEST_TOKEN}

    def get(self, url, **kwargs):
        """Sends GET request and returns the response."""
        return self.service.get(f"/{self.project}/{url}", **kwargs)

    def post(self, url, **kwargs):
        """Sends POST request and returns the response."""
        return self.service.post(f"/{self.project}/{url}", **kwargs)
