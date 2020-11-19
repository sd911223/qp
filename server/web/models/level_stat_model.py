from models import table_name


def get_active_uids(conn, start_time):
    if not conn or not start_time:
        return []
    sql = "SELECT uid,reg_time FROM `{0}` WHERE login_time>={1}".format(table_name.players, start_time)
    return conn.query(sql)


def get_room_count(conn_logs, uid, start_time):
    if not conn_logs or not uid or not start_time:
        return []
    sql = 'SELECT count(1) AS count FROM {0} WHERE ' \
          '`uid1`={1} or `uid2`={1} or `uid3`={1} or `uid4`={1} or `uid5`={1} or `uid6`={1} ' \
          'or `uid7`={1} or `uid8`={1} or `uid9`={1} or `uid10`={1}'.format(table_name.room_logs, uid,
                                                                                    start_time)
    data = conn_logs.get(sql)
    if not data:
        return 0
    return data.get("count", 0)


def get_all_level_conf(conn):
    if not conn:
        return []
    sql = 'SELECT * FROM {0} ORDER BY round_count DESC'.format(table_name.level_ip)
    return conn.query(sql)


def get_ips_by_level(conn, level):
    sql = 'SELECT ips FROM {0} WHERE level={1}'.format(table_name.level_ip, level)
    return conn.get(sql)


def update_user_level(conn, uid, level):
    sql = "UPDATE `{0}` SET level = {1} WHERE uid = {2} and level < {1} LIMIT 1".format(table_name.players, level, uid)
    return conn.execute_rowcount(sql)
