# coding:utf-8

from models import table_name
from models.database import share_db


# 获取群信息
def get(robot_id, group_id):
    sql = "SELECT * FROM `{0}` WHERE robot_id='{1}' AND group_id='{2}' "\
        .format(table_name.robot_group, robot_id, group_id)
    return share_db().get(sql)


# 插入群信息
def insert(group_id, wx_id, robot_id, update_time):
    sql = "INSERT IGNORE INTO {0} (group_id, wx_id, robot_id, time) " \
          "VALUES ('{1}', '{2}', '{3}', {4} )"\
        .format(table_name.robot_group, group_id, wx_id, robot_id, update_time)
    return share_db().execute_rowcount(sql)


# 更新群信息
def update(group_id, robot_id, update_time):
    sql = "UPDATE {0} SET time={1} WHERE robot_id='{2}' AND group_id='{3}'"\
        .format(table_name.robot_group, update_time, robot_id, group_id)
    return share_db().execute_rowcount(sql)
