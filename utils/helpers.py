import os

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_asset_path(filename: str) -> str:
    return os.path.join(_BASE_DIR, "assets", filename)


def format_number(n: int | float) -> str:
    return f"{int(n):,}".replace(",", ".")
