# coding:utf-8

import os
from tornado.options import define
from utils import utils

root_path = os.path.join(os.path.dirname(__file__), "..")
sub_static_path = "static"
static_path = os.path.join(root_path, sub_static_path)

# json配置文件里面的所有数据
_json_items = utils.read_json_file(
    os.path.dirname(
        os.path.realpath(__file__)) +
    '/config.json')

# iap数据
_iap_items = utils.read_json_file(
    os.path.dirname(
        os.path.realpath(__file__)) +
    '/iap.json')

# 是否是开发模式中
IS_DEBUG = _json_items.get('is_debug')

# 杀进程前的等待时间
if IS_DEBUG:
    SHUTDOWN_WAIT_SECONDS = 1
else:
    SHUTDOWN_WAIT_SECONDS = 5


def get_by_key(key):
    return _json_items.get(key)


def get_game_name():
    return _json_items.get("game_name")


def get_iap_by_item(key):
    return _iap_items.get(key)


def in_white_list(uid, channel_id):
    is_open = _json_items.get("open_white_list")
    if not is_open:
        return True
    white_channels = _json_items.get("white_list_channels")
    if white_channels and channel_id in white_channels:
        return True
    data = _json_items.get("white_list")
    if not data or type(data) is not list:
        return False
    return uid in data


game_id = 10

# 客户端签名key
define("app_sign_key", default="", help="")

# 注册时的钻石
define("register_diamond", default=60, help="注册时的钻石")
define("room_round_base", default=8, help="开房的基本局数")
define("create_room_diamonds", default=1, help="开基本房所需要的钻石数量")

# cookie的签名key
define("cookie_secret", default="", help="cookie加密密钥")
define('cookie_info', default='info.gl')  # 存放用户是否已经登录等cookie信息
define('cookie_info_timeout', default=30)  # 过期时间天数

# 微信开放平台APP_ID
define("we_chat_app_id", default="", help="微信开放平台APP_ID")
# 微信开放平台APP_SECRET
define("we_chat_app_secret", default="", help="微信开放平台APP_SECRET")


# COS配置数据
cos_app_id = ''
cos_secret_id = ''
cos_secret_key = ''
cos_bucket_name = "game2"

# OSS配置数据
oss_secret_id = ""
oss_secret_key = ""
oss_bucket_name = ""
