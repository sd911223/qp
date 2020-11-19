from models import database
from models import table_name
from utils import utils


def get(conn, uid):
    if not conn or uid <= 0:
        return {}
    sql = "SELECT * FROM `{0}` WHERE uid='{1}' LIMIT 1".format(table_name.online, uid)
    return conn.get(sql)


def clear_tid(conn, uid, tid):
    if not conn or not uid or not tid:
        return 0
    sql = "UPDATE `{0}` SET tid=0 WHERE uid={1} AND tid={2} LIMIT 1".format(table_name.online, uid, tid)
    return conn.execute_rowcount(sql)


def get_token(conn, uid):
    data = get(conn, uid)
    if not data:
        return ''
    return data.get('token')


def get_by_token(conn, token):
    if not conn or not token:
        return {}
    token = database.escape(token)
    sql = "SELECT * FROM `{0}` WHERE token='{1}' LIMIT 1".format(table_name.online, token)
    return conn.get(sql)

def get_by_tid(conn, tid):
    if not conn or not tid:
        return {}
    sql = "SELECT uid FROM `{0}` WHERE tid={1} LIMIT 1".format(table_name.online, tid)
    return conn.query(sql)

def insert(conn, uid):
    if not conn or uid <= 0:
        return {}

    inserts = dict()
    inserts['uid'] = int(uid)
    inserts['token'] = utils.random_string(40)
    inserts['login_time'] = utils.timestamp()

    insert_list = []
    for k, v in inserts.items():
        insert_list.append("{0}='{1}'".format(k, v))
    sql = "INSERT INTO `{0}` SET " + ",".join(insert_list)
    sql = sql.format(table_name.online)
    conn.execute(sql)
    return inserts


def fresh_online(conn, uid):
    if not conn or not uid:
        return 0
    time = utils.timestamp()
    sql = "UPDATE `{0}` SET login_time={1} WHERE uid={2} LIMIT 1".format(table_name.online, time, uid)
    return conn.execute_rowcount(sql)
