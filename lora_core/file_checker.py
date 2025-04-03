#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Project: https://github.com/cloudedbats/wurb_lora
# Author: Arnold Andreasson, info@cloudedbats.org
# License: MIT http://opensource.org/licenses/mit

import pathlib
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import lora_core


class FileChecker:
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
        self.is_active = False
        self.observer = None

    def configure(self):
        """ """
        # self.check_path = "."
        self.check_path = "/home/wurb/wurb_recordings"

    async def startup(self):
        """ """
        if self.is_active == False:
            if self.observer == None:
                self.observer = Observer()
                event_handler = FileCheckHandler()
                self.observer.schedule(
                    event_handler,
                    path=self.check_path,
                    recursive=True,
                )
            self.observer.start()
            self.is_active = True

    async def shutdown(self):
        """ """
        if self.is_active == True:
            if self.observer:
                self.observer.stop()
            self.is_active = False


class FileCheckHandler(FileSystemEventHandler):
    # def on_modified(self, event):
    #     print(f"File {event.src_path} has been modified")

    def on_created(self, event):
        print(f"File {event.src_path} has been created")
        file = pathlib.Path(event.src_path)
        if file.is_file:
            if file.suffix.lower() == ".wav":
                lora_core.lora_comm.lora_send("File " + file.name)
            message = "FileChecker: Sound file added: " + str(file.name)
            lora_core.file_checker.logger.info(message)

    # def on_deleted(self, event):
    #     print(f"File {event.src_path} has been deleted")
