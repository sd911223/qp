from models import database
from models import table_name
import re

STATUS_WAITING = 0
STATUS_PLAYING = 1


def get_by_uid(uid):
    sql = "SELECT * FROM `{0}` WHERE uid='{1}' LIMIT 1".format(table_name.onlines, uid)
    return database.share_db().get(sql)


def get_by_token(token):
    # 根据玩家的token值来获得在线记录
    if not token:
        return {}
    token = database.escape(token)
    sql = "SELECT * FROM `{0}` WHERE token='{1}' LIMIT 1".format(table_name.onlines, token)
    return database.share_db().get(sql)


def set_state_by_uid(state, uid):
    # 设置在线玩家状态
    if len(uid) > 0:
        uid = re.sub('\[|\]', '', str(uid))
        sql = "UPDATE `{0}` SET state={1} WHERE uid in ({2}) ".format(table_name.onlines, state, uid)
        return database.share_db().execute_rowcount(sql)


def set_tid(uid, tid):
    """设置玩家的在线表里面的tid"""
    sql = "UPDATE `{0}` SET tid='{1}' WHERE uid='{2}' LIMIT 1".format(table_name.onlines, tid, uid)
    return database.share_db().execute_rowcount(sql)


def insert_online_many(start, length):
    sql = "INSERT IGNORE INTO onlines (uid, token, login_time, tid) VALUES ({0}, '{1}', '{2}', 0)"
    for i in range(start, length):
        sql2 = sql.format(i, 'token' + str(i), 123)
        database.share_db().execute(sql2)
