#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Project: https://github.com/cloudedbats/wurb_lora
# Author: Arnold Andreasson, info@cloudedbats.org
# License: MIT http://opensource.org/licenses/mit

import logging
import lora_core
import lora_core.file_checker


class LoraManager:
    """ """

    def __init__(self, config=None, logger=None, logger_name="DefaultLogger"):
        """ """
        self.config = config
        self.logger = logger
        if self.config == None:
            self.config = {}
        if self.logger == None:
            self.logger = logging.getLogger(logger_name)
        #
        self.clear()
        self.configure()

    def clear(self):
        """ """
        self.is_lora_active = False
        self.is_file_checker_active = False
        self.check_lora_worker = None

    def configure(self):
        """ """
        self.queue_max_size = 10000
        self.selected_idx_part = "1A86:55D3"  # "USB Single Serial" for USB-TO-LoRa-LF.
        self.at_commands = [
            "AT+PWR=30",
            "AT+ADDR=0",
            "AT+RSSI=0",
            "AT+AllP?",
            "AT+EXIT",
        ]

    async def startup(self):
        """ """
        await lora_core.lora_comm.startup()
        await lora_core.lora_comm.lora_at_config(self.at_commands)
        if self.is_file_checker_active == False:
            await lora_core.file_checker.startup()
            self.is_file_checker_active = True

    async def shutdown(self):
        """ """
        await lora_core.lora_comm.shutdown()
        await lora_core.file_checker.shutdown()
