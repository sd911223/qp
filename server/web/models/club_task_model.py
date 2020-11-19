from utils import utils


def update_club_task(conn, club_id, task_share, task_today_game_round):
    sql = f"UPDATE `club` SET task_share={task_share}," \
        f"task_today_game_round='{task_today_game_round}' WHERE id = {club_id}"
    return conn.execute_rowcount(sql)


def get_club_tasks(conn, club_id):
    sql = f"SELECT task_share,task_today_game_round FROM club WHERE id={club_id}"
    return conn.get(sql)


def get_user_club_task(conn, club_id, uid):
    sql = f"SELECT share_time,bonus_share_time,today_game_round,bonus_today_game_round FROM club_user WHERE " \
        f"club_id={club_id} and uid={uid}"
    return conn.get(sql)


def modify_user_task_update_time(conn, club_id, uid):
    sql = f"UPDATE `club_user` SET share_time={utils.timestamp()} WHERE club_id={club_id} AND uid = {uid}"
    return conn.execute_rowcount(sql)


def bonus_user(conn, uid, diamond):
    sql = f"UPDATE `players` SET diamond=diamond+{diamond} WHERE uid = {uid}"
    return conn.execute_rowcount(sql)


def update_bonus_user_time(conn, club_id, uid):
    sql = f"UPDATE `club_user` SET bonus_share_time={utils.timestamp()} WHERE club_id = {club_id} AND uid = {uid}"
    return conn.execute_rowcount(sql)


def update_user_today_game_round(conn, club_id, uid, game_round):
    sql = f"UPDATE `club_user` SET bonus_today_game_round='{game_round}' WHERE club_id = {club_id} AND uid = {uid}"
    return conn.execute_rowcount(sql)
