#! /usr/bin/python3
# -*- coding: utf-8 -*-

__author__ = 'Dieter Vansteenwegen'
__project__ = 'Novastar_MCTRL300_basic_controller'
__project_link__ = 'https://boxfish.be/posts/20230213-novastar-mctrl300-basic-control-software/'

import logging
from enum import Enum

import PyQt5.QtCore as qtc

log = logging.getLogger(__name__)


class ConnState(Enum):
    UNKNOWN = -1
    NO_SERIAL_PORTS_DETECTED = 0
    SERIAL_PORTS_DETECTED = 1
    SERIAL_PORT_OPENED = 2
    SCREEN_CONNECTED = 3


class Status(qtc.QObject):
    sign_conn_status_changed = qtc.pyqtSignal(ConnState)
    sign_statusbar_msg_changed = qtc.pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.conn_state: ConnState = ConnState.UNKNOWN
        self.set_conn_state(ConnState.UNKNOWN)

    def set_conn_state(self, state: ConnState) -> None:
        if state.value == self.conn_state.value:
            log.debug("connection state hasn't changed")
        elif state.value > self.conn_state.value:
            self.conn_state = state
            self.sign_conn_status_changed.emit(self.conn_state)
        else:
            # TODO: Handle "downgrading" states (i.e. "connected" but no ports are found anymore)
            msg = (
                f'Trying to set connection state to {state.name} but currently '
                f'already on {self.conn_state.name}',
            )
            raise NotImplementedError(msg)

    @property
    def statusbar_msg(self) -> str:
        return self._statusbar_msg

    @statusbar_msg.setter
    def statusbar_msg(self, msg: str) -> None:
        self._statusbar_msg = msg
        self.sign_statusbar_msg_changed.emit(msg)
