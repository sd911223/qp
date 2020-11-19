from models import table_name


def get_agent_club_score(conn_logs, club_id, owner, start_time, end_time, score=0):
    if not conn_logs:
        return []
    if not club_id or not start_time or not end_time:
        return []
    sql = "SELECT record_id,uid1,score1," \
          "name1,uid2,score2,name2," \
          "uid3,score3,name3,uid4,score4,name4,finish_time,game_type,round_count FROM `{0}` WHERE 1=1".format(
        table_name.room_logs)
    sql += " AND club_id = {0}".format(club_id)
    if score != 0:
        sql += " AND (score1 >= {0} or score2 >= {0} or score3 >= {0} or score4 >= {0})".format(score)
    sql += " AND finish_time >= {0} and finish_time <= {1}".format(start_time, end_time)
    return conn_logs.query(sql)


def get_all_club_ids_by_owner(conn, owner):
    if not owner:
        return []
    sql = "SELECT id,name FROM `{0}` WHERE uid={1}".format(table_name.club, owner)
    return conn.query(sql)


def get_all_club_ids_by_refer_uid(conn, refer_uid):
    sql = f"SELECT c.id FROM club AS c WHERE c.uid IN (SELECT uid FROM players WHERE invite_uid_2 = {refer_uid})"
    return conn.query(sql)
