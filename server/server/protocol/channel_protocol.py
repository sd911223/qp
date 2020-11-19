# coding:utf-8

CHANNEL_GATEWAY = "channel_gateway"  # 网关频道
CHANNEL_ROOMS = "channel_rooms"  # 房间频道


def explode_command(command):
    return command // 100, command % 100


def packet_command(service_type, cmd):
    return service_type * 100 + cmd


def packet_client_body(data, code):
    """ 打包客户端消息内容 """
    data = data or {}
    if not data.get('code'):
        data['code'] = code
    return data


def packet_client_message(service_type, cmd, data):
    """ 打包客户端消息的完整内容 """
    return {
        'cmd': packet_command(service_type, cmd),
        'msg': data or {},
    }


def format_channel_struct(sid: int, service: int, cmd: int, uid: int, message) -> list:
    """ 格式化要发送到频道的消息 """
    return [sid, service, cmd, uid, message]


def read_channel_struct(message: list):
    """ 读取频道广播的数据 """
    if 5 != len(message):
        return 0, 0, 0, 0, None
    sid, service, cmd, uid, msg = message
    return sid, service, cmd, uid, msg
