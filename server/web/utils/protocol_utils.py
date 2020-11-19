# coding:utf-8
from utils import utils
from configs.commands_s2s import S2S_SEND


def unpack_command(command):
    return command // 100, command % 100


def pack_command(service_type, cmd):
    return service_type * 100 + cmd


def pack_client_body(data, code):
    """ 打包客户端消息内容 """
    data = data or {}
    if not data.get('code'):
        data['code'] = code
    return data


def pack_client_message(service_type, cmd, data):
    """ 打包客户端消息的完整内容 """
    return {
        'cmd': pack_command(service_type, cmd),
        'msg': data or {},
    }


def unpack_s2s_package(line):
    obj = utils.json_decode(line)
    if type(obj) is not list or len(obj) <= 0:
        return None, None
    head = obj[0]
    body = None
    if len(obj) == 2:
        body = obj[1]
    return head, body


def unpack_s2s_head(head):
    if len(head) != 7:
        return 0, 0, 0, 0, 0, 0, 0
    [cid, from_sid, from_service, to_sid, to_service, with_ack, cmd] = head
    return cid, from_sid, from_service, to_sid, to_service, with_ack, cmd


def pack_s2s_head(cid, from_sid, from_service, to_sid, to_service, with_ack, cmd):
    head = [cid, from_sid, from_service, to_sid, to_service, with_ack, cmd]
    return head


def pack_s2s_package(cid, from_sid, from_service, to_sid, to_service, with_ack, cmd, body):
    head = pack_s2s_head(cid, from_sid, from_service, to_sid, to_service, with_ack, cmd)
    return [head, body]


def pack_s2s_send(cid, from_sid, from_service, to_sid, to_service, with_ack, body):
    return pack_s2s_package(cid, from_sid, from_service, to_sid, to_service, with_ack, S2S_SEND, body)


def pack_to_player_body(cmd: int, uid: int, message) -> list:
    return [cmd, uid, message]


def unpack_to_player_body(message: list):
    if not message or type(message) is not list or 3 != len(message):
        return 0, 0, None
    cmd, uid, msg = message
    return cmd, uid, msg
