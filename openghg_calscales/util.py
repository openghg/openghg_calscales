from pathlib import Path


def path(sub_path):
    return Path(__file__).parent / sub_path
