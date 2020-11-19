from models import table_name
from utils import utils

WITHDRAW_NOT_ENOUGH_MONEY = -3
WITHDRAW_OFFICAL_REJECT = -2
WITHDRAW_USER_CANCEL = -1
WITHDRAW_NEED_CHECK = 0
WITHDRAW_PROCESS = 1
WITHDRAW_OK = 2


def __set_withdraw(conn, mid, status):
    if not conn or not mid:
        return 0
    sql = "UPDATE `{0}` SET status={1} WHERE id={2} and status=0 LIMIT 1".format(table_name.verify_withdraw, status,
                                                                                 mid)
    return conn.execute_rowcount(sql)


def deny_money_withdraw(conn, mid):
    __set_withdraw(conn, mid, WITHDRAW_NOT_ENOUGH_MONEY)


def deny_withdraw(conn, mid):
    __set_withdraw(conn, mid, WITHDRAW_OFFICAL_REJECT)


def allow_withdraw(conn, mid):
    # TODO : 待接入支付流程
    __set_withdraw(conn, mid, WITHDRAW_OK)


def get_withdraw_by_id(conn, mid):
    if not conn or not mid:
        return 0
    sql = "SELECT * FROM `{0}` WHERE id={1} LIMIT 1".format(table_name.verify_withdraw, mid)
    return conn.get(sql)


# TODO : 分页
def get_by_opts(conn, opts):
    if not conn:
        return [None, None]
    sql = "select a.id,a.uid,a.nick_name,a.money,a.time,a.status,b.bank from `{0}` as a,`{1}`" \
          " as b where a.uid = b.uid ".format(table_name.verify_withdraw, table_name.players)
    for k, v in opts.items():
        if k is 'uid':
            sql += " AND a.uid = {0} ".format(v)
        elif k is 'status':
            sql += " AND a.status = '{0}' ".format(v)
        elif k is 'start_time':
            sql += " AND a.time >= {0} ".format(v)
        elif k is 'end_time':
            sql += " AND a.time <= {0} ".format(v)
    sql += " ORDER BY time DESC LIMIT 0,10"
    return conn.query(sql)


# ----------------------

def add_withdraw(conn, uid, money, refer_uid):
    if not conn:
        return 0
    sql = f'INSERT INTO `withdraw` SET refer_uid={uid},uid={refer_uid},money={money},time={utils.timestamp()}'
    return conn.execute(sql)


def query_withdraw_admin_count(conn):
    sql = 'SELECT count(1) as count FROM `withdraw`'
    return conn.get(sql)


def query_withdraw_admin(conn, page):
    per_page_count = 30
    sql = f'SELECT * FROM `withdraw` ORDER BY status,time desc LIMIT {(page - 1) * per_page_count},{per_page_count}'
    return conn.query(sql)


def query_withdraw_count(conn, uid):
    sql = f'SELECT count(1) as count FROM `withdraw` WHERE uid={uid}'
    return conn.get(sql)


def query_withdraw(conn, page, uid):
    per_page_count = 30
    sql = f'SELECT * FROM `withdraw` WHERE refer_uid={uid} ORDER BY status,time desc LIMIT {(page - 1) * per_page_count},' \
          f'{per_page_count}'
    return conn.query(sql)


def modify_withdraw(conn, wid, admin_id):
    sql = f'UPDATE withdraw set status=1,admin_id={admin_id},accept_time={utils.timestamp()} where id={wid}'
    return conn.execute(sql)


def get_withdraw_by_wid(conn, wid):
    sql = f'SELECT * FROM `withdraw` where id ={wid}'
    return conn.get(sql)
