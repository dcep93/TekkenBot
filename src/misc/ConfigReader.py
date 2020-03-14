from configparser import ConfigParser

from misc import Path

class ConfigReader(ConfigParser):
    def __init__(self, filename):
        super().__init__()
        path = Path.path('./config/%s.ini' % filename)
        parsed = self.read(path)
        if not parsed:
            raise Exception('Error reading config data from %s' % path)
