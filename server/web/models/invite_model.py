from models import table_name
from utils import utils


def get_withdraw_count_by_unionid(conn, start_time, end_time, unionid):
    if not conn or not unionid:
        return {}
    sql = "SELECT COUNT(1) as count FROM `{0}` WHERE union_id='{1}' and time>={2} and time<={3} and type = 1 LIMIT 1".format(
        table_name.share_logs, unionid, start_time, end_time)
    return conn.get(sql)


def get_exchange_or_withdraw_uids(conn, uid, min_round_count, start_time, end_time):
    if not conn or not uid or not min_round_count:
        return []
    sql = "select p.`uid` from game.players as p,game_logs.players_round_count_logs as b where " \
          "p.withdraw_time = -1 and p.uid = b.uid and b.time>p.`refer_time` " \
          "and b.time>={0} and b.time <= {1} " \
          "and p.refer_uid={2} having sum(b.round_count) >= {3}".format(start_time, end_time, uid, min_round_count)
    return conn.query(sql)


def get_all_refer_players(conn, uid):
    if not conn or not uid:
        return []
    sql = "select p.`uid`,p.`avatar`,p.`nick_name`,p.`withdraw_time`,p.`refer_time` " \
          "from game.players as p where " \
          "p.refer_uid={0}".format(uid)
    return conn.query(sql)


def modify_players_withdraw_time(conn, uids=[]):
    if not conn or len(uids) == 0:
        return 0
    uids_str = ",".join(uids)
    sql = "UPDATE `{0}` SET withdraw_time = {1} WHERE uid in ({2})".format(table_name.players, utils.timestamp(),
                                                                           uids_str)
    return conn.execute_rowcount(sql)


def get_player_play_count(conn_logs, uid, time, start_time, end_time):
    sql = "select sum(round_count) as round_count " \
          "from players_round_count_logs where " \
          "time > {0} and uid = {1} and time >= {2} and time <= {3}".format(time, uid, start_time, end_time)
    return conn_logs.get(sql)


def get_today_withdraw_money(conn_logs, start_time, end_time):
    sql = "select sum(amount) as amount " \
          "from share_logs where " \
          "type = 1 and time >= {0} and time <= {1}".format(start_time, end_time)
    return conn_logs.get(sql)
