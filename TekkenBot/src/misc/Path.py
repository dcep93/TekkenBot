import os

__path__ = 'assets'

def path(rel_path):
    return os.path.join(__path__, rel_path)
