from configparser import ConfigParser
from collections import defaultdict

from misc import Path

class ConfigReader:
    def __init__(self, filename):
        self.file_name = filename
        self.path = self.get_path(filename)

        self.parse()

    def parse(self):
        self.parser = ConfigParser()
        parsed = self.parser.read(self.path)
        if not parsed:
            print('Error reading config data from %s. Using default values.' % self.path)

    @staticmethod
    def get_path(filename):
        return Path.path('config/%s.ini' % filename)

    def get_property(self, enum_item, default_value):
        section = enum_item.__class__.__name__
        property_string = enum_item.name
        if self.parser.has_option(section, property_string):
            f = self.parser.getboolean if type(default_value) is bool else self.parser.get
            return f(section, property_string)
        else:
            value = default_value
            if default_value is not None:
                self.set_property(enum_item, value)
            return value

    def set_property(self, enum_item, value):
        section = enum_item.__class__.__name__
        property_string = enum_item.name
        if section not in self.parser.sections():
            self.parser.add_section(section)
        self.parser.set(section, property_string, str(value))

    def write(self):
        with open(self.path, 'w') as fw:
            self.parser.write(fw)

    def get_all(self, enum_class, default):
        return {enum: self.get_property(enum, default) for enum in enum_class}

class ReloadableConfig(ConfigReader):
    # Store configs so we can reload and update them later when needed
    configs = []

    def parse(self):
        self.config = CaseInsensitiveDict()

        self.reload_self()

        ReloadableConfig.configs.append(self)

    def __getitem__(self, key):
        if key not in self.config:
            print('{} section missing from {}.ini'.format(key, self.file_name))
            return defaultdict(lambda: defaultdict(int))
        else:
            return self.config[key]

    @classmethod
    def reload(cls):
        for config in cls.configs:
            config.reload_self()

    def reload_self(self):
        config_data = ConfigParser(inline_comment_prefixes=('#', ';'))
        try:
            config_data.read(self.path)
        except:
            print("Error reading config data from %s" % self.path)
            return

        for section, proxy in config_data.items():
            if section == 'DEFAULT':
                continue
            if section not in self.config:
                self.config[section] = CaseInsensitiveDict()
            for key, value in proxy.items():
                if ' ' not in value:
                    try:
                        # NonPlayerDataAddresses consists of space delimited lists of hex numbers
                        # so just ignore strings with spaces in them
                        if value.startswith('0x'):
                            value = int(value, 16)
                        else:
                            value = int(value)
                    except ValueError:
                        pass

                self.config[section][key] = value

class CaseInsensitiveDict(dict):
    def __contains__(self, key):
        return super().__contains__(key.lower())

    def __setitem__(self, key, value):
        super().__setitem__(key.lower(), value)

    def __getitem__(self, key):
        return super().__getitem__(key.lower())
