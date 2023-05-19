import logging
import os
from typing import Optional
import sys

log = logging.getLogger(__name__)


def setup_logging(
        log_file_path: Optional[os.PathLike] = None,
        log_level: str = "INFO",
        write_to_file_and_std_out: bool = True) -> None:
    """
    Set up the logging for the app. A rotating file handler is used to cap the overall size of the logs.
    Parameters
    ----------
    log_file_path : Optional[os.PathLike]
        The path to log to. If not set will write to stdout.
    log_level : str
        The level at which to log, as a string. There are 6 available values,
        listed at https://docs.python.org/3/library/logging.html#logging-levels
    write_to_file_and_std_out: bool
        If set True will write to file and std_out
    """

    if log_file_path is not None:
        logging.basicConfig(
            filename=log_file_path,
            level=log_level,
            filemode='a',
            format='[%(levelname)6s %(asctime)s, %(filename)17s, '
            'ln%(lineno)4s, in %(funcName)25s()] %(message)s',
            datefmt="%Y-%m-%d %H:%M:%S")  # add timezone to date format
    else:
        logging.basicConfig(
            level=log_level,
            format='[%(levelname)6s %(asctime)s, %(filename)17s, '
            'ln%(lineno)4s, in %(funcName)25s()] %(message)s',
            datefmt="%Y-%m-%d %H:%M:%S")  # add timezone to date format

    # disable debug logging for matplotlib, as they generate a large number of unecessary logs
    if log_level == 'DEBUG':
        logging.getLogger("matplotlib.backends.backend_pdf").setLevel(logging.INFO)
        logging.getLogger("matplotlib.colorbar").setLevel(logging.INFO)
        logging.getLogger("matplotlib.font_manager").setLevel(logging.INFO)
        logging.getLogger("matplotlib.ticker").setLevel(logging.INFO)

    if write_to_file_and_std_out and log_file_path is not None:  # enable writing to std_out if file specified
        logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

    if (log_file_path is not None) and (not os.path.exists(log_file_path)):
        with open(log_file_path, 'a') as _:
            pass
        # chmod the log file in order to ensure that it can be appended to by other users
        os.chmod(log_file_path, 0o777)

    log.info('Logging setup complete.')
    return log
