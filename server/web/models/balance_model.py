# coding:utf-8


def add_balance_user(conn, uid, refer_uid, level):
    sql = f"INSERT INTO `balance` SET uid={uid},refer_uid={refer_uid},`level`={level}"
    return conn.execute(sql)


def add_balance_amount(conn, uid, refer_uid, amount):
    sql = f"UPDATE `balance` SET total_charge=total_charge+{amount},current_charge=current_charge+{amount} " \
          f"WHERE uid={uid} " \
          f"AND `refer_uid`={refer_uid}"
    return conn.execute_rowcount(sql)


def add_withdraw(conn, uid, refer_uid, amount):
    sql = f'UPDATE `balance` SET current_charge=current_charge-{amount},withdraw_count=withdraw_count+1 ' \
          f'WHERE refer_uid={uid}' \
          f' AND ' \
          f'`uid`={refer_uid} AND current_charge>={amount}'
    return conn.execute_rowcount(sql)


def query_all_balance(conn, uid):
    sql = f"SELECT a.refer_uid,a.level,a.total_charge,a.current_charge,a.withdraw_count,b.nick_name FROM `balance` " \
          f"as a,`players` as b WHERE a.uid={uid} and a.refer_uid = b.uid ORDER BY current_charge DESC"
    return conn.query(sql)


def query_all_balance_count(conn, uid):
    sql = f"SELECT count(1) as count FROM `balance` " \
          f"as a,`players` as b WHERE a.refer_uid={uid} and a.uid = b.uid ORDER BY current_charge DESC"
    return conn.get(sql)


def get_by_opts_with_limit(conn, opts, uid):
    per_page_count = 30
    page = opts['page']
    sql = f"SELECT a.uid,a.refer_uid,a.level,a.total_charge,a.current_charge,a.withdraw_count,b.nick_name FROM `balance` " \
          f"as a,`players` as b WHERE a.refer_uid={uid} and a.uid = b.uid " \
          f"ORDER BY current_charge DESC LIMIT {(page - 1) * per_page_count},{per_page_count}"
    return conn.query(sql)


# 默认
def get_players_by_opts_with_limit(conn, opts, uid):
    per_page_count = 30
    page = opts['page']
    sql = f"SELECT * from players where invite_uid_1 = '{uid}' or invite_uid_2 = '{uid}' " \
          f"LIMIT {(page - 1) * per_page_count},{per_page_count}"
    return conn.query(sql)


def get_players_count_by_opts(conn, uid):
    sql = f"SELECT count(1) as count FROM `players` where invite_uid_1 = '{uid}' or invite_uid_2 = '{uid}'"
    return conn.get(sql)


# 三级分销
def get_agent_players_by_opts_with_limit(conn, opts, uid):
    per_page_count = 100
    page = opts['page']
    sql = f"SELECT * from players where invite_uid_1 = '{uid}' or invite_uid_2 = '{uid}' " \
          f"LIMIT {(page - 1) * per_page_count},{per_page_count}"
    return conn.query(sql)


def get_agent_players_count_by_opts(conn, uid):
    sql = f"SELECT count(1) as count FROM `players` where invite_uid_1 = '{uid}' or invite_uid_2 = '{uid}'"
    return conn.get(sql)


def add_charge(conn, refer_uid, amount):
    sql = f"UPDATE `balance` SET total_charge=total_charge+{amount},current_charge=current_charge+{amount} " \
          f"WHERE uid={refer_uid}"
    return conn.execute_rowcount(sql)


def get_charge(conn, uid):
    sql = f"SELECT uid,withdraw_count,level,current_charge FROM balance where refer_uid={uid}"
    return conn.query(sql)
