from models import table_name
from utils import utils


def get_club_room_rank(conn_logs, start_time=None, end_time=None):
    if not conn_logs:
        return []
    sql = 'select c.id as club_id,c.name,' \
          'c.uid,p.nick_name,p.phone,sum(1) as room_count from game.{0} as c,game.{1} as p' \
          ',game_logs.{2} as b where b.finish_time >= {3} and b.finish_time <= {4} and ' \
          'c.uid = p.uid and b.club_id != -1 and b.club_id = c.id and b.diamond > 0' \
          ' group by b.club_id order by room_count ' \
          'desc limit 50' \
        .format(table_name.club, table_name.players, table_name.room_logs, start_time, end_time)
    info = conn_logs.query(sql)
    return info


def get_club_room_rank_over_100(conn_logs, start_time=None, end_time=None, limit=5):
    if not conn_logs:
        return []
    sql = 'select c.name,c.uid,p.nick_name,sum(1) as room_count from game.{0} as c,game.{1} as p' \
          ',game_logs.{2} as b where b.finish_time >= {3} and b.finish_time <= {4} and ' \
          'c.uid = p.uid and b.club_id != -1 and b.club_id = c.id and b.diamond > 0' \
          ' group by b.club_id having room_count > 0 ' \
          'order by room_count desc limit {5}' \
        .format(table_name.club, table_name.players, table_name.room_logs, start_time, end_time, limit)
    info = conn_logs.query(sql)
    return info


def get_club_room_playing_count_by_uid(conn_logs, start_time=None, end_time=None, uid=0):
    if not conn_logs or not uid:
        return 0
    sql = 'select sum(1) as room_count from game.{0} as c,game.{1} as p' \
          ',game_logs.{2} as b where b.finish_time >= {3} and b.finish_time <= {4} and ' \
          'c.uid = p.uid and b.club_id != -1 and b.club_id = c.id and p.uid = {5} and b.diamond > 0 ' \
          'group by b.club_id ' \
          'order by room_count desc ' \
        .format(table_name.club, table_name.players, table_name.room_logs, start_time, end_time, uid)
    info = conn_logs.get(sql)
    return info


def get_club_user_rank(conn_logs):
    if not conn_logs:
        return []
    sql = 'select c.name,c.uid,p.nick_name,p.phone,d.time as time,d.user_count as user_count from game.{0}' \
          ' as c,game.{1} as p' \
          ',game_logs.{3} as d where d.club_id = c.id and ' \
          'c.uid = p.uid order by user_count desc limit 10' \
        .format(table_name.club, table_name.players, table_name.room_logs, table_name.club_user_stat)
    info = conn_logs.query(sql)
    return info


def get_robot_stat(conn_logs, start_time, end_time, min_count):
    if not conn_logs or not start_time or not end_time:
        return []
    sql = 'SELECT wx_id,group_id,SUM(red_packet_count) as red_packet_count,SUM(message_count) as message_count' \
          ',SUM(open_room_count) as open_room_count,' \
          'FROM_UNIXTIME(time, "%%m-%%d") as date FROM `{0}` ' \
          'WHERE time >= {1} and time <= {2} ' \
          'GROUP BY date,group_id HAVING SUM(open_room_count)>={3} ORDER BY time desc'. \
        format(table_name.robot_stat, start_time, end_time, min_count)
    info = conn_logs.query(sql)
    return info


def get_robot_rooms(conn_logs, start_time, end_time, min_count, uid):
    if not conn_logs or not start_time or not end_time or not min_count or not uid:
        return []
    sql = 'SELECT remark,game_logs.robot_logs.wx_id,game_logs.robot_logs.group_id,' \
          'SUM(game_logs.robot_logs.open_room_count) as open_room_count,' \
          'FROM_UNIXTIME(game_logs.robot_logs.time, "%%m-%%d") as date FROM game_logs.robot_logs as' \
          ' robot_logs,game.robot_group as g WHERE game_logs.robot_logs.group_id = g.group_id and ' \
          'game_logs.robot_logs.time >= {1} and game_logs.robot_logs.time <= {2} and ' \
          'g.diamond_uid = {3} GROUP BY date,group_id HAVING SUM(game_logs.robot_logs.open_room_count)>={4} ' \
          'ORDER BY game_logs.robot_logs.time desc'.format(start_time, end_time, uid, min_count)
    info = conn_logs.query(sql)
    return info


def get_club_users(conn, club_id):
    sql = f"select a.uid,a.avatar,a.nick_name,a.reg_time,a.login_time from players as a," \
        f"club_user as b where a.uid = b.uid and b.club_id = {club_id} order by a.login_time desc"
    info = conn.query(sql)
    return info


def get_sign_bonus_by_day(conn, day):
    sql = f"SELECT * FROM sign_activity_item where id = {day}"
    return conn.get(sql)


def query_sign_bonus(conn):
    sql = f"SELECT * FROM sign_activity_item"
    return conn.query(sql)


def get_spring_activity_status(conn, uid):
    sql = f"SELECT * FROM spring_activity where uid={uid}"
    return conn.get(sql)


def query_spring_activity_logs(conn_logs, uid):
    sql = f"SELECT * FROM spring_activity_logs where uid = {uid} ORDER BY time DESC LIMIT 60"
    return conn_logs.query(sql)


def insert_spring_activity_log(conn_logs, uid, item_id):
    sql = f'INSERT INTO spring_activity_logs set uid={uid},item_id={item_id},item_type=0,time={utils.timestamp()}'
    return conn_logs.execute_rowcount(sql)


def modify_spring_activity_user_status(conn, uid, key, val, valid_key="", symbol="=", limit=0, score=0):
    sql = f"UPDATE `spring_activity` SET {key}={val},use_score=use_score+{score} WHERE uid={uid} " \
        f"AND {valid_key}{symbol}{limit} AND curr_score>={score}"
    return conn.execute_rowcount(sql)


def modify_spring_activity_user_game_status(conn, uid):
    sql = f"UPDATE `spring_activity` SET game_bonus_time={utils.timestamp()} WHERE uid={uid} " \
        f"AND game_bonus_time<={utils.timestamp_today()} and last_game_time>={utils.timestamp_today()}"
    return conn.execute_rowcount(sql)


def modify_player_info(conn, uid, key, val):
    sql = f"UPDATE `players` SET {key}={key}+{val} WHERE uid={uid}"
    return conn.execute_rowcount(sql)


def insert_spring_activity_user(conn, uid):
    sql = f"INSERT INTO `spring_activity` SET uid={uid}"
    try:
        conn.execute_rowcount(sql)
    except Exception as e:
        print(e)
    return 1
