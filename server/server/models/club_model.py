from models import table_name, database
from utils.torndb import Connection
from utils import utils


# club 操作
def get_club(conn, club_id):
    if not conn or not club_id:
        return None
    club_id = int(club_id)
    sql = "SELECT * FROM `{0}` WHERE id={1} LIMIT 1".format(table_name.club, club_id)
    return conn.get(sql)


def get_club_over_score_and_reduce_score(club_id):
    sql = "SELECT over_score,reduce_score FROM `{0}` WHERE id={1} LIMIT 1".format(table_name.club, club_id)
    return database.share_db().get(sql)


def get_score_by_club_id_and_uid(club_id, uid):
    sql = "SELECT score FROM `{0}` WHERE club_id={1} and uid={2} LIMIT 1".format(table_name.club_user, club_id, uid)
    return database.share_db().get(sql)


def get_club_by_owner(conn: Connection, uid):
    if not conn or not uid:
        return list()
    uid = int(uid)
    sql = "SELECT * FROM `{0}` WHERE uid={1}".format(table_name.club, uid)
    return conn.query(sql)


def query_club_by_uid(conn: Connection, uid):
    if not conn or not uid:
        return list()

    uid = int(uid)
    sql = "SELECT * FROM `{0}` WHERE uid={1}".format(table_name.club_user, uid)
    return conn.query(sql)


def get_club_by_uid_and_club_id(conn: Connection, club_id, uid):
    if not conn or not uid or not club_id:
        return None

    uid = int(uid)
    club_id = int(club_id)
    sql = "SELECT * FROM `{0}` WHERE uid={1} AND club_id={2} LIMIT 1".format(table_name.club_user, uid, club_id)
    return conn.get(sql)


def query_all_data_by_club_id(conn, club_id):
    if not conn or not club_id:
        return list()

    sql = "SELECT * FROM `{0}` WHERE club_id={1}".format(table_name.club_user, club_id)
    return conn.query(sql)


# club_level_config
def get_club_level_config(conn, level):
    if not conn or not level:
        return list()
    level = int(level)
    sql = "SELECT * FROM `{0}` WHERE level={1} LIMIT 1".format(table_name.club_level_config, level)
    return conn.get(sql)


def get_all_club_level_config(conn):
    if not conn:
        return list()
    sql = "SELECT * FROM `{0}` LIMIT 1".format(table_name.club_level_config)
    return conn.query(sql)


def get_club_floor_config_by_floor(club_id, floor):
    sql = f"SELECT floor,play_config,auto_room FROM club_floor WHERE club_id = {club_id} AND floor = {floor}"
    return database.share_db().get(sql)


def get_player_money_by_club_id(club_id, uid):
    sql = f"SELECT score,lock_score FROM club_user WHERE club_id = {club_id} AND uid = {uid}"
    return database.share_db().get(sql)


def query_block_list(club_id, uid):
    sql = f"SELECT uid,ref_uid FROM club_block WHERE club_id={club_id} and (uid={uid} or ref_uid={uid})"
    return database.share_db().query(sql)
