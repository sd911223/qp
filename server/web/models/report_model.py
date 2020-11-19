import ujson as json
from configs import config
from utils import utils
from models import base_redis
from models import table_name
from decimal import Decimal


def default(obj):
    if isinstance(obj, Decimal):
        return str(obj)
    raise TypeError


def get_player_stat_by_time(conn, start_time=None, end_time=None):
    default_key = str(start_time) + "-" + str(end_time) + "-" + str(config.game_id) + "-player-stat"

    if not conn:
        return []
    if end_time and end_time == 0:
        return []
    if start_time and end_time:
        redis_data = base_redis.fetch(default_key)
        if redis_data is not None:
            return json.loads(redis_data)
        else:
            sql = 'SELECT from_unixtime(start_time, "%%m-%%d") date,' \
                  'SUM(login_count) AS login_count,SUM(reg_count) AS reg_count FROM {0} ' \
                  'WHERE start_time >= {1} AND end_time <= {2} GROUP BY DATE ORDER BY date DESC' \
                .format(table_name.players_statistics, start_time, end_time)
            info = conn.query(sql)
            base_redis.save_with_time(default_key, json.dumps(info))
            return info
    else:
        return []


def get_day_report_by_time(conn_logs, start_time=None, end_time=None):
    if not conn_logs:
        return []
    if end_time and end_time == 0:
        return []
    if start_time and end_time:
        sql = 'SELECT * FROM {0} WHERE time >= {1} AND time <= {2} ORDER BY time DESC' \
            .format(table_name.day_logs, start_time, end_time)
        info = conn_logs.query(sql)
        return info
    else:
        return []


def get_month_report(conn_logs):
    if not conn_logs:
        return []
    sql = 'SELECT * FROM {0} ORDER BY time DESC'.format(table_name.month_logs)
    info = conn_logs.query(sql)
    return info


def get_game_round_by_time(conn, start_time=None, end_time=None):
    default_key = str(start_time) + "-" + str(end_time) + "-" + str(config.game_id) + "-game-round"

    if not conn:
        return []
    if end_time and end_time == 0:
        return []
    if start_time and end_time:
        redis_data = base_redis.fetch(default_key)
        if redis_data is not None:
            return json.loads(redis_data)
        else:
            sql = 'SELECT from_unixtime(start_time, "%%m-%%d") date,' \
                  'SUM(room_count) AS room_count,SUM(round_count) AS round_count,SUM(pdk_room_count) ' \
                  'AS pdk_room_count,' \
                  'SUM(pdk_round_count) AS pdk_round_count,SUM(zzmj_room_count) AS zzmj_room_count,' \
                  'SUM(zzmj_round_count) AS zzmj_round_count,SUM(hzmj_room_count) AS hzmj_room_count,' \
                  'SUM(hzmj_round_count) AS hzmj_round_count,SUM(csmj_round_count) AS csmj_round_count,' \
                  'SUM(csmj_room_count) AS csmj_room_count,SUM(dtz_round_count) as dtz_round_count,SUM(dtz_room_count) as dtz_room_count ' \
                  'FROM {0} ' \
                  'WHERE start_time >= {1} AND end_time <= {2} GROUP BY date ORDER BY date DESC' \
                .format(table_name.room_logs_statistics, start_time, end_time)
            info = conn.query(sql)
            base_redis.save_with_time(default_key, json.dumps(info))
            return info
    else:
        return []


def get_round_rank_by_time(conn, start_time=None, end_time=None):
    default_key = str(start_time) + "-" + str(end_time) + "-" + str(config.game_id) + "-round-rank"

    if not conn:
        return []
    if end_time and end_time == 0:
        return []
    if start_time and end_time:
        redis_data = base_redis.fetch(default_key)
        if redis_data is not None:
            return json.loads(redis_data)
        else:
            sql = "SELECT uid1,uid2,uid3,uid4,uid5,uid6,uid7,uid8,uid9,uid10,round_count " \
                  "FROM {0} " \
                  "WHERE finish_time >= {1} AND finish_time <= {2} ".format(table_name.room_logs, start_time, end_time)
            info = conn.query(sql)
            base_redis.save_with_time(default_key, json.dumps(info))
            return info
    else:
        return []


def get_game_round_details_by_minute(conn, start_time=None, end_time=None):
    if not conn:
        return []
    if end_time and end_time == 0:
        return []
    if start_time and end_time:
        sql = "SELECT record_id,game_type " \
              "FROM {0} " \
              "WHERE finish_time >= {1} AND finish_time <= {2} ".format(table_name.room_logs, start_time, end_time)
        return conn.query(sql)
    else:
        return []


def get_round_count_by_record_id(conn_logs, record_id):
    sql = "SELECT max(seq) as count " \
          "FROM {0} " \
          "WHERE record_id = '{1}'".format(table_name.round_logs, record_id)
    data = conn_logs.get(sql)
    if data and 'count' in data:
        return data['count']
    return 0


def add_room_logs_statistics(conn, opts):
    if not conn:
        return []
    insert_list = []
    for k, v in opts.items():
        insert_list.append("{0}='{1}'".format(k, v))
    sql = "INSERT INTO `{0}` SET " + ",".join(insert_list)
    sql = sql.format(table_name.room_logs_statistics)
    return conn.execute_rowcount(sql)


def get_player_details_by_minute(conn, start_time=None, end_time=None):
    if not conn:
        return []
    if end_time and end_time == 0:
        return []
    if start_time and end_time:
        sql = "SELECT COUNT(login_time) AS count FROM {0} WHERE login_time >= {1} AND login_time <= {2} " \
              "UNION ALL " \
              "SELECT COUNT(reg_time) AS count FROM {0} WHERE reg_time >= {1} AND reg_time <= {2}" \
            .format(table_name.players, start_time, end_time)
        return conn.query(sql)
    else:
        return []


def add_player_logs_statistics(conn, opts):
    if not conn:
        return []
    insert_list = []
    for k, v in opts.items():
        insert_list.append("{0}='{1}'".format(k, v))
    sql = "INSERT INTO `{0}` SET " + ",".join(insert_list)
    sql = sql.format(table_name.players_statistics)
    sql += " ON DUPLICATE KEY UPDATE reg_count={0},login_count=login_count+{0}".format(opts['reg_count'])
    return conn.execute_rowcount(sql)


def increase_player_login_statistics(conn):
    if not conn:
        return []
    opts = dict()
    opts['start_time'], opts['end_time'] = utils.get_current_start_end_timestamp()
    opts['login_count'] = 1
    insert_list = []
    for k, v in opts.items():
        insert_list.append("{0}='{1}'".format(k, v))
    sql = "INSERT INTO `{0}` SET " + ",".join(insert_list)
    sql = sql.format(table_name.players_statistics)
    sql += " ON DUPLICATE KEY UPDATE login_count=login_count+1"
    return conn.execute_rowcount(sql)


def add_ip_geo(conn, opts):
    if not conn:
        return []
    insert_list = []
    for k, v in opts.items():
        insert_list.append("{0}='{1}'".format(k, v))
    sql = "REPLACE INTO `{0}` SET " + ",".join(insert_list)
    sql = sql.format(table_name.ip_geo)
    return conn.execute_rowcount(sql)


def get_yesterday_no_geo(conn, start_time=None, end_time=None):
    if not conn:
        return []
    if end_time and end_time == 0:
        return []
    if start_time and end_time:
        sql = "SELECT CONCAT(x,'') AS x ,CONCAT(y,'') AS y FROM {0} " \
              "WHERE (x NOT IN (SELECT x FROM ip_geo) or y NOT IN (SELECT y from ip_geo)) " \
              "AND time >= {1} AND time <= {2}".format(table_name.active_user_geo_logs, start_time, end_time)
        return conn.query(sql)
    else:
        return []


def get_activity_geo_by_time(conn, start_time=None, end_time=None):
    if not conn:
        return []
    if end_time and end_time == 0:
        return []
    if start_time and end_time:
        sql = "SELECT CONCAT(x,'') AS x ,CONCAT(y,'') AS y FROM {0} " \
              "WHERE time >= {1} AND time <= {2}" \
            .format(table_name.active_user_geo_logs, start_time, end_time)
        return conn.query(sql)
    else:
        return []


def get_activity_detail_by_time(conn, start_time=0, end_time=0, group_by='province'):
    if not conn:
        return []
    if end_time and end_time == 0:
        return []
    if start_time and end_time:
        if group_by == 'province':
            sql = "SELECT province,count(province) AS count FROM {0},{1} " \
                  "WHERE {0}.x = {1}.x AND {0}.y = {1}.y " \
                  "AND time >= {2} AND time <= {3} GROUP BY province ORDER BY count DESC"
        elif group_by == 'city':
            sql = "SELECT province,city,count(city) AS count FROM {0},{1} " \
                  "WHERE {0}.x = {1}.x AND {0}.y = {1}.y " \
                  "AND time >= {2} AND time <= {3} GROUP BY province,city ORDER BY count DESC"
        else:
            sql = "SELECT province,city,county_area,count(county_area) AS count FROM {0},{1} " \
                  "WHERE {0}.x = {1}.x AND {0}.y = {1}.y " \
                  "AND time >= {2} AND time <= {3} GROUP BY province,city,county_area ORDER BY count DESC"
        sql = sql.format(table_name.active_user_geo_logs, table_name.ip_geo, start_time, end_time)
        return conn.query(sql)
    else:
        return []


def get_yesterday_emotions(conn, start_time=None, end_time=None):
    if not conn:
        return []
    if end_time and end_time == 0:
        return []
    if start_time and end_time:
        sql = "SELECT emotion_id,sum(1) as counts FROM {0} " \
              "WHERE time >= {1} AND time <= {2} GROUP BY emotion_id".format(table_name.emotion_logs, start_time,
                                                                             end_time)
        return conn.query(sql)
    else:
        return []


def add_emotion_logs_statistics(conn, opts):
    if not conn:
        return []
    insert_list = []
    for k, v in opts.items():
        insert_list.append("{0}='{1}'".format(k, v))
    sql = "INSERT INTO `{0}` SET " + ",".join(insert_list)
    sql = sql.format(table_name.emotion_logs_statistics)
    return conn.execute_rowcount(sql)


def get_emotion_by_time(conn, start_time, end_time):
    if not conn:
        return []
    if end_time and end_time == 0:
        return []
    if start_time and end_time:
        sql = "SELECT emotion_id AS id,sum(emotion_count) AS count FROM {0} " \
              "WHERE start_time >= {1} AND end_time <= {2} GROUP BY emotion_id ORDER BY count DESC". \
            format(table_name.emotion_logs_statistics, start_time, end_time)
        return conn.query(sql)
    else:
        return []


def add_active_user_login_ip_logs(conn, uid, ip, opt_type):
    if not conn:
        return []
    sql = "INSERT INTO `{0}` SET uid={1},ip='{2}',time={3},type={4}". \
        format(table_name.active_user_login_ip_logs, uid, ip, utils.timestamp(), opt_type)
    return conn.execute_rowcount(sql)


def get_total_diamond(conn):
    if not conn:
        return []
    sql = "SELECT SUM(diamond) AS count FROM {0}".format(table_name.players)
    return conn.get(sql)


def add_diamond_logs_statistics(conn, total, diamond_type, count):
    current_time = utils.timestamp_today()
    if not conn:
        return []
    sql = "INSERT INTO `{0}` SET time={1},total={2},diamond_type={3},count={4}". \
        format(table_name.diamond_logs_statistics, current_time, total, diamond_type, count)
    return conn.execute_rowcount(sql)


def get_diamond_detail_by_time(conn, start_time, end_time):
    if not conn:
        return []
    if start_time and end_time:
        sql = "SELECT reason_id,SUM(diamonds) AS diamond FROM {0} WHERE time >= {1} AND time <= {2}" \
              " GROUP BY reason_id".format(table_name.diamond_logs, start_time, end_time)
        return conn.query(sql)
    else:
        return []


def get_diamond_report_by_start_end(conn, start, end):
    if not conn:
        return []
    if start is not 0 and end is not 0:
        sql = "SELECT FROM_UNIXTIME(time,'%%Y-%%m-%%d') date,total," \
              "diamond_type,SUM(count) as count FROM {0} " \
              "WHERE TIME >= {1} and TIME <= {2} GROUP BY date,total,diamond_type ORDER BY time DESC". \
            format(table_name.diamond_logs_statistics, start, end)
        return conn.query(sql)
    else:
        return []


def get_online_player_count(conn):
    if not conn:
        return 0
    sql = "SELECT count(1) AS count FROM {0} UNION ALL SELECT count(1) AS count FROM {0}" \
          " WHERE tid != 0 AND state = 0 UNION ALL SELECT count(1) as count FROM {0} WHERE tid != 0 AND state = 1" \
        .format(table_name.online)
    return conn.query(sql)


def insert_online_player_statistics(conn, count, in_table_count, playing_count, time):
    if not conn:
        return 0
    hall_count = count - in_table_count - playing_count
    sql = "INSERT INTO `{0}` SET count={1},in_table_count={2},playing_count={3},hall_count={4},time={5}" \
        .format(table_name.online_player_statistics, count, in_table_count, playing_count, hall_count, time)
    return conn.execute_rowcount(sql)


def get_online_player_count_chart(conn, start, end):
    if not conn:
        return 0
    if end is 0:
        limit = 120
        sql = "SELECT * FROM `{0}` WHERE time > {1} ORDER BY TIME DESC LIMIT {2}". \
            format(table_name.online_player_statistics, start, limit)
    else:
        sql = "SELECT * FROM `{0}` WHERE time >= {1} and time <= {2} ORDER BY TIME DESC". \
            format(table_name.online_player_statistics, start, end)
    return conn.query(sql)


def get_playing_table_count(conn):
    if not conn:
        return 0
    sql = "SELECT COUNT(1) AS count FROM {0} WHERE state=1 UNION ALL SELECT COUNT(1) AS count FROM {0} " \
          "WHERE state=0".format(table_name.tables)
    return conn.query(sql)


def insert_playing_table_statistics(conn, count, time, ready_count):
    if not conn:
        return 0
    sql = "INSERT INTO `{0}` SET count={1},time={2},ready_count={3}".format(table_name.playing_table_statistics,
                                                                            count, time, ready_count)
    return conn.execute_rowcount(sql)


def get_playing_table_count_chart(conn, start, end):
    if not conn:
        return 0
    if end is 0:
        limit = 120
        sql = "SELECT ready_count,count,time FROM `{0}` WHERE time > {1} ORDER BY TIME DESC LIMIT {2}". \
            format(table_name.playing_table_statistics, start, limit)
    else:
        sql = "SELECT ready_count,count,time FROM `{0}` WHERE time >= {1} and time <= {2} ORDER BY TIME DESC". \
            format(table_name.playing_table_statistics, start, end)
    return conn.query(sql)


def insert_geo_information(conn, uid, x, y):
    time = utils.timestamp()
    if not conn:
        return 0
    sql = "INSERT INTO `{0}` SET uid={1},x={2},y={3},time={4}".format(table_name.active_user_geo_logs,
                                                                      uid, x, y, time)
    return conn.execute_rowcount(sql)


def get_club_statistics(conn, start, end):
    if not conn:
        return 0
    if end is 0:
        limit = 120
        sql = "SELECT FROM_UNIXTIME(time,'%%Y-%%m-%%d') time,room_club_count,club_open_room_count,club_round_count" \
              " FROM `{0}` WHERE time > {1} ORDER BY TIME DESC LIMIT {2}". \
            format(table_name.club_statistics, start, limit)
    else:
        sql = "SELECT  FROM_UNIXTIME(time,'%%Y-%%m-%%d') time,room_club_count,club_open_room_count,club_round_count" \
              " FROM `{0}` WHERE time >= {1} and time <= {2} ORDER BY TIME DESC". \
            format(table_name.club_statistics, start, end)
    return conn.query(sql)
