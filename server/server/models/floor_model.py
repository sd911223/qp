from .database import share_db, share_db_logs
from utils import utils


def get_floor_by_club_id_and_match_type(conn, club_id, match_type):
    sql = f"SELECT id,game_type FROM club_floor WHERE club_id={club_id} AND match_type={match_type}"
    return conn.query(sql)


def get_sub_floor_by_floor(conn, floor):
    sql = f"SELECT id,play_config FROM club_sub_floor WHERE floor_id={floor}"
    return conn.query(sql)


def del_sub_floor_by_sub_floor_and_club_id_and_game_type(conn, sub_floor, club_id, game_type):
    sql = f"DELETE FROM club_sub_floor WHERE id={sub_floor} AND club_id={club_id} AND game_type={game_type}"
    return conn.execute_rowcount(sql)


def query_club_floor_count_by_club_id_and_match_type(conn, club_id, match_type):
    sql = f"SELECT count(1) AS count FROM club_floor WHERE club_id={club_id} AND match_type={match_type}"
    return conn.get(sql)


def add_club_floor(conn, club_id, match_type, game_type):
    sql = f"INSERT INTO `club_floor` SET club_id={club_id},game_type={game_type},match_type={match_type}"
    return conn.execute_rowcount(sql)


def get_club_floor(conn, club_id, floor_id):
    sql = f"SELECT floor,game_type FROM club_floor WHERE club_id={club_id} AND id={floor_id}"
    return conn.get(sql)


def edit_club_floor(conn, floor_id, game_type):
    sql = f"UPDATE `club_floor` SET game_type={game_type} WHERE id={floor_id}"
    return conn.execute_rowcount(sql)


def del_club_floor(conn, club_id, floor_id, game_type):
    sql = f"DELETE FROM `club_floor` WHERE id={floor_id} AND club_id={club_id} AND game_type={game_type}"
    return conn.execute_rowcount(sql)


def del_club_sub_floor(conn, floor_id):
    sql = f"DELETE FROM `club_sub_floor` WHERE floor_id={floor_id}"
    return conn.execute_rowcount(sql)


def query_club_sub_floor_count_by_club_id_and_match_type(conn, floor, match_type):
    sql = f"SELECT count(1) AS count FROM club_sub_floor WHERE floor_id={floor} AND match_type={match_type}"
    return conn.get(sql)


def get_club_sub_floor_config(club_id, floor_id):
    sql = f"SELECT play_config,game_type,auto_room FROM club_sub_floor WHERE club_id = {club_id} AND id = {floor_id}"
    return share_db().get(sql)


def update_sub_floor_play_config(conn, club_id, play_config, sub_floor, auto_room):
    if not conn or not club_id or not play_config or not sub_floor:
        return 0
    play_config = str(play_config)
    sql = f"UPDATE `club_sub_floor` SET play_config='{play_config}',auto_room={auto_room}" \
          f" WHERE club_id={club_id} and id={sub_floor}"
    return conn.execute_rowcount(sql)


def insert_sub_floor_play_config(conn, club_id, floor, play_config, auto_room, game_type, match_type):
    if not conn or not club_id or not play_config:
        return 0
    play_config = str(play_config)
    sql = f"INSERT INTO `club_sub_floor` SET club_id={club_id}," \
          f"floor_id={floor},play_config='{play_config}',auto_room={auto_room}," \
          f"game_type={game_type},match_type={match_type}"
    return conn.execute_rowcount(sql)


def get_max_sub_floor_by_floor(conn, floor):
    sql = f"SELECT max(id) AS id FROM club_sub_floor WHERE floor_id={floor}"
    return conn.get(sql)


def get_idle_table_count_by_sub_floor(sub_floor):
    sql = f"SELECT count(1) AS count FROM tables WHERE sub_floor={sub_floor} and state=0"
    return share_db().get(sql)


def update_club_user_score_by_lock_score(uid, club_id):
    sql = f"UPDATE `club_user` SET score=score+lock_score," \
          f"lock_score=0,lock_table=0,lock_time=0 WHERE club_id={club_id} and uid={uid}"
    return share_db().execute_rowcount(sql)


def update_club_user_score_and_empty_lock_score(uid, club_id, score, limit_score, game_score):
    sql = f"UPDATE `club_user` SET score=score+{score},lock_score=0,lock_table=0,lock_time=0,game_round=game_round+1," \
          f"limit_score=limit_score+{limit_score}" \
          f",game_score=game_score+{game_score} WHERE club_id={club_id} and uid={uid}"
    return share_db().execute_rowcount(sql)


def insert_club_user_score_logs(uid, club_id, reason, before_score, score, record_id):
    sql = f"INSERT INTO `club_send_log` SET club_id={club_id}," \
          f"uid={uid},reason={reason},before_count={before_score},count={score}," \
          f"record_id='{record_id}',time={utils.timestamp()}"
    return share_db_logs().execute_rowcount(sql)
