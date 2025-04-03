#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Project: https://github.com/cloudedbats/wurb_lora_2025
# Author: Arnold Andreasson, info@cloudedbats.org
# License: MIT, http://opensource.org/licenses/mit

import asyncio
import logging
import serial
import serial.tools.list_ports


class LoraCommunication(object):
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
        self.lora = None
        self.send_worker = None
        self.receive_worker = None
        self.parser_worker = None
        self.lora_out_queue = None
        self.lora_in_queue = None

    def configure(self):
        """ """
        self.queue_max_size = 10000
        self.selected_idx_part = "1A86:55D3"  # "USB Single Serial" for USB-TO-LoRa-LF.

    def lora_send(self, data):
        """ """
        try:
            if self.lora_out_queue != None:
                # print("SEND: ", data)
                self.lora_out_queue.put_nowait(data)
        except Exception as e:
            print("A: ", e)
            self.logger.debug("LoraWorker, lora_send " + str(e))

    def select_comport(self):
        """ """
        result = None
        try:
            print("List of comports:")
            for info in serial.tools.list_ports.comports(
                # include_links=True,
            ):
                if info.hwid in ["n/a", None, ""]:
                    continue
                print("device: ", info.device)
                # print("name: ", info.name)
                print("hwid: ", info.hwid)
                # print("vid: ", info.vid)
                # print("pid: ", info.pid)
                # print("serial_number: ", info.serial_number)
                # print("location: ", info.location)
                # print("manufacturer: ", info.manufacturer)
                print("product: ", info.product)
                # print("interface: ", info.interface)

                if self.selected_idx_part in info.hwid:
                    result = info.device
                print("")
        except Exception as e:
            print("C: ", e)
            self.logger.debug("LoraWorker, select_comport " + str(e))
        return result

    def lora_connect(self, comport):
        """ """
        try:
            self.lora_disconnect()
            #
            self.lora = serial.Serial(
                comport,
                baudrate=115200,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS,
                timeout=2,
            )
        except Exception as e:
            print("D: ", e)
            self.logger.debug("LoraWorker, lora_connect" + str(e))

    def lora_disconnect(self):
        """ """
        try:
            if self.lora != None:
                if self.lora.isOpen():
                    self.lora.close()
        except Exception as e:
            print("E: ", e)
            self.logger.debug("LoraWorker, lora_disconnect" + str(e))

    async def lora_at_config(self, at_commands):
        """ """
        # await asyncio.sleep(3)
        self.lora.write("+++\r\n".encode())
        await asyncio.sleep(0.1)
        for command in at_commands:
            data = command + "\r\n"
            self.lora.write(data.encode())
        await asyncio.sleep(1)

    async def startup(self):
        """ """
        try:
            selected_device = self.select_comport()
            if selected_device != None:
                self.lora_connect(selected_device)
                # Create queues.
                if self.lora_out_queue == None:
                    self.lora_out_queue = asyncio.Queue(maxsize=self.queue_max_size)
                if self.lora_in_queue == None:
                    self.lora_in_queue = asyncio.Queue(maxsize=self.queue_max_size)
                # Clear queues if created earlier.
                self.remove_items_from_queue(self.lora_out_queue)
                self.remove_items_from_queue(self.lora_in_queue)
                # Start send worker.
                if self.send_worker == None:
                    self.send_worker = asyncio.create_task(
                        self.lora_send_worker(), name="LoRa-send-task"
                    )
                    self.logger.debug("LoRa-send-task STARTED.")
                # Start receive worker.
                if self.receive_worker == None:
                    self.receive_worker = asyncio.create_task(
                        self.lora_receive_worker(), name="LoRa-receive-task"
                    )
                    self.logger.debug("LoRa-receive-task STARTED.")
                # Start parser worker.
                if self.parser_worker == None:
                    self.parser_worker = asyncio.create_task(
                        self.lora_parser_worker(), name="LoRa-parser-task"
                    )
                    self.logger.debug("LoRa-parser-task STARTED.")
                #
                await asyncio.sleep(0)
        except Exception as e:
            print("F: ", e)
            self.logger.debug("LoraWorker, start_lora " + str(e))

    async def lora_send_worker(self):
        """ """
        try:
            while True:
                try:
                    item = await self.lora_out_queue.get()
                    print("SEND-Q: ", item)
                    try:
                        if item == None:
                            # Terminated by process.
                            break
                        elif item == False:
                            self.remove_items_from_queue(self.to_target_queue)
                        else:
                            # Send LoRa message.
                            # print("LoRa write: ", item)
                            data = item + "\r\n"
                            self.lora.write(data.encode())
                            # print("LoRa write done: ", item)
                    finally:
                        self.lora_out_queue.task_done()
                        await asyncio.sleep(0)

                except asyncio.CancelledError:
                    self.logger.debug("LoRa send was cancelled.")
                    break
                except Exception as e:
                    print("G: ", e)
                    message = "RecWorker - rec_send_worker(1): " + str(e)
                    self.logger.debug(message)

                await asyncio.sleep(0)

        except Exception as e:
            print("H: ", e)
            message = "RecWorker - rec_send_worker(2). Exception: " + str(e)
            self.logger.debug(message)
        finally:
            self.logger.debug("LoRaWorker - LoRa send ended.")

    async def lora_receive_worker(self):
        """ """
        buffer = b""
        try:
            try:
                while True:
                    try:
                        if self.lora.inWaiting() > 0:
                            buffer += self.lora.read(self.lora.inWaiting())
                            # print("BUFFER: ", buffer.replace(b"\r\n", b"--", -1).decode())
                            while b"\r\n" in buffer:
                                index = buffer.index(b"\r\n")
                                data = buffer[:index]
                                buffer = buffer[index + 2 :]
                                # print("DATA: ", data.decode())
                                try:
                                    # print(data.decode())
                                    self.lora_in_queue.put_nowait(data.decode())
                                except Exception as e:
                                    print("Exception: ", e)
                        await asyncio.sleep(0.1)
                    except serial.SerialException:
                        print("SerialException.")
                    except Exception as e:
                        print("I: ", e)
                        self.logger.debug("LoraWorker, ???: " + str(e))
                    await asyncio.sleep(0.1)
            finally:
                self.lora.close()
                print("Closed.")
        except Exception as e:
            print("J: ", e)
            self.logger.debug("LoraWorker, ???: " + str(e))

    async def lora_parser_worker(self):
        """ """
        try:
            while True:
                try:
                    item = await self.lora_in_queue.get()
                    print("PARSER: ", item)
                    try:
                        if item == None:
                            # Terminated by process.
                            break
                        elif item == False:
                            self.remove_items_from_queue(self.lora_in_queue)
                        else:

                            if "TEST" in item:
                                data = item.replace("TEST", "ACK")
                                self.lora_send(data)
                    finally:
                        self.lora_in_queue.task_done()
                        await asyncio.sleep(0)

                except asyncio.CancelledError:
                    self.logger.debug("LoRa parser was cancelled.")
                    break
                except Exception as e:
                    print("K: ", e)
                    message = "RecWorker - rec_parser_worker(1): " + str(e)
                    self.logger.debug(message)

                await asyncio.sleep(0)

        except Exception as e:
            print("L: ", e)
            message = "RecWorker - rec_parser_worker(2). Exception: " + str(e)
            self.logger.debug(message)
        finally:
            self.logger.debug("LoRaWorker - LoRa parser ended.")

    def remove_items_from_queue(self, queue):
        """Helper method."""
        try:
            if queue:
                while True:
                    try:
                        queue.get_nowait()
                        queue.task_done()
                    except asyncio.QueueEmpty:
                        return
        except Exception as e:
            print("M: ", e)
            message = "Remove_items_from_queue. Exception: " + str(e)
            self.logger.debug(message)
