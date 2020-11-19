from models import table_name


def get_all_config(conn):
    if not conn:
        return {}
    sql = "SELECT * FROM `{0}`".format(table_name.agent_config)
    return conn.query(sql)


def get_config_by_key(conn, key):
    if not conn or not key:
        return {}
    sql = "SELECT * FROM `{0}` WHERE var='{1}' LIMIT 1".format(table_name.agent_config, key)
    return conn.get(sql)


def set_config(conn, key, value):
    if not conn or not key or not value:
        return 0
    sql = "UPDATE `{0}` SET value=`{1}` WHERE var=`{2}` LIMIT 1".format(table_name.agent_config, value, key)
    return conn.execute_rowcount(sql)


def set_all_configs(db, params):
    # 代理管理使用
    if not db:
        return 0
    count = 0
    for k, v in params.items():
        sql = "UPDATE `{0}` SET value='{1}' WHERE var='{2}'".format(table_name.agent_config, v, k)
        try:
            count += db.execute_rowcount(sql)
        except Exception as data:
            print(data)
            return 0
    return count
