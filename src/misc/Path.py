import os
import sys

__path__ = '%s/' % os.path.dirname(os.path.dirname(__file__))
print(__path__)
__path__ = os.path.dirname(sys.argv[0])

def path(rel_path):
    return os.path.join(__path__, rel_path)
