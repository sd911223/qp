# coding:utf-8
import os
import sys
import time

from utils import utils
from .database import escape
from .table_name import iap_ticket, pay_iap

sys.path.append('..')


def saveRawData(DB, pid, ticket):
    # 保存IAP原始电子凭证
    sql = "INSERT INTO %s SET pid=%d,ticket='%s'"
    sql = sql % (pay_iap, pid, ticket)
    return DB.execute_rowcount(sql)

# 保存IAP电子凭证


def save(DB, uid, stype, ticket_id, ticket):
    sql = "INSERT INTO %s SET uid=%d,stype=%d,time='%d',ticket='%s',ticket_id='%s' \
        ON DUPLICATE KEY UPDATE time='%d'"
    seconds = utils.timestamp()
    sql = sql % (iap_ticket, uid, stype, seconds, escape(
        ticket), escape(str(ticket_id)), seconds)
    return DB.execute_rowcount(sql)

# 获得某订单的情况


def get(DB, ticket_id):
    sql = "SELECT * FROM %s WHERE ticket_id='%s' LIMIT 1"
    sql = sql % (iap_ticket, escape(str(ticket_id)))
    return DB.get(sql)

# 更新订单状态


def updateStatus(DB, ticket_id, status):
    sql = "UPDATE `%s` SET status='%d' WHERE ticket_id='%s' and status=0 LIMIT 1"
    sql = sql % (iap_ticket, status, escape(ticket_id))
    return DB.execute_rowcount(sql)
