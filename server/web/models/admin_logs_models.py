from . import database
from . import table_name
from utils import utils


def add(db, params):
    if not db:
        return 0
    database.escape_dict(params)
    cols = ("admin_id", "admin_username", "refer_id", "type", "action")
    sql = "INSERT INTO `%s` SET " % (table_name.admin_logs,)
    middle_sql = ''
    for k, v in params.items():
        if k not in cols:
            continue
        if database.is_string(v):
            if k == "action":
                v = v.replace("'", "\"")
            middle_sql += "%s='%s'," % (k, v)
        else:
            middle_sql += "%s='%d'," % (k, v)

    if not middle_sql:
        return 0

    middle_sql += "time='%d'" % utils.timestamp()
    sql = sql + middle_sql
    try:
        count = db.execute(sql)
    except Exception as data:
        print(data)
        return 0
    return count


def get_last_10(db):
    if not db:
        return 0
    sql = "SELECT * FROM `%s` ORDER BY ID DESC LIMIT 10" % table_name.admin_logs
    try:
        admin_logs = db.query(sql)
    except Exception as data:
        print(data)
        return None
    return admin_logs
