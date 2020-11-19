# coding:utf-8
import datetime
import random
from models import table_name
from models.database import share_db, escape
from models.database import share_redis_game as share_connect
from utils import utils

STATUS_WAITING = 0
STATUS_PLAYING = 1


def gettablesbyredis():
    data = share_connect().hgetall('redistables')
    tables = list()
    for tab in data.items():
        tables.append(utils.json_decode(str(tab[1],encoding='utf8')))
    return tables


def get_android_settings(union_id):
    """根据联盟编号获取机器人设置"""
    android = share_connect().hget('android_settings', union_id)
    if not android:
        sql = f'select minnum,maxnum,cast(start as char(10)) start,cast(end as char(10)) end ,state from unionAndroid as a where a.union_id={union_id}'
        sql = f'select concat( '\
              f'case when start1 < 10 then \'0\' else \'\' end, ' \
              f'start1,\':\', ' \
              f'case when start2 < 10 then \'0\' else \'\' end, ' \
              f'start2) `start`, ' \
              f'        concat( ' \
              f'case when end1 < 10 then \'0\' else \'\' end,  ' \
              f'end1,\':\', '\
              f'case when end2 < 10 then \'0\' else \'\' end, '\
              f'end2) `end`,a.maxnum,a.minnum,a.state from( ' \
              f'select hour(a.`start`)start1, ' \
              f'minute(a.`start`)start2, ' \
              f'hour(a.`end`)end1, ' \
              f'minute(a.`end`)end2,minnum,maxnum,state ' \
              f'from unionandroid as a where a.union_id={union_id}' \
              f')as a'
        android = share_db().get(sql)
        if android:
            share_connect().hset('android_settings',union_id,utils.json_encode(android))
    else:
        android = utils.json_decode(str(android,encoding='utf8'))
    return android



def get_online_uids():
    """获取在桌子里面玩家UID"""
    data = share_connect().hgetall('table_info')
    data = [utils.json_decode(str(x,encoding='utf8')) for x in data.values()]
    uids = list()
    for x in data:
        player_list = x.get('player_list')
        if not player_list:
            continue
        if len(player_list) == 0:
            continue
        uids.extend(player_list)
    return uids



def get_table_by_union(union_id,  sub_floor_id):
    """获取联盟桌子"""
    tables = gettablesbyredis()
    """根据条件筛选桌子"""
    data = [x for x in tables if x['union_id'] == union_id and
            x['sub_floor'] == (sub_floor_id if sub_floor_id > 0 else x['sub_floor'])]
    """定义结果集"""
    result = list()
    """定义每一个玩法只保留一个空桌子"""
    emptytablesubfloor = list()
    for tab in data:
        room_id = tab['tid']
        room = share_connect().hget('table_info', room_id) or b"{\"player_list\":[],\"players\":[],\"round_index\":1,\"table_status\":0}"
        room = str(room,encoding='utf8')
        room = utils.json_decode(room)
        players = room['players']
        lst = [x['nickName'] for x in players]
        lst_img = [x['avatar'] for x in players]
        table = dict(playerList=room['player_list'])
        table['nickname'] = lst
        table['subFloor'] = tab['sub_floor']
        table['status'] = room['table_status']
        table['totalRound'] = tab['round_count']
        table['tid'] = room_id
        table['roundIndex'] = 1
        table['img'] = lst_img
        if table['subFloor'] not in emptytablesubfloor and \
                len(table['playerList']) == 0:
            emptytablesubfloor.append(table['subFloor'])
            result.append(table)
        elif len(table['playerList']) > 0:
            result.append(table)
    return result





# 获得桌子数据
def get(tid):
    # sql = "SELECT * FROM `{0}` WHERE tid='{1}' LIMIT 1 ".format(table_name.tables, tid)
    # return share_db().get(sql)
    tables = gettablesbyredis()
    if not tables or len(tables) == 0:
        return {}
    if 'tid' not in tables[0]:
        return {}
    data = [x for x in tables if x['tid'] == tid]
    if len(data) > 0:
        return data[0]
    return {}


def get_by_server(sid, tid):
    # sql = "SELECT * FROM `{0}` WHERE tid='{1}' AND sid='{2}' ".format(table_name.tables, tid, sid)
    # return share_db().get(sql)
    tables = gettablesbyredis()
    if not tables or len(tables) == 0:
        return {}
    if 'sid' not in tables[0] or 'tid' not in tables[0]:
        return {}
    data = [x for x in tables if x['sid'] == sid and x['tid'] == tid]
    if len(data) > 0:
        return data[0]
    return {}


def get_count_by_club_id(club_id):
    # sql = "SELECT COUNT(*) as room_count FROM `{0}` WHERE club_id='{1}'".format(table_name.tables, club_id)
    # return share_db().get(sql)
    tables = gettablesbyredis()
    if not tables or len(tables) == 0:
        return {}
    if 'owner' not in tables[0]:
        return {}
    data = [x['tid'] for x in tables if x['club_id'] == club_id]
    return {'room_count':len(data)}


# 获得代开的所有桌子
def get_all_by_owner(owner):
    # sql = "SELECT * FROM `{0}` WHERE owner={1}".format(table_name.tables, owner)
    # return share_db().query(sql)
    tables = gettablesbyredis()
    if not tables or len(tables) == 0:
        return []
    if 'owner' not in tables[0]:
        return []
    data = [x for x in tables if x['owner'] == owner]
    return data


def get_all_by_owner_without_club(owner):
    # sql = "SELECT * FROM `{0}` WHERE owner={1} and club_id = -1".format(table_name.tables, owner)
    # return share_db().query(sql)
    tables = gettablesbyredis()
    if not tables or len(tables) == 0:
        return []
    if 'owner' not in tables[0] or 'is_agent' not in tables[0] or 'club_id' not in tables[0]:
        return []
    data = [x for x in tables if x['owner'] == owner and x['club_id'] == -1]
    return data


def remove(tid):
    if tid < 100000:
        return 1
    # sql = "DELETE FROM `{0}` WHERE tid={1} LIMIT 1".format(table_name.tables, int(tid))
    # return share_db().execute_rowcount(sql)
    tables = gettablesbyredis()
    if not tables or len(tables) == 0:
        return 0
    if 'tid' not in tables[0]:
        return 0
    data = [x['tid'] for x in tables if x['tid'] == tid]
    if len(data) > 0 :
        share_connect().hdel('redistables',tid)
    return len(data)


def modify_status_by_tid(status, tid):
    # sql = "UPDATE {0} SET state={1} WHERE tid={2}".format(table_name.tables, status, tid)
    # return share_db().execute_rowcount(sql)
    tables = gettablesbyredis()
    if not tables or len(tables) == 0:
        return 0
    if 'tid' not in tables[0]:
        return 0
    data = [x for x in tables if x['tid'] == tid]
    if len(data) > 0:
        data[0]['state'] = status
        share_connect().hset('redistables',tid,utils.json_encode(data[0]))
    return len(data)


def get_by_owner_diamonds(owner):
    conn = share_db()
    if not conn or not owner:
        return {}
    owner = int(owner)
    # sql = "SELECT sum(diamonds) as all_room_diamonds_count FROM `{0}` WHERE owner='{1}'".format(table_name.tables
    #                                                                                             , owner)
    # return conn.get(sql)
    tables = gettablesbyredis()
    if not tables or len(tables) == 0:
        return 0
    if 'owner' not in tables[0]:
        return 0
    data = [x['diamonds'] for x in tables if x['owner'] == owner]
    data =  sum(data)
    return {'all_room_diamonds_count':data}


def get_dai_kai_by_owner_and_status_without_club(owner, state):
    conn = share_db()
    if not conn or not owner:
        return {}
    owner = int(owner)
    # sql = "SELECT * FROM `{0}` WHERE owner={1} AND state='{2}' AND is_agent = 1 AND club_id=-1 LIMIT 1". \
    #     format(table_name.tables, owner, state)
    # return conn.get(sql)
    tables = gettablesbyredis()
    if not tables or len(tables) == 0:
        return {}
    if 'owner' not in tables[0] or 'is_agent' not in tables[0] or 'club_id' not in tables[0]:
        return {}
    data = [x for x in tables if x['owner'] == owner and x['is_agent'] == 1 and x['club_id'] == -1 and x['state'] == state]
    if len(data) > 0:
        return data[0]
    return {}


def get_dai_kai_count_by_owner(owner):
    conn = share_db()
    if not conn or not owner:
        return {}
    owner = int(owner)
    # sql = "SELECT COUNT(*) as room_count FROM `{0}` WHERE owner={1} and is_agent = 1".format(table_name.tables, owner)
    # return conn.get(sql)

    tables = gettablesbyredis()
    if not tables or len(tables) == 0:
        return {}
    if 'owner' not in tables[0] or 'is_agent' not in tables[0] or 'club_id' not in tables[0]:
        return {}
    data = [x['tid'] for x in tables if x['owner'] == owner and x['is_agent'] == 1]

    if len(data) > 0:
        return {'room_count':len(data)}
    return {'room_count':0}


def get_dai_kai_count_by_owner_without_club(owner):
    conn = share_db()
    if not conn or not owner:
        return {}
    owner = int(owner)
    # sql = "SELECT COUNT(*) as room_count FROM `{0}` WHERE owner={1} and is_agent = 1 and club_id=-1".format(
    #     table_name.tables, owner)
    # return conn.get(sql)

    tables = gettablesbyredis()
    if not tables or len(tables) == 0:
        return {}
    if 'owner' not in tables[0] or 'is_agent' not in tables[0] or 'club_id' not in tables[0]:
        return {}
    data = [x['tid'] for x in tables if x['owner'] == owner and x['is_agent'] == 1 and x['club_id'] == -1]
    if len(data) > 0:
        return {'room_count':len(data)}
    return {'room_count':0}


def insert(sid, game_type, tid, owner, is_agent, total_round, diamonds, rule_type, club_id, rules, group_id=-1,
           robot_id=-1, floor=-1, consume_type=0, match_type=0, sub_floor=-1, match_config={}, union_id=-1):
    if not tid or not owner or not total_round or not game_type or not rules:
        return 0
    sid = sid or 1  # 服务器ID
    inserts = dict()
    inserts['tid'] = int(tid)
    inserts["game_type"] = int(game_type)
    inserts["is_agent"] = int(is_agent)
    inserts['owner'] = int(owner)
    inserts['time'] = utils.timestamp()
    inserts['round_count'] = int(total_round)
    inserts['diamonds'] = diamonds
    inserts['sid'] = sid
    inserts['rule_type'] = int(rule_type)
    inserts['rules'] = escape(utils.json_encode(rules))
    inserts['match_config'] = escape(utils.json_encode(match_config))
    inserts['club_id'] = club_id
    inserts['group_id'] = group_id
    inserts['robot_id'] = robot_id
    inserts['floor'] = floor
    inserts['consume_type'] = consume_type
    inserts['match_type'] = match_type
    inserts['sub_floor'] = sub_floor
    inserts['union_id'] = union_id
    inserts['state'] = 0

    # insert_list = []
    # sql = "INSERT INTO `{0}` SET ".format(table_name.tables)
    # for k, v in inserts.items():
    #     insert_list.append("{0}='{1}'".format(k, v))
    # sql += ",".join(insert_list)
    # return share_db().execute_rowcount(sql)

    """直接把桌子放到redis里面，不放mysql里面"""
    share_connect().hset('redistables',inserts['tid'],utils.json_encode(inserts))
    return 1


# def insert_many_tables(start, length):
#     import random
#     sql = "INSERT IGNORE INTO tables (tid, owner, state, time, round_count, diamonds, sid) " \
#           " VALUES ({0}, {1}, 0, 12345, {2}, {3}, 1)"
#     for i in range(start, length):
#         round_count = 8
#         diamonds = int(round_count / 8)
#         owner = random.randint(10000, 20001)
#         sql2 = sql.format(i, owner, round_count, diamonds)
#         share_db().execute(sql2)


def close_tables_by_server(sid, game_type):
    """ 关闭某服务器的全部桌子 """
    # sql = "DELETE FROM `{0}` WHERE sid='{1}' AND game_type={2} and union_id=-1 ".format(table_name.tables, int(sid), game_type)
    # share_db().execute_rowcount(sql)  # 删除全部此服务器的桌子
    tables = gettablesbyredis()
    if not tables or len(tables) == 0:
        return 0
    if 'club_id' not in tables[0] or 'state' not in tables[0]:
        return 0
    data = [x['tid'] for x in tables if x['sid'] == sid and x['game_type'] == game_type \
            and x['union_id'] == -1]
    for i in data:
        share_connect().hdel('redistables',i)
    sql = "SELECT a.tid FROM `{0}` AS a LEFT JOIN `{1}` AS b ON a.tid=b.tid WHERE a.tid>0 AND b.tid IS null". \
        format(table_name.onlines, table_name.tables)
    sql = 'select a.tid from onlines as a'
    result = share_db().query(sql)
    tids = [x['tid'] for x in tables]
    effects = 0
    if result and len(result) > 0:
        tids = []
        for item in result:
            if item.tid not in tids:
                tids.append(str(item.tid))
        # sql = "UPDATE `{0}` SET tid=0 WHERE tid IN ({1})".format(table_name.onlines, ",".join(tids))
        effects = len(tids)
        for id in tids:
            share_connect().hdel('redistables',id)
    #share_db().execute_rowcount(sql)  # 将全部没有桌子的玩家的桌子ID清空
    return effects


def update_all_club_table_sid(to_sid, game_type):
    # sql = "UPDATE `{0}` SET sid={1} WHERE club_id!=-1 AND state=0 AND game_type={2}".format(table_name.tables,
    #                                                                                         int(to_sid), game_type)
    # return share_db().execute_rowcount(sql)
    tables = gettablesbyredis()
    if not tables or len(tables) == 0:
        return 0
    if 'owner' not in tables[0] or 'is_agent' not in tables[0] or 'club_id' not in tables[0]:
        return 0

    data = [x for x in tables if x['state'] == 0 and x['club_id'] != -1 and \
            x['game_type'] == game_type ]
    for i in data:
        i['sid'] = to_sid
        share_connect().hset('redistables',i['tid'],utils.json_encode(i))
    return len(data)


def delete_all_idle_and_daikai_tables(sid, game_type):
    # sql = "DELETE FROM `{0}` WHERE `sid`={1} AND `is_agent`=1 AND `state`=0 AND `game_type`={2} and union_id=-1 ". \
    #     format(table_name.tables, int(sid), int(game_type))
    # return share_db().execute_rowcount(sql)
    tables = gettablesbyredis()
    if not tables or len(tables) == 0:
        return 0
    if 'owner' not in tables[0] or 'is_agent' not in tables[0] or 'club_id' not in tables[0]:
        return 0

    data = [x['tid'] for x in tables if x['state'] == 0 and x['is_agent'] == 1 and \
            x['game_type'] == game_type and x['sid'] == sid and x['union_id'] == -1 ]
    for i in data:
        share_connect().hdel('redistables',i)
    return len(data)


def query_all_idle_and_daikai_tables_tid(sid, game_type):
    # sql = f"SELECT tid FROM `tables` WHERE `sid`={sid} AND `is_agent`=1 AND `state`=0 AND `game_type`={game_type}"
    # return share_db().query(sql)
    tables = gettablesbyredis()
    if not tables or len(tables) == 0:
        return []
    if 'owner' not in tables[0] or 'is_agent' not in tables[0] or 'club_id' not in tables[0]:
        return []

    data = [{'tid':x['tid']} for x in tables if x['state'] == 0 and x['is_agent'] == 1 and \
            x['game_type'] == game_type and x['sid'] == sid and x['union_id'] == -1 ]
    return data


def query_club_id_and_table_count():
    sql = "SELECT club.id,club.auto_room - COUNT(tables.tid) AS count FROM {0} LEFT JOIN {1} ON " \
          "tables.club_id = club.id".format(table_name.club, table_name.tables)
    return share_db().query(sql)


def update_table_info(room_id, data):
    if not share_connect():
        return 0
    key = "table_info"
    share_connect().hset(key, room_id, utils.json_encode(data))


def get_table_info(room_id):
    if not share_connect():
        return ""
    key = "table_info"
    data = utils.json_decode((share_connect().hget(key, room_id) or b"").decode("utf-8"))
    return data

def get_table_from_redis():
    if not share_connect():
        return ""
    key = "table_info"
    data = (share_connect().hgetall(key) or b"")
    return data

def query_table_with_not_start_and_club(club_id, floor):
    sql = f"SELECT tid FROM tables WHERE club_id = {club_id} and state = 0 and floor = {floor}"
    return share_db().query(sql)


def query_table_with_not_start_and_floor(floor):
    # sql = f"SELECT tid FROM tables WHERE floor = {floor} and state = 0"
    # return share_db().query(sql)
    tables = gettablesbyredis()
    if not tables or len(tables) == 0:
        return []
    if 'club_id' not in tables[0] or 'floor' not in tables[0]:
        return []
    data = [{'tid':x['tid']} for x in tables if x['state'] == 0 and x['floor'] == floor]
    return data


def query_table_with_not_start_and_club_and_sub_floor(club_id, sub_floor):
    # sql = f"SELECT tid FROM tables WHERE club_id = {club_id} and state = 0 and sub_floor = {sub_floor}"
    # return share_db().query(sql)
    tables = gettablesbyredis()
    if not tables or len(tables) == 0:
        return []
    if 'club_id' not in tables[0] or 'floor' not in tables[0]:
        return []
    data = [{'tid':x['tid']} for x in tables if x['state'] == 0 and x['sub_floor'] == sub_floor and \
            x['club_id'] == club_id]
    return data


def query_table_with_not_start_and_sub_floor(sub_floor):
    # sql = f"SELECT tid, rules FROM tables WHERE sub_floor = {sub_floor} and state = 0"
    # return share_db().query(sql)
    tables = gettablesbyredis()
    if not tables or len(tables) == 0:
        return []
    if 'club_id' not in tables[0] or 'floor' not in tables[0]:
        return []
    data = [{'tid':x['tid'],'rules':x['rules']} for x in tables if x['state'] == 0 and x['sub_floor'] == sub_floor]
    return data

#根据联盟编号和subfloor查找所有的桌子信息
def query_table_with_not_start_and_sub_floor2(sub_floor,union_id):
    # sql = f"SELECT tid, rules FROM tables WHERE sub_floor = {sub_floor} and state = 0 and union_id={union_id}  "
    # return share_db().query(sql)
    tables = gettablesbyredis()
    if not tables or len(tables) == 0:
        return []
    if 'club_id' not in tables[0] or 'floor' not in tables[0]:
        return []
    data = [{'tid':x['tid'],'rules':x['rules']} for x in tables if x['state'] == 0 and x['sub_floor'] == sub_floor and \
            x['union_id'] == union_id]
    return data

def query_table_with_not_start_and_sub_floor1(sub_floor,tid):
    # sql = f"SELECT tid FROM tables WHERE sub_floor = {sub_floor} and state = 0 and tid !={tid}"
    # return share_db().query(sql)
    tables = gettablesbyredis()
    if not tables or len(tables) == 0:
        return []
    if 'club_id' not in tables[0] or 'floor' not in tables[0]:
        return []
    data = [{'tid':x['tid']} for x in tables if x['state'] == 0 and x['sub_floor'] == sub_floor and \
            x['tid'] != tid]
    return data

def del_table_info(room_id):
    if not share_connect():
        return ""
    key = "table_info"
    return share_connect().hdel(key, room_id)


def get_count_by_club_id_and_floor(club_id, floor):
    # conn = share_db()
    # sql = f"SELECT COUNT(*) as room_count FROM `tables` WHERE club_id='{club_id}' and floor={floor}"
    # return conn.get(sql)
    tables = gettablesbyredis()
    if not tables or len(tables) == 0:
        return {}
    if 'club_id' not in tables[0] or 'floor' not in tables[0]:
        return {}
    data = [x['tid'] for x in tables if x['club_id'] == club_id and x['floor'] == floor]
    if len(data) > 0:
        return {'room_count':len(data)}
    return {"room_count":0}


def get_count_by_club_id_and_sub_floor(club_id, sub_floor_id):
    # conn = share_db()
    # sql = f"SELECT COUNT(*) as room_count FROM `tables` WHERE club_id='{club_id}' and sub_floor={sub_floor_id}"
    # return conn.get(sql)
    tables = gettablesbyredis()
    if not tables or len(tables) == 0:
        return {}
    if 'club_id' not in tables[0] or 'floor' not in tables[0]:
        return {}
    data = [x['tid'] for x in tables if x['club_id'] == club_id and x['sub_floor'] == sub_floor_id]
    if len(data) > 0:
        return {'room_count':len(data)}
    return {'room_count':0}

def get_count_by_union_id_and_sub_floor(union_id, sub_floor_id):
    # conn = share_db()
    # sql = f"SELECT COUNT(*) as room_count FROM `tables` WHERE union_id='{union_id}' and sub_floor={sub_floor_id}"
    # return conn.get(sql)
    tables = gettablesbyredis()
    if not tables or len(tables) == 0:
        return {}
    if 'club_id' not in tables[0] or 'floor' not in tables[0]:
        return {}
    data = [x['tid'] for x in tables if x['union_id'] == union_id and x['sub_floor'] == sub_floor_id]
    if len(data) > 0:
        return {'room_count':len(data)}
    return {"room_count":0}

def query_all_club_ids():
    sql = "SELECT id FROM {0} WHERE status = 0".format(table_name.club)
    return share_db().query(sql)


def get_total_idle_diamonds_by_uid(conn, uid):
    # sql = f"SELECT SUM(diamonds) as diamonds FROM `tables` WHERE owner='{uid}' " \
    #       f" and consume_type=0 and match_type=0"
    # data = conn.get(sql)
    # if not data or not data['diamonds']:
    #     return 0
    # return data['diamonds']
    tables = gettablesbyredis()
    if not tables or len(tables) == 0:
        return 0
    if 'owner' not in tables[0] or 'consume_type' not in tables[0] \
            or 'match_type' not in tables[0]:
        return 0
    data = [x['diamonds'] for x in tables if x['owner'] == uid and x['consume_type'] == 0 \
            and x['match_type'] == 0]

    return sum(data)


def query_all_sub_floor_by_club_id(club_id, game_type):
    sql = f"SELECT * FROM `club_sub_floor` WHERE club_id={club_id} and game_type={game_type}"
    return share_db().query(sql)


def get_sub_floor_by_id(sub_floor_id):
    sql = f"SELECT * FROM `club_sub_floor` WHERE id={sub_floor_id}"
    return share_db().get(sql)

def get_union_sub_floor_by_id(sub_floor_id):
    sql = f"SELECT * FROM `union_sub_floor` WHERE id={sub_floor_id}"
    return share_db().get(sql)

def get_auto_room_by_club_and_sub_floor(sub_floor):
    sql = f"SELECT auto_room as count FROM `club_sub_floor` WHERE id={sub_floor}"
    return share_db().get(sql)

def get_auto_room_by_union_and_sub_floor(sub_floor):
    sql = f"SELECT auto_room as count FROM `union_sub_floor` WHERE id={sub_floor}"
    return share_db().get(sql)


def get_total_match_idle_diamonds_by_uid(conn, uid):
    # sql = f"SELECT SUM(diamonds) as diamonds FROM `tables` WHERE owner='{uid}'  " \
    #       f"AND consume_type=0 AND match_type=1"
    # data = conn.get(sql)
    # if not data or not data['diamonds']:
    #     return 0
    # return data['diamonds']
    tables = gettablesbyredis()
    if not tables or len(tables) == 0:
        return 0
    if 'owner' not in tables[0] or 'consume_type' not in tables[0] \
            or 'match_type' not in tables[0]:
        return 0
    data = [x['diamonds'] for x in tables if x['owner'] == uid and x['consume_type'] == 0 \
            and x['match_type'] == 1]
    data = [x['diamonds'] for x in data]
    return sum(data)


def create_sub_floor_room( uid, auto_room_count, floor, sub_floor,union_id):
    from models import union_model
    subfloorresult =  union_model.get_sub_floor_by_floor1(share_db(),sub_floor)
    match_config = {}
    if not subfloorresult:
        return -1
    if len(subfloorresult) ==0:
        return -1
    from utils import utils

    params =  utils.json_decode(subfloorresult[0]['play_config'])

    match_config = utils.json_decode(subfloorresult[0]['match_config'])
    rules = params.get("rules") or params.get("ruleDetails")
    game_type = params["gameType"]
    from models import  game_room_model
    from models import  database
    sid = game_room_model.get_best_server_sid(share_db(), share_connect(), game_type)
    if not sid:
        return -2

    consume_type = params.get('consumeType')
    total_round = int(params["totalRound"])
    rule_type = params["ruleType"]
    diamonds = calc_sub_floor_diamonds(share_db(), total_round, game_type)
    match_type = params.get("matchType")
    from models import logs_model
    for i in range(auto_room_count):
        while True:
            tid = database.spop_table_id() or utils.get_random_num(6)
            try:
                insert( sid, game_type, int(tid), uid, 1, total_round,
                                    diamonds, rule_type, -1, rules, floor=floor, consume_type=consume_type,
                                    match_type=match_type, sub_floor=sub_floor, match_config=match_config,union_id=union_id)
            except Exception as data:
                logs_model.error(f"insert club table error: {-1} {data}")
                continue
            break
    return 0


def calc_sub_floor_diamonds(share_db, round_count: int, game_type):
    from models import room_config_model
    data = room_config_model.get_room_config( game_type)
    diamonds = utils.json_decode(data['data'])
    for i in diamonds["diamondInfo"]:
        if i['count'] == round_count:
            return i['diamond']
    return -1


def android(union_id: int, min_num: int, max_num: int, start: str, end: str):
    """"""
    from models import union_model, database
    result = list()
    tids = list()
    tablesubfloor = union_model.querysubfloortable1(database.share_db(),union_id)
    d_time = datetime.datetime.strptime(str(datetime.datetime.now().date())+start, '%Y-%m-%d%H:%M')
    d_time1 =  datetime.datetime.strptime(str(datetime.datetime.now().date())+end, '%Y-%m-%d%H:%M')
    n_time = datetime.datetime.now()
    ishas = False
    if n_time > d_time and n_time<d_time1:
        ishas = True
    else:
        ishas = False
    if len(tablesubfloor) >= 1 and True:
        ids = database.share_redis_game().hget('android',union_id)
        if ids != None:
            ids = utils.json_decode(str(ids,encoding='utf8') )
        if not ids or len(ids) == 0:
            android_num = random.randint(min_num,max_num)
            ids = union_model.queryandroid(database.share_db(), 0, android_num)
            random.shuffle(ids)
            for i, id in enumerate(ids):
                id['roundIndex'] = random.randint(1,5)
                id['jointime'] = utils.timestamp() + random.randint(10,60)
                tids.append(dict(tid=i, state=0))
                id['tid'] = i#tablesubfloor[(i + 1) % len(tablesubfloor)]['tid']
                id['subfloorid'] = tablesubfloor[(i + 1) % len(tablesubfloor)]['sub_floor']
            database.share_redis_game().hset('android',union_id,utils.json_encode(ids))
            database.share_redis_game().hset('androidtids',union_id,utils.json_encode(tids))
            print(ids)
        else:
            autotime = random.randint(2,10) * 60
            roundtime = random.randint(30,50)
            if isinstance(ids,str):
                ids = utils.json_decode(ids)
            round_person = random.randint(0,len(ids)-1)
            resultone = utils.timestamp() - ids[round_person]['jointime']
            if resultone > autotime or ids[round_person]['roundIndex'] >= 8:
                random.shuffle(ids)
                for i,id in  enumerate( ids ):
                    if id['roundIndex'] >= 8:
                        id['roundIndex'] = 1
                        id['jointime'] = utils.timestamp() + random.randint(10,60)
                        #id['tid'] = tablesubfloor[(i + 1) % len(tablesubfloor)]['tid']
                        id['subfloorid'] = tablesubfloor[(i + 1) % len(tablesubfloor)]['sub_floor']
                database.share_redis_game().hset('android',union_id,utils.json_encode(ids))
            if True:
                roundnum = random.randint(3,7)
                #random.shuffle(ids)
                for i,id in  enumerate( ids ):
                    resultone = utils.timestamp() - id['jointime']
                    if resultone < roundtime:
                        continue
                    if i >= roundnum and roundnum % 2 == 0:
                        break
                    id['jointime'] = utils.timestamp() + random.randint(10,60)
                    id['roundIndex'] = id['roundIndex'] + random.randint(0,5)
                    if id['roundIndex'] > 8:
                        id['roundIndex'] = 8
                database.share_redis_game().hset('android',union_id,utils.json_encode(ids))


        arr = []
        ids = sorted(ids, key=lambda x: x['tid'],reverse=True)
        ip = '39.101.163.242'
        # ip = '192.168.0.30'

        for i , j in enumerate(ids):
            if len(arr) == 1:
                arr.append(j)
                head = 'http://%s:8194/static/ps/%d.png' % tuple([ip, arr[0]['uid']])
                head1 = 'http://%s:8194/static/ps/%d.png' % tuple([ip, arr[1]['uid']])
                keyval = {"playerList":[arr[0]['uid'],arr[1]['uid']],"img":[head,head1], "nickname":[arr[0]['nickname'],arr[1]['nickname']],"roundIndex":arr[0]['roundIndex'],"subFloor":arr[0]['subfloorid'],"status":10,"totalRound":"8","tid":arr[0]['tid']}
                result.append(keyval)
                arr.clear()
            else:
                arr.append(j)
    return result


def close_random_to_android_list(android_list: list,union_id: int)->list:
    """随机有一定概率机器人关禁闭"""
    k = share_connect().hget('android_close', union_id)
    if not k:
        k = -1
    else:
        k = int(k)
    k1 = random.randint(50, 100)
    if k < k1:
        k = k + 1
        if k >= 50:
            k = 100
        share_connect().hset('android_close',union_id,k)
        return android_list
    else:
        k = k - 1
        if k < 50:
            k = 0
        share_connect().hset('android_close',union_id,k)
        num = int(len(android_list)/2) + 1
        num = random.randint(1,len(android_list)-1)
        return android_list[0:num]


def one_by_one_to_step(start: str, last: str, android_list: list, union_id: int)->list:
    """在开始时间节点做成一个慢慢增加的效果"""
    """在快要结束慢慢减少效果"""
    d_time = datetime.datetime.strptime(str(datetime.datetime.now().date())+start, '%Y-%m-%d%H:%M')
    d_time1 =  datetime.datetime.strptime(str(datetime.datetime.now().date())+last, '%Y-%m-%d%H:%M')
    n_time = datetime.datetime.now()
    yesterday = d_time1 + datetime.timedelta(days=-1)
    key = 'android_pointer'
    if n_time >= d_time and n_time < d_time1:
        seconds = (n_time-d_time).seconds
        """获取联盟指针"""
        cursor = share_connect().hget(key, union_id)
        if not cursor:
            cursor = 0
        else:
            cursor = int(cursor)
        if cursor >= len(android_list):
            return android_list
        rb = random.randint(50,70)
        if seconds >= (cursor * rb) and seconds > rb:
            cursor = cursor + random.randint(1,2)
        """保存索引位置"""
        share_connect().hset(key, union_id,cursor)
        return android_list[0:cursor + 1]
    elif n_time >= d_time1:
        seconds = (n_time-d_time).total_seconds()
        """获取联盟指针"""
        cursor = share_connect().hget(key, union_id)
        if not cursor:
            cursor = len(android_list) - 1
        else:
            cursor = int(cursor)
        if cursor >= len(android_list):
            cursor = len(android_list) - 1
        elif cursor < 0:
            return []
        rb = random.randint(50,70)
        lstnum = len(android_list)
        if seconds >= (abs(lstnum-cursor) * rb) and seconds > rb:
            cursor = cursor - random.randint(1,2)
        """保存索引位置"""
        if cursor < 0:
            return []
        share_connect().hset(key, union_id,cursor)
        return android_list[0:cursor + 1]
    else:
        seconds = (n_time-yesterday).total_seconds()
        if seconds > 60 * 60 * 2:
            return []
        """获取联盟指针"""
        cursor = share_connect().hget(key, union_id)
        if not cursor:
            cursor = len(android_list) - 1
        else:
            cursor = int(cursor)
        if cursor >= len(android_list):
            cursor = len(android_list) - 1
        elif cursor < 0:
            return []
        rb = random.randint(50,70)
        lstnum = len(android_list)
        if seconds >= (abs(lstnum-cursor) * rb) and seconds > rb:
            cursor = cursor - random.randint(1,2)
        """保存索引位置"""
        if cursor < 0:
            return []
        share_connect().hset(key, union_id,cursor)
        return android_list[0:cursor + 1]





if __name__ == '__main__':
    data = one_by_one_to_step('23:49','23:50',list(),0)
    print(data)
