#! /usr/bin/python3
# -*- coding: utf-8 -*-

__author__ = 'Dieter Vansteenwegen'
__project__ = 'Novastar_MCTRL300_basic_controller'
__project_link__ = 'https://boxfish.be/posts/20230213-novastar-mctrl300-basic-control-software/'

import contextlib
import datetime as dt
import itertools
import logging
import logging.handlers
from typing import List

import novastar_mctrl300.mctrl300 as mctrl300
import serial.serialutil
from novastar_mctrl300 import serports
from PyQt5 import QtWidgets
from PyQt5.QtCore import QTimer

from gui.ui_sources.main_window import Ui_MainWindow

LOG_FMT = (
    '%(asctime)s|%(levelname)-8.8s|%(module)-15.15s|%(lineno)-0.3d|'
    '%(funcName)-20.20s |%(message)s'
)
DATEFMT = '%d/%m/%Y %H:%M:%S'
LOGFILE = './logfile.log'
LOGMAXBYTES = 500000
TMR_MSECS = 1000


class MilliSecondsFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):  # noqa: N802
        # sourcery skip: lift-return-into-if, remove-unnecessary-else
        ct = dt.datetime.fromtimestamp(record.created)  # noqa: DTZ006
        if datefmt:
            s = ct.strftime(datefmt)
        else:
            t = ct.strftime(DATEFMT)
            s = f'{t}.{int(record.msecs)}'
        return s


def setup_logger() -> logging.Logger:
    """Setup logging.
    Returns logger object with (at least) 1 streamhandler to stdout.

    Returns:
        logging.Logger: configured logger object
    """
    logger = logging.getLogger()  # DON'T specifiy name in order to create root logger!
    logger.setLevel(logging.DEBUG)

    stream_handler = logging.StreamHandler()  # handler to stdout
    stream_handler.setLevel(logging.ERROR)
    stream_handler.setFormatter(MilliSecondsFormatter(LOG_FMT))
    logger.addHandler(stream_handler)
    return logger


def add_rotating_file(logger: logging.Logger) -> None:
    rot_fil_handler = logging.handlers.RotatingFileHandler(
        LOGFILE,
        maxBytes=LOGMAXBYTES,
        backupCount=3,
    )
    rot_fil_handler.doRollover()
    rot_fil_handler.setLevel(logging.DEBUG)
    rot_fil_handler.setFormatter(MilliSecondsFormatter(LOG_FMT))
    logger.addHandler(rot_fil_handler)


log = setup_logger()
add_rotating_file(log)


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, *args, obj=None, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        log.debug('Starting')
        self.setupUi(self)
        self._refresh_serial_ports()
        self.serport = None
        self.led_screen = None
        self.state = 1
        self._connect_slots()
        self._update_to_state()
        self._set_up_timer_brightness()
        self._set_up_timer()
        self._setup_pattern_generator()
        self.statusbar = QtWidgets.QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage('Started...', msecs=2000)

    def _setup_pattern_generator(self) -> None:
        """Pattern generator to cycle through colors/pattern."""
        self.pattern_list = itertools.cycle(
            [
                mctrl300.MCTRL300.PATTERN_RED,
                mctrl300.MCTRL300.PATTERN_GREEN,
                mctrl300.MCTRL300.PATTERN_BLUE,
                mctrl300.MCTRL300.PATTERN_WHITE,
            ],
        )

    def _set_up_timer(self) -> None:
        """Timer will be used to cycle through colors."""
        self.timer = QTimer()
        self.timer.setInterval(TMR_MSECS)
        self.timer.timeout.connect(self._timer_timeout)

    def _set_up_timer_brightness(self):
        # TODO: Timer querying brightness and setting slider value + label
        # TODO: Code for setting/getting brightness
        pass

    def _connect_slots(self):
        self.btn_serial_refresh.clicked.connect(self._refresh_serial_ports)
        self.btn_serial_open.clicked.connect(lambda checked: self._open_serial_port(checked))
        self.cmb_output.currentIndexChanged.connect(lambda index: self._output_changed(index))
        self.btn_blackout.clicked.connect(self._pattern_black)
        self.btn_blue.clicked.connect(self._pattern_blue)
        self.btn_freeze.clicked.connect(self._pattern_freeze)
        self.btn_cycle_colors.clicked.connect(self._pattern_cycle_colors)
        self.btn_green.clicked.connect(self._pattern_green)
        self.btn_normal.clicked.connect(self._pattern_normal)
        self.btn_red.clicked.connect(self._pattern_red)
        self.btn_slash.clicked.connect(self._pattern_slash)
        self.btn_white.clicked.connect(self._pattern_white)
        self.sldr_brightness.valueChanged.connect(self._brightness_value_changed)
        # self.sldr_brightness.sliderMoved.connect(self._brightness_value_changed)
        self.set_normal.triggered.connect(self._pattern_normal)
        self.set_red.triggered.connect(self._pattern_red)
        self.set_green.triggered.connect(self._pattern_green)
        self.set_blue.triggered.connect(self._pattern_blue)
        self.set_white.triggered.connect(self._pattern_white)
        self.set_slash.triggered.connect(self._pattern_slash)
        # self.set_blackout.triggered.connect(self._pattern_blackout)
        self.set_freeze.triggered.connect(self._pattern_freeze)
        self.set_cycle_colors.triggered.connect(self._pattern_cycle_colors)
        log.debug('Signals/slots connected')
        self.set_1_pct.triggered.connect(lambda _: self.sldr_brightness.setValue(1))
        self.set_5_pct.triggered.connect(lambda _: self.sldr_brightness.setValue(5))
        self.set_100_pct.triggered.connect(lambda _: self.sldr_brightness.setValue(100))

    def _brightness_value_changed(self, v):
        # TODO: send out brightness set commands
        self.lbl_brightness_value.setText(str(v))
        if self.led_screen:
            self.led_screen.set_brightness(self.selected_port, v)

    def _output_changed(self, index: int):
        success = False
        if index in {1, 2} and self.serport is not None:
            success: bool = bool(self.create_screen(index))

        if not success:
            self._initialize_state()

    def _initialize_state(self) -> None:
        self.led_screen = None
        self._change_state_to(2)

    def create_screen(self, output):
        success = False
        with contextlib.suppress(mctrl300.MCTRL300Error):
            self.led_screen: mctrl300.MCTRL300 = mctrl300.MCTRL300(serport=self.serport)
            self.selected_port = output
            self._change_state_to(3)
            self._update_brightness_from_screen()
            success = True
        return success

    def _update_brightness_from_screen(self) -> None:
        """Query brightness from screen.

        Query brightness from screen, update slider and slider textbox or show messagebox if
            query fails.
        """
        log.debug(f'Querying brightness from output {self.selected_port}')
        try:
            brightness = self.led_screen.get_brightness(self.selected_port)
        except mctrl300.MCTRL300IncorrectReplyError:
            brightness = None

        if brightness is not None:
            self.lbl_brightness_value.setText(brightness.__str__())
            self.sldr_brightness.setValue(brightness)
            log.debug(f'Response: {brightness}')
        else:
            QtWidgets.QMessageBox.critical(
                self,
                'No reply from screen',
                'Screen did not reply when requesting current brightness'
                f' from output {self.selected_port}. Check: \n'
                '* Cabling \n* Configuration\n* MCTRL3000 powered on',
                buttons=QtWidgets.QMessageBox.Ok,
            )
            log.error('Issue while getting brightness.')
            self.cmb_output.setCurrentIndex(0)
            self._change_state_to(2)

    def _refresh_serial_ports(self) -> None:
        """Refresh the available serial ports.

        Query the OS for available serial ports. Update listbox and enable button to
            open selected port if ports are available.
        """
        self.lst_serial_ports.clear()
        self.serial_available_ports: List = []
        for port in sorted(serports.get_available_ports()):
            self.serial_available_ports.append(port)
            log.debug(f'Found serial port: {port[1:]}')
            self.lst_serial_ports.addItem(f' {port[1]}  ({port[2]}, {port[3]})')
            # if port[3][:6] == 'CP2102':
            # TODO: color item in list green (this is a possible controller)
        if len(self.serial_available_ports) > 0:
            self.btn_serial_open.setEnabled(True)
            self.lst_serial_ports.setCurrentRow(0)
        else:
            self.btn_serial_open.setEnabled(False)
            self.lbl_serial_status.setText('No ports found...')
            self.lbl_serial_status.setStyleSheet('background-color:orange')
            self._change_state_to(1)

    def _open_serial_port(self, checked: bool) -> None:
        if checked:
            if len(self.serial_available_ports) == 0:
                # self.lbl_serial_status.setText('No serial ports')
                self.btn_serial_open.setChecked(False)
                self._change_state_to(1)
                return
            index = self.lst_serial_ports.currentRow()
            try:
                p = self.serial_available_ports[index]
                log.debug(f'opening serial port {p[1:]}')
                self.serport = serports.Mctrl300Serial(p[1])
            except (FileNotFoundError, serial.serialutil.SerialException):
                log.exception('Issue during opening.')
                self._refresh_serial_ports()
                self.btn_serial_open.setChecked(False)
                self._change_state_to(1)
            if self.serport and self.serport.isOpen():
                self.lbl_serial_status.setText(f'Opened {self.serial_available_ports[index][1]}')
                log.debug('Port open.')
                self.btn_serial_open.setText(
                    f'Click to close {self.serial_available_ports[index][1]}',
                )
                self.lbl_serial_status.setStyleSheet('background-color:green')
                self._change_state_to(2)
            else:
                log.error(f'Issue during opening port {p}.')
                self.lbl_serial_status.setText('Error opening port. See logs.')
                self.lbl_serial_status.setStyleSheet('background-color:red')
                self.serport = None
                self._change_state_to(1)
        else:
            if self.serport:
                self.serport.close()
                log.debug(f'Closed {self.serport}')
            self.lbl_serial_status.setText('Closed serial port')
            self.lbl_serial_status.setStyleSheet('background-color:orange')
            self.btn_serial_open.setText('Click to open selected port')
            self._change_state_to(1)

    def _change_state_to(self, state: int):
        if state == 2 and self.cmb_output.currentIndex() > 0:
            state = 3
        self.state = state
        self._update_to_state()

    def _update_to_state(self):
        self.cmb_output.setEnabled(self.state > 1)
        self.menubar_pattern.setEnabled(self.state > 2)
        self.sldr_brightness.setEnabled(self.state > 2)
        self.btn_normal.setEnabled(self.state > 2)
        self.btn_red.setEnabled(self.state > 2)
        self.btn_green.setEnabled(self.state > 2)
        self.btn_blue.setEnabled(self.state > 2)
        self.btn_white.setEnabled(self.state > 2)
        self.btn_slash.setEnabled(self.state > 2)
        self.btn_cycle_colors.setEnabled(self.state > 2)
        # self.btn_freeze.setEnabled(self.state > 2)
        # self.btn_blackout.setEnabled(self.state > 2)
        self.btn_freeze.setEnabled(False)
        self.btn_blackout.setEnabled(False)

    def _timer_timeout(self) -> None:
        """Timeout callback for cycle colors timer.

        If currently set to cycle colors, go to next pattern.
            If not, stop timer and reset the cycle colors generator.
        """
        if self.btn_cycle_colors.isChecked():
            self.led_screen.set_pattern(next(self.pattern_list), self.selected_port)
        else:
            self.timer.stop()
            self._setup_pattern_generator()

    def _pattern_cycle_colors(self) -> None:
        if self.led_screen:
            # self.led_screen.set_pattern(mctrl300.MCTRL300.PATTERN_RED, self.selected_port)
            self.btn_cycle_colors.setChecked(True)
            log.debug('Cycle colors activated.')
            self.timer.start()
            self._timer_timeout()

    def _pattern_red(self):
        if self.led_screen:
            self.led_screen.set_pattern(mctrl300.MCTRL300.PATTERN_RED, self.selected_port)
            self.btn_red.setChecked(True)

    def _pattern_blue(self):
        if self.led_screen:
            self.led_screen.set_pattern(mctrl300.MCTRL300.PATTERN_BLUE, self.selected_port)
            self.btn_blue.setChecked(True)

    def _pattern_green(self):
        if self.led_screen:
            self.led_screen.set_pattern(mctrl300.MCTRL300.PATTERN_GREEN, self.selected_port)
            self.btn_green.setChecked(True)

    def _pattern_white(self):
        if self.led_screen:
            self.led_screen.set_pattern(mctrl300.MCTRL300.PATTERN_WHITE, self.selected_port)
            self.btn_white.setChecked(True)

    def _pattern_slash(self):
        if self.led_screen:
            self.led_screen.set_pattern(mctrl300.MCTRL300.PATTERN_SLASH, self.selected_port)
            self.btn_slash.setChecked(True)

    def _pattern_normal(self):
        if self.led_screen:
            self.led_screen.deactivate_pattern(self.selected_port)
            self.btn_normal.setChecked(True)

    def _pattern_black(self):
        if self.led_screen:
            self.led_screen.set_pattern(mctrl300.MCTRL300.PATTERN_RED, self.selected_port)
            self.btn_black.setChecked(True)

    def _pattern_freeze(self):
        if self.led_screen:
            self.led_screen.set_pattern(mctrl300.MCTRL300.PATTERN_RED, self.selected_port)
            self.btn_freeze.setChecked(True)


def start_gui():
    app = QtWidgets.QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()
    window.show()
    app.exec_()
