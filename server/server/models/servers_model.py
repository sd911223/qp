# coding:utf-8

import random
from utils import utils
from models import table_name
from models.database import share_db


# 获得服务器数据
def get(server_id):
    sql = "SELECT * FROM `{0}` WHERE sid='{1}' ".format(table_name.servers, server_id)
    return share_db().get(sql)


def get_room(sid, game_type):  # 获得服务器数据
    sql = "SELECT * FROM `{0}` WHERE sid='{1}' AND game_type='{2}' LIMIT 1". \
        format(table_name.server_rooms, int(sid), int(game_type))
    return share_db().get(sql)


def get_idle_room(sid, game_type):  # 获得服务器数据
    sql = "SELECT * FROM `{0}` WHERE sid='{1}' AND game_type='{2}' AND status=0 LIMIT 1". \
        format(table_name.server_rooms, int(sid), int(game_type))
    return share_db().get(sql)


def update_status(sid, status):
    if not sid:
        return 0
    sql = "UPDATE `{0}` SET status='{1}' WHERE sid='{2}' LIMIT 1".format(table_name.servers, status, int(sid))
    return share_db().execute_rowcount(sql)


def set_room_status(server_id, from_status, status, game_type, pid=0, version=""):
    if not server_id or not game_type:
        return 0
    if from_status is None:
        sql = "UPDATE `{0}` SET status='{1}',pid='{2}' WHERE sid='{3}' AND game_type='{4}' LIMIT 1". \
            format(table_name.server_rooms, status, pid, int(server_id), int(game_type))
    else:
        sql = "UPDATE `{0}` SET status='{1}',pid='{2}',version='{3}' WHERE sid='{4}' AND status='{5}' " \
              "AND game_type='{6}' LIMIT 1". \
            format(table_name.server_rooms, status, pid, version, int(server_id), int(from_status), int(game_type))
    return share_db().execute_rowcount(sql)


def set_room_start(server_id, game_type, pid, version):
    return set_room_status(server_id, 0, 1, game_type, pid, version)


def set_room_stop(server_id, game_type, pid):
    return set_room_status(server_id, None, 2, game_type, pid)


def set_room_shutdown(server_id, game_type):
    return set_room_status(server_id, None, 0, game_type)


def choose_idle_server(game_type):
    sql = f"SELECT * FROM `server_rooms` WHERE game_type={game_type} AND status=0"
    result = share_db().query(sql)
    if not result:
        return 0
    server = result[random.randrange(0, len(result))]
    return server['sid']


def pick_one_idle_gateway():
    sql = f"SELECT sid FROM `servers` WHERE status=0"
    result = share_db().query(sql)
    if not result:
        return 0
    server = result[random.randrange(0, len(result))]
    return server['sid']


def all_gate_shutdown():
    sql = "UPDATE `{0}` SET status=0".format(table_name.servers)
    return share_db().execute_rowcount(sql)


def all_server_shutdown():
    sql = "UPDATE `{0}` SET status=0".format(table_name.server_rooms)
    return share_db().execute_rowcount(sql)


def update_ack_time(sid, game_type):
    sql = "UPDATE `{0}` SET ack_time={1} WHERE sid={2} AND game_type={3} AND status={4}".format(
        table_name.server_rooms, utils.timestamp(), sid, game_type, 1)
    return share_db().execute_rowcount(sql)
