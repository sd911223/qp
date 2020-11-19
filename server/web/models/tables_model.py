from configs import const
from models import database
from models import table_name
from utils import utils


def get(conn, tid):
    if not conn or not tid:
        return {}
    tid = int(tid)
    # sql = "SELECT * FROM `{0}` WHERE tid='{1}' LIMIT 1".format(table_name.tables, tid)
    # return conn.get(sql)

    tables = gettablesbyredis()
    if not tables or len(tables) == 0:
        return {}
    if 'owner' not in tables[0] or 'is_agent' not in tables[0] or 'club_id' not in tables[0]:
        return {}
    data = [x for x in tables if x['tid'] == tid]
    if len(data) > 0:
        return data[0]
    return {}


def get_table_by_club_id(conn, club_id):
    if not conn or not club_id:
        return list()
    club_id = int(club_id)
    # sql = "SELECT * FROM `{0}` WHERE club_id='{1}'".format(table_name.tables, club_id)
    # return conn.query(sql)

    tables = gettablesbyredis()
    if not tables or len(tables) == 0:
        return []
    if 'owner' not in tables[0] or 'is_agent' not in tables[0] or 'club_id' not in tables[0]:
        return []
    data = [x for x in tables if x['club_id'] == club_id]
    return data


def get_count_by_club_id(conn, club_id):
    # sql = "SELECT COUNT(*) as room_count FROM `{0}` WHERE club_id='{1}'".format(table_name.tables, club_id)
    # return conn.get(sql)

    tables = gettablesbyredis()
    if not tables or len(tables) == 0:
        return {}
    if 'owner' not in tables[0] or 'is_agent' not in tables[0] or 'club_id' not in tables[0]:
        return {}
    data = [x['tid'] for x in tables if x['club_id'] == club_id]
    if len(data) > 0:
        return data[0]
    return {}


def get_by_owner_not_agent(conn, owner):
    if not conn or not owner:
        return {}
    owner = int(owner)
    # sql = "SELECT * FROM `{0}` WHERE owner='{1}' AND is_agent=0 LIMIT 1".format(table_name.tables, owner)
    # return conn.get(sql)

    tables = gettablesbyredis()
    if not tables or len(tables) == 0:
        return {}
    if 'owner' not in tables[0] or 'is_agent' not in tables[0] or 'club_id' not in tables[0]:
        return {}
    data = [x for x in tables if x['owner'] == owner and x['is_agent'] == 0]
    if len(data) > 0:
        return data[0]
    return {}


def get_tables_by_owner_not_club(conn, owner):
    if not conn or not owner:
        return {}
    owner = int(owner)
    # sql = "SELECT * FROM `{0}` WHERE owner='{1}' AND is_agent=1 AND club_id=-1".format(table_name.tables, owner)
    # return conn.query(sql)
    tables = gettablesbyredis()
    if not tables or len(tables) == 0:
        return []
    if 'owner' not in tables[0] or 'is_agent' not in tables[0] or 'club_id' not in tables[0]:
        return []
    data = [x for x in tables if x['owner'] == owner and x['is_agent'] == 1 and x['club_id'] == -1]
    return data


def get_all_tables_by_owner(conn, owner):
    if not conn or not owner:
        return {}
    owner = int(owner)
    # sql = "SELECT * FROM `{0}` WHERE owner='{1}'".format(table_name.tables, owner)
    # return conn.query(sql)
    tables = gettablesbyredis()
    if not tables or len(tables) == 0:
        return []
    if 'owner' not in tables[0]:
        return []
    data = [x for x in tables if x['owner'] == owner]
    return data

def get_by_owner(conn, owner):
    if not conn or not owner:
        return {}
    owner = int(owner)
    # sql = "SELECT * FROM `{0}` WHERE owner='{1}' LIMIT 1".format(table_name.tables, owner)
    # return conn.get(sql)


    tables = gettablesbyredis()
    if not tables or len(tables) == 0:
        return {}
    if 'owner' not in tables[0]:
        return {}
    data = [x for x in tables if x['owner'] == owner]
    if len(data) > 0:
        return data[0]
    return {}


def get_dai_kai_count_by_owner(conn, owner):
    if not conn or not owner:
        return {}
    owner = int(owner)
    # sql = "SELECT COUNT(*) as room_count FROM `{0}` WHERE owner='{1}' AND is_agent=1 and club_id=-1".format(
    #     table_name.tables, owner)
    # return conn.get(sql)
    tables = gettablesbyredis()
    if not tables or len(tables) == 0:
        return {}
    if 'owner' not in tables[0] or 'is_agent' not in tables[0] or 'club_id' not in tables[0]:
        return {}
    data = [x['tid'] for x in tables if x['owner'] == owner and x['is_agent'] == 1 and x['club_id'] == -1]

    return {'room_count':len(data)}

def get_by_owner_diamonds(conn, owner):
    if not conn or not owner:
        return {}
    owner = int(owner)
    # sql = "SELECT sum(diamonds) as all_room_diamonds_count FROM `{0}` WHERE owner='{1}'" \
    #     .format(table_name.tables, owner)
    #return conn.get(sql)
    tables = gettablesbyredis()
    if not tables or len(tables) == 0:
        return {}
    if 'owner' not in tables[0]:
        return {}
    data = [x['diamonds'] for x in tables if x['owner'] == owner]
    data = sum(data)
    return {'all_room_diamonds_count':data}


def gettablesbyredis():
    from models import base_redis
    redis = base_redis.share_connect()
    data = redis.hgetall('redistables')
    tables = list()
    for tab in data.items():
        tables.append(utils.json_decode(str(tab[1],encoding='utf8')))
    return tables

def getuniontablebyunionid(union_id):
    tables = gettablesbyredis()
    data = [{'tid':x['tid'],'sub_floor':x['sub_floor'],'round_count':x['round_count']} for x in tables if x['union_id'] == union_id]
    return data

def get_room_count_by_club(conn, club_id):
    if not conn or not club_id:
        return 0
    sql = "SELECT COUNT(*) as room_count FROM `{0}` WHERE club_id={1}".format(table_name.tables, club_id)
    #return conn.get(sql)

    tables = gettablesbyredis()
    if not tables or len(tables) == 0:
        return {}
    if 'owner' not in tables[0]:
        return {}
    data = [x['tid'] for x in tables if x['club_id'] == club_id]
    data =  len(data)
    return {'room_count':data}



def insert(conn, sid, game_type, tid, owner, is_agent, total_round, diamonds, rule_type, club_id, rules, group_id=-1,
           robot_id=-1, floor=-1, consume_type=0, match_type=0, sub_floor=-1, match_config={}, union_id=-1):
    if not conn or not tid or not owner or not total_round or not game_type or not rules:
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
    inserts['rules'] = database.escape(utils.json_encode(rules))
    inserts['match_config'] = database.escape(utils.json_encode(match_config))
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
    #return conn.execute_rowcount(sql)
    """直接把桌子放到redis里面，不放mysql里面"""
    from models import base_redis
    redis = base_redis.share_connect()
    redis.hset('redistables',inserts['tid'],utils.json_encode(inserts))
    return 1


def get_table_info(conn, room_id):
    if not conn:
        return ""
    key = "table_info"
    data = utils.json_decode((conn.hget(key, room_id) or b"").decode("utf-8"))
    return data

def get_table_info(conn, room_id):
    if not conn:
        return ""
    key = "table_info"
    data = utils.json_decode((conn.hget(key, room_id) or b"").decode("utf-8"))
    return data


def get_table_by_club_id_and_floor(conn, club_id, floor):
    if not conn or not club_id or not floor:
        return list()
    club_id = int(club_id)
    floor = int(floor)
    # sql = f"SELECT * FROM `tables` WHERE club_id={club_id} AND floor={floor}"
    # return conn.query(sql)

    tables = gettablesbyredis()
    if not tables or len(tables) == 0:
        return []
    if 'club_id' not in tables[0] or 'floor' not in tables[0]:
        return []
    data = [x for x in tables if x['club_id'] == club_id and x['floor'] == floor]
    return data




def get_table_by_club_id_and_match_type(conn, club_id, match_type):
    if not conn or not club_id:
        return list()
    club_id = int(club_id)
    match_type = int(match_type)
    # sql = f"SELECT * FROM `tables` WHERE club_id={club_id} AND match_type={match_type}"
    # return conn.query(sql)

    tables = gettablesbyredis()
    if not tables or len(tables) == 0:
        return []
    if 'club_id' not in tables[0] or 'match_type' not in tables[0]:
        return []
    data = [x for x in tables if x['club_id'] == club_id and x['match_type'] == match_type]
    return data



def get_count_by_club_id_and_floor(conn, club_id, floor):
    # sql = f"SELECT COUNT(*) as room_count FROM `tables` WHERE club_id='{club_id}' and floor={floor}"
    # return conn.get(sql)

    tables = gettablesbyredis()
    if not tables or len(tables) == 0:
        return {}
    if 'club_id' not in tables[0] or 'floor' not in tables[0]:
        return {}
    data = [x['tid'] for x in tables if x['club_id'] == club_id and x['floor'] == floor]

    return {'room_count':len(data)}


def remove_idle_table_by_club_id(conn, club_id):
    # sql = f"DELETE FROM `tables` WHERE club_id='{club_id}' and state=0"
    # return conn.execute_rowcount(sql)
    # redistables
    tables = gettablesbyredis()
    if not tables or len(tables) == 0:
        return 0
    if 'club_id' not in tables[0] or 'state' not in tables[0]:
        return 0
    data = [x['tid'] for x in tables if x['club_id'] == club_id and x['state'] == 0]
    from models import base_redis
    redis = base_redis.share_connect()
    for i in data:
        redis.hdel('redistables',i)
    return len(data)


def get_total_idle_diamonds_by_uid(conn, uid):
    # sql = f"SELECT SUM(diamonds) as diamonds FROM `tables` WHERE owner='{uid}' " \
    #     f"and consume_type=0 and match_type={const.DIAMOND_ROOM}"
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
            and x['match_type'] == const.DIAMOND_ROOM]
    #data = [x['diamonds'] for x in data]
    return sum(data)



def get_total_match_idle_diamonds_by_uid(conn, uid):
    # sql = f"SELECT SUM(diamonds) as diamonds FROM `tables` WHERE owner='{uid}' " \
    #     f"AND consume_type=0 AND match_type={const.MATCH_ROOM}"
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
            and x['match_type'] == const.MATCH_ROOM]
    #data = [x['diamonds'] for x in data]
    return sum(data)


def get_table_id(conn, tid):
    if not conn or not tid:
        return {}
    # sql = f"SELECT tid FROM `tables` WHERE tid={tid} LIMIT 1"
    # return conn.get(sql)

    tables = gettablesbyredis()
    if not tables or len(tables) == 0:
        return {}
    if 'tid' not in tables[0]:
        return {}
    data = [x['tid'] for x in tables if x['tid'] == tid]
    if len(data) > 0 :
        return {'tid':tid}
    return {'tid':0}




def remove_table(conn, tid):
    # sql = f"DELETE FROM `tables` WHERE tid='{tid}'"
    # return conn.execute_rowcount(sql)
    tables = gettablesbyredis()
    if not tables or len(tables) == 0:
        return 0
    if 'tid' not in tables[0]:
        return 0
    data = [x['tid'] for x in tables if x['tid'] == tid]
    from models import base_redis
    redis = base_redis.share_connect()
    if len(data) > 0:
        redis.hdel('redistables',tid)
    return len(data)

def remove_tablebysubfloorandunionid(union_id,sub_floor):
    """
    根据union_id 和 subfloorid 删除桌子
    :param union_id:联盟编号
    :param sub_floor:玩法编号
    :return:
    """
    # sql = f"DELETE FROM `tables` WHERE tid='{tid}'"
    # return conn.execute_rowcount(sql)
    tables = gettablesbyredis()
    if not tables or len(tables) == 0:
        return 0
    if 'tid' not in tables[0]:
        return 0
    data = [x['tid'] for x in tables if x['union_id'] == union_id and x['sub_floor'] == sub_floor]
    from models import base_redis
    redis = base_redis.share_connect()
    for tid in data:
        redis.hdel('redistables',tid)
    return len(data),data