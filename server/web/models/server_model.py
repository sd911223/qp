import random
from models import table_name


def pick_one(conn, game_type):
    if not game_type:
        return 0
    sql = "SELECT sid FROM `{0}` WHERE game_type={1} AND status=1 LIMIT 10". \
        format(table_name.server_rooms, game_type)
    result = conn.query(sql)
    if not result:
        return 0
    server = result[random.randrange(0, len(result))]
    return int(server.get('sid', 0))


def get(conn, sid):
    sql = "SELECT * FROM `{0}` WHERE sid='{1}' LIMIT 1".format(table_name.servers, int(sid))
    server = conn.get(sql)
    return server.get('IP'), int(server.get('port'))


def pick_one_gateway(conn):
    sql = f"SELECT ip,port FROM `servers` WHERE status=1"
    result = conn.query(sql)
    if not result:
        return 0, 0
    server = result[random.randrange(0, len(result))]
    return server['ip'], int(server['port'])
