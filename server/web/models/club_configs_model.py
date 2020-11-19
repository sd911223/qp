# coding:utf-8

from . import table_name
from . import database


def get_all_config_items(db):
    # 从DB里面加载全局配置
    sql = 'SELECT * FROM {0}'.format(table_name.club_config)
    ret = db.query(sql)
    items = {}
    for item in ret:
        items[item.var] = item.value if not item.value.isdigit() else int(item.value)
    return items


# db里面的全局配置字典
_cfg_items = dict()


def _return_num_or_string(data):
    # 根据字符串的类型来返回不同的数据
    if isinstance(data, int):
        return data
    if data.isdigit():
        return int(data)
    return data


def get(db, key, not_in_cache=False):
    # 获得某个配置的值
    global _cfg_items
    if (len(_cfg_items) == 0) or not_in_cache:
        _cfg_items = get_all_config_items(db)
    if key in _cfg_items:
        return _return_num_or_string(_cfg_items.get(key))
    return ''


def set_config(conn, key, value):
    key, value = database.escape(key), database.escape(value)
    sql = "UPDATE `{0}` SET `value`='{1}' WHERE `var`='{2}' LIMIT 1". \
        format(table_name.club_config, value, key)
    return conn.execute_rowcount(sql)


def get_all_configs(db):
    # 代理管理使用
    sql = 'SELECT * FROM {0}'.format(table_name.club_config)
    return db.query(sql)


def get_all_level_configs(db):
    # 代理管理使用
    sql = 'SELECT * FROM {0}'.format(table_name.club_level_config)
    return db.query(sql)


def delete_level_config_by_level(db, level):
    sql = "DELETE FROM `{0}`  WHERE `level`='{1}' ". \
        format(table_name.club_level_config, level)
    return db.execute_rowcount(sql)


def modify_level_config(db, level, price, limit):
    sql = "UPDATE `{0}` SET `price`='{1}',`limit`='{2}' WHERE `level`='{3}' LIMIT 1". \
        format(table_name.club_level_config, price, limit, level)
    return db.execute_rowcount(sql)


def add_level_config(db, level, price, limit):
    sql = "INSERT INTO `{0}` SET `level`={1},`limit`={2},`price`={3}".format(table_name.club_level_config, level, limit,
                                                                             price)
    return db.execute_rowcount(sql)


def set_all_configs(db, params):
    # 代理管理使用
    if not db:
        return 0
    count = 0
    for k, v in params.items():
        sql = "UPDATE `{0}` SET value='{1}' WHERE var='{2}'".format(table_name.club_config, v, k)
        try:
            count += db.execute_rowcount(sql)
        except Exception as data:
            print(data)
            return 0
    return count


def get_announcement_timestamp(db):
    # 获取代理公告 & 游戏公告更新时间戳
    sql = 'SELECT * FROM {0} WHERE var in ("agent_notice_id_readonly","notice_id_readonly")' \
        .format(table_name.club_config)
    return db.query(sql)
