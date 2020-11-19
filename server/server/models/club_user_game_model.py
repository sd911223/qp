# coding:utf-8

from utils import utils
from models import database
from .database import share_db_logs


def insert_or_update_same_player_game_count(club_id, uid, ref_uid):
    sql = f"INSERT INTO `club_user_game_count` " \
          f"SET club_id={club_id},uid={uid},ref_uid={ref_uid},count=1 ON DUPLICATE KEY " \
          f"UPDATE count=count+1"
    return share_db_logs().execute_rowcount(sql)


def remove_same_player_game_count(club_id, uid, ref_uids):
    sql = f"UPDATE club_user_game_count SET COUNT = 0 WHERE club_id = {club_id} AND" \
          f" uid = {uid} AND ref_uid NOT IN ({ref_uids})"
    return share_db_logs().execute_rowcount(sql)


def remove_same_player_game_count_by_uid(club_id, uid, ref_uids):
    sql = f"UPDATE club_user_game_count SET COUNT = 0 WHERE club_id = {club_id} AND" \
          f" uid NOT IN ({ref_uids}) AND ref_uid IN ({uid})"
    return share_db_logs().execute_rowcount(sql)


def query_same_table_player(club_id, uid, count):
    sql = f"SELECT * FROM club_user_game_count where club_id = {club_id} AND uid IN ({uid}) AND count >= {count}"
    return share_db_logs().query(sql)


def insert_same_player_game_logs(uid1, uid2, name1, name2, avatar1, avatar2, club_id, count=0):
    name1 = utils.filter_emoji(database.escape(name1))
    name2 = utils.filter_emoji(database.escape(name2))
    avatar1 = database.escape(avatar1)
    avatar2 = database.escape(avatar2)
    sql = "INSERT INTO `club_game_count_logs` " \
          f"SET uid1={uid1},uid2={uid2}," \
          f"name1='{name1}',name2='{name2}'," \
          f"avatar1='{avatar1}',avatar2='{avatar2}',club_id={club_id},count={count},time={utils.timestamp()}"
    return share_db_logs().execute_rowcount(sql)
