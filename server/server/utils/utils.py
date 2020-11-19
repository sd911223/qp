# coding:utf-8

import datetime
import hashlib
import ujson as json
import random
import time
import os
import re

from jsmin import jsmin

from base import const


# 写文件
def write(content, fname):
    try:
        f = open(const.BASE_PATH + fname, 'w')
        f.write(content)
        f.close()
    except Exception as data:
        print(data)
    return True


# 写日志文件
def log(obj, fname):
    try:
        f = open(const.LOG_PATH + fname, 'a')
        f.write(time_mdh() + str(obj) + "\n")
        f.close()
    except Exception as data:
        print(data)
    return True


# 记录pid文件
def save_pid(pid, fname):
    try:
        f = open(const.BASE_PATH + "pids/" + fname, 'w')
        f.write(str(pid))
        f.close()
    except Exception as data:
        print(data)
    return True


# 返回 月日 时分秒 的时间字符串
def time_mdh():
    return time.strftime("%m-%d %X ", time.localtime())


# 返回时间戳int型
def timestamp():
    return int(time.time())


# 返回当天0时的时间戳int型
def timestamp_today():
    any_day = datetime.date(2011, 11, 1)
    date_today = any_day.today()
    date_str = time.strptime(str(date_today), "%Y-%m-%d")
    return int(time.mktime(date_str))


# 返回昨天的0点的时间戳
def timestamp_yesterday():
    return timestamp_today() - 24 * 60 * 60


def md5(data):
    return hashlib.md5(data).hexdigest()


# 读json文件，并返回对应的对象，适用于小配置文件的读取
def read_json_file(filename):
    try:
        with open(filename) as js_file:
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
        print('eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee')
        try:
            log(str(exp) , 'json_decode.log')
            log( str(data), 'json_decode.log')
        except Exception as e:
            print(e)
        return []


# 对象到json字符串
def json_encode(data):
    return str(json.dumps(data, ensure_ascii=False))


# 获得随机数字，并返回字符串
def get_random_num(length=5):
    assert 0 < length <= 20
    min_num = 10 ** (length - 1)
    max_num = 10 ** length - 1
    return str(random.randint(min_num, max_num))


def randint(min_num=0, max_num=0):
    return random.randint(min_num, max_num)


def str_to_int(data):
    # 从字符串转换成INT
    if not data:
        return 0
    try:
        return int(data)
    except Exception as data:
        print(data)
    return 0


def bytes_to_str(data):
    if isinstance(data, bytes):
        return data.decode('utf-8','ignore')
    return data


def check_int(data):
    if not isinstance(data, str):
        return data
    if not data.isdigit():
        return data
    return int(data)


def check_float(data):
    # 从字符串转换成double
    if not data:
        return 0.0
    try:
        return float(data)
    except Exception as data:
        print(data)
    return 0.0


def _round_by_base_rate(num, rate):
    assert rate != 0
    tail_num = rate if num % rate - rate / 2 >= 0 else 0
    return int(num / rate) * rate + tail_num


def round_by_hundred(num):  # 百分位四舍五入
    return _round_by_base_rate(num, 100)


def round_by_ten(num):  # 十分位四舍五入
    return _round_by_base_rate(num, 10)


def underscore_to_camel(data: dict):
    result = dict()
    for k, v in data.items():
        if type(k) == str:
            words = k.split("_")
            new_key = [word[0].upper() + word[1:] for word in words]
            new_key = new_key[0].lower() + new_key[1:]

        if type(v) == dict:
            result[new_key] = underscore_to_camel(v)
        else:
            result[new_key] = v

    return result


# 获取 GIT 当前版本号 & 时间
def read_version():
    t = time.strftime("%m%d%H%M", time.localtime())
    try:
        for filename in os.listdir(const.BASE_PATH + '/version'):
            return f"{filename} {t}"
    except Exception as e:
        return t
    return t


def remove_by_value(data, value, remove_count=1):
    """
    :param data: list
    :param value:
    :param remove_count: 为-1的时候表示删除全部, 默认为1
    :return: already_remove_count: int
    """
    data_len = len(data)
    count = remove_count == -1 and data_len or remove_count

    already_remove_count = 0

    for i in range(0, count):
        if value in data:
            data.remove(value)
            already_remove_count += 1
        else:
            break

    return already_remove_count


class ObjectDict(dict):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            return None

    def __setattr__(self, name, value):
        self[name] = value


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
