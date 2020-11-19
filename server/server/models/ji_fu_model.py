from .database import share_db
from models import table_name
from utils import utils


def finish_round(uid):
    """ 玩家完成邀请 """
    if not uid:
        return 0
    time = utils.timestamp()
    sql = "UPDATE `{0}` SET first_round=1, first_round_time={1} WHERE invitee={2} AND first_round=0 LIMIT 1". \
        format(table_name.ji_fu, time, uid)
    return share_db().execute_rowcount(sql)
