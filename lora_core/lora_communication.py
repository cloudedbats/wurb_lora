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
        self.serial = None
        self.send_task = None
        self.receive_task = None
        self.parser_task = None
        self.lora_out_queue = None
        self.lora_in_queue = None

    def configure(self):
        """ """
        self.queue_max_size = 1000
        self.selected_idx_part = "1A86:55D3"  # "USB Single Serial" for USB-TO-LoRa-LF.

    def is_lora_connected(self):
        """ """
        if self.serial != None:
            try:
                self.serial.inWaiting()
                return self.serial.isOpen()
            except:
                return False
        else:
            return False

    def lora_send(self, data):
        """ """
        if not self.is_lora_connected():
            return
        try:
            if self.lora_out_queue != None:
                # print("SEND: ", data)
                self.lora_out_queue.put_nowait(data)
        except Exception as e:
            print("A: ", e)
            self.logger.debug("LoraComm, lora_send " + str(e))

    async def lora_at_config(self, at_commands):
        """ """
        if not self.is_lora_connected():
            return
        await asyncio.sleep(5)
        self.serial.write("+++\r\n".encode())
        await asyncio.sleep(0.2)
        for command in at_commands:
            data = command + "\r\n"
            self.serial.write(data.encode())
        await asyncio.sleep(5)

    def check_devices(self, device_hwid_part):
        """ """
        selected_device = None
        try:
            self.logger.debug("LoRA: Connected devices: ")
            for info in serial.tools.list_ports.comports():
                if info.hwid in ["n/a", None, ""]:
                    continue
                self.logger.debug("LoRa: hwid: " + info.hwid)
                if device_hwid_part in info.hwid:
                    selected_device = info.device
        except Exception as e:
            print("C: ", e)
            self.logger.debug("LoraComm, select_comport " + str(e))
        return selected_device

    def open_serial(
        self,
        selected_device,
        baudrate=115200,
        timeout=1,
    ):
        """ """
        self.serial = None
        try:
            if selected_device != None:
                self.serial = serial.Serial(
                    selected_device,
                    baudrate=baudrate,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    bytesize=serial.EIGHTBITS,
                    timeout=timeout,
                )
                self.serial.reset_input_buffer()
                self.serial.reset_output_buffer()
        except Exception as e:
            print("D: ", e)
            self.logger.debug("LoraComm, open_serial: " + str(e))

    def close_serial(self):
        """ """
        try:
            if self.serial != None:
                if self.serial.isOpen():
                    self.serial.close()
                self.serial = None
        except Exception as e:
            print("E: ", e)
            self.logger.debug("LoraComm, close_serial: " + str(e))

    async def startup(self):
        """ """
        try:
            selected_device = self.check_devices(self.selected_idx_part)
            if selected_device == None:
                return False
            else:
                self.open_serial(selected_device)
                # Create queues.
                if self.lora_out_queue == None:
                    self.lora_out_queue = asyncio.Queue(maxsize=self.queue_max_size)
                if self.lora_in_queue == None:
                    self.lora_in_queue = asyncio.Queue(maxsize=self.queue_max_size)
                # Clear queues if created earlier.
                self.remove_items_from_queue(self.lora_out_queue)
                self.remove_items_from_queue(self.lora_in_queue)
                # Start send task.
                if self.send_task == None:
                    self.send_task = asyncio.create_task(
                        self.lora_send_task(), name="LoRa-send-task"
                    )
                    self.logger.debug("LoRa-send-task STARTED.")
                # Start receive task.
                if self.receive_task == None:
                    self.receive_task = asyncio.create_task(
                        self.lora_receive_task(), name="LoRa-receive-task"
                    )
                    self.logger.debug("LoRa-receive-task STARTED.")
                # Start parser task.
                if self.parser_task == None:
                    self.parser_task = asyncio.create_task(
                        self.lora_parser_task(), name="LoRa-parser-task"
                    )
                    self.logger.debug("LoRa-parser-task STARTED.")
                #
                await asyncio.sleep(0)
            return True
        except Exception as e:
            print("F: ", e)
            self.logger.debug("LoraComm, start_lora " + str(e))
            return False

    async def shutdown(self):
        """ """

    async def lora_send_task(self):
        """ """
        try:
            while True:
                try:
                    if not self.is_lora_connected():
                        break
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
                            self.serial.write(data.encode())
                            # print("LoRa write done: ", item)
                    finally:
                        self.lora_out_queue.task_done()
                        await asyncio.sleep(0)

                except asyncio.CancelledError:
                    self.logger.debug("LoRa send was cancelled.")
                    break
                except Exception as e:
                    print("G: ", e)
                    message = "LoraComm,  LoRa send(1): " + str(e)
                    self.logger.debug(message)
                await asyncio.sleep(0)
        except Exception as e:
            print("H: ", e)
            message = "LoraComm,  LoRa send(2). Exception: " + str(e)
            self.logger.debug(message)
        finally:
            self.close_serial()
            self.send_task = None
            self.logger.debug("LoraComm - LoRa send ended.")

    async def lora_receive_task(self):
        """ """
        buffer = b""
        try:
            try:
                while True:
                    try:
                        if not self.is_lora_connected():
                            break
                        if self.serial.inWaiting() > 0:
                            buffer += self.serial.read(self.serial.inWaiting())
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
                                    print(
                                        "LoraComm, LoRa receive(1). Exception: ", str(e)
                                    )
                        await asyncio.sleep(0.1)
                    except serial.SerialException:
                        self.serial = None
                        print("LoraComm, SerialException.")
                    except Exception as e:
                        self.serial = None
                        self.logger.debug(
                            "LoraComm, LoRa receive(2). Exception: " + str(e)
                        )
                    await asyncio.sleep(0.1)
            finally:
                self.close_serial()
                self.receive_task = None
                print("Closed.")
        except Exception as e:
            print("J: ", e)
            self.logger.debug("LoraComm, LoRa receive(3). Exception:  " + str(e))

    async def lora_parser_task(self):
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
                    message = "LoraComm - LoRa parser(1): " + str(e)
                    self.logger.debug(message)

                await asyncio.sleep(0)

        except Exception as e:
            print("L: ", e)
            message = "LoraComm - LoRa parser(2). Exception: " + str(e)
            self.logger.debug(message)
        finally:
            self.parser_task = None
            self.logger.debug("LoraComm - LoRa parser ended.")

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
