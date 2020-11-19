import logging
import logging.handlers
from base import const

_gate_log_name = "__gate__"
_gate_file_name = "gate{0}.log"
_game_log_name = "__game__"
_game_file_name = "game{0}.log"
_max_bytes = 1024 * 1024
_back_up_count = 50
_format = '%(asctime)s - %(process)d:%(filename)s:%(lineno)s:%(levelname)s - %(message)s'
_log_level = logging.DEBUG
_judge_log_name = "__judge__"
_judge_file_name = "judge{0}.log"
_server_id = 0

gate_logger = logging.getLogger(_gate_log_name)
gate_file_no = 0

game_logger = logging.getLogger(_game_log_name)
game_file_no = 0

judge_logger = logging.getLogger(_judge_log_name)
judge_file_no = 0


def _init_loger(logger, file_name):
    global _server_id
    file_path = const.LOG_PATH + file_name.format(_server_id)

    # 实例化handler
    handler = logging.handlers.RotatingFileHandler(file_path, mode="aw+",
                                                   maxBytes=_max_bytes, backupCount=_back_up_count)
    formatter = logging.Formatter(_format)  # 实例化formatter
    handler.setFormatter(formatter)  # 为handler添加formatter
    logger.addHandler(handler)
    logger.setLevel(_log_level)
    return handler


def set_server_id(server_id):
    global gate_logger, gate_file_no, _server_id, judge_logger, judge_file_no, _judge_file_name, \
        game_logger, game_file_no
    _server_id = server_id

    main_handler = _init_loger(gate_logger, _gate_file_name)
    gate_file_no = main_handler.stream.fileno()

    judge_handler = _init_loger(judge_logger, _judge_file_name)
    judge_file_no = judge_handler.stream.fileno()

    game_handler = _init_loger(game_logger, _game_file_name)
    game_file_no = game_handler.stream.fileno()
