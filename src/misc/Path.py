import os

__path__ = '%s/' % os.path.dirname(os.path.dirname(__file__))

def path(rel_path):
    return '%s/%s' % (__path__, rel_path)
