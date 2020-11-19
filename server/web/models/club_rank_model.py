from utils import utils


def get_club_user_rank(conn_logs, club_id, start_time, end_time):
    sql = f"SELECT a.uid,b.nick_name,b.avatar,a.game_type as game_type," \
        f"sum(a.game_count) as game_count,sum(a.total_score) as total_score " \
        f"FROM game_logs.club_user_rank_logs as a,game.players as b where a.club_id = {club_id} " \
        f"and a.start_time <= {end_time} and a.start_time >= {start_time} " \
        f"and a.uid = b.uid group by a.uid,a.game_type " \
        f"order by total_score desc"
    return conn_logs.query(sql)


def _find_user_and_type(data, uid, nick_name, game_type, avatar):
    for i in data:
        if i['uid'] == uid and i['game_type'] == game_type:
            return i
    i = {"uid": uid, "game_type": game_type, "game_count": 0, "nick_name": nick_name, "avatar": avatar}
    data.append(i)
    return i


def _find_user_without_type(data, uid, nick_name, avatar):
    for i in data:
        if i['uid'] == uid:
            return i
    i = {"uid": uid, "game_count": 0, "nick_name": nick_name, "avatar": avatar}
    data.append(i)
    return i


def get_club_user_rank_today(conn_logs, club_id):
    sql = f"SELECT * from room_logs where club_id={club_id} and finish_time >= {utils.timestamp_today()}\
     and finish_time <= {utils.timestamp()}"
    data = conn_logs.query(sql)
    ret_data = []
    for i in data:
        for idx in range(10):
            if i['uid' + str(idx + 1)] != 0:
                find_user = _find_user_and_type(ret_data, i['uid' + str(idx + 1)], i['name' + str(idx + 1)],
                                                i['game_type'], i['avatar' + str(idx + 1)])
                find_user['game_count'] += 1
    return ret_data


def get_club_user_rank_today_without_game_type(conn_logs, club_id):
    sql = f"SELECT * from room_logs where club_id={club_id} and finish_time >= {utils.timestamp_today()}\
     and finish_time <= {utils.timestamp()}"
    data = conn_logs.query(sql)
    ret_data = []
    for i in data:
        for idx in range(10):
            if i['uid' + str(idx + 1)] != 0:
                find_user = _find_user_without_type(ret_data, i['uid' + str(idx + 1)], i['name' + str(idx + 1)],
                                                    i['avatar' + str(idx + 1)])
                find_user['game_count'] += 1
    return ret_data


def get_club_user_rank_without_game_type(conn_logs, club_id, start_time, end_time):
    sql = f"SELECT a.uid,b.nick_name,b.avatar," \
        f"sum(a.game_count) as game_count,sum(a.total_score) as total_score " \
        f"FROM game_logs.club_user_rank_logs as a,game.players as b where a.club_id = {club_id} " \
        f"and a.start_time <= {end_time} and a.start_time >= {start_time} " \
        f"and a.uid = b.uid group by a.uid " \
        f"order by total_score desc"
    return conn_logs.query(sql)


def get_club_user_room_info(conn_logs, club_id, game_type, start_time, end_time):
    sql = f"SELECT uid, SUM(winner_count) AS winnerCount, SUM(winner_score) as winnerScore, " \
        f"SUM(round_count) AS totalCount, SUM(total_score) AS totalScore, SUM(lose_count) AS loseCount, " \
        f"SUM(lose_score) as loseScore  FROM club_player_room_logs  where club_id = {club_id} and game_type = {game_type} and " \
        f"start_time >= {start_time} and end_time <= {end_time} GROUP BY uid"
    return conn_logs.query(sql)


def get_club_tag_user_room_info(conn_logs, club_id, start_time, end_time):
    sql = f"SELECT tag_uid, SUM(winner_count) AS winnerCount,SUM(round_count) AS totalCount,SUM(score_less_10_count) AS " \
        f"less10Count FROM club_tag_player_room_logs " \
        f"WHERE club_id = {club_id} AND start_time >= {start_time} AND end_time <= {end_time} GROUP BY tag_uid"
    return conn_logs.query(sql)


def get_club_game_logs(conn_logs, club_id, start_time, end_time):
    sql = f"SELECT uid1,score1,uid2,score2,uid3,score3,uid4,score4,game_type from room_logs where " \
        f"club_id={club_id} and " \
        f"finish_time >= {start_time} and" \
        f" finish_time <= {end_time}"
    return conn_logs.query(sql)
