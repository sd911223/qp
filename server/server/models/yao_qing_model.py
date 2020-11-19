from .database import share_db
from models import table_name


def finish_round(uid):
    """ 玩家完成邀请 """
    if not uid:
        return 0
    sql = "UPDATE `{0}` SET first_round=1 WHERE invitee={1} AND first_round=0 LIMIT 1". \
        format(table_name.yao_qing, uid)
    return share_db().execute_rowcount(sql)
