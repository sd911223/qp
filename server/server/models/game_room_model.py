def _get_running_sid_by_game_type(conn, game_type):
    sql = f"SELECT sid FROM `server_rooms` WHERE game_type={game_type} and status=1"
    return conn.query(sql)


def _get_server_sid_from_redis(redis_conn, game_type, servers):
    rooms = {}

    for i in servers:
        count = redis_conn.get(f"table:{game_type}:{i['sid']}")
        count = 0 if not count else count.decode('utf-8')
        rooms[i['sid']] = int(count)

    max_desk = 1000000
    default_sid = 1
    for key in rooms:
        if rooms[key] <= max_desk:
            default_sid = key
            max_desk = rooms[key]

    return default_sid


def get_best_server_sid(conn, redis_conn, game_type):
    server = _get_running_sid_by_game_type(conn, game_type)
    if not server:
        return 0
    if len(server) == 1:
        return server[0]['sid']
    return _get_server_sid_from_redis(redis_conn, game_type, server)
