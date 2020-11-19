# coding:utf-8
import os
import sys
import time
sys.path.append('..')

from utils import utils
from .database import escape
from .table_name import denny_words


def insertMulti(DB, lists):
    if not lists:
        return 0
    sql = "INSERT IGNORE INTO %s (`word`) VALUES " % (denny_words, )
    for item in lists:
        sql += "('%s')," % (item.strip(), )
    sql = sql[0:-1]
    return DB.execute(sql)
