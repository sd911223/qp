import os
import logging
import logging.handlers

from base import const
from configs import config

_main_log_name = "__main__"
_main_file_name = "main.log"
_max_bytes = 1024 * 1024 * 5
_back_up_count = 20
_format = '%(asctime)s - %(process)d:%(filename)s:%(lineno)s:%(levelname)s - %(message)s'
_server_id = 0


def make_logger(server_name, server_id):
    # assert server_name
    # assert server_id
    obj = logging.getLogger(server_name)
    server_name = os.path.relpath(server_name)
    file_path = const.LOG_PATH + server_name + "/"
    if not os.path.exists(file_path):
        os.makedirs(file_path)
    file_name = file_path + server_name + str(server_id) + ".log"
    handler = logging.handlers.RotatingFileHandler(file_name, mode="aw+",
                                                   maxBytes=_max_bytes, backupCount=_back_up_count)
    formatter = logging.Formatter(_format)  # 实例化formatter
    handler.setFormatter(formatter)  # 为handler添加formatter
    obj.addHandler(handler)
    obj.setLevel(config.get_log_level())
    return obj


def _init_logger(logger, file_name):
    global _server_id
    file_path = const.LOG_PATH + file_name.format(_server_id)

    if not os.path.exists(const.LOG_PATH):
        os.makedirs(const.LOG_PATH)

    # 实例化handler
    handler = logging.handlers.RotatingFileHandler(file_path, mode="aw+",
                                                   maxBytes=_max_bytes, backupCount=_back_up_count)
    formatter = logging.Formatter(_format)  # 实例化formatter
    handler.setFormatter(formatter)  # 为handler添加formatter
    logger.addHandler(handler)
    logger.setLevel(config.get_log_level())
    return handler


main_logger = logging.getLogger(_main_log_name)
_init_logger(main_logger, _main_file_name)
