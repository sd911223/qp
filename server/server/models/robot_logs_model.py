# coding:utf-8

from models import table_name
from models.database import share_db_logs
from utils import utils


def insert(robot_id, group_id, red_packet_count=0, message_count=0, open_room_count=0):
    update_time = utils.timestamp()
    sql = "INSERT INTO {0} (wx_id,group_id,time,red_packet_count,message_count,open_room_count) " \
          "VALUES ('{1}', '{2}', {3},{4}, {5},{6})" \
        .format(table_name.robot_logs, robot_id, group_id, update_time, red_packet_count, message_count,
                open_room_count)
    return share_db_logs().execute_rowcount(sql)


def get_total_round_by_day_and_group_id(start_time, end_time, group_id):
    sql = "SELECT SUM(open_room_count) AS count FROM robot_logs WHERE time>={0} AND time<={1} AND group_id='{2}'". \
        format(start_time, end_time, group_id)
    return share_db_logs().get(sql)
