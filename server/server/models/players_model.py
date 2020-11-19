# coding:utf-8

from models import logs_model
from models import table_name
from utils import utils
from . import configs_model
from .database import share_db, share_db_logs


# 根据用户ID来获得用户信息
def get(uid):
    sql = "SELECT * FROM %s WHERE uid='%d' LIMIT 1" % (table_name.players, uid)
    return share_db().get(sql)


def dec_diamonds(uid, num):
    if not uid or not num:
        return 0
    sql = "UPDATE %s SET diamond=diamond-'%d' WHERE uid='%d' AND diamond>='%d' LIMIT 1" \
          % (table_name.players, num, uid, num)
    return share_db().execute_rowcount(sql)


def dec_la_jiao_dou(uid, num):
    if not uid or not num:
        return 0
    sql = "UPDATE %s SET la_jiao_dou=la_jiao_dou-'%d' WHERE uid='%d' AND la_jiao_dou>='%d' LIMIT 1" \
          % (table_name.players, num, uid, num)
    return share_db().execute_rowcount(sql)


def insert_many_many(start, length):
    sql = "INSERT IGNORE INTO players (uid, nick_name, avatar, sex, imei, imsi, mac, model, reg_time, channel_id, " \
          "platform, ver, diamond) VALUES ({0}, '{1}', '', 2, '{2}', '{3}', '{4}', '{5}', '122', 0, 0, '{6}', 10000)"
    for i in range(start, length):
        sql2 = sql.format(i, 'name' + str(i), 'imei' + str(i), 'imsi' + str(i),
                          'mac' + str(i), 'model' + str(i), 'abtest')
        share_db().execute(sql2)


# 机器人注册
def robot_sign_in(uid, level):
    if uid <= 0 or level <= 0:
        return 0
    urtime = utils.timestamp()
    chips = configs_model.get('signin_bonus_chip')
    sql = "INSERT INTO %s SET uid='%d',uchip=%d,utime=%d,urobot=%d" % \
          (table_name.players, uid, chips, urtime, level)
    return share_db().execute_rowcount(sql)


# 创建一个测试玩家
def add_test_account():
    sql = "INSERT IGNORE INTO %s SET uid=1,nick_name='test1',avatar='',imei='test1',imsi='test1'," \
          "mac='test1',model='test1',platform=0,ver='0',diamond=100" % (table_name.players,)
    return share_db().execute_rowcount(sql)


# 清除玩家上线时间
def clear_login_time(uid):
    sql = "UPDATE %s SET utime='%d' WHERE uid=%d LIMIT 1" % (table_name.players, 0, uid)
    return share_db().execute_rowcount(sql)


# 带检查的更新玩家的上线时间
def update_login_time(uid, is_straight_login):
    time_curr = utils.timestamp()
    time_today = utils.timestamp_today()
    uldays = "uldays=1" if not is_straight_login else "uldays = uldays+1"
    sql = "UPDATE %s SET utime='%d',%s WHERE uid=%d AND utime<'%d' LIMIT 1" % \
          (table_name.players, time_curr, uldays, uid, time_today)
    return share_db().execute_rowcount(sql)


# 增加玩家钻石
def add_diamonds(uid, diamonds):
    if diamonds <= 0 or uid <= 0:
        return 0
    sql = "UPDATE `{0}` SET diamond=diamond+{1} WHERE uid={2} LIMIT 1". \
        format(table_name.players, diamonds, uid)
    return share_db().execute_rowcount(sql)


# 增加玩家钻石 & 写入日志
def add_diamonds_with_log(uid, diamonds, refer_uid, refer_nick_name, reason_id, left_diamonds, memo=''):
    if add_diamonds(uid, diamonds) > 0:
        logs_model.add_diamonds_log(uid, diamonds, reason_id, 1, left_diamonds, refer_uid, refer_nick_name, memo)
        return 1
    return 0


def get_player_pdk_index(uid):
    sql = f"SELECT pdk_index from `players` WHERE uid={uid} LIMIT 1"
    return share_db().get(sql)


def get_diamond_by_uid(uid):
    sql = f"SELECT diamond,yuan_bao from `players` WHERE uid={uid} LIMIT 1"
    return share_db().get(sql)


def update_player_pdk_index(uid, idx):
    sql = f"UPDATE players SET pdk_index = {idx} WHERE uid={uid}"
    return share_db().execute_rowcount(sql)


def get_player_zzmj_index(uid):
    sql = f"SELECT zzmj_index from `players` WHERE uid={uid} LIMIT 1"
    return share_db().get(sql)


def update_player_zzmj_index(uid, idx):
    sql = f"UPDATE players SET zzmj_index = {idx} WHERE uid={uid}"
    return share_db().execute_rowcount(sql)


def update_player_score_with_reason(uid, score, reason, record_id=""):
    count = update_player_score(uid, score)
    if count == 1:
        sql = f'INSERT INTO player_score_logs set uid={uid},score={score},reason={reason},' \
            f'refer_id="{record_id}",time={utils.timestamp()}'
        return share_db_logs().execute_rowcount(sql)
    return 0


def update_player_club_today_game_count(uid, club_id):
    sql = f"UPDATE club_user SET today_game_round=today_game_round+1 WHERE club_id={club_id} and uid={uid}"
    return share_db().execute_rowcount(sql)


def update_player_score(uid, score, round_count=1):
    sql = f"UPDATE players SET score=score+{score},round_count=round_count+{round_count} WHERE uid={uid}"
    return share_db().execute_rowcount(sql)


def update_lock_score_by_club_id_and_uid(club_id, uid, lock_score, lock_table):
    sql = f"UPDATE club_user SET lock_score=lock_score+{lock_score},score=score-{lock_score},lock_table={lock_table}," \
        f"lock_time={utils.timestamp()} " \
        f"WHERE club_id={club_id} and uid={uid}"
    return share_db().execute_rowcount(sql)


def add_yuan_bao(uid, yuan_bao):
    sql = f"UPDATE `players` SET yuan_bao=yuan_bao+{yuan_bao} WHERE uid={uid} LIMIT 1"
    return share_db().execute_rowcount(sql)


def add_manage_yuan_bao(uid, yuan_bao):
    sql = f"UPDATE `players` SET manage_yuan_bao=manage_yuan_bao+{yuan_bao} WHERE uid={uid} LIMIT 1"
    return share_db().execute_rowcount(sql)


def dec_yuan_bao(uid, yuan_bao):
    sql = f"UPDATE `players` SET yuan_bao=yuan_bao-{yuan_bao} WHERE uid={uid} LIMIT 1"
    return share_db().execute_rowcount(sql)


def write_consume_logs(uid, club_id, union_id, count, pay_type, reason, time, status, record_id):
    sql = f"INSERT INTO `player_consume_logs` SET record_id='{record_id}', count={count}, club_id={club_id}, " \
        f"pay_type={pay_type}, reason={reason}, time={time},status={status},uid={uid}, union_id={union_id}"
    return share_db_logs().execute_rowcount(sql)


def write_admin_logs(uid, room_id, owner, count, time, record_id):
    sql = f"INSERT INTO `Rewards` SET record_id='{record_id}', Staues=0, " \
        f"reward_count={count},RoomId={room_id},Uid={owner},UserId={uid},CreationTime={time}"
    return share_db().execute_rowcount(sql)


def update_player_spring_activity(uid):
    sql = f'UPDATE spring_activity set last_game_time={utils.timestamp()},curr_score=curr_score+1 WHERE uid={uid}'
    return share_db().execute_rowcount(sql)

def get_is_lucker(uid):
    sql = f"SELECT is_lucker from `players` WHERE uid={uid} LIMIT 1"
    return share_db().get(sql)

if __name__ == "__main__":
    print(share_db())
    print(add_test_account())
