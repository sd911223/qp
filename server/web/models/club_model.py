from models import database
from models import table_name
from utils import utils
from utils.torndb import Connection


# club 操作
def get_club(conn, club_id):
    if not conn or not club_id:
        return None
    club_id = int(club_id)
    sql = "SELECT * FROM `{0}` WHERE id={1} LIMIT 1".format(table_name.club, club_id)
    return conn.get(sql)


def get_all_club_count_without_dismiss_time(conn):
    if not conn:
        return 0
    sql = "SELECT COUNT(1) as count FROM `{0}` WHERE dismiss_time=0".format(table_name.club)
    return conn.get(sql)


def get_club_waiting_table(conn, club_id):
    if not conn:
        return []
    sql = "SELECT tid FROM `{0}` WHERE club_id={1} and state=0".format(table_name.tables, club_id)
    return conn.query(sql)


def get_score_by_club_id_and_uid(conn, club_id, uid):
    sql = "SELECT score FROM `{0}` WHERE club_id={1} and uid={2} LIMIT 1".format(table_name.club_user, club_id, uid)
    return conn.get(sql)


def get_club_by_owner(conn: Connection, uid):
    if not conn or not uid:
        return list()
    uid = int(uid)
    sql = "SELECT * FROM `{0}` WHERE uid={1} AND status=0".format(table_name.club, uid)
    return conn.query(sql)


def get_club_by_owner_and_club_id(conn: Connection, uid, club_id):
    if not conn or not uid:
        return None
    uid = int(uid)
    club_id = int(club_id)
    sql = "SELECT * FROM `{0}` WHERE uid={1} AND id={2}".format(table_name.club, uid, club_id)
    return conn.get(sql)


def create_club(conn, club_id, uid, name, notice, level, count, status, auto_room, play_config="", wet_chat=""):
    if not conn or not club_id or not uid:
        return 0

    inserts = dict()
    inserts['id'] = int(club_id)
    inserts['uid'] = int(uid)
    inserts['name'] = database.escape(str(name or ""))
    inserts['notice'] = str(notice or "")
    inserts['level'] = int(level or 1)
    inserts['count'] = int(count or 0)
    inserts['status'] = int(status or 0)
    inserts['create_time'] = utils.timestamp()
    inserts['wet_chat'] = database.escape(wet_chat)

    insert_list = []
    for k, v in inserts.items():
        insert_list.append("{0}='{1}'".format(k, v))
    sql = "INSERT INTO `{0}` SET " + ",".join(insert_list)
    sql = sql.format(table_name.club)
    return conn.execute_rowcount(sql)


def delete_club(conn, club_id):
    if not conn or not club_id:
        return 0
    club_id = int(club_id)
    sql = "UPDATE `{0}` SET status=-1 WHERE id={1}".format(table_name.club, club_id)
    return conn.execute_rowcount(sql)


def dismiss_club(conn, club_id):
    if not conn or not club_id:
        return 0
    club_id = int(club_id)
    timestamp = utils.timestamp()
    sql = "UPDATE `{0}` SET dismiss_time={1} WHERE id={2}".format(table_name.club, timestamp, club_id)
    return conn.execute_rowcount(sql)


def update_club_player_count(conn, club_id, count):
    if not conn or not club_id or not count:
        return 0
    club_id = int(club_id)
    count = int(count)
    sql = "UPDATE `{0}` SET count=count+({1}) WHERE id={2}".format(table_name.club, count, club_id)
    return conn.execute_rowcount(sql)


def update_club_name(conn, club_id, name):
    if not conn or not club_id or not name:
        return 0
    club_id = int(club_id)
    name = database.escape(name)
    name = utils.filter_emoji(name)
    sql = "UPDATE `{0}` SET name='{1}' WHERE id={2}".format(table_name.club, name, club_id)
    return conn.execute_rowcount(sql)


def update_club_level(conn, club_id, level):
    if not conn or not club_id or not level:
        return 0
    club_id = int(club_id)
    level = int(level)
    sql = "UPDATE `{0}` SET level={1} WHERE id={2}".format(table_name.club, level, club_id)
    return conn.execute_rowcount(sql)


def update_club_auto_room_count(conn, club_id, auto_room_count, floor):
    if not conn or not club_id or not auto_room_count:
        return 0
    club_id = int(club_id)
    auto_room_count = int(auto_room_count)
    floor = int(floor)
    sql = f"UPDATE `club_floor` SET auto_room={auto_room_count} WHERE club_id={club_id} and floor={floor}"
    return conn.execute_rowcount(sql)


def update_club_tag_id(conn, club_id, origin_tag_id, to_tag_id):
    club_id = int(club_id)
    origin_tag_id = int(origin_tag_id)
    to_tag_id = int(to_tag_id)
    sql = f"UPDATE `club_user` SET tag_uid={to_tag_id} WHERE club_id={club_id} and tag_uid={origin_tag_id}"
    return conn.execute_rowcount(sql)


def update_club_notice(conn, club_id, notice):
    if not conn or not club_id or not notice:
        return 0
    club_id = int(club_id)
    notice = database.escape(notice)
    notice = utils.filter_emoji(notice)
    sql = "UPDATE `{0}` SET notice='{1}' WHERE id={2}".format(table_name.club, notice, club_id)
    return conn.execute_rowcount(sql)


def update_club_play_config(conn, club_id, play_config, floor):
    if not conn or not club_id or not play_config or not floor:
        return 0
    club_id = int(club_id)
    floor = int(floor)
    play_config = str(play_config)
    sql = f"UPDATE `club_floor` SET play_config='{play_config}' WHERE club_id={club_id} and floor={floor}"
    return conn.execute_rowcount(sql)


# club_user 操作
def join_club(conn, uid, club_id, club_owner, permission=99):
    if not conn or not club_id or not uid:
        return 0

    inserts = dict()
    inserts['club_id'] = int(club_id)
    inserts['club_owner'] = int(club_owner)
    inserts['uid'] = int(uid)
    inserts['remark'] = str("")
    inserts['permission'] = int(permission)
    inserts['join_time'] = utils.timestamp()
    inserts['tag_uid'] = int(club_owner)

    insert_list = []
    for k, v in inserts.items():
        insert_list.append("{0}='{1}'".format(k, v))
    sql = "INSERT INTO `{0}` SET " + ",".join(insert_list)
    sql = sql.format(table_name.club_user)
    return conn.execute_rowcount(sql)


def get_club_admin(conn, club_id):
    if not conn or not club_id:
        return list()

    club_id = int(club_id)
    sql = "SELECT * FROM `{0}` WHERE club_id={1} AND (permission=1 OR permission=0)".format(table_name.club_user,
                                                                                            club_id)
    return conn.query(sql)


def get_club_owner(conn, club_id):
    if not conn or not club_id:
        return None

    club_id = int(club_id)
    sql = "SELECT * FROM `{0}` WHERE club_id={1} AND permission=0 LIMIT 1".format(table_name.club_user, club_id)
    return conn.get(sql)


def update_permission_by_uid_and_club_id(conn, uid, club_id, permission=99):
    if not conn or not club_id or not uid:
        return 0

    sql = "UPDATE `{0}` SET permission={1} WHERE uid={2} AND club_id={3}". \
        format(table_name.club_user, permission, uid, club_id)
    return conn.execute_rowcount(sql)


def update_remark_by_uid_and_club_id(conn, uid, club_id, remark):
    if not conn or not club_id or not uid:
        return 0

    remark = database.escape(remark)
    remark = utils.filter_emoji(remark)

    sql = "UPDATE `{0}` SET remark='{1}' WHERE uid={2} AND club_id={3}". \
        format(table_name.club_user, remark, uid, club_id)
    return conn.execute_rowcount(sql)


def query_club_by_uid(conn: Connection, uid):
    if not conn or not uid:
        return list()

    uid = int(uid)
    sql = "SELECT * FROM `{0}` WHERE uid={1}".format(table_name.club_user, uid)
    return conn.query(sql)


def get_club_by_uid_and_club_id(conn, uid, club_id):
    uid = int(uid)
    sql = "SELECT * FROM `{0}` WHERE uid={1} and club_id={2}".format(table_name.club_user, uid, club_id)
    return conn.get(sql)


def delete_user(conn: Connection, club_id, uid):
    if not conn or not uid or not club_id:
        return 0

    uid = int(uid)
    club_id = int(club_id)
    sql = "DELETE FROM `{0}` WHERE uid={1} AND club_id={2}".format(table_name.club_user, uid, club_id)
    return conn.execute_rowcount(sql)


def query_all_data_by_club_id(conn, club_id):
    if not conn or not club_id:
        return list()

    sql = "SELECT * FROM `{0}` WHERE club_id={1}".format(table_name.club_user, club_id)
    return conn.query(sql)


def query_club_by_uid_and_club_id(conn: Connection, club_id, uid):
    if not conn or not uid or not club_id:
        return None
    sql = f"SELECT * FROM `club_user` WHERE club_id={club_id} AND uid={uid} LIMIT 1"
    return conn.get(sql)


# club_verify
def get_verify_list(conn: Connection, club_id, status=0):
    if not conn or not club_id:
        return list()
    club_id = int(club_id)
    status = int(status)
    sql = "SELECT * FROM `{0}` WHERE club_id={1} AND status={2}".format(table_name.club_verify, club_id, status)
    return conn.query(sql)


# club_verify
def get_verify_list_record(conn: Connection, club_id):
    if not conn or not club_id:
        return list()
    club_id = int(club_id)
    sql = f"select p.nick_name,v.uid,v.update_time,v.status,v.operator_user from club_verify as v " \
        f"inner join players as p on v.uid = p.uid where v.club_id = {club_id} and v.status != 0 " \
        f"and DATE_SUB(CURDATE(), INTERVAL 7 DAY) <= date(from_unixtime(update_time))"
    return conn.query(sql)


def get_verify_list_by_uid(conn: Connection, club_id, uid, status=0):
    club_id = int(club_id)
    status = int(status)
    sql = "SELECT * FROM `{0}` WHERE club_id={1} AND uid={2} AND status={3}". \
        format(table_name.club_verify, club_id, uid, status)
    return conn.query(sql)


def insert_user_with_copy_club(conn, club_id, users):
    if not conn or not club_id or not users:
        return -1
    row = 0
    # TODO : 事务支持?
    for user in users:
        sql = "INSERT INTO `{0}` SET uid={1},remark='{2}',permission={3},club_id={4},join_time={5}". \
            format(table_name.club_user, user['uid'], user['remark'], user['permission'], club_id, utils.timestamp())
        row += conn.execute_rowcount(sql)
    return row


def insert_user_in_club(conn, club_id, uid, tag_uid=0):
    sql = "INSERT INTO `{0}` SET uid={1},remark='',permission={2},club_id={3},join_time={4},tag_uid={5}". \
        format(table_name.club_user, uid, 99, club_id, utils.timestamp(), tag_uid)
    return conn.execute_rowcount(sql)


def update_user_verify(conn, uid, club_id, status, operator_name=""):
    if not conn or not club_id or not uid:
        return 0

    inserts = dict()
    inserts['club_id'] = int(club_id)
    inserts['uid'] = int(uid)
    inserts["status"] = int(status)

    if inserts["status"] == 0:
        inserts["time"] = utils.timestamp()
        inserts["update_time"] = 0
    else:
        inserts["update_time"] = utils.timestamp()
        if len(operator_name) > 0:
            inserts["operator_user"] = database.escape(operator_name)
        else:
            inserts["operator_user"] = ''
    insert_list = []
    for k, v in inserts.items():
        insert_list.append("{0}='{1}'".format(k, v))

    set_sql = ",".join(insert_list)
    sql = "INSERT INTO `{0}` SET " + set_sql + " ON DUPLICATE KEY UPDATE " + set_sql
    sql = sql.format(table_name.club_verify)
    return conn.execute_rowcount(sql)


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


def set_quit_club(conn, club_id, uid):
    if not conn or not club_id or not uid:
        return 0

    return delete_user(conn, club_id, uid)


def create_floor(conn, club_id, max_floor=3):
    for i in range(max_floor):
        floor = i + 1
        inserts = dict()
        inserts['club_id'] = int(club_id)
        inserts['floor'] = floor
        inserts['auto_room'] = 16
        insert_list = []
        for k, v in inserts.items():
            insert_list.append("{0}='{1}'".format(k, v))
        sql = "INSERT INTO `{0}` SET " + ",".join(insert_list)
        sql = sql.format(table_name.club_floor)
        conn.execute_rowcount(sql)


def get_club_floor_config(conn, club_id):
    sql = f"SELECT id,game_type FROM club_floor WHERE club_id = {club_id}"
    return conn.query(sql)


def get_club_floor_config_by_floor(conn, club_id, floor):
    sql = f"SELECT floor,play_config FROM club_floor WHERE club_id = {club_id} AND floor = {floor}"
    return conn.get(sql)


def set_club_owner(conn, club_id, owner):
    sql = f"UPDATE `club` SET uid={owner} WHERE id={club_id}"
    return conn.execute_rowcount(sql)


def query_dou_by_club_id_and_uid(conn_logs: Connection, club_id, uid):
    sql = f"SELECT count,time,reason FROM `club_send_log` WHERE club_id={club_id} " \
        f"AND uid={uid} ORDER BY TIME DESC LIMIT 20"
    return conn_logs.query(sql)


def query_consume_diamond_by_club_id(conn_logs, club_id, start_time, end_time):
    sql = f"SELECT sum(diamond) as diamond FROM `room_logs` WHERE " \
        f"club_id={club_id} AND finish_time>={start_time} and finish_time<={end_time}"
    return conn_logs.get(sql)


def query_club_total_dou(conn: Connection, club_id):
    if not conn:
        return None
    sql = f"SELECT sum(score) as score FROM `club_user` WHERE club_id={club_id}"
    return conn.get(sql)


def query_club_total_limit_dou(conn_logs: Connection, club_id, start_time, end_time):
    if not conn_logs:
        return None
    sql = f"SELECT sum(count) as score FROM `club_send_log` WHERE club_id={club_id} " \
        f"AND reason = 29 AND time>={start_time} AND time<={end_time}"
    return conn_logs.get(sql)


def query_user_info_by_club_id(conn, club_id):
    sql = f"SELECT a.uid,a.game_round,a.limit_score,a.score,a.game_score,a.add_score,a.minus_score,a.add_time," \
        f"a.minus_time,b.nick_name FROM `club_user` as a,`players` as b " \
        f"WHERE a.club_id={club_id} and a.uid = b.uid"
    return conn.query(sql)


def get_user_score_by_time(conn, club_id, uid, start_time, end_time):
    sql = f"SELECT sum(count) as score from club_send_log where club_id = {club_id}" \
        f" and uid={uid} and time>={start_time} and time <={end_time} and reason in (27,28,29)"
    return conn.get(sql)


def get_need_verify_data(conn, club_id):
    sql = f"SELECT id FROM club_verify WHERE club_id={club_id} AND update_time = 0 limit 1"
    return conn.get(sql)


def query_dou_oper_by_club_id(conn_logs: Connection, club_id):
    sql = f"SELECT b.uid,b.count,b.time,b.reason,c.nick_name as nickname" \
        f",d.nick_name as oper_nickname,b.before_count as score,a.lock_score FROM " \
        f"game_logs.club_send_log as b,game.club_user as a,game.players " \
        f"as c,game.players as d WHERE b.club_id={club_id} and b.uid = c.uid " \
        f"and b.operation_uid = d.uid and b.uid = a.uid and b.reason in (25,26) " \
        f"ORDER BY TIME DESC LIMIT 20"
    return conn_logs.query(sql)


def query_club_user_data_and_online_time_by_club_id(conn, club_id):
    if not conn or not club_id:
        return list()
    sql = "SELECT c.nick_name,c.avatar, a.uid,a.remark,a.permission,a.tag_name,a.tag_uid," \
          "a.join_time,b.login_time " \
          "FROM club_user AS a LEFT JOIN onlines AS b " \
          "ON a.uid = b.uid LEFT JOIN players AS c " \
        f"ON c.uid = a.uid WHERE a.club_id = {club_id}"
    return conn.query(sql)


def query_game_count_logs(conn_logs, club_id, status):
    sql = f"SELECT * from club_game_count_logs WHERE club_id = {club_id} and status={status} " \
        f"ORDER BY time desc LIMIT 50"
    return conn_logs.query(sql)


def set_club_game_count_logs(conn_logs, club_id, msg_id, status):
    sql = f"UPDATE `club_game_count_logs` SET status={status} WHERE club_id={club_id} AND id={msg_id}"
    return conn_logs.execute_rowcount(sql)


def add_club_block_list(conn, club_id, uid1, uid2, block_status):
    sql = f"INSERT INTO `club_block` SET club_id={club_id},uid={uid1},ref_uid={uid2}," \
        f"time={utils.timestamp()},block_status={block_status}"
    return conn.execute_rowcount(sql)


def remove_club_block_list(conn, club_id, uid1, uid2):
    sql = f"DELETE FROM `club_block` WHERE club_id={club_id} AND " \
        f"((uid={uid1} AND ref_uid={uid2}) OR " \
        f"(uid={uid2} AND ref_uid={uid1}))"
    return conn.execute_rowcount(sql)


def get_club_game_by_logs_table(conn_logs, club_id):
    sql = f"SELECT DISTINCT game_type from room_logs WHERE club_id = {club_id} and " \
        f"DATE_SUB(CURDATE(), INTERVAL 7 DAY) <= date(from_unixtime(finish_time))"
    return conn_logs.query(sql)


def modify_club_user_tag(conn, club_id, uid, tag_uid, tag_name):
    tag_uid = int(tag_uid)
    tag_name = utils.filter_emoji(database.escape(tag_name))
    sql = f"UPDATE `club_user` SET tag_uid={tag_uid},tag_name='{tag_name}' WHERE club_id={club_id} AND uid={uid}"
    return conn.execute_rowcount(sql)


def query_club_block_list(conn, club_id):
    sql = f"select a.block_status,a.uid as uid1,c.nick_name as name1," \
        f"a.ref_uid as uid2," \
        f"d.nick_name as name2 " \
        f"from club_block as a," \
        f"players as c,players as d where a.club_id = {club_id} " \
        f"and a.uid = c.uid and a.ref_uid = d.uid"
    return conn.query(sql)


def count_by_club_id_and_tag_id(conn, club_id, tag_uid):
    sql = f"SELECT COUNT(1) as count FROM club_user WHERE club_id={club_id} AND tag_uid={tag_uid}"
    return conn.get(sql)


def modify_club_winner_score(conn, club_id, score):
    sql = "UPDATE `{0}` SET query_winner_score={1} WHERE id={2}".format(table_name.club, score, club_id)
    return conn.execute_rowcount(sql)


def modify_club_tag_uid_to_owner_uid(conn, club_id, origin_tag_uid, owner):
    sql = f"UPDATE `club_user` SET tag_uid={owner} WHERE club_id={club_id} and tag_uid = {origin_tag_uid}"
    return conn.execute_rowcount(sql)


def get_club_consume_diamond_by_time(conn_logs, club_id, start_time, end_time):
    sql = f"SELECT SUM(diamonds) AS diamonds FROM club_diamond_logs WHERE club_id = {club_id} " \
        f"AND time >={start_time} AND time <= {end_time}"
    count = conn_logs.get(sql)
    if count and count['diamonds']:
        return int(count['diamonds'])
    return 0
