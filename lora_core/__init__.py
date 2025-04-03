#!/usr/bin/python3
# -*- coding:utf-8 -*-

import os
from os import getcwd
import sys
import pathlib

import lora_utils

__version__ = "2025.0.0-development"

# Absolute paths to working directory and executable.
workdir_path = pathlib.Path(__file__).parent.parent.resolve()
executable_path = pathlib.Path(os.path.dirname(sys.argv[0]))
getcwd_path = pathlib.Path(getcwd())  # TODO - for test.
print()
print("DEBUG: Working directory path: ", str(workdir_path))
print("DEBUG: Executable path: ", str(executable_path))
print("DEBUG: getcwd path (for test): ", str(getcwd_path))

logger_name = "LoRaLogger"
logging_dir = pathlib.Path(executable_path.parent, "lora_logging")
log_file_name = "lora_info_log.txt"
debug_log_file_name = "lora_debug_log.txt"
settings_dir = pathlib.Path(executable_path.parent, "lora_settings")
config_dir = pathlib.Path(executable_path.parent, "lora_settings")
config_file = "lora_config.yaml"
config_default_file = pathlib.Path(workdir_path, "lora_config_default.yaml")

from lora_core.lora_communication import LoraCommunication
from lora_core.lora_manager import LoraManager
from lora_core.file_checker import FileChecker

# Instances of classes.
config = lora_utils.Configuration(logger_name=logger_name)
config.load_config(
    config_dir=config_dir,
    config_file=config_file,
    config_default_file=config_default_file,
)
# LoRa.
lora_comm = LoraCommunication(config, logger_name=logger_name)
lora_manager = LoraManager(config, logger_name=logger_name)
file_checker = FileChecker(config, logger_name=logger_name)
