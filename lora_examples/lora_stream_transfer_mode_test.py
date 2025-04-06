#!/usr/bin/python3
# -*- coding:utf-8 -*-

import asyncio
import serial
import serial.tools.list_ports


class LoraStreamTransferModeTest(object):
    """ """

    def __init__(self):
        """ """
        self.serial = None
        self.listener_task = None

    def check_devices(self, device_hwid_part):
        """ """
        selected_device = None
        try:
            print("Connected devices: ")
            for info in serial.tools.list_ports.comports():
                if info.hwid in ["n/a", None, ""]:
                    continue
                print("hwid: ", info.hwid)
                if device_hwid_part in info.hwid:
                    selected_device = info.device
        except:
            print("Exception: Failed to check devices.")
        print("Device: ", selected_device)
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
        except:
            pass

    def start_listener_task(self):
        """ """
        self.listener_task = asyncio.create_task(
            self.lora_listener_task(), name="LoRa-listener-task"
        )

    async def lora_listener_task(self):
        """ """
        buffer = b""
        try:
            while True:
                try:
                    if not self.is_lora_connected():
                        break
                    if self.serial.inWaiting() > 0:
                        buffer += self.serial.read(self.serial.inWaiting())
                        while b"\r\n" in buffer:
                            index = buffer.index(b"\r\n")
                            data = buffer[:index]
                            buffer = buffer[index + 2 :]
                            try:
                                self.lora_command_parser(data.decode())
                            except Exception as e:
                                print("Exception: ", str(e))
                except serial.SerialException:
                    self.serial = None
                    print("Exception: SerialException.")
                except Exception as e:
                    self.serial = None
                    print("Exception: " + str(e))
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            print("LoRa listener task was cancelled.")
        except Exception as e:
            print("Exception: ", str(e))
        finally:
            await self.close_lora()

    async def lora_at_commands(self):
        """ """
        await asyncio.sleep(5)
        self.lora_write("+++")
        await asyncio.sleep(0.1)
        self.lora_write("AT+PWR=30")
        self.lora_write("AT+ADDR=0")
        self.lora_write("AT+AllP?")
        self.lora_write("AT+EXIT")
        await asyncio.sleep(5)

    def lora_write(self, data):
        """ """
        data = data + "\r\n"
        self.serial.write(data.encode())

    def lora_command_parser(self, data):
        """ """
        print("Received: ", data)

        # Send acknowledge when receiving TEST commands.
        if "TEST" in data:
            response = data.replace("TEST", "ACK")
            self.lora_write(data)

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

    async def close_lora(self):
        """ """
        if self.serial != None:
            self.serial.close()
            self.serial = None
            print("LoRa closed.")
        await asyncio.sleep(0)
        if self.listener_task != None:
            self.listener_task.cancel()
            self.listener_task = None
        await asyncio.sleep(0)


async def main():
    """ """
    device_hwid_part = "1A86:55D3"
    lora = LoraStreamTransferModeTest()
    while True:
        device = lora.check_devices(device_hwid_part)
        while device == None:
            await asyncio.sleep(5)
            device = lora.check_devices(device_hwid_part)
        if device != None:
            try:
                lora.open_serial(device)
                lora.start_listener_task()
                await lora.lora_at_commands()
                counter = 0
                while True:
                    data = "TEST-" + str(counter)
                    print("Sending: " + data)
                    data += "\r\n"
                    if lora.is_lora_connected():
                        lora.serial.write(data.encode())
                    else:
                        break
                    counter += 1
                    await asyncio.sleep(2.0)
            except asyncio.CancelledError:
                print("Main loop was cancelled.")
                break
            finally:
                await lora.close_lora()


if __name__ == "__main__":
    """ """
    asyncio.run(main())
