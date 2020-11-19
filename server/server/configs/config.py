# coding:utf-8

from base import const
from utils import utils


def _read_config_file():
    return utils.read_json_file(const.BASE_PATH + 'configs/configs.json')


def get_item(name):
    return _read_config_file().get(name)


# db main
def get_db_info(name):
    return _read_config_file().get(name)


# 获得游戏的redis的相关配置
def get_redis(redis_name="redis_game"):
    return _read_config_file().get(redis_name)


const.IS_DEBUG = get_item("is_debug")


def get_log_level():
    level = get_item("log_level") or "debug"
    return level.upper()

