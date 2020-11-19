# coding:utf-8

from .database import share_db
from .table_name import configs as _config


# 从DB里面加载全局配置
def get_all_config_items():
    sql = 'SELECT * FROM {0}'.format(_config)
    ret = share_db().query(sql)
    items = {}
    for item in ret:
        items[item.var] = item.value
    return items


# db里面的全局配置字典
_cfg_items = {}


# 根据字符串的类型来返回不同的数据
def _return_num_or_string(data):
    if data.isdigit():
        return int(data)
    return data


# 获得某个配置的值
def get(key, not_in_cache=False):
    global _cfg_items
    if (len(_cfg_items) == 0) or not_in_cache:
        _cfg_items = get_all_config_items()
    if key in _cfg_items:
        return _return_num_or_string(_cfg_items[key])
    return ''
