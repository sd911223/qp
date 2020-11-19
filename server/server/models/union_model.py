from models import database, table_name
from utils import utils
from utils.torndb import Connection

UNION_SMALL_MANAGER = 10
UNION_SMALL_PARTNER = 11

game_db = 'zsw_game'
game_logs_db = 'zsw_game_logs'


def get_union_userinfo_by_uid(conn, uid):
    if not conn or not uid:
        return None
    sql = f"SELECT * FROM `union_user` WHERE uid={uid} LIMIT 1"
    return conn.get(sql)

def get_union_userinfo_by_uid_and_union_id(conn, uid, union_id):
    if not conn or not uid:
        return None
    sql = f"SELECT * FROM `union_user` WHERE uid={uid} and union_id={union_id} LIMIT 1"
    return conn.get(sql)

def query_all_small_union_manager(conn, union_id):
    if not conn or not union_id:
        return None
    sql = f"SELECT c.nick_name,c.avatar,a.uid,a.permission,a.tag_uid,a.tag_name,d.avatar as ref_avatar," \
        f"d.nick_name as ref_nick_name,d.uid as ref_uid " \
        f"FROM union_user AS a LEFT JOIN players AS c ON c.uid = a.uid LEFT JOIN players as d on " \
        f"a.union_user_id = d.uid WHERE a.union_id = {union_id} and " \
        f"a.permission = {UNION_SMALL_MANAGER}"
    return conn.query(sql)


def query_all_union_manager(conn, union_id):
    if not conn or not union_id:
        return None
    sql = f"SELECT c.nick_name,c.avatar,c.sex,a.uid,a.permission,a.join_time,a.game_round  " \
        f"FROM union_user AS a LEFT JOIN players AS c ON c.uid = a.uid WHERE a.union_id = {union_id} and " \
        f"a.permission <= {UNION_SMALL_MANAGER}"
    return conn.query(sql)


def query_all_union_users(conn, union_id):
    if not conn or not union_id:
        return None
    sql = f"SELECT c.nick_name,c.avatar,c.sex,a.uid,a.tag_uid,d.tag_name,d.avatar as tag_avatar " \
        f"FROM union_user AS a LEFT JOIN players AS c ON c.uid = a.uid LEFT JOIN players as d on a.tag_uid = d.uid" \
        f" WHERE a.union_id = {union_id}"
    return conn.query(sql)


def query_all_small_union_partner(conn, union_id, uid):
    if not conn or not union_id:
        return None
    sql = f"SELECT c.nick_name,c.avatar,a.uid,a.permission,a.tag_uid,a.tag_name,d.avatar as ref_avatar," \
        f"d.nick_name as ref_nick_name ,d.uid as ref_uid " \
        f"FROM union_user AS a LEFT JOIN players AS c ON c.uid = a.uid LEFT JOIN players as d on a.union_user_id = d.uid" \
        f" WHERE a.union_id = {union_id} and " \
        f"a.permission = {UNION_SMALL_PARTNER} and a.union_user_id = {uid}"
    return conn.query(sql)


def set_small_union_profit(conn, uid, union_id, refer_union_user_id, sub_floor, percent):
    if not conn or not uid:
        return 0
    if percent < 0 or percent > 100:
        return 0
    sql = f"INSERT INTO `union_energy_config` SET union_id={union_id},sub_floor={sub_floor},time={utils.timestamp()}," \
        f"uid={refer_union_user_id},operator_user={uid},energy_percent={percent}" \
        f" ON DUPLICATE KEY UPDATE energy_percent={percent}"
    return conn.execute_rowcount(sql)


def query_small_union_profit(conn, union_id, uid):
    sql = f"SELECT game_type,sub_floor,energy_percent as percent FROM `union_energy_config` WHERE union_id={union_id} and " \
        f"uid = {uid}"
    return conn.query(sql)


def query_small_union_users(conn, union_id, uid):
    sql = f"SELECT uid,energy,limit_energy  FROM `union_user` WHERE union_id={union_id} and union_user_id = {uid}"
    return conn.query(sql)


def query_small_union_users_only_id(conn, union_id, uid):
    sql = f"SELECT uid FROM `union_user` WHERE union_id={union_id} and union_user_id = {uid}"
    return conn.query(sql)


def query_small_union_partner_users(conn, union_id, uid):
    sql = f"SELECT uid,energy,limit_energy  FROM `union_user` WHERE union_id={union_id} and tag_uid = {uid}"
    return conn.query(sql)


def query_small_union_partner_users_only_id(conn, union_id, uid):
    sql = f"SELECT uid FROM `union_user` WHERE union_id={union_id} and tag_uid = {uid}"
    return conn.query(sql)


def create_union(conn, union_id, uid, name, notice, count, status, wechat=""):
    if not conn or not union_id or not uid:
        return 0

    inserts = dict()
    inserts['id'] = int(union_id)
    inserts['uid'] = int(uid)
    inserts['name'] = database.escape(str(name or ""))
    inserts['notice'] = str(notice or "")
    inserts['union_type'] = 0
    inserts['count'] = int(count or 0)
    inserts['status'] = int(status or 0)
    inserts['create_time'] = utils.timestamp()
    inserts['wechat'] = database.escape(wechat)

    insert_list = []
    for k, v in inserts.items():
        insert_list.append("{0}='{1}'".format(k, v))
    sql = "INSERT INTO `union` SET " + ",".join(insert_list)
    return conn.execute_rowcount(sql)


def join_union(conn, uid, union_id, tag_uid=-1, union_user_id=-1, permission=99):
    if not conn or not union_id or not uid:
        return 0

    inserts = dict()
    inserts['union_id'] = int(union_id)
    inserts['uid'] = int(uid)
    inserts['remark'] = str("")
    inserts['permission'] = int(permission)
    inserts['join_time'] = utils.timestamp()
    inserts['tag_uid'] = int(tag_uid)
    inserts['union_user_id'] = int(union_user_id)

    insert_list = []
    for k, v in inserts.items():
        insert_list.append("{0}='{1}'".format(k, v))
    sql = "INSERT INTO `{0}` SET " + ",".join(insert_list)
    sql = sql.format('union_user')
    return conn.execute_rowcount(sql)


def update_union_notice(conn, union_id, notice):
    if not conn or not union_id or not notice:
        return 0
    union_id = int(union_id)
    notice = database.escape(notice)
    notice = utils.filter_emoji(notice)
    sql = "UPDATE `{0}` SET notice='{1}' WHERE id={2}".format(table_name.union, notice, union_id)
    return conn.execute_rowcount(sql)


def update_union_name(conn, union_id, name):
    if not conn or not union_id or not name:
        return 0
    union_id = int(union_id)
    name = database.escape(name)
    name = utils.filter_emoji(name)
    sql = "UPDATE `{0}` SET name='{1}' WHERE id={2}".format(table_name.union, name, union_id)
    return conn.execute_rowcount(sql)


def get_union_info(conn, union_id):
    sql = f"SELECT a.id,a.union_type,b.uid,a.name,b.avatar,a.wechat,a.notice,b.nick_name as ownerName,a.count," \
        f"a.dismiss_time " \
        f"FROM `union` as a,`players` as b " \
        f"WHERE a.id={union_id} and a.uid = b.uid  LIMIT 1"
    return conn.get(sql)


def get_my_union_info(conn, union_id, uid):
    union_id = int(union_id)
    sql = f"SELECT a.id,a.union_type,b.uid,a.name,b.avatar,a.wechat,a.notice,b.nick_name as ownerName" \
        f",a.dismiss_time,a.count,c.energy,c.permission,c.game_round " \
        f"FROM `union` as a,`players` as b,`union_user` as c " \
        f"WHERE a.id={union_id} and a.uid = b.uid and c.uid = {uid} and c.union_id = a.id  LIMIT 1"
    return conn.get(sql)


# ----------- 楼层相关

def get_floor_by_union_id(conn, union_id):
    sql = f"SELECT id,game_type FROM union_floor WHERE union_id={union_id}"
    return conn.query(sql)


def get_sub_floor_by_floor(conn, floor):
    sql = f"SELECT id,play_config,match_config,auto_room,tip,game_type FROM union_sub_floor WHERE floor_id={floor}"
    return conn.query(sql)

def get_sub_floor_by_floor1(conn, floor):
    sql = f"SELECT id,play_config,match_config,auto_room,tip,game_type FROM union_sub_floor WHERE id={floor}"
    return conn.query(sql)

def del_sub_floor_by_sub_floor_and_union_id_and_game_type(conn, sub_floor, union_id, game_type):
    sql = f"DELETE FROM union_sub_floor WHERE id={sub_floor} AND union_id={union_id} AND game_type={game_type}"
    return conn.execute_rowcount(sql)


def query_union_floor_count_by_union_id(conn, union_id):
    sql = f"SELECT count(1) AS count FROM union_floor WHERE union_id={union_id}"
    return conn.get(sql)


def add_union_floor(conn, union_id, game_type):
    sql = f"INSERT INTO `union_floor` SET union_id={union_id},game_type={game_type}"
    return conn.execute_rowcount(sql)


def get_union_floor(conn, union_id, floor_id):
    sql = f"SELECT game_type FROM union_floor WHERE union_id={union_id} AND id={floor_id}"
    return conn.get(sql)


def edit_union_floor(conn, floor_id, game_type):
    sql = f"UPDATE `union_floor` SET game_type={game_type} WHERE id={floor_id}"
    return conn.execute_rowcount(sql)


def del_union_floor(conn, union_id, floor_id, game_type):
    sql = f"DELETE FROM `union_floor` WHERE id={floor_id} AND union_id={union_id} AND game_type={game_type}"
    return conn.execute_rowcount(sql)


def del_union_sub_floor(conn, floor_id):
    sql = f"DELETE FROM `union_sub_floor` WHERE floor_id={floor_id}"
    return conn.execute_rowcount(sql)


def query_union_sub_floor_count_by_union_id(conn, floor):
    sql = f"SELECT count(1) AS count FROM union_sub_floor WHERE floor_id={floor}"
    return conn.get(sql)


def get_union_sub_floor_config(conn, union_id, floor_id):
    sql = f"SELECT play_config,game_type FROM union_sub_floor WHERE union_id = {union_id} AND id = {floor_id}"
    return conn.get(sql)

def get_union_sub_floor_config1(conn, union_id, sub_floor_id):
    sql = f"SELECT play_config,game_type FROM union_sub_floor WHERE union_id = {union_id} AND id = {sub_floor_id}"
    return conn.get(sql)

def update_sub_floor_play_config(conn, union_id, play_config, sub_floor, auto_room, match_config, tip=0, tip_limit=0,
                                 tip_payment_method=0):
    if not conn or not union_id or not play_config or not sub_floor:
        return 0
    play_config = str(play_config)
    sql = f"UPDATE `union_sub_floor` SET play_config='{play_config}',match_type=1," \
        f"auto_room={auto_room},tip={tip},tip_limit={tip_limit},tip_payment_method={tip_payment_method},match_config='{match_config}'" \
        f" WHERE union_id={union_id} and id={sub_floor}"

    return conn.execute_rowcount(sql)


def insert_sub_floor_play_config(conn, union_id, floor, play_config, auto_room, game_type, match_config,
                                 tip=0, tip_limit=0, tip_payment_method=0):
    if not conn or not union_id or not play_config:
        return 0
    play_config = str(play_config)
    sql = f"INSERT INTO `union_sub_floor` SET union_id={union_id},match_type=1," \
        f"floor_id={floor},tip={tip},tip_limit={tip_limit},tip_payment_method={tip_payment_method},play_config='{play_config}',auto_room={auto_room}," \
        f"game_type={game_type},match_config='{match_config}'"

    return conn.execute_rowcount(sql)


def get_max_sub_floor_by_floor(conn, floor):
    sql = f"SELECT max(id) AS id FROM union_sub_floor WHERE floor_id={floor}"
    return conn.get(sql)


def query_all_uids_by_union_id(conn, union_id):
    if not conn or not union_id:
        return list()

    sql = "SELECT uid FROM `{0}` WHERE union_id={1}".format('union_user', union_id)
    return conn.query(sql)


# --------- 其他

def get_union_consume_diamond_by_time(conn_logs, union_id, start_time, end_time):
    sql = f"SELECT SUM(diamonds) AS diamonds FROM union_diamond_logs WHERE union_id = {union_id} " \
        f"AND time >={start_time} AND time <= {end_time}"
    count = conn_logs.get(sql)
    if count and count['diamonds']:
        return int(count['diamonds'])
    return 0


def query_union_all_users(conn, union_id):
    sql = f"SELECT c.nick_name,c.avatar,c.sex,a.remark,a.join_time,a.uid,a.permission,a.energy,b.login_time," \
        f"a.limit_energy,a.game_round,a.tag_uid " \
        f"FROM union_user AS a LEFT JOIN onlines AS b " \
        f"ON a.uid = b.uid LEFT JOIN players AS c ON c.uid = a.uid WHERE a.union_id = {union_id}"
    return conn.query(sql)


def query_union_users_by_small_manager_id(conn, union_id, small_manager_id):
    sql = f"SELECT c.nick_name,c.avatar,c.sex,a.remark,a.join_time,a.uid,a.permission,a.energy,b.login_time," \
        f"a.limit_energy,a.game_round,a.tag_uid " \
        f"FROM union_user AS a LEFT JOIN onlines AS b " \
        f"ON a.uid = b.uid LEFT JOIN players AS c ON c.uid = a.uid " \
        f"WHERE a.union_id = {union_id} and (a.union_user_id = {small_manager_id} or a.uid={small_manager_id})"
    return conn.query(sql)


def query_union_users_by_partner_id(conn, union_id, partner_id):
    sql = f"SELECT c.nick_name,c.avatar,c.sex,a.remark,a.join_time,a.uid,a.permission,a.energy,b.login_time," \
        f"a.limit_energy,a.game_round,a.tag_uid " \
        f"FROM union_user AS a LEFT JOIN onlines AS b " \
        f"ON a.uid = b.uid LEFT JOIN players AS c ON c.uid = a.uid " \
        f"WHERE a.union_id = {union_id} and (a.tag_uid = {partner_id} or a.uid={partner_id})"
    return conn.query(sql)


def update_permission_by_uid_and_union_id(conn, uid, union_id, permission=99):
    if not conn or not union_id or not uid:
        return 0

    sql = "UPDATE `{0}` SET permission={1} WHERE uid={2} AND union_id={3}". \
        format('union_user', permission, uid, union_id)
    return conn.execute_rowcount(sql)


def update_remark_by_uid_and_union_id(conn, uid, union_id, remark):
    if not conn or not union_id or not uid:
        return 0

    remark = database.escape(remark)
    remark = utils.filter_emoji(remark)

    sql = "UPDATE `{0}` SET remark='{1}' WHERE uid={2} AND union_id={3}". \
        format('union_user', remark, uid, union_id)
    return conn.execute_rowcount(sql)


def modify_union_tag_uid_to_owner_uid(conn, union_id, origin_tag_uid, owner=0):
    sql = f"UPDATE `union_user` SET tag_uid={owner} WHERE union_id={union_id} and tag_uid = {origin_tag_uid}"
    return conn.execute_rowcount(sql)


def modify_union_user_tag(conn, union_id, uid, tag_uid, tag_name, current_id=-1):
    tag_uid = int(tag_uid)
    tag_name = utils.filter_emoji(database.escape(tag_name))
    sql = f"UPDATE `union_user` SET tag_uid={tag_uid},tag_name='{tag_name}' WHERE " \
        f"union_id={union_id} AND uid={uid} "
    if current_id != -1:
        sql += f" and union_user_id={current_id}"
    return conn.execute_rowcount(sql)


def reduce_energy(conn, union_id, uid, energy):
    sql = f"UPDATE `union_user` SET energy=energy-{energy} WHERE union_id={union_id} " \
        f"and uid={uid} and energy>={energy} LIMIT 1"
    return conn.execute_rowcount(sql)


def add_energy(conn, union_id, uid, energy):
    sql = f"UPDATE `union_user` SET energy=energy+{energy} WHERE union_id={union_id} " \
        f"and uid={uid} LIMIT 1"
    return conn.execute_rowcount(sql)


def write_energy_log(conn_logs, union_id, uid, before_count, count, reason, refer_uid):
    sql = f"INSERT INTO `union_energy_logs` SET union_id={union_id},uid={uid},before_count={before_count}" \
        f",count={count},time={utils.timestamp()},type={reason},refer_uid={refer_uid}"
    return conn_logs.execute_rowcount(sql)


def query_energy_logs(conn_logs, union_id, uid):
    sql = f"SELECT c.nick_name,c.uid,c.avatar,a.before_count,a.count,a.type,a.time,a.refer_uid,d.nick_name " \
        f"as refer_nickname,d.avatar as refer_avatar " \
        f"FROM union_energy_logs AS a LEFT JOIN {game_db}.players AS c ON c.uid = a.uid LEFT JOIN {game_db}.players " \
        f"as d on a.refer_uid = d.uid " \
        f"WHERE a.union_id = {union_id} and a.type in (0,1) and (a.uid = {uid} or a.refer_uid = {uid}) " \
        f"order by time desc limit 100"
    return conn_logs.query(sql)


def query_transfer_energy_logs(conn_logs, union_id, uid):
    sql = f"SELECT c.nick_name,c.avatar,c.uid,a.count,a.type,a.time,a.refer_uid,d.nick_name " \
        f"as refer_nickname,d.avatar as refer_avatar " \
        f"FROM union_energy_logs AS a LEFT JOIN {game_db}.players AS c ON c.uid = a.uid " \
        f"LEFT JOIN {game_db}.players AS d on a.refer_uid = d.uid " \
        f"WHERE a.union_id = {union_id} and a.type = 2 and (a.uid = {uid} or a.refer_uid = {uid}) " \
        f"order by time desc limit 100"
    return conn_logs.query(sql)


def query_union_block_list(conn, union_id):
    sql = f"select a.block_status,a.uid as uid1,c.nick_name as name1," \
        f"a.ref_uid as uid2," \
        f"d.nick_name as name2 " \
        f"from union_block as a," \
        f"players as c,players as d where a.union_id = {union_id} " \
        f"and a.uid = c.uid and a.ref_uid = d.uid"
    return conn.query(sql)

def query_block_list(union_id, uid):
    sql = f"SELECT uid,ref_uid FROM union_block WHERE union_id={union_id} and (uid={uid} or ref_uid={uid})"
    return database.share_db().query(sql)


def add_union_block_list(conn, union_id, uid1, uid2, block_status):
    sql = f"INSERT INTO `union_block` SET union_id={union_id},uid={uid1},ref_uid={uid2}," \
        f"time={utils.timestamp()},block_status={block_status}"
    return conn.execute_rowcount(sql)


def remove_union_block_list(conn, union_id, uid1, uid2):
    sql = f"DELETE FROM `union_block` WHERE union_id={union_id} AND " \
        f"((uid={uid1} AND ref_uid={uid2}) OR " \
        f"(uid={uid2} AND ref_uid={uid1}))"
    return conn.execute_rowcount(sql)


def remove_union_user_by_uid(conn, union_id, uid):
    sql = f"DELETE FROM `union_user` WHERE union_id={union_id} AND uid={uid}"
    return conn.execute_rowcount(sql)


# 审核部分
def get_verify_list_record(conn: Connection, union_id):
    if not conn or not union_id:
        return list()
    union_id = int(union_id)
    sql = f"select p.nick_name,v.uid,v.update_time,v.status,v.operator_user from union_verify as v " \
        f"inner join players as p on v.uid = p.uid where v.union_id = {union_id} and v.status != 0 " \
        f"and DATE_SUB(CURATE(), INTERVAL 7 DAY) <= date(from_unixtime(update_time))"
    return conn.query(sql)


def get_verify_list_by_uid(conn: Connection, union_id, uid, status=0):
    union_id = int(union_id)
    status = int(status)
    sql = "SELECT * FROM `{0}` WHERE union_id={1} AND uid={2} AND status={3}". \
        format('union_verify', union_id, uid, status)
    return conn.query(sql)


def update_user_verify(conn, uid, union_id, status, ref_union_id=-1, verify_type=1, operator_name=""):
    if not conn or not union_id or not uid:
        return 0

    inserts = dict()
    inserts['union_id'] = int(union_id)
    inserts['uid'] = int(uid)
    inserts["status"] = int(status)
    inserts["ref_union_id"] = int(ref_union_id)
    inserts["type"] = int(verify_type)

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
    sql = sql.format('union_verify')
    return conn.execute_rowcount(sql)


def update_user_verify_by_id(conn, vid, status, operator_name="", operator_uid=-1, union_id=-1):
    update_time = utils.timestamp()
    if len(operator_name) > 0:
        operator_user = database.escape(operator_name)
    else:
        operator_user = ""
    sql = f"UPDATE `union_verify` SET update_time={update_time},status={status}," \
        f"operator_user='{operator_user}',operator_uid={operator_uid} where id={vid}"
    # sql = sql.format('union_verify')
    return conn.execute_rowcount(sql)


# --- 绑定部分调整
def merge_union_id(conn, from_union_id, to_union_id, to_union_user_uid):
    sql = f"UPDATE union_user set union_user_id = " \
        f"{to_union_user_uid},union_id={to_union_id},limit_energy=0 WHERE union_id={from_union_id}"
    return conn.execute_rowcount(sql)


def add_user_count(conn, union_id, count):
    sql = f"UPDATE `union` set count=count+{count} WHERE id={union_id}"
    return conn.execute_rowcount(sql)


def merge_union_adjust_permission(conn, from_union_id):
    sql = f"UPDATE union_user set permission = 10 WHERE union_id={from_union_id} and permission = 0"
    conn.execute_rowcount(sql)
    sql = f"UPDATE union_user set permission = 99 WHERE union_id={from_union_id} and permission = 1"
    conn.execute_rowcount(sql)
    return 1


def update_dismiss_time(conn, union_id):
    sql = f"UPDATE `union` set dismiss_time = {utils.timestamp()} WHERE union_id={union_id}"
    conn.execute_rowcount(sql)


def modify_union_user_id(conn, union_id, from_union_user_uid, to_union_user_uid):
    sql = f"UPDATE union_user set union_user_id = " \
        f"{to_union_user_uid} WHERE union_user_id={from_union_user_uid} and union_id = {union_id}"
    return conn.execute_rowcount(sql)


def modify_union_tag_id(conn, union_id, from_tag_user_uid, to_tag_user_uid):
    sql = f"UPDATE union_user set tag_uid = {to_tag_user_uid} " \
        f"WHERE tag_uid={from_tag_user_uid} and union_id = {union_id}"
    return conn.execute_rowcount(sql)


def update_union_user_id(conn, union_id, uid, union_user_id):
    if not conn or not union_id or not uid:
        return 0

    sql = "UPDATE `{0}` SET union_user_id={1} WHERE union_id={2} AND uid={3}". \
        format('union_user', union_user_id, union_id, uid)
    return conn.execute_rowcount(sql)


def get_union_floor_config(conn, union_id):
    sql = f"SELECT id,game_type FROM union_floor WHERE union_id = {union_id}"
    return conn.query(sql)


def get_union_game_by_logs_table(conn_logs, union_id):
    sql = f"SELECT DISTINCT game_type from room_logs WHERE union_id = {union_id} and " \
        f"DATE_SUB(CURDATE(), INTERVAL 7 DAY) <= date(from_unixtime(finish_time))"
    return conn_logs.query(sql)


# 桌子相关
def get_table_by_union_id_and_floor(conn, union_id, floor):
    if not conn or not union_id or not floor:
        return list()
    union_id = int(union_id)
    floor = int(floor)
    sql = f"SELECT * FROM `tables` WHERE union_id={union_id} AND floor={floor}"
    return conn.query(sql)


def get_table_by_union_id(conn, union_id):
    if not conn or not union_id:
        return list()
    union_id = int(union_id)
    sql = f"SELECT * FROM `tables` WHERE union_id={union_id}"
    return conn.query(sql)


def update_remark_by_uid_and_union_id(conn, uid, union_id, remark):
    if not conn or not union_id or not uid:
        return 0

    remark = database.escape(remark)
    remark = utils.filter_emoji(remark)

    sql = "UPDATE `{0}` SET remark='{1}' WHERE uid={2} AND union_id={3}". \
        format('union_user', remark, uid, union_id)
    return conn.execute_rowcount(sql)


def get_union_game_logs(conn_logs, union_id, start_time, end_time):
    sql = f"SELECT uid1,score1,uid2,score2,uid3,score3,uid4,score4,game_type from room_logs where " \
        f"union_id={union_id} and " \
        f"finish_time >= {start_time} and" \
        f" finish_time <= {end_time}"
    return conn_logs.query(sql)


def get_union_small_manager_game_logs(conn_logs, union_id, start_time, end_time, manager_uid):
    pass


def get_union_small_partner_game_logs(conn_logs, union_id, start_time, end_time, partner_uid):
    pass


def get_union_room_list(conn, union_id, uid=0, limit=1000):
    """查询战绩列表"""

    sql = "SELECT * FROM `{0}` WHERE union_id='{1}' ".format(table_name.room_logs, union_id)
    if uid != 0:
        sql += " and (uid1='{0}' OR uid2='{0}' OR uid3='{0}' OR uid4='{0}' " \
               ") ".format(uid)
    sql += "AND finish_time >= {0} ORDER BY finish_time DESC LIMIT {1}".format(utils.timestamp_today() - 48 * 60 * 60,
                                                                               limit)
    return conn.query(sql)


def get_union_room_list_by_manager(conn, union_id, manager_id, limit=1000):
    pass


def get_union_id(conn,union_id):
    sql = f'SELECT uid  FROM `union` WHERE id={union_id} '
    return conn.get(sql)

def get_union_room_list_by_partner(conn, union_id, partner_id, limit=1000):
    pass


def get_not_empty_energy_count_by_union_id(conn, union_id):
    sql = f'SELECT COUNT(1) as count FROM union_user WHERE union_id={union_id} and (energy<>0 or lock_energy<>0)'
    return conn.get(sql)


def get_verify_by_id(conn: Connection, v_id):
    v_id = int(v_id)
    sql = f"SELECT * FROM `union_verify` WHERE id={v_id}"
    return conn.get(sql)


def query_verify_list(conn: Connection, union_id, status=0):
    if not conn or not union_id:
        return list()
    union_id = int(union_id)
    status = int(status)
    sql = "SELECT * FROM `{0}` WHERE union_id={1} AND status={2}".format('union_verify', union_id, status)
    return conn.query(sql)


def query_verify_list_record(conn: Connection, union_id):
    if not conn or not union_id:
        return list()
    union_id = int(union_id)
    sql = f"select p.nick_name,v.uid,v.update_time,v.status,v.operator_user from union_verify as v " \
        f"inner join players as p on v.uid = p.uid where v.union_id = {union_id} and v.status != 0 " \
        f"and DATE_SUB(CURATE(), INTERVAL 7 DAY) <= date(from_unixtime(update_time))"
    return conn.query(sql)


def query_verify_list_left_join_player_left_join_union(conn: Connection, union_id, status=0):
    if not conn or not union_id:
        return list()
    union_id = int(union_id)
    status = int(status)
    sql = f"SELECT v.id,v.uid,p.nick_name,p.avatar,v.time,v.type,v.ref_union_id,u.name as ref_union_name " \
        f"FROM `union_verify` v LEFT JOIN `union` as u on v.ref_union_id = u.id left join" \
        f" players as p on p.uid = v.uid  WHERE v.union_id={union_id} AND v.status={status}"
    return conn.query(sql)


def query_verify_list_record_join_player_join_union(conn: Connection, union_id):
    if not conn or not union_id:
        return list()
    one_week_before = utils.timestamp_before_7_days()
    sql = f"SELECT v.uid,p.nick_name,p.avatar,v.status,v.time,v.type,v.ref_union_id,u.name as ref_union_name," \
        f"v.operator_user,v.update_time " \
        f"FROM `union_verify` v LEFT JOIN `union` as u on v.ref_union_id = u.id left join" \
        f" players as p on p.uid = v.uid WHERE v.union_id={union_id} AND v.status!=0 and " \
        f"v.update_time >= {one_week_before}"
    return conn.query(sql)


def query_union_game_count_logs(conn_logs, union_id, status):
    sql = f"SELECT * from `union_game_count_logs` WHERE union_id = {union_id} and status={status} " \
        f"ORDER BY time desc LIMIT 50"
    return conn_logs.query(sql)


def set_union_game_count_logs(conn_logs, union_id, msg_id, status):
    sql = f"UPDATE `union_game_count_logs` SET status={status} WHERE union_id={union_id} AND id={msg_id}"
    return conn_logs.execute_rowcount(sql)


def get_sub_floor_by_union_id(conn, union_id):
    sql = f"SELECT id,game_type,match_config from union_sub_floor where union_id={union_id}"
    return conn.query(sql)


def query_energy_config_by_uid(conn, union_id, uid):
    sql = f"SELECT sub_floor,energy_percent from union_energy_config where union_id={union_id} and uid = {uid}"
    data = conn.query(sql)
    return data

def get_player_energy_by_union_id(union_id, uid):
    sql = f"SELECT energy,lock_energy FROM union_user WHERE union_id = {union_id} AND uid = {uid}"
    return database.share_db().get(sql)

def update_union_user_energy(uid, union_id, score, limit_score, game_score):
    sql = f"UPDATE `union_user` SET energy=energy+{score},lock_energy=0,lock_table=0,lock_time=0,game_round=game_round+1," \
          f"limit_energy=limit_energy+{limit_score}" \
          f" WHERE union_id={union_id} and uid={uid}"
    return database.share_db().execute_rowcount(sql)



def insert_union_user_energy_logs(uid, union_id, reason, before_score, score, record_id):
    sql = f"INSERT INTO `union_energy_logs` SET union_id={union_id}," \
          f"uid={uid},type={reason},before_count={before_score},count={score}," \
          f"time={utils.timestamp()}"
    return database.share_db_logs().execute_rowcount(sql)


#2019-11-19  添加
def compute_union(p,union_id,tid,score,subfloorid):
    ps = '<pl><uid>%d</uid><score>%d</score><iswin>%d</iswin></pl>'
    psa = []
    for i in p:
        psa.append( ps % tuple([ p[i]['uid'],score,p[i]['iswin'] ]) )
    list = "".join(psa)
    list = '<list>' + list + '</list>'
    pps = tuple([ list , union_id ,tid,subfloorid ])
    print( "call p_union('%s',%d,%d,%d)" %  pps )
    return  database.share_db().query("call p_union('%s',%d,%d,%d)" %  pps)

def getallenergy(union_id,uid):
    """
    获取所有的能量
    :param union_id:
    :param uid:
    :return:
    """
    pps = tuple([uid,union_id])
    return  database.share_db().query("call p_tiqu_unionuid(%d,%d)" %  pps)

def getenergybyuid(union_id,uid,selfuid):
    pps = tuple([selfuid,union_id,uid])
    return  database.share_db().query("call p_tiqu_unionuid1(%d,%d,%d)" %  pps)

def querysubfloortable(conn,union_id):
    sql = 'select d.id sub_floor,max(a.tid) tid from `tables` as a ' \
          f'inner join ' \
          f'union_sub_floor as d ' \
          f'on a.union_id=d.union_id and ' \
          f'a.sub_floor = d.id ' \
          f'where d.union_id = {union_id} and a.game_type in (42,21,66) ' \
          f'group by d.id '
    return conn.query(sql)

def querysubfloortable1(conn,union_id):
    sql = 'select d.id sub_floor, (@i:= @i+1) as tid '\
          'from union_sub_floor as d ,(SELECT @i:=0) as i ' \
          f'where d.union_id = {union_id} ' \
          'and d.game_type in (42,21,66) ' \
          'group by d.id '
    return conn.query(sql)

def queryandroid(conn,start:int,last:int):
    sql = f"select a.uid,0 jointime,0 tid,0 subfloorid ,a.nick_name nickname,1 roundIndex from players_android as a limit {start},{last}"
    return conn.query(sql)


def getalluniontables(union_id):
    data = database.share_redis_game().hgetall('autotable')
    data1 =[utils.json_decode(str(x,encoding='utf8')) for x in data.values() if utils.json_decode(str(x,encoding='utf8'))['union_id'] == union_id]
    data2 = database.share_redis_game().hgetall('table_info')

    sql = 'select a.id n from union_sub_floor as a ' \
          f'where a.union_id = {union_id} '
    n_data = database.share_db().query(sql)
    response_data = list()

    if len(n_data) > len(data1):
        print('fe')
        data5 = [str(x,encoding='utf8') for x in data.keys()]
        if len(data5) == 0:
            data5.append(0)
        notuids = ','.join(data5)
        sql = 'select a.tid,a.sub_floor,a.union_id,a.round_count from `tables` as a '\
              f'where a.union_id = 10000 and a.tid not in ({notuids})'
        n_tids = database.share_db().query(sql)
        for n in n_tids:
            tid = n['tid']
            n.pop('tid')
            data[tid] = n
            database.share_redis_game().hset('autotable',tid,utils.json_encode(n))

    for in_n in data2.keys():
        tid = int(in_n)
        b_tid  = str(tid).encode('utf-8')
        n_table = utils.json_decode(str(data2[in_n],encoding='utf8'))
        table = None
        totalRound = 8
        subfloor = 0
        if tid in data:
            table = data[tid]
        elif b_tid in data:
            table = data[b_tid]
        if table:
            if isinstance(table,str) or isinstance(table,bytes):
                table = utils.json_decode(str(table,encoding='utf8'))
            print(table)
            print(type(table))
            totalRound = table['round_count']
            subfloor = table['subfloor']
        nicknamelist = list()
        players = n_table['players']
        for np in players:
            nicknamelist.append(np['nickName'])
        response_data.append({'playerList':n_table['player_list'],
                              'nickname':nicknamelist,
                              'subFloor':subfloor,
                              'status':n_table['table_status'],
                              'totalRound':totalRound,
                              'tid':tid})


    print(response_data)
    usedtable = [int(x) for x in data2.keys() ]
    for nsub in n_data:
        pass

if __name__ == '__main__':
    getalluniontables(10000)
