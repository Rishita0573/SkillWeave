import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def resolve(path: str) -> str:
    return os.path.join(BASE_DIR, path)
