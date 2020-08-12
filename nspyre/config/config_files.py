#!/usr/bin/env python
"""
This module handles reading and writing YAML configuration files

Author: Jacob Feder
Date: 7/25/2020
"""

###########################
# imports
###########################

# std
import os
from importlib import import_module

# 3rd party
import yaml

# nspyre
from nspyre.definitions import join_nspyre_path, CLIENT_META_CONFIG_YAML

###########################
# Globals
###########################

META_CONFIG_FILES_ENTRY = 'config_files'

###########################
# Exceptions
###########################

class ConfigEntryNotFoundError(Exception):
    """Exception for when a configuration file doesn't contain the desired
    entry"""
    def __init__(self, config_path, msg=None):
        if msg is None:
            msg = 'Config file was expected to contain parameter: { %s } ' \
                    'but it wasn\'t found.' % \
                    (' -> '.join(config_path))
        super().__init__(msg)
        self.config_path = config_path

class ConfigError(Exception):
    """General Config file exception"""
    def __init__(self, msg):
        super().__init__(msg)

###########################
# Classes / functions
###########################

# A meta-config.yaml file contains a single entry with key 
# META_CONFIG_FILES_ENTRY and value = a list of all the config files that
# should be read

def load_raw_config(filepath):
    """Return a config file dictionary loaded from a YAML file"""
    with open(filepath, 'r') as f:
        conf = yaml.safe_load(f)
    return conf

def meta_config_add(meta_config_file, files):
    """Add config files to the meta-config"""
    meta_config = load_raw_config(meta_config_file)
    config_list,_ = get_config_param(meta_config, [META_CONFIG_FILES_ENTRY])
    new_files = []
    for f in files:
        if os.path.isabs(f):
            f_name = f
        else:
            f_name = os.path.abspath(os.path.join(os.getcwd(), f))
        if not os.path.isfile(f_name):
            raise FileNotFoundError('file %s not found' % (f_name))
        new_files.append(f_name)
    meta_config[META_CONFIG_FILES_ENTRY] = config_list + new_files
    write_config(meta_config, meta_config_file)

def meta_config_remove(meta_config_file, files):
    """Remove config files from the meta-config"""
    meta_config = load_raw_config(meta_config_file)
    config_list,_ = get_config_param(meta_config, [META_CONFIG_FILES_ENTRY])
    for c in files:
        try:
            c_int = int(c)
            # ran if c is an integer indicating an index rather than a file path
            config_list.pop(c_int)
        except:
            # otherwise c is a file path string
            if c in config_list:
                config_list.remove(c)
            else:
                raise ConfigError('config file %s was not found in the '
                                    'meta-config' % (c)) from None
    meta_config[META_CONFIG_FILES_ENTRY] = config_list
    write_config(meta_config, meta_config_file)

def meta_config_files(meta_config_file):
    """Return the paths of the config files in the meta-config"""
    meta_config = load_raw_config(meta_config_file)
    config_list,_ = get_config_param(meta_config, [META_CONFIG_FILES_ENTRY])
    return config_list

def load_config(meta_config_path=None):
    """Takes a 'meta' config file that specifies the location of other config
    files to load, then make a dictionary where the keys are the config file
    names and the values are the config dictionaries of that file."""
    if not meta_config_path:
        meta_config_path = join_nspyre_path(CLIENT_META_CONFIG_YAML)
    # load the meta config
    meta_config = load_raw_config(meta_config_path)
    # get the config file paths
    config_files = meta_config[META_CONFIG_FILES_ENTRY]
    config_dict = {}
    # iterate through the config file paths, load their dictionaries, and add
    # them to the combined dictionary
    meta_config_dir = os.path.dirname(meta_config_path)
    for cfg_file in config_files:
        if not os.path.isabs(cfg_file):
            cfg_file = os.path.join(meta_config_dir, cfg_file)
        config_dict[cfg_file] = load_raw_config(cfg_file)
    return config_dict

def write_config(config_dict, filepath):
    """Write a dictionary to a YAML file"""
    # open the file and write it's config dictionary
    with open(filepath, 'w') as file:
        yaml.dump(config_dict, file)

def get_config_param(config_dict, path):
    """Navigate a YAML-loaded config file and return a particular parameter 
    given by 'path'. If multiple config files contain the first element of
    'path', this will attempt to navigate the the first config file it finds
    that contains the first element of 'path'."""
    first_elem = path[0]
    for conf in config_dict:
        # first find the config file containing the first path element
        loc = config_dict[conf]
        if first_elem in loc:
            # now descend into the config dictionary, following the keys
            # one-by-one in path
            for p in path:
                try:
                    loc = loc[p]
                except KeyError:
                    raise ConfigEntryNotFoundError(path) from None
            return loc, conf
    # if we reach this point the first path element wasn't found in any
    # config file entries
    raise ConfigEntryNotFoundError(path) from None
