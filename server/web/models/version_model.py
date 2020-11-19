# coding:utf-8

from .table_name import versions


def get_versions(db, platform, channel_id):
    if not db or channel_id <= 0 or platform <= 0:
        return
    sql = "SELECT * FROM `{0}` WHERE platform={1} AND (channel_id={2} OR channel_id=0)"
    sql = sql.format(versions, int(platform), int(channel_id))
    return db.query(sql)


def get_all_versions(db):
    """后台端使用"""
    sql = "SELECT * FROM `{0}`"
    sql = sql.format(versions)
    return db.query(sql)


def set_version(db, channel_id, platform, origin_version, version, update_url, desc, is_force):
    """ 关键字 desc 导致 MySQL 1064 错误 """
    sql = 'UPDATE `{0}` SET update_url="{1}",is_force={2},`desc`="{3}",`version`="{4}" ' \
          "WHERE channel_id={5} AND platform={6} AND version='{7}' LIMIT 1" \
        .format(versions, update_url, int(is_force), desc, version, int(channel_id), int(platform), origin_version)
    return db.execute_rowcount(sql)
