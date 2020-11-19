# coding:utf-8

from utils import utils
from models import table_name

BUY_CARD = 1
GET_CASH = 2
GIVE_CARD = 3
SET_AGENT = 4


def add_get_cash_logs(conn, uid, ref_uid, money, card_count, current_money, logs_type=GET_CASH):
    if not uid or uid <= 0 or not conn:
        return 0
    status = 1
    sql = "INSERT INTO `%s` SET uid=%d,ref_uid=%d,`type`=%d,money=%f,card_count=%f,status=%d,`time`=%d," \
          "current_money=%f" % \
          (table_name.agent_operation_logs, uid, ref_uid, logs_type, money, card_count, status, utils.timestamp(),
           current_money)
    return conn.execute(sql)
