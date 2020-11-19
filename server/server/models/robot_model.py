# coding:utf-8

from models import table_name
from models.database import share_db


# 获取机器人数据
def get(robot_id):
    sql = "SELECT * FROM `{0}` WHERE wx_id='{1}' ".format(table_name.robot, robot_id)
    return share_db().get(sql)


# 更新机器人数据
def update(wx_id, status, update_time):
    sql = "UPDATE {0} SET status={1},time={2} WHERE wx_id='{3}'".format(table_name.robot, status, update_time, wx_id)
    return share_db().execute_rowcount(sql)


# 插入机器人信息
def insert(wx_id, update_time):
    sql = "INSERT IGNORE INTO {0} (wx_id, status, time) " \
          "VALUES ('{1}', 1, {2} )"\
        .format(table_name.robot, wx_id, update_time)
    return share_db().execute_rowcount(sql)

