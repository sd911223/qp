from models import table_name


def get_room_config(conn, game_id):
    if not conn or not game_id:
        return 0
    sql = "SELECT * FROM `{0}` WHERE id={1} LIMIT 1 ".format(table_name.room_config, game_id)
    return conn.get(sql)
