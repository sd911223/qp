from models import table_name
from utils import utils


def add_share_logs_count(conn, unionid, logs_type=2, amount=0):
    if not conn or not unionid:
        return 0
    sql = "INSERT INTO `{0}` SET union_id='{1}',type={2},time={3},amount={4}". \
        format(table_name.share_logs, unionid, logs_type, utils.timestamp(), amount)
    return conn.execute(sql)
