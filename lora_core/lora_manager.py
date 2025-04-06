#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Project: https://github.com/cloudedbats/wurb_lora
# Author: Arnold Andreasson, info@cloudedbats.org
# License: MIT http://opensource.org/licenses/mit

import asyncio
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
        self.lora_task = None

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
        #
        try:
            if self.is_file_checker_active == False:
                await lora_core.file_checker.startup()
                self.is_file_checker_active = True
        except Exception as e:
            print("LoraManager, startup(1). Exception: ", str(e))
        #
        try:
            if self.lora_task == None:
                self.lora_task = asyncio.create_task(
                    self.lora_check_task(), name="LoRa-activate-task"
                )
                self.logger.debug("LoRa-send-task STARTED.")
        except Exception as e:
            print("F: ", e)
            self.logger.debug("LoraManager, startup(2). Exception: " + str(e))

    async def shutdown(self):
        """ """
        if self.lora_task != None:
            self.lora_task.cancel()
        await lora_core.lora_comm.shutdown()
        await lora_core.file_checker.shutdown()

    async def lora_check_task(self):
        """ """
        lora_connected_old = False
        try:
            while True:
                try:
                    if not lora_core.lora_comm.is_lora_connected():
                        is_device_available = await lora_core.lora_comm.startup()
                        if is_device_available:
                            if lora_core.lora_comm.is_lora_connected():
                                self.logger.debug(
                                    "LoraManager: LoRa execute AT commands."
                                )
                                await lora_core.lora_comm.lora_at_config(
                                    self.at_commands
                                )
                    #
                    lora_connected = lora_core.lora_comm.is_lora_connected()
                    if lora_connected != lora_connected_old:
                        lora_connected_old = lora_connected
                        if lora_connected:
                            self.logger.debug("LoraManager: LoRa active.")
                        else:
                            self.logger.debug("LoraManager: LoRa NOT active.")
                except:
                    pass
                #
                await asyncio.sleep(5)
        except asyncio.CancelledError:
            self.logger.debug("LoraManager:LoRa task was cancelled.")
        finally:
            await lora_core.lora_comm.close_lora()
