import os
import sys

__dir__ = os.path.dirname(sys.argv[0])
__path__ = os.path.join(__dir__, 'export')

def path(rel_path):
    return os.path.join(__path__, rel_path)
