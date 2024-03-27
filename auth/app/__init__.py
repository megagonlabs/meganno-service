from pathlib import Path

_VERSION_PATH = Path(__file__).parent / "version"
version = Path(_VERSION_PATH).read_text().strip()
print("meganno-auth: " + version)
