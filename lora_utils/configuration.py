#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Project: https://github.com/cloudedbats/wurb_lora
# Author: Arnold Andreasson, info@cloudedbats.org
# License: MIT http://opensource.org/licenses/mit

import pathlib
import yaml
import logging
import collections


class Configuration:
    """ """

    def __init__(self, logger_name="DefaultLogger"):
        """ """
        self.logger = logging.getLogger(logger_name)
        self.clear()

    def clear(self):
        """ """
        self.config = {}
        self.config_default = {}
        self.config_flattend = {}
        self.config_default_flattend = {}

    def load_config(
        self,
        config_dir="",
        config_file="config.yaml",
        config_default_file="config_default.yaml",
    ):
        """ """
        self.clear()
        # Check if config file exists.
        config_default_path = pathlib.Path(config_default_file)
        config_path = pathlib.Path(config_dir, config_file)
        if not config_path.exists():
            if not config_path.parent.exists():
                config_path.parent.mkdir(parents=True)
            config_path.write_text(config_default_path.read_text())
            self.logger.debug(
                "Configuration - Config file missing. Copy of default config made: "
                + config_path.name
            )
        # Load config-default files.
        with open(config_default_path) as file:
            self.config_default = yaml.load(file, Loader=yaml.FullLoader)
        self.config_default_flattend = self.flatten_dict(self.config_default)
        # Load config files.
        with open(config_path) as file:
            self.config = yaml.load(file, Loader=yaml.FullLoader)
        self.config_flattend = self.flatten_dict(self.config)

    def flatten_dict(self, dictionary, parent_key=False, separator="."):
        """ """
        items = []
        for key, value in dictionary.items():
            new_key = str(parent_key) + separator + key if parent_key else key
            if isinstance(value, collections.abc.MutableMapping):
                items.extend(self.flatten_dict(value, new_key, separator).items())
            elif isinstance(value, list):
                for k, v in enumerate(value):
                    items.extend(self.flatten_dict({str(k): v}, new_key).items())
            else:
                items.append((new_key, value))
        return dict(items)

    def get(self, key_flat, default=""):
        """ """
        value = default
        if key_flat in self.config_flattend:
            value = self.config_flattend[key_flat]
        else:
            if key_flat in self.config_default_flattend:
                value = self.config_default_flattend[key_flat]

        if value in ["False", "false"]:
            value = False
        if value in ["True", "true"]:
            value = True
        return value
