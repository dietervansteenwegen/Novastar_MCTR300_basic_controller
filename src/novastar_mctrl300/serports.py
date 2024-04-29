#! /usr/bin/python3
# -*- coding: utf-8 -*-

__author__ = 'Dieter Vansteenwegen'
__project__ = 'Novastar_MCTRL300_basic_controller'
__project_link__ = 'https://boxfish.be/posts/20230213-novastar-mctrl300-basic-control-software/'

import serial
from serial.tools import list_ports

BAUDRATE = 115200
TIMEOUT = 4


def get_available_ports() -> list:
    ports = list_ports.comports(include_links=False)
    return [(i, port.device, port.manufacturer, port.product) for i, port in enumerate(ports)]


class Mctrl300Serial(serial.Serial):
    def __init__(self, port: str):
        super().__init__(
            port,
            baudrate=BAUDRATE,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=TIMEOUT,
        )
