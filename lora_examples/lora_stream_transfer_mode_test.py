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
        self.rssi = False

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
        if self.serial != None:
            self.close_lora()
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
            print("Exception: Failed to open serial: " + str(e))

    def start_listener_task(self):
        """ """
        if self.listener_task == None:
            self.listener_task = asyncio.create_task(
                self.lora_listener_task(), name="LoRa-listener-task"
            )

    def stop_listener_task(self):
        """ """
        if self.listener_task == None:
            self.listener_task.cancel()

    async def lora_listener_task(self):
        """ """
        buffer = b""
        try:
            while True:
                try:
                    if self.serial != None:
                        if self.serial.is_open:
                            if self.serial.inWaiting() > 0:
                                buffer += self.serial.read(self.serial.inWaiting())
                                while b"\r\n" in buffer:
                                    index = buffer.index(b"\r\n")
                                    data = buffer[:index]
                                    buffer = buffer[index + 2 :]
                                    if self.rssi:
                                        data = self.check_rssi(data)
                                    try:
                                        self.lora_command_parser(data.decode())
                                    except Exception as e:
                                        print("Exception(1): ", str(e))
                except serial.SerialException:
                    print("Exception: SerialException.")
                except Exception as e:
                    print("Exception(2): " + str(e))
                    # self.serial = None
                    self.close_lora()
                await asyncio.sleep(0.5)
        except asyncio.CancelledError:
            print("LoRa listener task was cancelled.")
        except Exception as e:
            print("Exception(3): ", str(e))

    def check_rssi(self, data):
        """ """
        result = data
        if len(data) >= 2:
            rssi_hex = data[:2]
            try:
                rssi = int(rssi_hex, 16) * -1
                if rssi < -10 and rssi > -120:
                    print("RSSI:", rssi, "dBm")
                    result = data[2:]
            except:
                pass
        return result

    async def lora_at_commands(self, rssi_on=False):
        """ """
        # Wait for LoRa startup.
        await asyncio.sleep(6)
        self.lora_write("+++")
        await asyncio.sleep(0.1)
        # self.lora_write("AT+SF=10")
        self.lora_write("AT+SF=12")
        self.lora_write("AT+PWR=22")
        self.lora_write("AT+ADDR=0")
        # RSSI, Received signal strength indication
        if rssi_on:
            self.lora_write("AT+RSSI=1")
            self.rssi = True
        else:
            self.lora_write("AT+RSSI=0")
            self.rssi = False
        self.lora_write("AT+AllP?")
        self.lora_write("AT+EXIT")
        # Wait for LoRa reboot.
        await asyncio.sleep(6)

    def lora_write(self, data):
        """ """
        try:
            data += "\r\n"
            data_encoded = data.encode()
        except Exception as e:
            print("Failed to encode: " + str(e))
            return
        if self.serial != None:
            try:
                self.serial.is_open
                self.serial.write(data_encoded)
            except Exception as e:
                print("Exception, lora_write: " + str(e))
                # self.serial = None
                self.close_lora()

    def lora_command_parser(self, data):
        """ """
        print("Received: ", data)

        # Send acknowledge when receiving TEST commands.
        if "TEST" in data:
            response = data.replace("TEST", "ACK")
            self.lora_write(data)

    def close_lora(self):
        """ """
        if self.serial != None:
            try:
                self.serial.close()
            except:
                pass
            self.serial = None
            print("LoRa closed.")


async def main():
    """ """
    device_hwid_part = "1A86:55D3"
    rssi_on = True
    lora = LoraStreamTransferModeTest()
    lora.start_listener_task()
    counter = 0
    try:
        while True:
            device = lora.check_devices(device_hwid_part)
            while device == None:
                await asyncio.sleep(5)
                device = lora.check_devices(device_hwid_part)
            if device != None:
                try:
                    lora.open_serial(device)
                    await lora.lora_at_commands(rssi_on = rssi_on)
                    while True:
                        if lora.serial == None:
                            break
                        data = "TEST-" + str(counter)
                        print("Sending: " + data)
                        lora.lora_write(data)
                        counter += 1
                        await asyncio.sleep(5.0)
                except Exception as e:
                    print("Exception in send loop: " + str(e))
                finally:
                    lora.close_lora()
                    await asyncio.sleep(1)
    except asyncio.CancelledError:
        print("Main loop was cancelled.")
    except Exception as e:
        print("Exception, main loop terminated: " + str(e))
    finally:
        lora.close_lora()
        lora.stop_listener_task()


if __name__ == "__main__":
    """ """
    asyncio.run(main())
