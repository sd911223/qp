from models import table_name
from utils import utils

INVITE_SUCCESS_ZUAN = 3  # 被绑定邀请人获得钻石
BIND_SUCCESS_ZUAN = 2  # 自己绑定成功获得钻石
RE_INVITE_ZUAN = 2  # 再邀请送钻
CREATE_ROOM_ZUAN = 2  # 首次开房送钻

INVITE_SUCCESS_ZUAN_5 = 5  # 邀请用户并首次微信登录时，赠送5钻


def get_yao_qing_list(conn, uid):
    if not conn or not uid:
        return 0
    sql = "SELECT * FROM `{0}` WHERE uid='{1}' LIMIT 1000".format(table_name.yao_qing, int(uid))
    return conn.query(sql)


def calc_zuan(item):
    return INVITE_SUCCESS_ZUAN + item.get("first_round", 0) * CREATE_ROOM_ZUAN + \
           item.get('re_invite_count', 0) * RE_INVITE_ZUAN


def get_my_yao_qing(conn, uid):
    """ 获得单个玩家的邀请信息 """
    result = get_yao_qing_list(conn, uid)
    zuan, invite_count, create_room_count, re_invite_count = 0, 0, 0, 0
    for item in result:
        invite_count += 1
        create_room_count += item.get('first_round', 0)
        re_invite_count += item.get('re_invite_count', 0)
        zuan += calc_zuan(item)
    invite_zuan = invite_count * INVITE_SUCCESS_ZUAN
    create_zuan = CREATE_ROOM_ZUAN * create_room_count
    re_invite_zuan2 = re_invite_count * RE_INVITE_ZUAN
    return {
        "totalZuan": zuan,
        "inviteCount": invite_count,
        "inviteZuan": invite_zuan,
        "createRoomCount": create_room_count,
        "createRoomZuan": create_zuan,
        "reInviteCount": re_invite_count,
        "reInviteZuan": re_invite_zuan2,
    }


def is_my_clients(conn, uid, check_uid):
    if not conn or not uid or not check_uid:
        return
    sql = "SELECT 1 FROM `{0}` WHERE uid={1} AND invitee='{2}' LIMIT 1". \
        format(table_name.yao_qing, int(uid), int(check_uid))
    return conn.get(sql)


def get_inviter(conn, uid):
    """获得玩家的邀请者"""
    if not conn or not uid:
        return 0
    sql = "SELECT uid FROM `{0}` WHERE invitee='{1}' LIMIT 1".format(table_name.yao_qing, int(uid))
    result = conn.get(sql)
    if not result:
        return 0
    return int(result.get('uid', 0))


def bind(conn, inviter, uid):
    """ 首次绑定邀请关系 """
    if not conn or not uid or not inviter:
        return 0
    time = utils.timestamp()
    try:
        sql = "INSERT INTO `{0}` SET uid={1},invitee={2},bind_time={3}". \
            format(table_name.yao_qing, inviter, uid, time)
        conn.execute(sql)
        return 1
    except Exception as e:
        print(e)
        return 0


def finish_re_invite(conn, uid, invitee):
    """ 完成再邀请 """
    if not conn or not uid or not invitee:
        return 0
    sql = "UPDATE `{0}` SET re_invite_count=re_invite_count+1 WHERE uid={1} AND invitee={2} LIMIT 1". \
        format(table_name.yao_qing, uid, invitee)
    return conn.execute_rowcount(sql)


def finish_create_room(conn, uid):
    """ 完成再邀请 """
    if not conn or not uid:
        return 0
    sql = "UPDATE `{0}` SET first_round_bonus=1 WHERE invitee={1} AND first_round_bonus=0 LIMIT 1". \
        format(table_name.yao_qing, uid)
    return conn.execute_rowcount(sql)


def get_100_no_bonus(conn):
    sql = "SELECT * FROM `{0}` WHERE first_round>0 AND first_round_bonus=0 LIMIT 100". \
        format(table_name.yao_qing, )
    return conn.query(sql)
