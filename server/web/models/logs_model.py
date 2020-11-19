from models import database
from models import table_name
from utils import utils


def get_round_log(conn, round_id):
    if not conn or not round_id:
        return {}
    sql = "SELECT * FROM `{0}` WHERE round_id='{1}' LIMIT 1".format(table_name.round_logs, round_id)
    return conn.get(sql)


def get_game_finish_data_by_record_id(conn, record_id):
    if not conn or not record_id:
        return {}
    sql = "SELECT * FROM `{0}` WHERE record_id='{1}' LIMIT 1".format(table_name.room_logs, record_id)
    return conn.get(sql)


def get_round_log_by_share_code(conn, share_code):
    if not conn or not share_code:
        return {}
    sql = "SELECT * FROM `{0}` WHERE share_code='{1}' LIMIT 1".format(table_name.round_logs, share_code)
    return conn.get(sql)


def set_resource_path_of_round_details(conn, round_id, record_id, resource_path):
    if not conn or not round_id or not record_id or not resource_path:
        return 0
    sql = "UPDATE `{0}` SET resource_path='{1}' WHERE round_id='{2}' AND record_id='{3}' LIMIT 1". \
        format(table_name.round_logs, resource_path, round_id, record_id)
    return conn.execute_rowcount(sql)


def set_round_share_code(conn, round_id, share_code):
    if not conn or not round_id or not share_code:
        return 0
    time = utils.timestamp()
    sql = "UPDATE `{0}` SET share_code={1},share_time={2} WHERE round_id={3} LIMIT 1". \
        format(table_name.round_logs, share_code, time, round_id)
    return conn.execute_rowcount(sql)


def get_room_log(conn, record_id):
    if not conn or not record_id:
        return {}
    sql = "SELECT * FROM `{0}` WHERE record_id='{1}' LIMIT 1".format(table_name.room_logs, record_id)
    return conn.get(sql)


def get_room_list(conn, uid, club_id=1):
    """查询自己参与或代开的房间记录列表"""
    # sql = "SELECT * FROM `{0}` WHERE club_id={2} AND (uid1='{1}' OR uid2='{1}' OR uid3='{1}' OR uid4='{1}' " \
    #       " OR owner='{1}') " \
    #       " ORDER BY finish_time DESC LIMIT 20"
    #xingxinghuyu
    sql = "SELECT * FROM `{0}` WHERE club_id={2} AND (uid1='{1}' OR uid2='{1}' OR uid3='{1}' OR uid4='{1}') " \
          " ORDER BY finish_time DESC LIMIT 20"

    sql = sql.format(table_name.room_logs, uid, club_id)
    return conn.query(sql)


def get_room_list_with_club_id_and_time(conn, uid, club_id, start_time, end_time):
    sql = "SELECT * FROM `{0}` " \
          "WHERE club_id='{4}' AND (uid1='{1}' OR uid2='{1}' OR uid3='{1}' OR uid4='{1}' " \
          ") AND " \
          "finish_time >= {2} AND finish_time <= {3} ORDER BY finish_time"
    sql = sql.format(table_name.room_logs, uid, start_time, end_time, club_id)
    return conn.query(sql)


def get_room_list_with_time(conn, uid, start_time, end_time):
    """
    查询玩家参与的房间记录列表
    :param conn:  数据库连接
    :param uid:   用户 ID
    :param start_time: 起始时间
    :param end_time:   结束时间
    :return: 
    """
    sql = "SELECT * FROM `{0}` " \
          "WHERE (uid1='{1}' OR uid2='{1}' OR uid3='{1}' OR uid4='{1}' " \
          ") AND " \
          "finish_time >= {2} AND finish_time <= {3} ORDER BY finish_time DESC LIMIT 60 "
    sql = sql.format(table_name.room_logs, uid, start_time, end_time)
    return conn.query(sql)


def get_round_list(conn, record_id):
    """查询自己所参与的房间的牌局列表"""
    record_id = database.escape(record_id)
    sql = "SELECT * FROM `{0}` WHERE record_id='{1}' ORDER BY seq ASC LIMIT 100"
    sql = sql.format(table_name.round_logs, record_id)
    return conn.query(sql)


def has_finish_round(conn, uid):
    if not conn or not uid:
        return False
    sql = "SELECT 1 FROM `{0}` WHERE uid1='{1}' OR uid2='{1}' OR uid3='{1}' or uid4='{1}' " \
          " LIMIT 1"
    sql = sql.format(table_name.room_logs, uid, uid, uid)
    return conn.get(sql)


def get_diamond_records_by_uid(conn, uid, limit=100):
    """查询自己的钻石记录"""
    sql = "SELECT * FROM `{0}` WHERE uid='{1}' ORDER BY `time` DESC LIMIT {2}"
    sql = sql.format(table_name.diamond_logs, uid, limit)
    return conn.query(sql)


def get_diamond_records(conn, opts, limit=100):
    sql = "SELECT * FROM `{0}` WHERE 1=1 ".format(table_name.diamond_logs)
    for k, v in opts.items():
        if k in ['uid', 'refer_uid', 'reason_id']:
            sql += " AND {0} = {1}".format(k, v)
        elif k is 'diamond_left_min':
            sql += " AND left_diamonds >= {0}".format(v)
        elif k is 'diamond_left_max':
            sql += " AND left_diamonds <= {0}".format(v)
        elif k is 'diamond_min':
            sql += " AND diamonds >= {0}".format(v)
        elif k is 'diamond_max':
            sql += " AND diamonds <= {0}".format(v)
        elif k is 'start_time':
            sql += " AND time >= {0}".format(v)
        elif k is 'end_time':
            sql += " AND time <= {0}".format(v)
    sql += " ORDER BY `time` DESC LIMIT {0}".format(limit)
    return conn.query(sql)


def add_diamonds_record(conn, uid, refer_uid, refer_nick_name, diamonds, reason_id, left_diamonds, step, memo=''):
    """插入钻石日志"""
    if not conn or not uid or not refer_uid or not diamonds or not reason_id:
        return 0

    time = utils.timestamp()
    inserts = {
        'uid': int(uid),
        'refer_uid': int(refer_uid),
        'refer_nick_name': database.escape(refer_nick_name),
        'diamonds': int(diamonds),
        'reason_id': int(reason_id),
        'left_diamonds': int(left_diamonds),
        'time': time,
        'memo': database.escape(memo),
        'step': int(step),
    }
    sql = database.make_insert(table_name.diamond_logs, inserts)
    return conn.execute(sql)


def get_last_round_index_by_record_id(conn, record_id):
    if not conn or not record_id:
        return 1
    sql = "SELECT max(seq) as seq FROM `{0}` WHERE record_id='{1}' ".format(table_name.round_logs, record_id)
    return conn.get(sql)


def get_club_room_list(conn, club_id, uid=0, limit=1000, match_type=None):
    """查询茶馆中的战绩列表"""

    sql = "SELECT * FROM `{0}` WHERE club_id='{1}' ".format(table_name.room_logs, club_id)
    if uid != 0:
        sql += " and (uid1='{0}' OR uid2='{0}' OR uid3='{0}' OR uid4='{0}' " \
               ") ".format(uid)
    if match_type:
        sql += f" AND match_type = {match_type} "
    sql += "AND finish_time >= {0} ORDER BY finish_time DESC LIMIT {1}".format(utils.timestamp_today() - 48 * 60 * 60,
                                                                               limit)
    return conn.query(sql)


def get_win_or_lose_info(data, uid, seq):
    if data['uid' + str(seq)] != int(uid):
        return 0, 0
    return 1, data['score' + str(seq)]


def update_score_info(week_round, day_round, week_params, day_params, finish_time):
    week_round += 1
    week_params += 1
    if utils.timestamp_today() <= finish_time < utils.timestamp_tomorrow():
        day_round += 1
        day_params += 1
    return week_round, day_round, week_params, day_params


def get_club_week_and_day_info_by_owner(conn, club_id, uid):
    start_week_time, end_week_time = utils.timestamp_week()
    sql = "SELECT * FROM `{0}` WHERE club_id='{1}' and owner='{2}' and finish_time>={3} and finish_time<{4}". \
        format(table_name.room_logs, club_id, uid, start_week_time, end_week_time)
    result = conn.query(sql)
    week_round, week_win, week_lose, day_round, day_win, day_lose = 0, 0, 0, 0, 0, 0
    for data in result:
        week_round, day_round, week_win, day_win = update_score_info(week_round, day_round, week_win, day_win,
                                                                     data['finish_time'])
    ret = {
        "weekRound": week_round,
        "dayRound": day_round,
    }
    return ret


def get_club_week_and_day_info(conn, club_id, uid, match_type):
    """查询自己或房主本周战绩以及当天战绩"""
    start_week_time, end_week_time = utils.timestamp_week()
    sql = "SELECT * FROM `{0}` WHERE club_id='{1}' and (uid1='{2}' OR uid2='{2}' OR uid3='{2}' or uid4='{2}' " \
          ") " \
          "AND finish_time>={3} AND finish_time<{4} ".format(table_name.room_logs, club_id, uid, start_week_time,
                                                             end_week_time)
    if match_type:
        sql += f" AND match_type={match_type}"

    result = conn.query(sql)
    week_round, week_win, week_lose, day_round, day_win, day_lose = 0, 0, 0, 0, 0, 0
    for data in result:
        for seq in range(10):
            round_count, score = get_win_or_lose_info(data, uid, seq + 1)
            if round_count > 0:
                if score > 0:
                    week_round, day_round, week_win, day_win = update_score_info(week_round, day_round, week_win,
                                                                                 day_win,
                                                                                 data['finish_time'])
                elif score < 0:
                    week_round, day_round, week_lose, day_lose = update_score_info(week_round, day_round, week_lose,
                                                                                   day_lose,
                                                                                   data['finish_time'])
    ret = {
        "weekRound": week_round,
        "weekWin": week_win,
        "weekLose": week_lose,
        "dayRound": day_round,
        "dayWin": day_win,
        "dayLose": day_lose
    }
    return ret


def set_club_winner_list(conn_logs, club_id, ids):
    sql = "UPDATE `{0}` SET is_read=1 WHERE club_id='{1}' AND id IN ({2})".format(table_name.club_winner, club_id, ids)
    return conn_logs.execute(sql)


def get_club_winner_list(conn_logs, club_id):
    sql = "SELECT * FROM `{0}` WHERE club_id='{1}' AND is_read=0".format(table_name.club_winner, club_id)
    return conn_logs.query(sql)


def get_club_winner_rank(conn_logs, club_id, start_time, end_time):
    sql = f"SELECT a.players AS uid,b.avatar AS avatar,b.nick_name AS nick_name,count(1) AS count " \
        f"FROM game_logs.club_winner AS a,game.players AS b WHERE b.uid = a.players AND a.club_id={club_id} " \
        f"AND a.time >= {start_time} AND a.time <= {end_time} GROUP BY a.players"
    return conn_logs.query(sql)


def get_club_room_list_by_time_and_game_type(conn, club_id, uid=0, limit=1000, match_type=None, game_type=0,
                                             start_time=0, end_time=0):
    """查询茶馆中的战绩列表"""

    sql = "SELECT * FROM `{0}` WHERE club_id='{1}' ".format(table_name.room_logs, club_id)
    if uid != 0:
        sql += " and (uid1='{0}' OR uid2='{0}' OR uid3='{0}' OR uid4='{0}' " \
               " ) ".format(uid)
    if match_type:
        sql += f" AND match_type = {match_type} "
    sql += f"AND finish_time >= {start_time} AND finish_time <= {end_time} ORDER BY finish_time DESC"
    return conn.query(sql)
