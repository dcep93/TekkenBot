"""
Reads in simple config files
"""

from configparser import ConfigParser
import collections

import misc.Path


class ConfigReader:
    DATA_FOLDER = 'config'

    values = {}

    def __init__(self, filename):
        self.parser = ConfigParser()
        self.path = self.get_path(filename)
        parsed = self.parser.read(self.path)
        if not parsed:
            print('Error reading config data from %s. Using default values.' % self.path)

    def get_path(self, filename):
        return misc.Path.path('%s/%s.ini' % (self.DATA_FOLDER, filename))

    def get_property(self, enum_item, default_value):
        section = enum_item.__class__.__name__
        property_string = enum_item.name
        try:
            f = self.parser.getboolean if type(default_value) is bool else self.parser.get
            return f(section, property_string)
        except:
            value = default_value

        self.set_property(enum_item, value)
        return value

    def set_property(self, enum_item, value):
        section = enum_item.__class__.__name__
        property_string = enum_item.name
        if section not in self.parser.sections():
            self.parser.add_section(section)
        self.parser.set(section, property_string, str(value))

    def add_comment(self, comment):
        self.set_property('Comments', '; %s' % comment, '')

    def write(self):
        with open(self.path, 'w') as fw:
            self.parser.write(fw)

    def get_all(self, enum_class, default):
        return {enum: self.get_property(enum, default) for enum in enum_class}


def config_from_path(config_path, input_dict=None, parse_nums=False):
    '''
    Parses the file from config_path with configparser and converts configparser's
    pseudo-dict in to a proper dict.
    Configparser's section proxies and string-only values are unsuitable for our use.

    Overwrites old values in input_dict
    '''
    if input_dict is None:
        input_dict = CaseInsensitiveDict()

    config_data = ConfigParser(inline_comment_prefixes=('#', ';'))
    try:
        config_data.read(config_path)
    except:
        print("Error reading config data from " + config_path)
    else:
        for section, proxy in config_data.items():
            if section == 'DEFAULT':
                continue
            if section not in input_dict:
                input_dict[section] = CaseInsensitiveDict()
            for key, value in proxy.items():
                if parse_nums:
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

                input_dict[section][key] = value
    return input_dict


class ReloadableConfig(ConfigReader):
    # Store configs so we can reload and update them later when needed
    configs = []

    def __init__(self, filename, parse_nums=False):
        '''
        Configuration class that can reload all class instances with the
        .reload() class method.

        'parse_nums' determines if we keep values as strings or try to convert
        to int/hex
        '''
        self.path = self.get_path(filename)
        self.parse_nums = parse_nums
        self.filename = filename

        self.config = None

        self.reload_self()

        ReloadableConfig.configs.append(self)

    def __getitem__(self, key):
        if key not in self.config:
            # This is maybe a bit ugly but won't crash the program if the config file
            # is broken or missing entries. Assumes int values.
            # Maybe not needed.
            print('{} section missing from {}.ini'.format(key, self.file_name))
            return collections.defaultdict(lambda: collections.defaultdict(int))
        else:
            return self.config[key]

    @classmethod
    def reload(cls):
        for config in cls.configs:
            config.reload_self()

    def reload_self(self):
        self.config = config_from_path(self.path, parse_nums=self.parse_nums, input_dict=self.config)


class CaseInsensitiveDict(dict):
    def __contains__(self, key):
        return super().__contains__(key.lower())

    def __setitem__(self, key, value):
        super().__setitem__(key.lower(), value)

    def __getitem__(self, key):
        return super().__getitem__(key.lower())

