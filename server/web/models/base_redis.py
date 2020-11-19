import redis
import ujson as json

from configs import config
from utils import utils

_seconds = 120  # 语音超时的秒数
_connect = None  # 共享的redis连接对象


def connect(redis_name='redis'):
    try:
        redis_info = config.get_by_key(redis_name)  # redis的数据
        return redis.StrictRedis(**redis_info)
    except Exception as data:
        print("Please set config of ", redis_name, data)


def share_connect() -> redis.StrictRedis:
    global _connect
    if not _connect:
        _connect = connect("redis")
    return _connect


def save(key, value):
    share_connect().set(key, value, ex=_seconds)


def save_with_time(key, value, time=3600):
    share_connect().set(key, value, ex=time)


def fetch(key):
    return share_connect().get(key)


def add_to_set(key, values):
    return share_connect().sadd(key, values)


def pop_from_set(key):
    return share_connect().spop(key)


def _hash_to_dict(data):
    result = dict()
    if not data:
        return result
    for k, v in list(data.items()):
        result[utils.bytes_to_str(k)] = utils.check_int(utils.bytes_to_str(v))
    return result


def get_all_configs():
    name = "all_system_configs"
    data = share_connect().hgetall(name)
    if not data:
        return dict()
    return _hash_to_dict(data)


def set_configs_multi(configs):
    name = "all_system_configs"
    return share_connect().hmset(name, configs)
    # return share_connect().hset(name, 1, 2)


def set_lottery_configs(configs):
    name = "lottery_configs"
    return save_with_time(name, json.dumps(configs), 7200)


def get_lottery_configs():
    name = "lottery_configs"
    return fetch(name)


def save_sign(sign, expired=1800):
    name = "sign:" + sign
    return share_connect().setex(name, expired, 1)


def get_sign_exist(sign):
    name = "sign:" + sign
    result = share_connect().get(name)
    return utils.str_to_int(utils.bytes_to_str(result)) > 0


def save_exception(data, max_nums=1000):
    key = "client_exceptions"
    share_connect().lpush(key, data)
    share_connect().ltrim(key, 0, max_nums)


def get_all_exception(max_nums=1000):
    key = "client_exceptions"
    return share_connect().lrange(key, 0, max_nums)


def remove_all_exception():
    key = "client_exceptions"
    return share_connect().ltrim(key, 0, 0)


def get_all_play_details():
    key = "round_review_logs"
    return share_connect().lrange(key, 0, -1)


def get_100_play_details():
    key = "round_review_logs"
    return share_connect().lrange(key, -100, -1)


def delete_play_detail(value):
    key = "round_review_logs"
    return share_connect().lrem(key, 1, value)


def get_login_info(ip):
    if not ip:
        return
    name = "al:{0}".format(ip)
    data = share_connect().hgetall(name)
    return _hash_to_dict(data)


def set_login_try_count(ip, count):
    if not ip:
        return
    name = "al:{0}".format(ip)
    share_connect().hmset(name, {"count": count, "time": utils.timestamp()})
    return share_connect().expire(name, 2 * 60 * 60)


def incr_club_sub_floor_count(club_id, sub_floor):
    return share_connect().hincrby(club_id, sub_floor, 1)


def decr_club_sub_floor_count(club_id, sub_floor):
    return share_connect().hincrby(club_id, sub_floor, -1)


def remove_club_sub_floor_count(club_id, sub_floor):
    return share_connect().hset(club_id, sub_floor, 0)


def remove_union_sub_floor_count(union_id, sub_floor):
    return share_connect().hset(f"union:{union_id}", sub_floor, 0)


def get_club_sub_floor_count(club_id, sub_floor):
    return share_connect().hget(club_id, sub_floor)


def spop_table_id():
    return share_connect().spop("table_id")


def sadd_table_id(table_id):
    return share_connect().sadd("table_id", table_id)
