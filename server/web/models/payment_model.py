# coding:utf-8

from utils import utils
from . import database
from models import table_name


def add_order(conn, uid, params):  # 添加订单
    if not uid or uid <= 0:
        return 0
    amount = params.get('amount', 0) or 0
    order_time = utils.timestamp()
    sql = "INSERT INTO `%s` SET uid=%d,order_time=%d,amount='%d'," % \
          (table_name.payment, uid, order_time, amount)
    int_vars = {
        'game_id': int(params['game_id']),
        'channel_id': int(params['channel_id']),
        'pay_method': int(params['pay_method']),
        'coins': int(params['coins']) if params.get('coins') else 0,
        'diamonds': int(params['diamonds']) if params.get('diamonds') else 0,
        'admin_id': int(params['admin_id']),
        # '' : int(params['']),
    }
    str_vars = {
        'billing_number': database.escape(params['billing_number']) if params.get('billing_number') else "",
        'ip': database.escape(params['ip']) if params.get('ip') else "",
        'nick_name': database.escape(params.get('nick_name', '')),
        'admin_name': database.escape(params.get('admin_name')),
        'memo': database.escape(params.get('memo')),
    }
    for k, v in list(int_vars.items()):
        sql += "%s='%d'," % (k, v)

    for k, v in list(str_vars.items()):
        sql += "%s='%s'," % (k, v)

    sql = sql[0:-1]
    return conn.execute(sql)


def edit_order(conn, pid, params):  # 修改订单数据
    if 0 >= pid:
        return 0

    sql = "UPDATE `%s` SET " % (table_name.payment,)
    flag = False
    if params.get('amount') and params['amount'] > 0:
        flag = True
        sql += "amount='%d'," % (params['amount'],)

    # 可修改的int型字段
    int_vars = (
        'game_id',
        'channel_id',
        'pay_method',
        'coins',
        'diamonds'
    )
    # 可修改的string型字段
    str_vars = ('billing_number', 'ip')

    for k, v in list(params.items()):
        if k in int_vars:
            flag = True
            sql += "%s='%d'," % (k, v)
        elif k in str_vars:
            flag = True
            sql += "%s='%s'," % (k, database.escape(v))

    if not flag:
        return 0

    sql = sql[0:-1]
    return conn.execute(sql)


def get_last_payments(conn, number=20):
    sql = "SELECT * FROM `%s` ORDER BY pid DESC LIMIT %d" % (table_name.payment, number)
    return conn.query(sql)


def get(conn, pid):  # 查询订单
    sql = "SELECT * FROM `%s` WHERE pid='%d' LIMIT 1" % (table_name.payment, pid)
    return conn.get(sql)


def get_by_opts_with_limit(conn, opts, uid=-1):
    if not conn:
        return [None, None]
    per_page_count = 15
    page = opts['page']
    sql = "SELECT payment.* FROM `{0}`,`{1}` WHERE 1=1 ".format(table_name.payment, table_name.players)
    for k, v in opts.items():
        if k is 'uid':
            sql += " AND {0}.{1} = {2} ".format(table_name.payment, k, v)
        elif k is 'admin_name':
            sql += " AND {0} = '{1}' ".format(k, v)
        elif k is 'diamond_min':
            sql += " AND diamonds >= {0} ".format(v)
        elif k is 'diamond_max':
            sql += " AND diamonds <= {0} ".format(v)
        elif k is 'payment_min':
            sql += " AND amount >= {0} ".format(v)
        elif k is 'payment_max':
            sql += " AND amount <= {0} ".format(v)
        elif k is 'start_time':
            sql += " AND order_time >= {0} ".format(v)
        elif k is 'end_time':
            sql += " AND order_time <= {0} ".format(v)
        elif k is 'phone':
            sql += " AND players.phone like '%%{0}%%' ".format(v)
    if uid != -1:
        sql += " AND base_refer_uid = {0} ".format(uid)
    sql += " AND {0}.uid = {1}.uid ORDER BY order_time DESC LIMIT {2},{3}".format(table_name.payment,
                                                                                  table_name.players,
                                                                                  (page - 1) * per_page_count,
                                                                                  per_page_count)
    return conn.query(sql)


def get_by_opts(conn, opts):
    if not conn:
        return [None, None]
    sql = "SELECT payment.* FROM `{0}`,`{1}` WHERE 1=1 ".format(table_name.payment, table_name.players)
    for k, v in opts.items():
        if k is 'uid':
            sql += " AND {0}.{1} = {2} ".format(table_name.payment, k, v)
        elif k is 'admin_name':
            sql += " AND {0} = '{1}' ".format(k, v)
        elif k is 'diamond_min':
            sql += " AND diamonds >= {0} ".format(v)
        elif k is 'diamond_max':
            sql += " AND diamonds <= {0} ".format(v)
        elif k is 'payment_min':
            sql += " AND amount >= {0} ".format(v)
        elif k is 'payment_max':
            sql += " AND amount <= {0} ".format(v)
        elif k is 'start_time':
            sql += " AND order_time >= {0} ".format(v)
        elif k is 'end_time':
            sql += " AND order_time <= {0} ".format(v)
        elif k is 'phone':
            sql += " AND players.phone like '%%{0}%%' ".format(v)
    sql += " AND {0}.uid = {1}.uid ORDER BY order_time DESC".format(table_name.payment, table_name.players)
    return conn.query(sql)


def get_consume_rank_by_day(conn, start_time, end_time):
    sql = "select a.uid,sum(a.diamonds) as diamond,b.agent as agent,b.phone as phone,b.nick_name as nick_name " \
          "from game.{0} as b,game_logs.{1} as a where a.uid = b.uid " \
          "and reason_id = 10 and a.time >= {2} and a.time <= {3} group by a.uid order by diamond" \
          " desc limit 20".format(table_name.players, table_name.diamond_logs, start_time, end_time)
    return conn.query(sql)


def get_consume_rank_by_week(conn, start_time, end_time):
    sql = "select a.uid,sum(a.diamonds) as diamond,b.agent as agent,b.phone as phone,b.nick_name as nick_name " \
          "from game.{0} as b,game_logs.{1} as a where a.uid = b.uid " \
          "and reason_id = 10 and a.time >= {2} and a.time <= {3} group by a.uid order by diamond" \
          " desc limit 20".format(table_name.players, table_name.diamond_logs, start_time, end_time)
    return conn.query(sql)


def get_consume_rank_by_month(conn, start_time, end_time):
    sql = "select a.uid,sum(a.diamonds) as diamond,b.agent as agent,b.phone as phone,b.nick_name as nick_name " \
          "from game.{0} as b,game_logs.{1} as a where a.uid = b.uid " \
          "and reason_id = 10 and a.time >= {2} and a.time <= {3} group by a.uid order by diamond" \
          " desc limit 20".format(table_name.players, table_name.diamond_logs, start_time, end_time)
    return conn.query(sql)


def get_total_payment_by_opts(conn, opts, uid=-1):
    sql = "SELECT sum(payment.amount) as amount FROM `{0}`,`{1}` WHERE 1=1 ".format(table_name.payment,
                                                                                    table_name.players)
    for k, v in opts.items():
        if k is 'uid':
            sql += " AND {0}.{1} = {2} ".format(table_name.payment, k, v)
        elif k is 'admin_name':
            sql += " AND {0} = '{1}' ".format(k, v)
        elif k is 'diamond_min':
            sql += " AND diamonds >= {0} ".format(v)
        elif k is 'diamond_max':
            sql += " AND diamonds <= {0} ".format(v)
        elif k is 'payment_min':
            sql += " AND amount >= {0} ".format(v)
        elif k is 'payment_max':
            sql += " AND amount <= {0} ".format(v)
        elif k is 'start_time':
            sql += " AND order_time >= {0} ".format(v)
        elif k is 'end_time':
            sql += " AND order_time <= {0} ".format(v)
        elif k is 'phone':
            sql += " AND players.phone like '%%{0}%%' ".format(v)
    if uid != -1:
        sql += " AND base_refer_uid = {0} ".format(uid)
    sql += " AND {0}.uid = {1}.uid".format(table_name.payment, table_name.players)
    return conn.get(sql)


def get_total_payment_player_count_by_opts(conn, opts, uid=-1):
    sql = "SELECT count(DISTINCT payment.uid) as count FROM `{0}`,`{1}` WHERE 1=1 ".format(table_name.payment,
                                                                                           table_name.players)
    for k, v in opts.items():
        if k is 'uid':
            sql += " AND {0}.{1} = {2} ".format(table_name.payment, k, v)
        elif k is 'admin_name':
            sql += " AND {0} = '{1}' ".format(k, v)
        elif k is 'diamond_min':
            sql += " AND diamonds >= {0} ".format(v)
        elif k is 'diamond_max':
            sql += " AND diamonds <= {0} ".format(v)
        elif k is 'payment_min':
            sql += " AND amount >= {0} ".format(v)
        elif k is 'payment_max':
            sql += " AND amount <= {0} ".format(v)
        elif k is 'start_time':
            sql += " AND order_time >= {0} ".format(v)
        elif k is 'end_time':
            sql += " AND order_time <= {0} ".format(v)
        elif k is 'phone':
            sql += " AND players.phone like '%%{0}%%' ".format(v)
    if uid != -1:
        sql += " AND base_refer_uid = {0} ".format(uid)
    sql += " AND {0}.uid = {1}.uid".format(table_name.payment, table_name.players)
    data = conn.get(sql)
    if data:
        return data['count']
    return 0


def get_total_count_by_opts(conn, opts, uid=-1):
    sql = "SELECT count(payment.pid) as count FROM `{0}`,`{1}` WHERE 1=1 ".format(table_name.payment,
                                                                                  table_name.players)
    for k, v in opts.items():
        if k is 'uid':
            sql += " AND {0}.{1} = {2} ".format(table_name.payment, k, v)
        elif k is 'admin_name':
            sql += " AND {0} = '{1}' ".format(k, v)
        elif k is 'diamond_min':
            sql += " AND diamonds >= {0} ".format(v)
        elif k is 'diamond_max':
            sql += " AND diamonds <= {0} ".format(v)
        elif k is 'payment_min':
            sql += " AND amount >= {0} ".format(v)
        elif k is 'payment_max':
            sql += " AND amount <= {0} ".format(v)
        elif k is 'start_time':
            sql += " AND order_time >= {0} ".format(v)
        elif k is 'end_time':
            sql += " AND order_time <= {0} ".format(v)
        elif k is 'phone':
            sql += " AND players.phone like '%%{0}%%' ".format(v)
    if uid != -1:
        sql += " AND base_refer_uid = {0} ".format(uid)
    sql += " AND {0}.uid = {1}.uid".format(table_name.payment, table_name.players)
    data = conn.get(sql)
    if data:
        return data['count']
    return 0


def get_by_billing_number(conn, pay_method, billing_number):  # 根据支付方式和平台方来查询订单信息
    sql = "SELECT * FROM `%s` WHERE billing_number='%s' AND pay_method='%d' LIMIT 1" % \
          (table_name.payment, database.escape(billing_number), pay_method)
    return conn.get(sql)


def update_order(conn, pid, amount, billing_number):  # 更新订单的数据
    update_amount = ("amount='%d'," % (amount,)) if amount > 0 else ""
    sql = "UPDATE `%s` SET %s billing_number='%s' WHERE pid='%d' and status=0 LIMIT 1" % \
          (table_name.payment, update_amount, database.escape(billing_number), pid)
    return conn.execute_rowcount(sql)


def set_order_success(conn, pid):  # 更新订单状态为已发货
    finish_time = utils.timestamp()
    sql = "UPDATE `%s` SET status=1,finish_time='%d' WHERE pid='%d' and status=0 LIMIT 1" % \
          (table_name.payment, finish_time, pid)
    return conn.execute_rowcount(sql)
