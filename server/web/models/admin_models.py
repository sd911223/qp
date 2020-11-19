from . import database
from . import table_name


def _make_admin_data(row):
    if not row:
        return None
    row['powers'] = database.split_to_list(row.powers)
    return row


def get_by_id(conn, admin_id):
    if not conn:
        return {}
    sql = "SELECT * FROM `{0}` WHERE id={1} LIMIT 1".format(table_name.admins, admin_id)
    return _make_admin_data(conn.get(sql))


def get(conn, name):
    if not conn or not name:
        return {}
    name = database.escape(name)
    sql = "SELECT * FROM `{0}` WHERE name='{1}' LIMIT 1".format(table_name.admins, name)
    return _make_admin_data(conn.get(sql))


def get_by_wx_username(conn, wx_username):
    if not conn or not wx_username:
        return {}
    wx_id = database.escape(wx_username)
    sql = "SELECT * FROM `{0}` WHERE wx_username='{1}' LIMIT 1".format(table_name.admins, wx_id)
    return _make_admin_data(conn.get(sql))


def get_all(conn):
    if not conn:
        return {}
    sql = "SELECT * FROM `{0}` WHERE 1 LIMIT 200".format(table_name.admins, )
    ret = []
    rows = conn.query(sql)
    for row in rows:
        ret.append(_make_admin_data(row))
    return ret


def modify_password(db, name, password):
    if not db or not name:
        return 0
    password = database.escape(password)
    sql = "UPDATE `%s` SET password='%s' WHERE name='%s' LIMIT 1" % \
          (table_name.admins, password, database.escape(name))
    return db.execute_rowcount(sql)


def modify_powers(db, name, powers):
    if not db or not name:
        return 0
    powers = database.escape(powers)
    sql = "UPDATE `%s` SET powers='%s' WHERE name='%s' LIMIT 1" % \
          (table_name.admins, powers, database.escape(name))
    return db.execute_rowcount(sql)


def modify_status(db, name, status):
    if not db or not name:
        return 0
    sql = "UPDATE `%s` SET status=%d WHERE name='%s' LIMIT 1" % \
          (table_name.admins, status, database.escape(name))
    return db.execute_rowcount(sql)


def add(db, params):  # 添加管理员函数
    if not db:
        return 0
    database.escape_dict(params)
    cols = ("name", "password", "powers")
    sql = "INSERT INTO `%s` SET " % (table_name.admins,)
    middle_sql = ''
    for k, v in params.items():
        if k not in cols:
            continue
        if database.is_string(v):
            middle_sql += "%s='%s'," % (k, v)
        else:
            middle_sql += "%s='%d'," % (k, v)

    if not middle_sql:
        return 0
    middle_sql = middle_sql[0:-1]
    sql = sql + middle_sql
    try:
        count = db.execute(sql)
    except Exception as data:
        print(data)
        return 0
    return count
