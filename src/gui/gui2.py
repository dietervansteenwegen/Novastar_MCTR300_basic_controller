#! /usr/bin/python3
# -*- coding: utf-8 -*-

__author__ = 'Dieter Vansteenwegen'
__project__ = 'Novastar_MCTRL300_basic_controller'
__project_link__ = 'https://boxfish.be/posts/20230213-novastar-mctrl300-basic-control-software/'

from typing import List

from core.status import ConnState, Status
from log.logging import add_rotating_file, setup_logger
from novastar_mctrl300 import serports
from PyQt5 import QtCore as qtc
from PyQt5 import QtGui as qtg
from PyQt5 import QtWidgets as qtw

from gui.ui_sources.main_window import Ui_MainWindow

TMR_MSECS = 2000

log = setup_logger()
add_rotating_file(log)


class MainWindow(qtw.QMainWindow, Ui_MainWindow):
    def __init__(self, *args, obj=None, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        log.debug('Starting')
        self.setupUi(self)
        self._create_status()
        # self.led_screen = None
        # self._setup_pattern_generator()
        # self.statusbar = QtWidgets.QStatusBar()
        # self.setStatusBar(self.statusbar)
        self._connect_signals()
        self._set_up_timer()

    def _connect_signals(self) -> None:
        self.btn_serial_refresh.clicked.connect(self._refresh_serial_ports)

    def _create_status(self) -> None:
        self.stat: Status = Status()
        self.stat.sign_conn_status_changed.connect(self._update_conn_state)
        self.stat.sign_statusbar_msg_changed.connect(self._update_statusbar)

    def _set_up_timer(self) -> None:
        """Timer will be used to cycle through colors."""
        self.timer = qtc.QTimer()
        self.timer.setInterval(TMR_MSECS)
        self.timer.timeout.connect(self._timer_timeout)
        self.timer.start()

    def _timer_timeout(self) -> None:
        self._refresh_serial_ports()
        # TODO add brightness and curr pattern request (or only when connecting?)

    @qtc.pyqtSlot(ConnState)
    def _update_conn_state(self, state: ConnState) -> None:
        log.debug(f'Conn state changed: {state.name}')
        self._update_enabled_elements(state)
        if state == ConnState.NO_SERIAL_PORTS_DETECTED:
            self._set_state_no_ports_detected()
        if state == ConnState.SERIAL_PORTS_DETECTED:
            self._set_state_ports_detected()
        if state == ConnState.SERIAL_PORT_OPENED:
            self._set_state_port_opened()

    def _set_state_port_opened(self) -> None:
        self.stat.statusbar_msg = 'Select output connected to screen...'

    def _update_enabled_elements(self, state: ConnState) -> None:
        curr_state = state.value
        self.btn_serial_open.setEnabled(curr_state > ConnState.NO_SERIAL_PORTS_DETECTED.value)
        self.cmb_output.setEnabled(curr_state >= ConnState.SERIAL_PORT_OPENED.value)
        self.sldr_brightness.setEnabled(curr_state >= ConnState.SCREEN_CONNECTED.value)
        self.grp_patterns.setEnabled(curr_state >= ConnState.SCREEN_CONNECTED.value)

    def _set_state_ports_detected(self) -> None:
        # self.lst_serial_ports.setCurrentRow(0)
        self.lbl_serial_status.setText('Select port to controller...')
        self.lbl_serial_status.setStyleSheet('background-color:green')
        self.stat.statusbar_msg = 'Select port from list and open port'

    def _set_state_no_ports_detected(self) -> None:
        self.lbl_serial_status.setStyleSheet('background-color:orange')
        self.lbl_serial_status.setText('No ports found...')
        self.stat.statusbar_msg = 'No ports found. Connect controller to USB port.'

    @qtc.pyqtSlot(str)
    def _update_statusbar(self, msg: str) -> None:
        self.statusbar.showMessage(msg)

    def _refresh_serial_ports(self) -> None:
        """Refresh the available serial ports.

        Query the OS for available serial ports. Update listbox and enable button to
            open selected port if ports are available.
        """
        self.lst_serial_ports.clear()
        self.serial_available_ports: List = []
        for port in sorted(serports.get_available_ports()):
            self.serial_available_ports.append(port)
            description: str = f' {port[1]}  ({port[2]}, {port[3]})'
            log.debug(f'Found serial port: {description}')
            list_item = qtw.QListWidgetItem(description)
            list_item.setBackground(
                qtg.QColor('#A4F4AA' if 'CP2102' in port[3] else '#ECC565'),
            )
            self.lst_serial_ports.addItem(list_item)

        self.stat.set_conn_state(
            ConnState.SERIAL_PORTS_DETECTED
            if len(self.serial_available_ports) > 0
            else ConnState.NO_SERIAL_PORTS_DETECTED,
        )
        # TODO add state for opened and screen connected
        # TODO add handler for if serial port is lost


def start_gui():
    app = qtw.QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()
    window.show()
    app.exec_()
    app.exec_()
    app.exec_()
