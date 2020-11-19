# coding:utf-8

from utils import utils
from models import table_name


def add_agent_logs(conn, uid, ref_uid, order_id, money, current_money, level_type):
    if not uid or uid <= 0 or not conn:
        return 0
    sql = "INSERT INTO `%s` SET uid=%d,ref_user_id=%d,ref_order_id=%d,money=%f,current_money=%f,`type`=%d,time=%d" % \
          (table_name.agent_logs, uid, ref_uid, order_id, money, current_money, level_type, utils.timestamp())
    return conn.execute(sql)
