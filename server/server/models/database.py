# coding:utf-8
import time

import pymysql
import redis

from base.logs import main_logger
from configs import config
from utils import utils
from utils.torndb import Connection, Row


def escape(data):
    if type(data) is int:
        return data
    if type(data) is float:
        return data
    if data is None:
        return ''
    if type(data) is bool:
        return int(data)
    if not data:
        return ''
    data = data.replace("%", "%%")
    return pymysql.escape_string(data)


def dict_to_row(dict_obj):
    return Row(dict_obj)


def resume_bool(data):
    if 'false' == data:
        return False
    if 'true' == data:
        return True
    return data


def resume_int(data):
    if type(data) is not str:
        return data
    if data.isdigit():
        return int(data)
    return data


def _db_connect(db_name="db_game") -> Connection:
    """ 连接数据库 """
    try:
        db_info = config.get_db_info(db_name)
        return Connection(**db_info)
    except Exception as data:
        main_logger.error("db connect error: %s", str(data))


_db_game = None  # _db_connect("db_game")  # 数据库连接对象


def _keep_db_connect(db: Connection):
    try:
        db.execute("SELECT 1")
    except Exception as data:
        main_logger.fatal("keep db error: %s", str(data))
        db.reconnect()


def keep_connect():
    """ 保持数据库在线的方法，需要定时调用一下 如果数据库无法ping通，则尝试重新连接"""
    global _db_game
    if not _db_game:
        _db_game = _db_connect("db_game")
    _keep_db_connect(_db_game)


def share_db() -> Connection:
    global _db_game
    if not _db_game:
        _db_game = _db_connect("db_game")
    return _db_game


_db_logs = None  # _db_connect("db_logs")  # 日志数据库连接对象


def keep_logs_connect():
    """ 保持日志数据库在线的方法，需要定时调用一下 如果数据库无法ping通，则尝试重新连接"""
    global _db_logs
    if not _db_logs:
        _db_logs = _db_connect("db_logs")
    _keep_db_connect(_db_logs)


def share_db_logs() -> Connection:
    global _db_logs
    if not _db_logs:
        _db_logs = _db_connect("db_logs")
    return _db_logs


def connect_redis(redis_name="redis_game"):
    """连接redis"""
    try:
        redis_info = config.get_redis(redis_name)  # redis的数据
        return redis.StrictRedis(**redis_info)
    except Exception as data:
        main_logger.error("connect redis error: ", str(data))


_redis_game = None  # 游戏redis连接对象


def ping_redis_game():
    """ 保持Redis在线的方法，调用ping时会尝试重新连接 """
    global _redis_game
    assert _redis_game or "redis game not exist!"
    try:
        _redis_game.ping()
    except Exception as data:
        main_logger.error("redis ping error: %s", str(data))


def share_redis_game() -> redis.StrictRedis:
    global _redis_game
    if not _redis_game:
        _redis_game = connect_redis()
    return _redis_game


def _hash_to_dict(data):
    result = dict()
    if not data:
        return result
    for k, v in list(data.items()):
        result[utils.bytes_to_str(k)] = utils.check_int(utils.bytes_to_str(v))
    return result


def get_all_configs():
    name = "all_system_configs"
    data = share_redis_game().hgetall(name)
    if not data:
        return dict()
    return _hash_to_dict(data)


def incr_club_sub_floor_count(club_id, sub_floor):
    return share_redis_game().hincrby(club_id, sub_floor, 1)


def decr_club_sub_floor_count(club_id, sub_floor):
    return share_redis_game().hincrby(club_id, sub_floor, -1)


def remove_club_sub_floor_count(club_id, sub_floor):
    return share_redis_game().hset(club_id, sub_floor, 0)


def get_club_sub_floor_count(club_id, sub_floor):
    return share_redis_game().hget(club_id, sub_floor)


def incr_union_sub_floor_count(uinon_id, sub_floor):
    return share_redis_game().hincrby(uinon_id, sub_floor, 1)


def decr_union_sub_floor_count(uinon_id, sub_floor):
    return share_redis_game().hincrby(uinon_id, sub_floor, -1)


def remove_union_sub_floor_count(uinon_id, sub_floor):
    return share_redis_game().hset(uinon_id, sub_floor, 0)


def get_union_sub_floor_count(uinon_id, sub_floor):
    return share_redis_game().hget(uinon_id, sub_floor)


def spop_table_id():
    return share_redis_game().spop("table_id")


def sadd_table_id(table_id):
    return share_redis_game().sadd("table_id", table_id)


# =========================== 中心REDIS的结束 ===============================

def make_insert(table_name, params):
    insert_list = []
    for k, v in params.items():
        insert_list.append("`{0}`='{1}'".format(k, v))
    sql = "INSERT INTO `{0}` SET " + ",".join(insert_list)
    sql = sql.format(table_name)
    return sql


def split_to_list(string_data):
    if not string_data:
        return []
    tmp = string_data.split(',')
    ret = []
    for item in tmp:
        ret.append(utils.str_to_int(item))
    return ret


if __name__ == '__main__':
    time.sleep(1)
    keep_connect()
