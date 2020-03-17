from configparser import RawConfigParser

from misc import Path

class ConfigReader(RawConfigParser):
    def __init__(self, filename):
        super().__init__(inline_comment_prefixes=('#', ';'))
        path = Path.path('./config/%s.ini' % filename)
        parsed = self.read(path)
        if not parsed:
            raise Exception('Error reading config data from %s' % path)

        for name, section in self.items():
            for key, val in section.items():
                try:
                    if val.startswith('0x'):
                        int_val = int(val, 16)
                    else:
                        int_val = int(val)
                except ValueError:
                    continue
                section[key] = int_val

    def _validate_value_types(self, **kwargs):
        pass
