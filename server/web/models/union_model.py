from models import database, table_name
from utils import utils
from utils.torndb import Connection

UNION_SMALL_MANAGER = 10
UNION_SMALL_PARTNER = 11

game_db = 'game'
game_logs_db = 'game_logs'


def get_union_userinfo_by_uid(conn, uid):
    if not conn or not uid:
        return None
    sql = f"SELECT * FROM `union_user` WHERE uid={uid} LIMIT 1"
    return conn.get(sql)
def get_union_userinfo_by_uidone(conn, uid,union_id):
    if not conn or not uid or not union_id:
        return None
    sql = f"select d.nick_name, d.avatar,d.uid,"\
        "(select cast(ifnull(sum(f.score),0) as char(10)) from union_cs as f "\
        "where a.union_id = f.union_id " \
        "and f.uid = a.uid ) score from `union_user` as a " \
        "inner join players as d " \
        "on a.uid = d.uid " \
        f"where a.union_id ={union_id} and  union_user_id={uid} and a.permission in (0,10,11) "
    return conn.query(sql)

def get_union_userinfoheadimage_by_uid(conn, uid):
    if not conn or not uid:
        return None
    sql = f"SELECT * FROM `union_user` WHERE uid={uid} LIMIT 1"
    return conn.get(sql)

def get_union_userinfo_by_uid1(conn, uid,union_id):
    if not conn or not uid:
        return None
    sql = f"SELECT * FROM `union_user` WHERE uid={uid}  and union_id={union_id} LIMIT 1"
    return conn.get(sql)

#查询保险箱余额
def query_union_safebox(conn, uid,union_id):
    if not conn or not uid:
        return None
    sql = f"call p_safebox_query({union_id},{uid});"
    return conn.get(sql)

def query_union_safebox_by_queryid(conn,uid,union_id,queryid):
    """
    根据queryid查询税钱
    :param conn:
    :param uid:
    :param union_id:
    :param queryid:
    :return:
    """
    if not conn or not uid:
        return None
    sql = f"select ifnull(sum(a.score),0.00) score from union_cs as a "\
        f"where a.union_id={union_id} and a.uid={uid} and a.queryid='{queryid}' and a.state = 0 "
    return conn.get(sql)

def get_union_userinfo_by_uid_and_union_id(conn, uid, union_id):
    if not conn or not uid or not union_id:
        return None
    sql = f"SELECT * FROM `union_user` WHERE uid={uid} and union_id ={union_id} LIMIT 1"
    return conn.get(sql)


def fetch_union_safebox(conn, uid,union_id,queryid):
    if not conn or not uid:
        return None
    sql = f"call p_safebox_fetch({union_id},{uid},'{queryid}')"
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
    sql = f"SELECT c.nick_name,c.avatar,c.sex,a.uid,a.tag_uid , d.avatar as tag_avatar " \
        f"FROM union_user AS a LEFT JOIN players AS c ON c.uid = a.uid LEFT JOIN players as d on a.tag_uid = d.uid" \
        f" WHERE a.union_id = {union_id}"
    return conn.query(sql)

# def query_union_cs_list(conn,union_id,valdiff):
#     if not conn or not union_id:
#         return None
#     sql = f"select a.*,d.nick_name,d.avatar from( " \
#         f"select a.union_id,a.uid, convert(sum(a.score) ,char(11))as score " \
#         f"from union_cs as a " \
#         f"where a.union_id = {union_id}  " \
#         f"and datediff(a.cs_date,now())=-{valdiff} "\
#         f"group by a.union_id,a.uid " \
#         f"order by score desc " \
#         f"limit 10 " \
#         f")as a " \
#         f"inner join " \
#         f"players as d " \
#         f"on a.uid = d.uid"
#     return conn.query(sql)

def query_union_cs_list(conn,union_id,valdiff):
    if not conn or not union_id:
        return None
    sql = f"select d.uid,d.nick_name,a.score,d.avatar from( " \
        f"select f.union_user_id,convert(sum(a.score) ,char(11))as score from(  " \
        f"select a.union_id,a.uid, sum(a.score) as score  " \
        f"from union_cs as a  " \
        f"where a.union_id = {union_id}  " \
        f"and datediff(a.cs_date,now())> -{valdiff}  " \
        f"group by a.union_id,a.uid " \
        f"order by score desc " \
        f")as a " \
        f"inner join " \
        f"union_user as f " \
        f"on a.uid = f.uid " \
        f"and f.union_id = {union_id} " \
        f"group by f.union_user_id " \
        f")as a " \
        f"inner join " \
        f"players as d  " \
        f"on a.union_user_id = d.uid "
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


def query_small_union_users(conn, union_id, small_union_id):
    sql = f"SELECT p.uid, p.nick_name, p.avatar, u.permission, u.energy, u.limit_energy " \
          f" FROM `union_user` u LEFT JOIN `players` p on u.uid = p.uid WHERE u.union_id = {union_id} " \
          f" and u.union_small_id = {small_union_id} "
    return conn.query(sql)
def query_small_union_users1(conn, union_id, small_union_id):
    sql = f"SELECT p.uid, p.nick_name, u.permission, u.energy, u.limit_energy " \
          f" FROM `union_user` u LEFT JOIN `players` p on u.uid = p.uid WHERE u.union_id = {union_id} " \
          f" and u.union_user_id={small_union_id}"
    return conn.query(sql)


def querysubfloortable(conn,union_id):
    sql = 'select d.id sub_floor,max(a.tid) tid from `tables` as a '\
          f'inner join ' \
          f'union_sub_floor as d ' \
          f'on a.union_id=d.union_id and ' \
          f'a.sub_floor = d.id ' \
          f'where d.union_id = {union_id} and a.game_type in (42,21,66) '\
          f'group by d.id '
    return conn.query(sql)

def queryandroid(conn,start:int,last:int):
    sql = f"select a.uid,0 jointime,0 tid,0 subfloorid ,a.nick_name nickname,1 roundIndex from players_android as a limit {start},{last}"
    return conn.query(sql)

def query_android(conn,num,uids):
    """
    查询机器人
    :param conn:
    :param num:
    :return:
    """
    ids = '0'
    for uid in uids:
        ids += ',%d' % uid['uid']
    sql = "select a.nick_name,a.uid from players as a "\
          f"where a.reg_time >= 1575698457 and a.reg_time < 1584126135 and " \
          f"length(a.auto_token) > 10 and " \
          f"a.uid in({ids}) "\
          f"limit {num}"
    return conn.query(sql)

def query_small_union_users_only_id(conn, union_id, uid)->list:
    sql = f"SELECT uid FROM `union_user` WHERE union_id={union_id} and union_user_id = {uid}"
    return conn.query(sql)


def query_small_union_partner_users(conn, union_id, uid):
    sql = f"SELECT uid,energy,limit_energy  FROM `union_user` WHERE union_id={union_id} and tag_uid = {uid}"
    return conn.query(sql)


def query_small_union_partner_users_only_id(conn, union_id, uid):
    sql = f"SELECT uid FROM `union_user` WHERE union_id={union_id} and (uid = {uid} or union_user_id={uid} )"
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


def join_union(conn, uid, union_id, small_union_id=0, partner_id=0, tag_uid=-1, union_user_id=-1, permission=99):
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
    inserts['union_small_id'] = small_union_id
    inserts['partner_id'] = partner_id

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
        f",a.dismiss_time,a.count,c.energy,c.permission,c.game_round  " \
        f"FROM `union` as a,`players` as b,`union_user` as c " \
        f"WHERE a.id={union_id} and a.uid = b.uid and c.uid = {uid} and c.union_id = a.id  LIMIT 1"
    return conn.get(sql)

def get_my_energy(conn,union_id,uid):
    sql = f'select energy,permission from union_user as a where a.union_id={union_id} and a.uid={uid}'
    return conn.get(sql)

def get_my_energy1(conn,union_id,uid,uid1):
    sql = f'select a.energy,a.uid from union_user as a where a.union_id={union_id} and (a.uid={uid} or a.uid={uid1})'
    return conn.query(sql)

def get_my_union_info1(conn, union_id, uid):
    union_id = int(union_id)
    sql = f"SELECT   " \
          f"(select distinct count(f.uid) from `tables` as a inner join " \
          f"union_sub_floor as d " \
          f"on a.sub_floor = d.id " \
          f"inner join " \
          f"onlines as f " \
          f"on a.tid=f.tid " \
          f"inner join " \
          f"union_user as g  " \
          f"on d.union_id=g.union_id and " \
          f"f.uid = g.uid " \
          f"where d.union_id = {union_id} and f.state > 0) onlinenum , " \
          f"(select count(1) from union_user as a where a.union_id={union_id} ) unionnum "
    return conn.get(sql)

def get_my_union_info11(conn, union_id, uid):
    union_id = int(union_id)
    sql = f'select 0 onlinenum , a.count unionnum from `union` as a where a.id={union_id}'
    return conn.get(sql)
# ----------- 楼层相关

def get_floor_by_union_id(conn, union_id):
    sql = f"SELECT id,game_type FROM union_floor WHERE union_id={union_id}"
    return conn.query(sql)


def get_sub_floor_by_floor(conn, floor):
    sql = f"SELECT id,play_config,match_config,auto_room,tip,game_type FROM union_sub_floor WHERE floor_id={floor}"
    return conn.query(sql)


def del_sub_floor_by_sub_floor_and_union_id_and_game_type(conn, sub_floor, union_id, game_type = 0 ):
    sql = f"DELETE FROM union_sub_floor WHERE id={sub_floor} AND union_id={union_id} " # xingxing AND game_type={game_type}
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
    sql = f"SELECT count(1) AS count FROM union_sub_floor WHERE union_id={floor}"# xingxing
    return conn.get(sql)


def get_union_sub_floor_config(conn, union_id, floor_id):
    sql = f"SELECT play_config,game_type FROM union_sub_floor WHERE union_id = {union_id} AND id = {floor_id}"
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
def query_union_users_by_small_manager_id1(conn, union_id, small_manager_id,is_all):
    if True:
        sql = f"SELECT c.nick_name,c.sex,a.remark,a.uid,a.permission,a.energy," \
              f"a.limit_energy,a.game_round,a.tag_uid " \
              f"FROM union_user AS a " \
              f"inner JOIN players AS c ON c.uid = a.uid " \
              f"WHERE a.union_id = {union_id} and (a.union_user_id = {small_manager_id} or a.uid = {small_manager_id}  )"
    else:
        sql = f"SELECT c.nick_name,c.avatar,c.sex,a.remark,a.join_time,a.uid,a.permission,"\
              "(select cast(sum(energy) as char(10)) from union_user as g where FIND_IN_SET(g.uid,queryuser(a.uid,a.union_id))) energy,b.login_time," \
              f"a.limit_energy,a.game_round,a.tag_uid " \
              f"FROM union_user AS a LEFT JOIN onlines AS b " \
              f"ON a.uid = b.uid LEFT JOIN players AS c ON c.uid = a.uid " \
              f"WHERE a.union_id = {union_id} and (a.union_user_id = {small_manager_id} or a.uid={small_manager_id} )"
    return conn.query(sql)

def query_union_users_by_partner_id(conn, union_id, uid, partner_id):
    sql = f"SELECT c.nick_name,c.avatar,c.sex,a.remark,a.join_time,a.uid,a.permission,a.energy,b.login_time," \
        f"a.limit_energy,a.game_round,a.tag_uid " \
        f"FROM union_user AS a LEFT JOIN onlines AS b " \
        f"ON a.uid = b.uid LEFT JOIN players AS c ON c.uid = a.uid " \
        f"WHERE a.union_id = {union_id} and (a.partner_id = {partner_id} or a.uid={uid})"
    return conn.query(sql)
def query_union_users_by_partner_id1(conn, union_id, uid, partner_id,is_all):
    sql = None
    if True:
        sql = f"SELECT c.nick_name,c.avatar,c.sex,a.remark,a.join_time,a.uid,a.permission,a.energy,b.login_time," \
              f"a.limit_energy,a.game_round,a.tag_uid " \
              f"FROM union_user AS a LEFT JOIN onlines AS b " \
              f"ON a.uid = b.uid LEFT JOIN players AS c ON c.uid = a.uid " \
              f"WHERE a.union_id = {union_id} and  (a.union_user_id={uid} or a.uid={uid}  )"
    else:
        sql = f"SELECT c.nick_name,c.avatar,c.sex,a.remark,a.join_time,a.uid,a.permission," \
              f"(select cast(sum(energy) as char(10)) from union_user as g where FIND_IN_SET(g.uid,queryuser(a.uid,a.union_id))) energy,b.login_time," \
              f"a.limit_energy,a.game_round,a.tag_uid " \
              f"FROM union_user AS a LEFT JOIN onlines AS b " \
              f"ON a.uid = b.uid LEFT JOIN players AS c ON c.uid = a.uid " \
              f"WHERE a.union_id = {union_id} and  (a.union_user_id={uid} or a.uid={uid})"
    return conn.query(sql)

# 只保留直属玩家与合伙人
def query_union_users_by_union_id(conn, union_id):
    sql = f"SELECT c.nick_name,c.avatar,c.sex,a.remark,a.join_time,a.uid,a.permission,a.energy,b.login_time," \
          f"a.limit_energy,a.game_round,a.tag_uid " \
          f"FROM union_user AS a LEFT JOIN onlines AS b " \
          f"ON a.uid = b.uid LEFT JOIN players AS c ON c.uid = a.uid WHERE a.union_id = {union_id} "
    # and a.union_small_id = a.union_small_id
    return conn.query(sql)
def query_union_users_by_union_id1(conn, union_id,uid,is_all):
    if True:
        sql = f"SELECT c.nick_name,c.sex,a.remark,a.uid,a.permission,a.energy," \
              f"a.limit_energy,a.game_round,a.tag_uid " \
              f"FROM union_user AS a  " \
              f" inner JOIN players AS c ON c.uid = a.uid WHERE a.union_id = {union_id} and (a.union_user_id={uid} or a.uid={uid}  ) " \
              f"order by a.permission asc "
    else:
        sql = f"SELECT c.nick_name,c.avatar,c.sex,a.remark,a.join_time,a.uid,a.permission,"\
              "(select cast(sum(energy) as char(10)) from union_user as g where FIND_IN_SET(g.uid,queryuser(a.uid,a.union_id)))energy,b.login_time," \
              f"a.limit_energy,a.game_round,a.tag_uid " \
              f"FROM union_user AS a LEFT JOIN onlines AS b " \
              f"ON a.uid = b.uid LEFT JOIN players AS c ON c.uid = a.uid WHERE a.union_id = {union_id} and a.union_user_id={uid} "
    # and a.union_small_id = a.union_small_id
    return conn.query(sql)

def query_cs_log(conn,union_id,uid,datetime):
    """
    查询保险箱提取记录
    :param conn:
    :param union_id:
    :param uid:
    :param datetime:
    :return:
    """
    if not conn or not union_id or not uid:
        return 0
    sql = f"select cast(a.score as char(10))as score,cast(a.addtime as char(16)) as addtime from union_cs_log as a where a.union_id={union_id} and a.uid={uid} and datediff(a.addtime,'{datetime}')=0 "
    return conn.query(sql)
def save_cs_log(conn,union_id,uid,score,queryid):
    """
    保存保险箱提取记录
    :param conn:
    :param union_id:
    :param uid:
    :param score:
    :return:
    """
    if not conn or not union_id or not uid:
        return 0
    sql = f"insert into union_cs_log set union_id={union_id},uid={uid},score={score},addtime=now(),queryid='{queryid}'"
    return conn.execute_rowcount(sql)

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


def write_energy_log(conn_logs, union_id, uid, before_count, count, reason, refer_uid ,after_count):
    sql = f"INSERT INTO `union_energy_logs` SET union_id={union_id},uid={uid},before_count={before_count}" \
        f",count={count},time={utils.timestamp()},type={reason},refer_uid={refer_uid},after_count={after_count}"
    return conn_logs.execute_rowcount(sql)


def query_energy_logs(conn_logs, union_id, uid):
    sql = f"SELECT c.nick_name,c.uid,c.avatar,a.before_count,a.count,a.type,a.time,a.refer_uid,a.after_count,d.nick_name " \
        f"as refer_nickname,d.avatar as refer_avatar " \
        f"FROM union_energy_logs AS a LEFT JOIN {game_db}.players AS c ON c.uid = a.uid LEFT JOIN {game_db}.players " \
        f"as d on a.refer_uid = d.uid " \
        f"WHERE a.union_id = {union_id} and a.type in (0,1,2) and (a.uid = {uid} or a.refer_uid = {uid} ) " \
        f"order by time desc limit 50"
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


def update_user_verify(conn, uid, union_id, promo, status, ref_union_id=-1, verify_type=1, operator_name=""):
    if not conn or not union_id or not uid:
        return 0

    inserts = dict()
    inserts['union_id'] = int(union_id)
    inserts['uid'] = int(uid)
    inserts["status"] = int(status)
    inserts["ref_union_id"] = int(ref_union_id)
    inserts["type"] = int(verify_type)
    inserts["promo"] = int(promo)

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

#根据联盟和subfloor获取桌子
def get_table_by_union_id_and_subfloor(conn, union_id, floor):
    if not conn or not union_id or not floor:
        return list()
    union_id = int(union_id)
    floor = int(floor)
    sql = f"SELECT * FROM `tables` WHERE union_id={union_id} AND sub_floor={floor} order by tid asc"
    return conn.query(sql)

def get_table_by_union_id_and_subfloor1(conn,union_id,floor):
    if not conn or not union_id:
        return list()
    union_id = int(union_id)
    sql = f"select * from `tables` as a  "\
            f"where a.union_id = {union_id} and a.sub_floor={floor} "\
            f"and exists("\
            f"select * from onlines as d "\
            f"where a.tid = d.tid"\
            f") "\
            f"union  "\
            f"select * from `tables` as f where exists("\
            f"select * from("\
            f"select a.sub_floor,max(tid) tid from `tables` as a "\
            f"where a.union_id = {union_id} and a.sub_floor={floor} "\
            f"and not exists( "\
            f"select * from onlines as d "\
            f"where a.tid = d.tid "\
            f") "\
            f"group by a.sub_floor "\
            f") as g where f.tid = g.tid and f.sub_floor = g.sub_floor "\
            f")"
    return conn.query(sql)

def get_table_by_union_id(conn, union_id):
    if not conn or not union_id:
        return list()
    union_id = int(union_id)
    sql = f"SELECT * FROM `tables` WHERE union_id={union_id}"
    return conn.query(sql)

def get_table_by_union_id1(conn,union_id):
    if not conn or not union_id:
        return list()
    union_id = int(union_id)
    sql = f"select tid,sub_floor,round_count from `tables` as a  "\
            f"where a.union_id = {union_id} "\
            f"and exists("\
            f"select * from onlines as d "\
            f"where a.tid = d.tid"\
            f") "\
            f"union  "\
            f"select tid,sub_floor,round_count from `tables` as f where exists("\
            f"select * from("\
            f"select a.sub_floor,max(tid) tid from `tables` as a "\
            f"where a.union_id = {union_id} "\
            f"and not exists( "\
            f"select * from onlines as d "\
            f"where a.tid = d.tid "\
            f") "\
            f"group by a.sub_floor "\
            f") as g where f.tid = g.tid and f.sub_floor = g.sub_floor "\
            f")"
    return conn.query(sql)


def get1(union_id):
    from models import tables_model
    return tables_model.getuniontablebyunionid(union_id)


# def GetUnionTable(**kwargs):
#     database.connect('db').query()

def update_remark_by_uid_and_union_id(conn, uid, union_id, remark):
    if not conn or not union_id or not uid:
        return 0

    remark = database.escape(remark)
    remark = utils.filter_emoji(remark)

    sql = "UPDATE `{0}` SET remark='{1}' WHERE uid={2} AND union_id={3}". \
        format('union_user', remark, uid, union_id)
    return conn.execute_rowcount(sql)


def get_union_game_logs(conn_logs, union_id, start_time, end_time):
    sql = f"SELECT uid1,score1,avatar1,uid2,score2,avatar2,uid3,score3,avatar3,uid4,score4,avatar4," \
          f"uid5,score5,avatar5,uid6,score6,avatar6,uid7,score7,avatar7,uid8,score8,avatar8," \
          f"game_type from room_logs where " \
          f"union_id={union_id} and " \
          f"finish_time >= {start_time} and " \
          f"finish_time <= {end_time}"
    return conn_logs.query(sql)


def get_union_small_manager_game_logs(conn_logs, union_id, start_time, end_time, manager_uid):
    pass


def get_union_small_partner_game_logs(conn_logs, union_id, start_time, end_time, partner_uid):
    pass


def get_union_room_list(conn, union_id, uid=0, limit=50):
    """查询战绩列表"""
    timestapn = utils.timestamp_today()
    sql = "SELECT * FROM `{0}` WHERE union_id='{1}' ".format(table_name.room_logs, union_id)
    if uid != 0:
        sql += " and (uid1='{0}' OR uid2='{0}' OR uid3='{0}' OR uid4='{0}' " \
               "OR uid5='{0}' OR uid6='{0}' OR uid7='{0}' OR uid8='{0}' OR uid9='{0}' OR uid10='{0}' " \
               ") ".format(uid)
    sql += "and finish_time >= {0} ORDER BY finish_time DESC ".format(timestapn)
    data =  conn.query(sql)
    if len(data) < 50:
        num = 50 - len(data)
        sql = "SELECT * FROM `{0}` WHERE union_id='{1}' ".format(table_name.room_logs, union_id)
        if uid != 0:
            sql += " and (uid1='{0}' OR uid2='{0}' OR uid3='{0}' OR uid4='{0}' " \
                   "OR uid5='{0}' OR uid6='{0}' OR uid7='{0}' OR uid8='{0}' OR uid9='{0}' OR uid10='{0}' " \
                   ") ".format(uid)
        sql += "and finish_time < {0} ORDER BY finish_time DESC limit {1} ".format(timestapn,num)
        data1 =  conn.query(sql)
        data.extend(data1)
    return data



def get_union_room_list_by_manager(conn, union_id, manager_id, limit=1000):
    pass


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


def query_verify_list_left_join_player_by_promo(conn: Connection, promo, status=0):
    if not conn or not promo:
        return list()
    promo = int(promo)
    status = int(status)
    sql = f"SELECT v.id,v.uid,p.nick_name,p.avatar,v.time,v.type,v.ref_union_id,u.name as ref_union_name " \
          f"FROM `union_verify` v LEFT JOIN `union` as u on v.ref_union_id = u.id left join" \
          f" players as p on p.uid = v.uid  WHERE v.promo={promo} AND v.status={status}"
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


def query_verify_list_record_by_promo(conn: Connection, promo):
    if not conn or not promo:
        return list()
    one_week_before = utils.timestamp_before_7_days()
    sql = f"SELECT v.uid,p.nick_name,p.avatar,v.status,v.time,v.type,v.ref_union_id,u.name as ref_union_name," \
          f"v.operator_user,v.update_time " \
          f"FROM `union_verify` v LEFT JOIN `union` as u on v.ref_union_id = u.id left join" \
          f" players as p on p.uid = v.uid WHERE v.promo={promo} AND v.status!=0 and " \
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
    #sql = f"SELECT id,game_type,match_config from union_sub_floor where union_id={union_id}"
    sql = f"SELECT id,play_config,match_config,auto_room,tip,game_type FROM union_sub_floor  where union_id={union_id} "
    return conn.query(sql)


def query_energy_config_by_uid(conn, union_id, uid):
    sql = f"SELECT sub_floor,energy_percent from union_energy_config where union_id={union_id} and uid = {uid}"
    data = conn.query(sql)
    return data




# 2019年8月20日开始修改

# 联盟删除子楼层对应的桌子
def del_table_by_sub_floor_and_union_id_and_game_type(conn, sub_floor, union_id, game_type):
    # sql = f"DELETE FROM `tables` WHERE sub_floor={sub_floor} AND union_id={union_id}  " # xingxing AND game_type={game_type}
    # return conn.execute_rowcount(sql)
    from models import tables_model
    return  tables_model.remove_tablebysubfloorandunionid(union_id,sub_floor )



# 联盟子楼层修改对应桌子玩法
def update_table_play_config(conn, union_id, rules, sub_floor, game_type):
    if not conn or not union_id or not rules or not sub_floor or not game_type:
        return 0
    sql = f"UPDATE `tables` SET rules='{rules}' WHERE sub_floor={sub_floor} AND union_id={union_id} " \
          f"AND game_type={game_type}"

    return conn.execute_rowcount(sql)


# 联盟编辑游戏时删掉该楼层下所有的桌子
def del_union_floor_table(conn, floor, union_id):
    sql = f"DELETE FROM `tables` WHERE floor={floor} AND union_id={union_id} "
    return conn.execute_rowcount(sql)


def get_union_userinfo_by_uid_and_union_id(conn, uid, union_id):
    if not conn or not uid:
        return None
    sql = f"SELECT * FROM `union_user` WHERE uid={uid} and union_id={union_id} LIMIT 1"
    return conn.get(sql)
# 获取玩家对应玩法的抽水比例设置
def get_union_wf(conn,uid,union_id,seluid):
    if not conn or not uid or not union_id:
        return None
    sql = f"select 0 enterScore, cast(ifnull((select j.limitscore  from union_small_wf as j where j.union_id={union_id} and j.uid={seluid} and j.subfloorid=d.id),0) as char(10)) limitRate,ifnull(a.subfloorid,d.id) as subfloorid,d.game_type,d.play_config,cast(a.limitscore as char(10)) as limitscore,cast( case when a.score is null then 0 else a.score end as char(10)) as score "\
        "from union_sub_floor as d " \
        "left join " \
        "union_small_wf as a " \
        "on a.union_id = d.union_id and " \
        f"a.subfloorid = d.id and a.uid = {uid} " \
        f"where d.union_id = {union_id}  "
    return conn.query(sql)
def getpermission(conn,uid,union_id):
    if not conn or not uid:
        return None
    sql = f"select  a.permission from union_user as a where a.union_id={union_id} and a.uid={uid}"
    return conn.get(sql)
def queryroundandamountbytoday(conn,uid,union_id):
    """
    获取当前用户总局数和小计
    :param conn:
    :param uid:
    :param union_id:
    :return:
    """
    if not conn or not uid:
        return None
    sql = f"select  1 id,cast(count(distinct(pid)) as char(10)) num from union_cs as a where a.union_id={union_id} and a.uid={uid} and datediff(now(),a.cs_date)=0 "\
          f" union all "\
          f"select 2 id ,ifnull((select cast(sum(a.score) as char(10)) from union_cs as a where a.union_id={union_id} and a.uid={uid} and datediff(now(),a.cs_date)=0),0) "
    return conn.query(sql)

def querysaftboxlist(conn,uid,union_id,date):
    """
    返回保险箱抽水详情
    :param conn:
    :param uid:
    :param union_id:
    :return:
    """
    if not conn or not uid:
        return None
    sql = "select cast(a.score as char(10)) as score,concat(cast(month(a.cs_date) as char(10)),'-',cast(day(a.cs_date) as char(10)),' ',cast(hour(a.cs_date) as char(10)),':',cast(minute(a.cs_date) as char(10))) as cs_date,d.game_type,d.play_config,0 enterScore,a.from_userid,ifnull(g.nick_name,'') as nick_name from union_cs as a " \
          "inner join " \
          "union_sub_floor as d " \
          "on a.subfloorid = d.id " \
          "left join " \
          "players as g on a.from_userid=g.uid " \
          "where datediff(now(),a.cs_date) < 7 and " \
          f"datediff(a.cs_date,'{date}')=0 and "\
          f"a.union_id={union_id} and a.uid = {uid} " \
          "order by a.cs_date asc "
    return conn.query(sql)
def get_union_userinfo_by_uid_and_union_idone(conn, uid, union_id):
    if not conn or not uid:
        return None
    sql = f"SELECT * FROM `union_user` WHERE uid={uid} and union_id={union_id} LIMIT 1"
    return conn.get(sql)

def create_small_union(conn, small_union_id, name, notice, count, status, union_id, promo, uid, divide, remark):
    if not conn or not union_id or not uid or not small_union_id:
        return 0

    inserts = dict()
    inserts['id'] = int(small_union_id)
    inserts['uid'] = int(uid)
    inserts['name'] = database.escape(str(name or ""))
    inserts['notice'] = str(notice or "")
    inserts['union_id'] = int(union_id)
    inserts['count'] = int(count or 0)
    inserts['status'] = int(status or 0)
    inserts['create_time'] = utils.timestamp()
    # inserts['wechat'] = database.escape(wechat)
    inserts['promo'] = int(promo)
    inserts['divide'] = int(divide)
    inserts['remark'] = database.escape(remark)

    insert_list = []
    for k, v in inserts.items():
        insert_list.append("{0}='{1}'".format(k, v))
    sql = "INSERT INTO `union_small` SET " + ",".join(insert_list)
    return conn.execute_rowcount(sql)


def get_small_union_by_id(conn, small_union_id):
    if not conn or not small_union_id:
        return None
    sql = f"SELECT * FROM `union_small` WHERE id={small_union_id} LIMIT 1"
    return conn.get(sql)


def get_small_union_by_owner_id(conn, owner_id):
    if not conn or not owner_id:
        return None
    sql = f"SELECT id,cast(divide as char(10)) as divide,promo FROM `union_small` WHERE uid={owner_id} LIMIT 1"
    return conn.get(sql)


def get_small_union_by_owner_id1(conn, owner_id,union_id):
    if not conn or not owner_id:
        return None
    sql = f"SELECT id,cast(divide as char(10)) as divide,promo FROM `union_small` WHERE id={owner_id} and union_id={union_id} LIMIT 1"
    return conn.get(sql)

def get_small_union_by_owner_id_and_union_id(conn, owner_id, union_id):
    if not conn or not owner_id or not union_id:
        return None
    sql = f"SELECT * FROM `union_small` WHERE uid={owner_id} and union_id={union_id} LIMIT 1"
    return conn.get(sql)


def create_union_partner(conn, partner_id, name, uid, union_id, small_union_id, parent_id, promo, divide, remark, notice, status):
    if not conn or not union_id or not uid:
        return 0

    inserts = dict()
    inserts['id'] = int(partner_id)
    inserts['uid'] = int(uid)
    inserts['name'] = database.escape(name)
    inserts['union_id'] = int(union_id)
    inserts['union_small_id'] = int(small_union_id)
    inserts['parent_id'] = int(parent_id)
    inserts['promo'] = int(promo)
    inserts['divide'] = int(divide)
    inserts['notice'] = str(notice or "")
    inserts['status'] = int(status or 0)
    inserts['create_time'] = utils.timestamp()
    inserts['remark'] = database.escape(remark)

    insert_list = []
    for k, v in inserts.items():
        insert_list.append("{0}='{1}'".format(k, v))
    sql = "INSERT INTO `union_partner` SET " + ",".join(insert_list)
    return conn.execute_rowcount(sql)


# 根据玩家ID 联盟ID 与小联盟ID 获取合伙人信息
def get_union_partner_by_id(conn, uid, union_id, small_union_id):
    if not conn or not uid:
        return None
    sql = f"SELECT * FROM `union_partner` WHERE uid={uid} and union_id={union_id} and union_small_id={small_union_id} LIMIT 1"
    return conn.get(sql)


# 根据合伙人ID获取合伙人信息
def get_union_partner_by_partner_id(conn, partner_id):
    if not conn or not partner_id:
        return None
    sql = f"SELECT * FROM `union_partner` WHERE id={partner_id} LIMIT 1"
    return conn.get(sql)
def get_union_partner_by_partner_id1(conn, partner_id):
    if not conn or not partner_id:
        return None
    sql = f"SELECT union_id FROM `union_user` WHERE uid={partner_id} LIMIT 1"
    return conn.get(sql)

def set_subfloorplaydivide(conn,union_id,uid,subfloorid,score,selfuid):
    """
    设置具体玩法抽水比例分数
    :param conn:
    :param union_id:
    :param uid:
    :param subfloorid:
    :param score:
    :return:
    """
    if not conn or not union_id or not uid or not subfloorid or not score:
        return 0
    sql = f"select cast(case when limitscore is null then 0 else limitscore end as char(10)) as score from union_small_wf as a where a.union_id={union_id} and a.uid={uid} and a.subfloorid={subfloorid}"
    data = conn.get(sql)
    if data and len(data) > 0:
        updatescore = float(data["score"])

        dataf = getpermission(conn,selfuid,union_id)
        if dataf["permission"] > 0:
            sql = f"select cast(case when limitscore is null then 0 else limitscore end as char(10)) as score from union_small_wf as a where a.union_id={union_id} and a.uid={selfuid} and a.subfloorid={subfloorid}"
            data = conn.get(sql)
            if not data:
                return 0
            if float(data["score"])  < score:
                return 0
        if score < updatescore:
            updatexiaji(conn,uid,union_id,updatescore-score,subfloorid)
        sql = f"update union_small_wf set score={score},limitscore={score} where union_id={union_id} and uid={uid} and subfloorid={subfloorid}"
    else:
        sql_subfloor = f"select a.play_config from union_sub_floor as a where a.id={subfloorid} and union_id={union_id}"
        datasubfloor = conn.get(sql_subfloor)
        play_config = datasubfloor["play_config"]
        data1 = utils.json_decode(play_config)
        limitRate = data1["matchConfig"]["limitRate"]
        if score > data1["matchConfig"]["limitRate"] :
            return 0
        sql_selfuid = f"select cast(case when score is null then 0 else score end as char(10)) as score,f.permission from union_small_wf as a right join union_user as f on a.union_id=f.union_id and a.uid=f.uid and subfloorid={subfloorid} where f.union_id={union_id} and f.uid={selfuid}"
        dataselfuid = conn.get(sql_selfuid)
        if dataselfuid:
            if float(dataselfuid["score"]) == 0 and dataselfuid["permission"] != 0:
                return 0
            elif float(dataselfuid["score"]) < score and dataselfuid["permission"] > 0:
                return 0
        if dataselfuid["permission"] == 0:
            sql = f"insert into union_small_wf set subfloorid={subfloorid},limitscore={score},union_id={union_id},uid={uid},score={score}"
        else:
            fscore = dataselfuid["score"]
            sql = f"insert into union_small_wf set subfloorid={subfloorid},limitscore={score},union_id={union_id},uid={uid},score={score}"
    return conn.execute_rowcount(sql)


def updatexiaji(conn,uid,union_id,score,subfloorid):
    if score <=0:
        return
    sql = f"select a.uid,cast(case when limitscore is null then 0 else limitscore end as char(10)) as score from union_small_wf as a inner join union_user as g on a.union_id=g.union_id and a.uid=g.uid where a.union_id={union_id} and g.union_user_id={uid} and a.subfloorid={subfloorid}"
    data = conn.query(sql)
    if not data:
        return
    if len(data) == 0:
        return
    for item in data:
        itemuid = item["uid"]
        updatescore = float(item["score"])
        if updatescore < score:
            sql = f"update union_small_wf set score=0,limitscore=0 where union_id={union_id} and uid={itemuid} and subfloorid={subfloorid}"
        else:
            sql = f"update union_small_wf set score=score-{score},limitscore={score} where union_id={union_id} and uid={itemuid} and subfloorid={subfloorid}"
        conn.execute_rowcount(sql)
        updatexiaji(conn,itemuid,union_id,score,subfloorid)


# 设置小联盟分成比例
def set_small_union_divide(conn, union_id, small_union_id, divide,uid):
    if not conn or not union_id or not small_union_id:
        return 0
    result =  get_small_union_by_owner_id1(conn,small_union_id,union_id)
    sql = ''
    from utils import utils
    if result and len(result) > 0:
        sql = f"UPDATE `union_small` SET divide={divide} WHERE id={small_union_id} AND union_id={union_id} "
    else:
        sql = f"insert into  `union_small` SET divide={divide},uid={uid},union_id={union_id},id = {uid},promo={uid},create_time={utils.timestamp()},count=0,status=0 "

    return conn.execute_rowcount(sql)


# 设置合伙人分成比例
def set_union_partner_divide(conn, partner_id, divide):
    if not conn or not partner_id:
        return 0

    sql = f"UPDATE `union_partner` SET divide={divide} WHERE id ={partner_id}"
    return conn.execute_rowcount(sql)


# 设置小联盟名称
def set_small_union_name(conn, union_id, small_union_id, name):
    if not conn:
        return 0

    sql = f"UPDATE `union_small` SET name='{name}' WHERE id={small_union_id} AND union_id={union_id} "
    return conn.execute_rowcount(sql)


# 获取直属的小盟主或者合伙人信息
def get_sub_manager_or_partner_by_id(conn, uid, union_id, small_union_id, partner_id):
    if not conn:
        return list()

    sql = f"SELECT p.uid, p.nick_name, p.avatar, u.permission FROM `union_user` u LEFT JOIN `players` p " \
          f"on u.uid = p.uid WHERE u.union_id = {union_id} and u.permission < 99 and u.permission > 0 " \
          f"and u.union_small_id = {small_union_id} and u.partner_id = {partner_id}"
    return conn.query(sql)

def get_sub_manager_or_partner_by_id1(conn, uid, union_id, small_union_id, partner_id):
    if not conn:
        return list()

    sql = f"SELECT p.uid, p.nick_name, p.avatar, u.permission FROM `union_user` u LEFT JOIN `players` p " \
          f"on u.uid = p.uid WHERE u.union_id = {union_id} and u.permission < 99 and u.permission > 0 " \
          f"and u.union_user_id={small_union_id}"
    return conn.query(sql)

def get_sub_manager_or_partner_by_id1(conn,union_id,uid):
    if not conn:
        return list()
    sql = f"SELECT cast(ifnull(g.divide,0) as char(10)) divide ,p.uid, p.nick_name, p.avatar, u.permission FROM `union_user` u LEFT JOIN `players` p " \
        f"on u.uid = p.uid left join union_small as g on u.union_id=g.union_id and u.uid=g.uid WHERE u.union_id = {union_id} and u.permission in ( 0,10,11 )and  u.union_user_id={uid} "
    return conn.query(sql)


def query_union_partner_users(conn, union_id, small_union_id, partner_id):
    if not conn:
        return list()

    sql = f"SELECT p.uid, p.nick_name, u.permission, u.energy, u.limit_energy " \
          f" FROM `union_user` u LEFT JOIN `players` p on u.uid = p.uid WHERE u.union_id = {union_id}" \
          f" and u.union_user_id={small_union_id}"
    return conn.query(sql)

