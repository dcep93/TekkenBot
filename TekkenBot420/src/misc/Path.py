import os

__path__ = 'assets'


def path(rel_path: str) -> str:
    return os.path.join(__path__, rel_path)
