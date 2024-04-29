#! /usr/bin/python3
# -*- coding: utf-8 -*-

__author__ = 'Dieter Vansteenwegen'
__project__ = 'Novastar_MCTRL300_basic_controller'
__project_link__ = 'https://boxfish.be/posts/20230213-novastar-mctrl300-basic-control-software/'

import logging
from time import sleep
from typing import List, Union

import serial

from novastar_mctrl300.serports import Mctrl300Serial

BAUDRATE = 115200
TIMEOUT = 4


class MCTRL300Error(Exception):
    pass


class MCTRL300IncorrectReplyError(MCTRL300Error):
    pass


class MCTRL300:
    REG_TEST_PATTERN = 0x02000101
    REG_BRIGHTNESS_OVERALL = 0x02000001

    PATTERN_NORMAL = 1
    PATTERN_RED = 2
    PATTERN_GREEN = 3
    PATTERN_BLUE = 4
    PATTERN_WHITE = 5
    PATTERN_HORIZONTAL = 6
    PATTERN_VERTICAL = 7
    PATTERN_SLASH = 8
    PATTERN_GRAYSCALE = 9

    def __init__(self, serport: serial.Serial):
        """Class for basic control of the Novastar MCTRL300 LED controller.

        Args:
            serport (serial.Serial): Serial port to which the MCTRL300 is connected.
                                    Initialized to 115200 baud, 8N1
        """
        self.log = logging.getLogger(__name__)
        self._init_serport(serport)
        self._msg_id: int = 0  # increasing number for each message sent
        self.output = 0
        self.creator = MCTRL300CreateCommand()
        self.log.debug('Created MCTRL300 object.')

    def _init_serport(self, serport: serial.Serial) -> None:
        """Initialize the serial port.

        Args:
            serport (serial.Serial): Serial port to which the MCTRL300 is connected.
                                    Initialized to 115200 baud, 8N1
        """
        self.serport = serport
        self.serport.close()
        self.serport.open()

    def set_pattern(self, pattern: int, port: int) -> None:
        """Activate an internal test pattern.

        Pattern can be an int from 1 to 10 or one of the PATTERN constants.

        Args:
            pattern (int): one of the above test patterns, i.e. PATTERN_RED
            port (int): port to which screen is connected, 1 or 2.
        """
        cmd = self.creator.generate(
            serno=self._msg_id,
            port=port,
            reg_addr=self.REG_TEST_PATTERN,
            data_len=1,
            data=pattern,
        )
        self.log.debug(f'Set output {port} to pattern no {pattern}')
        self._send_cmd(cmd)

    def deactivate_pattern(self, port: int) -> None:
        """Deactivate test pattern on port.

        Display normal/live incoming video signal.

        Args:
            port (int): port to which screen is connected, 1 or 2.
        """
        cmd = self.creator.generate(
            serno=self._msg_id,
            port=port,
            reg_addr=self.REG_TEST_PATTERN,
            data_len=1,
            data=self.PATTERN_NORMAL,
        )
        self._send_cmd(cmd)

    def _print_cmd(self, cmd):
        print('cmd: ', end='')
        for i in cmd:
            print(hex(i), end=' ')
        print()

    def set_brightness(self, port: int, value: int) -> None:
        """Set brightness of screen on port.

        Sets the overall brightness, leaving the individual color brightness values to default.

        Args:
            port (int): port to which screen is connected, 1 or 2.
            value (int): brightness value, 0 to 0xFF.
        """
        cmd = self.creator.generate(
            serno=self._msg_id,
            port=port,
            reg_addr=self.REG_BRIGHTNESS_OVERALL,
            data_len=1,
            data=value,
        )
        self._send_cmd(cmd)

    def _send_cmd(self, cmd: bytearray) -> None:
        """Send command and increase message id.

        Args:
            cmd (bytearray): command to be sent to port/processor.
        """
        self.serport.reset_input_buffer()
        self.serport.write(cmd)
        self._msg_id += 1
        if self._msg_id > 0xFF:
            self._msg_id = 0
        sleep(0.1)

    def get_brightness(self, port: int) -> Union[int, None]:
        cmd = self.creator.generate(
            serno=self._msg_id,
            port=port,
            reg_addr=self.REG_BRIGHTNESS_OVERALL,
            data_len=1,
            data=None,
            is_write=False,
        )
        used_msg_id = self._msg_id
        self._send_cmd(cmd)
        response = self._get_response(used_msg_id, reply_data_length=1)
        return response[0] if response else None

    def _get_response(
        self,
        used_msg_id,
        reply_data_length: int,
        timeout: int = 1,
    ) -> Union[bytearray, None]:
        timeout_cntr: float = 0
        rx_buff: bytearray = bytearray()
        msg_without_data_length = 20
        complete = False

        while timeout_cntr < timeout:
            while self.serport.in_waiting > 0:
                rx_buff.extend(self.serport.read())
            rx_buff = self._cleanup_rx_buff(rx_buff)
            if len(rx_buff) >= msg_without_data_length + reply_data_length:
                complete = True
                rx_buff = rx_buff[:-2]  # strip checksum
                break
            sleep(0.05)
            timeout_cntr += 0.05
        correct_reply = complete and rx_buff[3] == used_msg_id and rx_buff[2] == 00
        if not correct_reply:
            self.log.error(f'Got an incorrect reply: {rx_buff}')
            raise MCTRL300IncorrectReplyError(rx_buff)

        return rx_buff[-reply_data_length:] if correct_reply else None

    def _cleanup_rx_buff(self, rx_buff: bytearray) -> bytearray:
        if len(rx_buff) < 2:
            return rx_buff
        start = rx_buff.find(0xAA)
        return rx_buff[start:] if rx_buff[start + 1] == 0x55 else bytearray()


class MCTRL300CreateCommand:
    def __init__(self):
        self.msg = bytearray()

    def generate(
        self,
        serno: int,
        reg_addr: int,
        data_len: int,
        data: Union[int, List[int], None],
        port: int,
        is_cmd: bool = True,
        is_write: bool = True,
        ack=0,
    ) -> bytearray:
        """Generate a command to be sent to processor.

        Args:
            serno (int): message id, used to reference commands and responses. Can be any value.
            reg_addr (int): address of the register to be written/read.
            data_len (int): number of bytes to be sent/read to/from device.
            data (Union[int, List[int]]): data to be sent.
            port (int): port to which screen is connected, 1 or 2.
            is_cmd (bool, optional): cmd is a command, not request. Defaults to True.
            is_write (bool, optional): indicates a write command. Defaults to True.
            ack (int, optional): is an acknowledge command. Defaults to 0.

        Returns:
            bytearray: complete command
        """
        self.msg = bytearray()
        self._append_header(is_cmd)
        self._append_ack(ack)
        self.msg.append(serno)
        self._append_src()
        self._append_dest()
        self._append_card_type()
        self._append_port_addr(port)
        self._append_board_addr(is_cmd)
        self._append_cmd_type(is_write)
        self._append_reserved()
        self._append_reg_addr(reg_addr)
        self._append_data_len(data_len)
        self._append_data(data)
        self._append_checksum()
        return self.msg

    def _append_ack(self, ack) -> None:
        self.msg.append(ack)

    def _append_checksum(self) -> None:
        """Add checksum at the end of message.

        Checksum is calculated by taking the sum of all bytes starting with message id/number, then
        adding 0xFFFF. The resulting two bytes are then added LSB, MSB
        """
        c = sum(self.msg[3:])
        c += 0x5555
        self.msg.append(c & 0xFF)
        self.msg.append(c >> 8)

    def _append_data(self, data: Union[int, list, None]) -> None:
        """Append the data payload to the message.

        Message might be a list of bytes, a single value (int), or None (ie for a request).

        Args:
            data (Union[int, list, None]): data payload (None if no data to be sent)
        """
        if data and isinstance(data, list):
            self.msg.append(*data)
        elif data is not None:
            self.msg.append(data)

    def _append_data_len(self, data_len) -> None:
        """Add the data length.

        2 bytes, first LSB then MSB.

        Args:
            data_len (int): Length of data to read/write. Range 0 - 0xFFFF
        """
        self.msg.append(data_len & 0xFF)
        self.msg.append((data_len & 0xFF) >> 8)

    def _append_reg_addr(self, reg_addr) -> None:
        self.msg.append(reg_addr & 0xFF)
        self.msg.append((reg_addr & 0x0000FF00) >> 8)
        self.msg.append((reg_addr & 0x00FF0000) >> 16)
        self.msg.append((reg_addr & 0xFF000000) >> 24)

    def _append_header(self, is_cmd) -> None:
        header = [0x55, 0xAA] if is_cmd else [0xAA, 0x55]
        for i in header:
            self.msg.append(i)  # header

    def _append_src(self) -> None:
        self.msg.append(0xFE)

    def _append_dest(self) -> None:
        self.msg.append(0x00)

    def _append_card_type(self) -> None:
        # 00 for sender, 01 for receiver, 02 for function
        self.msg.append(0x01)

    def _append_port_addr(self, port) -> None:
        self.msg.append(port - 1)

    def _append_board_addr(self, is_cmd: bool) -> None:
        for i in [0xFF, 0xFF] if is_cmd else [0x0, 0x0]:
            self.msg.append(i)

    def _append_cmd_type(self, is_write) -> None:
        self.msg.append(0x01 if is_write else 0x00)

    def _append_reserved(self) -> None:
        self.msg.append(0x00)


if __name__ == '__main__':
    p = Mctrl300Serial('/dev/ttyUSB0')
    s = MCTRL300(p)
    # s.get_brightness(1)
    # s.set_pattern(MCTRL300.PATTERN_RED, 1)
    # s.set_brightness(1, 0x10)
    for i in range(0x2):
        s.set_brightness(1, i)
        j = s.get_brightness(1)
        print(f'set to: {i}, reply: {j}.......{j == i}\n')
