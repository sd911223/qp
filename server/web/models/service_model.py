def get_tables_by_status(conn, status):
    sql = f"SELECT a.tid,a.game_type,a.state,a.sid,a.time,b.version FROM tables AS a, server_rooms AS b " \
          f"WHERE a.game_type = b.game_type " \
          f"AND a.sid = b.sid " \
          f"AND b.status = {status}"
    return conn.query(sql)


def get_all_game_service(conn):
    sql = "SELECT * FROM server_rooms"
    return conn.query(sql)


def get_game_service_status_by_game_type_and_sid(conn, game_type, sid):
    sql = f"SELECT status,file_path,pid FROM server_rooms WHERE game_type={game_type} AND sid={sid}"
    return conn.get(sql)


def set_game_service_status_by_game_type_and_sid(conn, game_type, sid):
    sql = f"UPDATE `server_rooms` SET status=0 WHERE game_type={game_type} AND sid={sid}"
    return conn.execute_rowcount(sql)


def get_running_game_service_by_game_type(conn, game_type):
    sql = f"SELECT sid FROM server_rooms WHERE game_type={game_type} AND status=1 LIMIT 1"
    return conn.get(sql)


def modify_table_by_game_service_sid(conn, game_type, origin_sid, to_sid):
    sql = f"UPDATE `tables` SET sid={to_sid} WHERE game_type={game_type} AND sid={origin_sid}"
    return conn.execute_rowcount(sql)


def remove_table_by_game_service_sid(conn, game_type, sid):
    sql = f"DELETE FROM `tables` WHERE game_type='{game_type}' AND sid={sid}"
    return conn.execute_rowcount(sql)
