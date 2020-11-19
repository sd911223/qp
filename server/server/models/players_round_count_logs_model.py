# coding:utf-8

from utils import utils
from .database import share_db_logs
from models import table_name


def insert_round_count(uid, round_count=1):
    if not uid or not round_count:
        return 0
    sql = "INSERT INTO `{0}` SET uid={1},round_count={2},time={3}".format(table_name.players_round_count_logs, uid,
                                                                          round_count, utils.timestamp())
    return share_db_logs().execute_rowcount(sql)
