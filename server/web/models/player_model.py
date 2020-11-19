from tornado.options import options

import random

from models import base_redis
from models import database
from models import table_name
from utils import utils


def get_nick_name(info):
    if not info:
        return ''
    name = info.get('nick_name', '') or info.get('model', '')
    return utils.filter_emoji(name)


def get_diamonds(info):
    if not info:
        return ''
    diamond = info.get('diamond', '') or 0
    return utils.filter_emoji(diamond)


def get_by_uid(conn, uid):
    if not conn or not uid:
        return {}
    sql = "SELECT * FROM `{0}` WHERE uid='{1}' LIMIT 1".format(table_name.players, int(uid))
    return conn.get(sql)
def get_by_uid1(conn, uid):
    if not conn or not uid:
        return {}
    sql = "SELECT * FROM `{0}` WHERE uid='{1}' LIMIT 1".format('players_android', int(uid))
    return conn.get(sql)

def get_by_uid_json(conn, uid, default_query='nick_name,diamond'):
    if not conn or not uid:
        return {}
    sql = "SELECT {0} FROM `{1}` WHERE uid='{2}' LIMIT 1".format(default_query, table_name.players, int(uid))
    return conn.get(sql)


def get_by_uid_with_refer_uid_json(conn, uid, refer_uid):
    if not conn or not uid:
        return {}
    sql = "SELECT * FROM `{0}` WHERE uid='{1}' and base_refer_uid={2} LIMIT 1".format(
        table_name.players, int(uid),
        refer_uid)
    return conn.get(sql)


def set_share_time(conn, uid):
    if not conn or not uid:
        return 0
    time = utils.timestamp()
    sql = "UPDATE `{0}` SET share_time={1} WHERE uid={2} LIMIT 1". \
        format(table_name.players, time, uid)
    return conn.execute_rowcount(sql)


def get_only_agents(conn, opts):
    """
    设置代理页面列表，默认只显示代理
    :param conn: 数据库连接
    :param opts:
    :return: [数据列表，列表长度]
    """
    default_query = "uid,avatar,nick_name,diamond,sex,model,ver,reg_time,phone,agent"
    per_page_count = 10

    if not conn:
        return [None, None]
    page = opts['page']
    all_count = "SELECT COUNT(*) as count FROM `{0}` WHERE agent=1".format(table_name.players)
    sql = "SELECT {0} FROM `{1}` WHERE agent=1 ORDER BY reg_time DESC LIMIT {2},{3}".format(default_query,
                                                                                            table_name.players,
                                                                                            (page - 1) * per_page_count,
                                                                                            per_page_count)
    rows = conn.query(sql)
    all_count = conn.query(all_count)
    return [rows, all_count[0]['count']]


def get_with_options_with_refer(conn, opts, uid):
    all_count = -1
    default_query = "uid,avatar,nick_name,diamond,sex,model,ver,reg_time,phone,agent"
    per_page_count = 10

    if not conn:
        return [None, None]
    if not opts:
        page = 1
        all_count = "SELECT COUNT(*) as count FROM `{0}` where base_refer_uid = {1}".format(table_name.players, uid)
        sql = "SELECT {0} FROM `{1}` WHERE base_refer_uid = {2} ORDER BY reg_time DESC LIMIT {3},{4}".format(
            default_query, table_name.players, uid, (page - 1) * per_page_count, per_page_count)
    else:
        if 'page' in opts:
            page = opts['page']
            all_count = "SELECT COUNT(*) as count FROM `{0}` where base_refer_uid = {1}".format(table_name.players, uid)
            if 'sort_name' in opts:
                sql = "SELECT {0} FROM `{1}` WHERE base_refer_uid = {2} ORDER BY {3} {4} LIMIT {5},{6}".format(
                    default_query, table_name.players,
                    uid,
                    database.escape(opts['sort_name']),
                    database.escape(opts['sort_type']),
                    (page - 1) * per_page_count,
                    per_page_count)
            else:
                sql = "SELECT {0} FROM `{1}` WHERE base_refer_uid = {2} ORDER BY reg_time DESC LIMIT {3},{4}".format(
                    default_query,
                    table_name.players, uid,
                    (page - 1) * per_page_count,
                    per_page_count)
        else:
            if 'uid' in opts:
                sql = "SELECT {0} FROM `{1}` WHERE {2}={3} AND base_refer_uid={4} ORDER BY reg_time DESC".format(
                    default_query,
                    table_name.players, 'uid',
                    opts['uid'], uid)
            else:
                sql = "SELECT {0} FROM `{1}` WHERE 1=1 and ".format(default_query, table_name.players)
                for k, v in opts.items():
                    if k in ['nick_name', 'phone', 'model', 'ver']:
                        sql += " {0} LIKE '%%{1}%%' AND ".format(k, v)
                    elif k is 'diamond_min':
                        sql += "diamond >= {0} AND ".format(v)
                    elif k is 'diamond_max':
                        sql += "diamond <= {0} AND ".format(v)
                    elif k is 'start_time':
                        sql += "reg_time >= {0} AND ".format(v)
                    elif k is 'end_time':
                        sql += "reg_time <= {0} AND ".format(v)
                    elif k in ['sex', 'agent']:
                        sql += "{0} = {1} AND ".format(k, v)
                sql += " base_refer_uid={0} ORDER BY reg_time DESC LIMIT 0,30".format(uid)
    rows = conn.query(sql)
    if all_count is not -1:
        all_count = conn.query(all_count)
        return [rows, all_count[0]['count']]
    else:
        return [rows, len(rows)]


def get_with_options(conn, opts):
    """
    通过不同参数获取玩家列表

    默认返回字段 : uid,avatar,nick_name,diamond,sex,model,ver,reg_time,phone,agent
    默认返回数量 : 10 条

    opts 附带参数 page 设置当前页数
    opts 附带参数 sort_name 以及 sort_type 处理排序字段及正逆排序

    :param conn: 数据库连接
    :param opts:
    :return: [数据列表，列表长度]
    """
    all_count = -1
    default_query = "uid,avatar,nick_name,diamond,sex,model,ver,reg_time,phone,agent"
    per_page_count = 10

    if not conn:
        return [None, None]
    if not opts:
        page = 1
        all_count = "SELECT COUNT(*) as count FROM `{0}`".format(table_name.players)
        sql = "SELECT {0} FROM `{1}` ORDER BY reg_time DESC LIMIT {2},{3}".format(default_query, table_name.players,
                                                                                  (page - 1) * per_page_count,
                                                                                  per_page_count)
    else:
        if 'page' in opts:
            page = opts['page']
            all_count = "SELECT COUNT(*) as count FROM `{0}`".format(table_name.players)
            if 'sort_name' in opts:
                sql = "SELECT {0} FROM `{1}` ORDER BY {2} {3} LIMIT {4},{5}".format(default_query, table_name.players,
                                                                                    database.escape(opts['sort_name']),
                                                                                    database.escape(opts['sort_type']),
                                                                                    (page - 1) * per_page_count,
                                                                                    per_page_count)
            else:
                sql = "SELECT {0} FROM `{1}` ORDER BY reg_time DESC LIMIT {2},{3}".format(default_query,
                                                                                          table_name.players,
                                                                                          (page - 1) * per_page_count,
                                                                                          per_page_count)
        else:
            if 'uid' in opts:
                sql = "SELECT {0} FROM `{1}` WHERE {2}={3} ORDER BY reg_time DESC".format(default_query,
                                                                                          table_name.players, 'uid',
                                                                                          opts['uid'])
            else:
                sql = "SELECT {0} FROM `{1}` WHERE 1=1 and ".format(default_query, table_name.players)
                for k, v in opts.items():
                    if k in ['nick_name', 'phone', 'model', 'ver']:
                        sql += " {0} LIKE '%%{1}%%' AND ".format(k, v)
                    elif k is 'diamond_min':
                        sql += "diamond >= {0} AND ".format(v)
                    elif k is 'diamond_max':
                        sql += "diamond <= {0} AND ".format(v)
                    elif k is 'start_time':
                        sql += "reg_time >= {0} AND ".format(v)
                    elif k is 'end_time':
                        sql += "reg_time <= {0} AND ".format(v)
                    elif k in ['sex', 'agent']:
                        sql += "{0} = {1} AND ".format(k, v)
                sql += " 1=1 ORDER BY reg_time DESC LIMIT 0,30"
    rows = conn.query(sql)
    if all_count is not -1:
        all_count = conn.query(all_count)
        return [rows, all_count[0]['count']]
    else:
        return [rows, len(rows)]


def get(conn, params):
    if not conn or not params:
        return {}
    mac = database.escape(params.get('mac'))
    imei = database.escape(params.get('imei'))
    sql = "SELECT * FROM `{0}` WHERE mac='{1}' AND imei='{2}' LIMIT 1".format(table_name.players, mac, imei)
    return conn.get(sql)


def get_by_auto_token(conn, auto_token):
    if not conn or not auto_token:
        return {}
    auto_token = database.escape(auto_token)
    sql = "SELECT * FROM `{0}` WHERE auto_token='{1}' LIMIT 1".format(table_name.players, auto_token)
    return conn.get(sql)


def get_by_openid(conn, openid):
    if not conn or not openid:
        return {}
    openid = database.escape(openid)
    sql = "SELECT * FROM `{0}` WHERE openid='{1}' LIMIT 1".format(table_name.players, openid)
    return conn.get(sql)


def get_by_unionid(conn, unionid):
    if not conn or not unionid:
        return {}
    unionid = database.escape(unionid)
    sql = "SELECT * FROM `{0}` WHERE unionid='{1}' LIMIT 1".format(table_name.players, unionid)
    return conn.get(sql)


def save_union_id(conn, uid, union_id):
    if not conn or not uid or not union_id:
        return False
    sql = "UPDATE `{0}` SET unionid='{1}' WHERE uid='{2}' LIMIT 1".format(table_name.players, union_id, uid)
    return conn.execute_rowcount(sql)


def get_by_auth_info(conn, auth_info):
    if not conn or not auth_info or not auth_info.get('unionid'):
        return
    union_id = database.escape(auth_info.get('unionid'))
    sql = "SELECT * FROM `{0}` WHERE unionid='{1}' LIMIT 1".format(table_name.players, union_id)
    result = conn.get(sql)
    if result:
        return result

    result = get_by_openid(conn, auth_info.get('openid'))
    if not result:
        return
    save_union_id(conn, result.uid, union_id)
    return result


def _make_guest_cols(params, fixed_params):
    inserts = dict()
    inserts['uid'] = make_uid()
    inserts['imei'] = database.escape(params.get('imei'))
    inserts['imsi'] = database.escape(params.get('imsi'))
    inserts['mac'] = database.escape(params.get('mac'))
    inserts['model'] = database.escape(params.get('model'))
    inserts['platform'] = int(fixed_params['platform'])
    inserts['ver'] = database.escape(
        str(fixed_params['ver']) + "." + str(fixed_params['channel_id']) + '.' + str(fixed_params['script_ver']))
    inserts['channel_id'] = int(fixed_params['channel_id'])
    inserts['reg_time'] = utils.timestamp()
    inserts['diamond'] = int(options.register_diamond)
    inserts['yuan_bao'] = 12
    inserts['sex'] = 2
    inserts['login_time'] = utils.timestamp()
    inserts['ip'] = params.get("ip") or 0
    return inserts


def _format_we_chat_sex(sex):
    sex = utils.str_to_int(sex)
    if 1 == sex:
        return 1
    if 2 == sex:
        return 0
    return 2


def _make_auto_token(unionid):
    return utils.sha1(unionid + utils.random_string(20))


def delete_union_id_and_modify_union_id_with_refer_info(conn, openid, unionid, refer_uid, refer_time):
    if not conn:
        return 0
    sql = "DELETE FROM `{0}` WHERE unionid='{1}'".format(table_name.players, unionid)
    count = conn.execute_rowcount(sql)
    if count > 0:
        sql = "UPDATE `{0}` SET unionid='{1}',refer_uid='{2}',refer_time='{3}',bind_after_login_time='{4}' " \
              "WHERE openid='{5}'" \
            .format(table_name.players, unionid, refer_uid, refer_time, utils.timestamp(), openid)
        return conn.execute_rowcount(sql)
    return 0


def we_chat_sign_up(conn, params, fixed_params, auth_info, user_info):
    if not conn or not params or not fixed_params or not user_info:
        return {}
    inserts = _make_guest_cols(params, fixed_params)
    nick_name = utils.filter_emoji(database.escape(user_info.get('nickname', '')))
    inserts['nick_name'] = nick_name.replace('%', '%%')
    inserts['openid'] = database.escape(user_info.get('openid'))
    inserts['unionid'] = database.escape(user_info.get('unionid'))
    inserts['sex'] = _format_we_chat_sex(user_info.get('sex'))
    inserts['avatar'] = database.escape(user_info.get('headimgurl'))

    inserts['token'] = database.escape(auth_info.get('access_token'))
    inserts['refresh_token'] = database.escape(auth_info.get('refresh_token'))
    inserts['expires_at'] = utils.timestamp() + int(auth_info.get('expires_in'))
    inserts['auto_token'] = _make_auto_token(inserts['unionid'])

    sql = database.make_insert(table_name.players, inserts)
    return conn.execute(sql)


def update_auto_token_and_openid_and_bind_time(conn, uid, unionid, openid):
    if not conn or not uid:
        return 0
    sql = "UPDATE `{0}` SET auto_token='{1}',openid='{2}' WHERE uid='{3}'" \
        .format(table_name.players, _make_auto_token(unionid), openid, uid)
    return conn.execute(sql)


def update_bind_after_login_time(conn, uid):
    if not conn or not uid:
        return 0
    sql = "UPDATE `{0}` SET bind_after_login_time='{1}' WHERE uid='{2}'" \
        .format(table_name.players, utils.timestamp(), uid)
    return conn.execute(sql)


def we_chat_modify_union_id(conn, user_info):
    if not conn or not user_info:
        return {}
    sql = "UPDATE `{0}` SET unionid='{1}' WHERE openid='{2}'" \
        .format(table_name.players, database.escape(user_info.get('unionid')), database.escape(user_info.get('openid')))
    return conn.execute(sql)


def we_chat_refresh(conn, user_info, uid, auth_info):
    if not conn or not user_info or not uid or not auth_info:
        return {}
    update = dict()
    update['nick_name'] = utils.filter_emoji(database.escape(user_info.get('nickname', '')))
    update['sex'] = _format_we_chat_sex(user_info.get('sex'))
    update['avatar'] = database.escape(user_info.get('headimgurl'))
    update['token'] = database.escape(auth_info.get('access_token'))
    if int(auth_info.get('expires_in')) <= 10000000:
        update['expires_at'] = utils.timestamp() + int(auth_info.get('expires_in'))
    else:
        update['expires_at'] = auth_info.get('expires_in')
    sql = "UPDATE `{0}` SET nick_name='{1}',sex={2},avatar='{3}',token='{4}',expires_at={5}" \
        .format(table_name.players, update['nick_name'], update['sex'], update['avatar'], update['token'],
                update['expires_at'])
    if auth_info['refresh_token']:
        update['refresh_token'] = database.escape(auth_info.get('refresh_token'))
        sql += ",refresh_token='{0}'".format(update['refresh_token'])
    sql += " WHERE uid={0}".format(uid)
    return conn.execute(sql)


def insert_guest(conn, params, fixed_params):
    if not conn or not params or not fixed_params:
        return {}
    inserts = _make_guest_cols(params, fixed_params)
    sql = database.make_insert(table_name.players, inserts)
    return conn.execute(sql)


def make_uid():
    # key = "all_uids"
    # uid = base_redis.pop_from_set(key)
    # if not uid:
    #     return 0

    uid = random.randint(100000, 1000000)

    return int(uid)


def remove_uid_from_pool(value):
    key = "all_uids"
    return base_redis.share_connect().srem(key, value)


def edit_pwd(conn, uid, pwd):
    if not conn or not uid or not pwd:
        return 0
    pwd = utils.md5(str(uid) + str(pwd))
    sql = "UPDATE `{0}` SET pwd='{1}' WHERE uid={2} LIMIT 1". \
        format(table_name.players, pwd, uid)
    return conn.execute_rowcount(sql)


def check_password(info, pwd) -> bool:
    """检查密码是否匹配"""
    if not info or not info.get('pwd', '') or not pwd:
        return False
    return utils.md5(str(info.get('uid')) + pwd) == info.get('pwd', '')


def verify_by_code(conn, uid, verify_code):
    if not conn or not uid or not verify_code:
        return 0
    time = utils.timestamp() - 30 * 60
    sql = "UPDATE `{0}` SET verify_code='', verify_expire_at=0 WHERE uid={1} AND verify_code='{2}' " \
          "AND verify_expire_at>{3} LIMIT 1". \
        format(table_name.players, uid, database.escape(verify_code), time)
    return conn.execute_rowcount(sql)


def set_verify_code(conn, uid):
    if not conn or not uid:
        return 0
    time = utils.timestamp()
    verify_code = int(utils.get_random_num(6))
    sql = "UPDATE `{0}` SET verify_code='{1}', verify_expire_at={2} WHERE uid={3} LIMIT 1". \
        format(table_name.players, verify_code, time, uid)
    if conn.execute_rowcount(sql) > 0:
        return verify_code
    return 0


def add_diamonds_with_log(conn, conn_logs, uid, diamonds,
                          refer_uid, refer_nick_name, reason_id, left_diamonds, memo=''):
    if add_diamonds(conn, uid, diamonds) > 0:
        from models import logs_model
        logs_model.add_diamonds_record(conn_logs, uid, refer_uid,
                                       refer_nick_name, diamonds, reason_id, left_diamonds, 1, memo)
        return 1
    return 0


def add_diamonds(conn, uid, diamonds):
    if diamonds <= 0 or uid <= 0:
        return 0
    sql = "UPDATE `{0}` SET diamond=diamond+{1} WHERE uid={2} LIMIT 1". \
        format(table_name.players, diamonds, uid)
    return conn.execute_rowcount(sql)


def sub_diamonds(conn, uid, diamonds):
    if diamonds <= 0 or uid <= 0:
        return 0
    sql = "UPDATE `{0}` SET diamond=diamond-{1} WHERE uid={2} AND diamond>={1} LIMIT 1". \
        format(table_name.players, diamonds, uid)
    return conn.execute_rowcount(sql)


def set_agent(conn, uid, agent, phone):
    if not conn or not uid or not phone or len(phone) != 11:
        return 0
    sql = "UPDATE `{0}` SET agent={1},phone='{2}' WHERE uid={3} LIMIT 1". \
        format(table_name.players, int(agent), database.escape(phone), uid)
    return conn.execute_rowcount(sql)


def set_phone_number(conn, uid, phone):
    if not conn or not uid or not phone or len(phone) != 11:
        return 0
    sql = "UPDATE `{0}` SET phone='{1}' WHERE uid={2} AND (phone='' OR phone=NULL) LIMIT 1". \
        format(table_name.players, database.escape(phone), uid)
    return conn.execute_rowcount(sql)


def update_login_info(conn, uid, params, ip):
    if not uid or not ip or not params:
        return 0
    ver = database.escape(str(params['ver']) + "." + str(params['channel_id']) + '.' + str(params['script_ver']))
    sql = "UPDATE `{0}` SET login_time={1},ip={2},ver='{3}' WHERE uid={4} LIMIT 1". \
        format(table_name.players, utils.timestamp(), ip, ver, uid)
    return conn.execute_rowcount(sql)


def bind_agent(conn, uid, agent_id, father_id, hierarchical):
    if not uid or not conn:
        return 0
    hierarchical += ',' + str(uid)
    sql = f"UPDATE `players` SET agent_id={agent_id}," \
        f"father_id={father_id},hierarchical='{hierarchical}' WHERE uid={uid}"
    return conn.execute_rowcount(sql)


def sub_money(conn, uid, money):
    if money <= 0 or uid <= 0:
        return 0
    sql = "UPDATE `{0}` SET money=money-{1} WHERE uid={2} AND money>={1} LIMIT 1". \
        format(table_name.players, money, uid)
    return conn.execute_rowcount(sql)


def add_money(conn, uid, money):
    if money <= 0 or uid <= 0:
        return 0
    sql = "UPDATE `{0}` SET money=money+{1} WHERE uid={2} LIMIT 1". \
        format(table_name.players, money, uid)
    return conn.execute_rowcount(sql)


def get_consume_diamond_by_time(conn_logs, uid, club_id, start_time, end_time):
    sql = f"SELECT SUM(diamonds) AS diamonds FROM club_diamond_logs WHERE uid = {uid} AND club_id = {club_id} " \
        f"AND time >={start_time} AND time <= {end_time}"
    count = conn_logs.get(sql)
    if count and count['diamonds']:
        return int(count['diamonds'])
    return 0


def get_qr_code(conn, uid):
    sql = f"SELECT qcodes FROM UserInfo WHERE UseNumber = {uid}"
    return conn.get(sql)


def edit_address(conn, address, real_name, phone, uid):
    sql = f"INSERT INTO `player_address` SET uid={uid},address='{address}'," \
        f"real_name='{real_name}',phone='{phone}' " \
        f"ON DUPLICATE KEY UPDATE uid={uid},address='{address}'," \
        f"real_name='{real_name}',phone='{phone}'"
    return conn.execute_rowcount(sql)


def get_address(conn, uid):
    sql = f"SELECT * from player_address WHERE uid={uid}"
    return conn.get(sql)


def modify_score(conn, uid, score):
    sql = f"UPDATE players set score=score+{score} WHERE uid={uid}"
    return conn.execute_rowcount(sql)


def update_player_score_with_reason(conn, conn_logs, uid, score, reason):
    count = modify_score(conn, uid, score)
    if count == 1:
        sql = f'INSERT INTO player_score_logs set uid={uid},score={score},reason={reason},time={utils.timestamp()}'
        return conn_logs.execute_rowcount(sql)
    return 0


def update_player_sign_time_and_count(conn, uid, sign_time, sign_count):
    sql = f'UPDATE players set sign_time={sign_time},sign_count={sign_count} WHERE uid={uid}'
    return conn.execute_rowcount(sql)


def add_la_jiao_dou(conn, uid, la_jiao_dou):
    sql = f"UPDATE `players` SET la_jiao_dou=la_jiao_dou+{la_jiao_dou} WHERE uid={uid} LIMIT 1"
    return conn.execute_rowcount(sql)


def add_score(conn, uid, score):
    sql = f"UPDATE `players` SET score=score+{score} WHERE uid={uid} LIMIT 1"
    return conn.execute_rowcount(sql)


def change_yuan_bao_to_diamond(conn, uid, count):
    sql = f"UPDATE `players` SET diamond=diamond+{count},yuan_bao=yuan_bao-{count} " \
        f"WHERE uid={uid} AND yuan_bao>={count} LIMIT 1"
    return conn.execute_rowcount(sql)


def write_change_yuan_bao_to_diamond_logs(conn_logs, uid, count, extra_count, yuan_bao):
    sql = f'INSERT INTO exchange_gold_logs set uid={uid},diamond={count},' \
        f'extra_diamond={extra_count},time={utils.timestamp()},status=0,gold={yuan_bao}'
    return conn_logs.execute_rowcount(sql)


def add_yuan_bao(conn, uid, yuan_bao):
    sql = f"UPDATE `players` SET yuan_bao=yuan_bao+{yuan_bao} WHERE uid={uid} LIMIT 1"
    return conn.execute_rowcount(sql)


def dec_yuan_bao(conn, uid, yuan_bao):
    sql = f"UPDATE `players` SET yuan_bao=yuan_bao-{yuan_bao} WHERE uid={uid} LIMIT 1"
    return conn.execute_rowcount(sql)
