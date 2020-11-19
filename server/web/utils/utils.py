# coding:utf-8

import datetime
import hashlib
import ipaddress
import random
import re
import time
import urllib.error
import urllib.parse
import urllib.request

import requests
import ujson as json
from dateutil import relativedelta
from jsmin import jsmin
from tornado.httpclient import AsyncHTTPClient

from configs.const import *


def make_dir(path):
    """创建目录"""
    return os.makedirs(path, 0o777, True)


def write(content, fname):
    # 写文件
    try:
        f = open(BASE_PATH + fname, 'w')
        f.write(content)
        f.close()
    except Exception as data:
        print(data)
    return True


def log(obj, fname):  # 写日志文件
    try:
        f = open(LOG_PATH + fname, 'a')
        f.write(time_mdh() + str(obj) + "\n")
        f.close()
    except Exception as data:
        print(data)
    return True


def save_pid(pid, fname):  # 记录pid文件
    try:
        f = open(fname, 'w')
        f.write(str(pid))
        f.close()
    except Exception as data:
        print(data)
    return True


def play_log_start(tid):  # 清空记录桌子流程数据的日志文件
    try:
        f = open(LOG_PATH + 'table' + str(tid) + '.log', 'w')
        f.write(time_mdh() + "Clear:\n")
        f.close()
    except Exception as data:
        print(data)
        pass
    return True


def time_mdh():
    return time.strftime("%m-%d %X ", time.localtime())


def time_format(format_str, time_stamp):
    return time.strftime(format_str, time.localtime(time_stamp))


def timestamp():  # 返回时间戳int型
    return int(time.time())


def timestamp_today():  # 返回当天0时的时间戳int型
    any_day = datetime.date(2011, 11, 1)
    date_today = any_day.today()
    date_str = time.strptime(str(date_today), "%Y-%m-%d")
    return int(time.mktime(date_str))


def timestamp_yesterday():  # 返回昨天的0点的时间戳
    return timestamp_today() - 24 * 60 * 60


def timestamp_tomorrow():  # 返回明天0点的时间戳
    return timestamp_today() + 24 * 60 * 60


def timestamp_month_start():
    first = datetime.date.today().replace(day=1)
    return int(time.mktime(first.timetuple()))


def timestamp_month_end():
    end = datetime.date.today().replace(day=1)
    end = end + relativedelta.relativedelta(months=1)
    return int(time.mktime(end.timetuple())) - 1


def timestamp_before_7_days():  # 7天
    return timestamp_today() - 24 * 60 * 60 * 7


def timestamp_week():  # 一周内时间戳
    today = datetime.datetime.today()
    s = int(today.strftime("%w"))
    if s != 0:
        start_days_diff = s - 1
        end_days_diff = (7 - s) % 7 + 1
    else:
        start_days_diff = 6
        end_days_diff = 1

    start_week_str = (today - datetime.timedelta(days=start_days_diff)).strftime("%Y-%m-%d")
    end_week_str = (today + datetime.timedelta(days=end_days_diff)).strftime("%Y-%m-%d")

    start_week_timestamp = int(time.mktime(time.strptime(start_week_str, "%Y-%m-%d")))
    end_week_timestamp = int(time.mktime(time.strptime(end_week_str, "%Y-%m-%d")))

    return start_week_timestamp, end_week_timestamp


def sha1(data):
    return hashlib.sha1(data.encode(encoding='UTF-8')).hexdigest()


def md5(data):
    return hashlib.md5(data.encode(encoding='UTF-8')).hexdigest()


def sha256(data):
    return hashlib.sha256(data.encode(encoding='UTF-8')).hexdigest()


def read_json_file(filename):  # 读json文件，并返回对应的对象，适用于小配置文件的读取
    try:
        with open(filename, encoding='utf-8') as js_file:
            mini_con = jsmin(js_file.read())
            obj = json.loads(mini_con)
            return obj
    except Exception as data:
        print("read json file fail:", filename, data)
    return {}


def json_decode(data):
    # 解析JSON数据，可以解析str或bytes
    try:
        if isinstance(data, bytes):
            data = data.decode('utf8')
        py_ret = json.loads(data)
        return py_ret
    except Exception as exp:
        log(str(exp) + ': ' + str(data), 'jsondecode.log')
        return []


def json_encode(data):
    # 从JSON中获取成对象,之所以要把此方法写在这里，请看文件开头的 reload 方法，这样才可以处理utf-8字符
    return str(json.dumps(data, ensure_ascii=False))


_string_list = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c',
                'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p',
                'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', 'A', 'B', 'C',
                'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P',
                'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']


def random_string(length=32):
    r_start, r_end = 0, len(_string_list) - 1
    result = ''
    for i in range(0, length - 1):
        result += _string_list[random.randint(r_start, r_end)]
    return result


def get_random_num(length=5):  # 获得随机数字，并返回字符串
    assert 0 < length <= 20
    min_num = 10 ** (length - 1)
    max_num = 10 ** length - 1
    return str(random.randint(min_num, max_num))


def get_random_small_union_id():
    # 小联盟ID段 200000 - 299999
    return random.randint(200000, 299999)


def get_random_union_partner_id():
    # 联盟合伙人ID段 300000 - 499999
    return random.randint(300000, 499999)


def http_get(url, success_func, fail_func):
    # 注意要使用 tornado 启动APP后此函数才有效
    def handle_request(response):
        if response.body:
            success_func(response.body)
            return

        if response.error:
            fail_func()
        else:
            success_func(response.body)

    http_client = AsyncHTTPClient()
    params = {'method': 'GET'}
    http_client.fetch(url, handle_request, **params)


def http_post(url, post_params, success_func, fail_func, body=None):
    # 注意要使用 tornado 启动APP后此函数才有效
    def handle_request(response):
        if response.body:
            success_func(response.body)
            return

        if response.error:
            fail_func()
        else:
            success_func(response.body)

    http_client = AsyncHTTPClient()
    params = {'method': 'POST', 'body': '', 'validate_cert': False}
    if post_params:
        params['body'] = urllib.parse.urlencode(post_params)
    if body:
        params['body'] = body
    http_client.fetch(url, handle_request, **params)


def cos_upload(url, headers, file_params):
    """ 使用 requests 库 发送http请求 """
    try:
        http_resp = requests.post(url, None, headers=headers, verify=False, files=file_params)
        status_code = http_resp.status_code
        if status_code == 200 or status_code == 400:
            return http_resp.json()
        else:
            return "NETWORK_ERROR"
    except Exception as e:
        print(e)
        return "SERVER_ERROR"


class ObjectDict(dict):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            return None

    def __setattr__(self, name, value):
        self[name] = value


def format_time_by_time(t, f="%Y-%m-%d %H:%M:%S"):
    return time.strftime(f, time.localtime(t))


def bytes_to_str(data):
    if isinstance(data, bytes):
        return data.decode('utf-8')
    return data


def check_int(data):
    if not isinstance(data, str):
        return data
    if not data.isdigit():
        return data
    return int(data)


def check_list(data):
    if not isinstance(data, list):
        return data
    return list(data)


def str_to_int(data):
    # 从字符串转换成INT
    if not data:
        return 0
    try:
        return int(data)
    except Exception as data:
        print(data)
    return 0


def filter_emoji(source):
    """将中文、英文大小写、数字以外的字符全过滤掉"""
    if not source or type(source) is not str:
        return source
    pattern = re.compile(
        "([abcdefghijklmnopqrstuvwxyz"
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789,\.\-\+\_\=\;<>\!\@#$%^&*()，。［］（）\u4e00-\u9fff]+)")
    results = pattern.findall(source)
    if not results:
        return ""
    return "".join(results)


def get_last_time(date_str=""):
    """
    返回上一分钟的起始时间戳，与结束时间戳
    Example : 
        now : 0:39:12
    :return: [0:38:00,0:38:59]
    """
    if not date_str:
        format_str = '%Y-%m-%d %H:%M:00'
        time_str = datetime.datetime.now().strftime(format_str)
        date_str = time.strptime(time_str, format_str)
    time_minute = int(time.mktime(date_str))
    return time_minute - 60, time_minute - 1


def get_current_start_end_timestamp(date_str=""):
    """
    返回当前的起始时间戳，与结束时间戳
    """
    if not date_str:
        format_str = '%Y-%m-%d %H:%M:00'
        time_str = datetime.datetime.now().strftime(format_str)
        date_str = time.strptime(time_str, format_str)
    time_minute = int(time.mktime(date_str))
    return time_minute, time_minute + 59


def ipaddress_format(ip):
    """
    INT 型 IP 地址转换成 IPV4 字符串
    :param ip: 1912018224
    :return: '113.247.21.48'
    """
    return str(ipaddress.ip_address(ip))


def get_public_phone_number(params):
    phone = params.get('phone', '')
    if not phone:
        return ''
    if len(phone) != 11:
        return phone
    return phone[0:3] + "****" + phone[7:]
