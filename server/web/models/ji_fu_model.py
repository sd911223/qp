from models import table_name
from utils import utils


_bind_fu = 1  # 绑定送福
_first_invite_fu = 2  # 首次推广送福
_create_room_fu = 2  # 首次开房送福


def get_ji_fu_list(conn, uid):
    if not conn or not uid:
        return 0
    sql = "SELECT * FROM `{0}` WHERE uid='{1}' LIMIT 1000".format(table_name.ji_fu, int(uid))
    return conn.query(sql)


def calc_fu(item):
    return _bind_fu + item.get("first_round", 0) * _create_room_fu + item.get('first_invite', 0) * _first_invite_fu


def get_my_ji_fu(conn, uid):
    """ 获得单个玩家的积福信息 """
    result = get_ji_fu_list(conn, uid)
    fu, invite_count, create_room_count, re_invite_count = 0, 0, 0, 0
    for item in result:
        invite_count += 1
        create_room_count += item.get('first_round', 0)
        re_invite_count += item.get('first_invite', 0)
        fu += calc_fu(item)
    invite_fu = invite_count * _bind_fu
    create_room_fu = _create_room_fu * create_room_count
    re_invite_fu = re_invite_count * _first_invite_fu
    return {
        "totalFu": fu,
        "inviteCount": invite_count,
        "inviteFu": invite_fu,
        "createRoomCount": create_room_count,
        "createRoomFu": create_room_fu,
        "reInviteCount": re_invite_count,
        "reInviteFu": re_invite_fu,
    }


def is_my_clients(conn, uid, check_uid):
    if not conn or not uid or not check_uid:
        return
    sql = "SELECT 1 FROM `{0}` WHERE uid={1} AND invitee='{2}' LIMIT 1".\
        format(table_name.ji_fu, int(uid), int(check_uid))
    return conn.get(sql)


def get_inviter(conn, uid):
    """获得玩家的邀请者"""
    if not conn or not uid:
        return 0
    sql = "SELECT uid FROM `{0}` WHERE invitee='{1}' LIMIT 1".format(table_name.ji_fu, int(uid))
    result = conn.get(sql)
    if not result:
        return 0
    return int(result.get('uid', 0))


def bind(conn, inviter, uid):
    """ 首次绑定邀请关系 """
    if not conn or not uid or not inviter:
        return 0
    time = utils.timestamp()
    sql = "INSERT IGNORE INTO `{0}` SET uid={1},invitee={2},bind_time={3}".\
        format(table_name.ji_fu, inviter, uid, time)
    conn.execute(sql)


def finish_play_game(conn, uid):
    """ 玩家完成一局游戏 """
    if not conn or not uid:
        return 0
    inviter = get_inviter(conn, uid)
    if not inviter:
        return 0
    time = utils.timestamp()
    sql = "UPDATE `{0}` SET first_round=1, first_round_time={1} " \
          "WHERE uid={2} AND invitee={3} AND first_round=0 LIMIT 1". \
        format(table_name.ji_fu, time, inviter, uid)
    return conn.execute_rowcount(sql)


def finish_invite(conn, uid):
    """ 玩家完成邀请 """
    if not conn or not uid:
        return 0
    inviter = get_inviter(conn, uid)
    if not inviter:
        return 0
    time = utils.timestamp()
    sql = "UPDATE `{0}` SET first_invite=1, first_invite_time={1} " \
          "WHERE uid={2} AND invitee={3} AND first_invite=0 LIMIT 1". \
        format(table_name.ji_fu, time, inviter, uid)
    return conn.execute_rowcount(sql)
