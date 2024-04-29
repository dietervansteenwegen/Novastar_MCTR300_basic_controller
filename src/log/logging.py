import datetime as dt
import logging
import logging.handlers

LOG_FMT = (
    '%(asctime)s|%(levelname)-8.8s|%(module)-15.15s|%(lineno)-0.3d|'
    '%(funcName)-20.20s |%(message)s|'
)
DATEFMT = '%d/%m/%Y %H:%M:%S'
LOGFILE = './logfile.log'
LOGMAXBYTES = 500000


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
