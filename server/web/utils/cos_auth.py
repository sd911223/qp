#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
import time
import urllib.request
import urllib.parse
import urllib.error
import hmac
import hashlib
import binascii
import base64
from configs import config


class Auth(object):
    def __init__(self):
        pass

    @staticmethod
    def app_sign(bucket_name, cos_path, expired, upload_sign=True):
        app_id = config.cos_app_id
        secret_id = config.cos_secret_id
        now = int(time.time())
        rdm = random.randint(0, 999999999)
        cos_path = urllib.parse.quote(cos_path.encode('utf8'), '~/')
        if upload_sign:
            file_id = '/%s/%s%s' % (app_id, bucket_name, cos_path)
        else:
            file_id = cos_path

        if expired != 0 and expired < now:
            expired += now

        sign_tuple = (app_id, secret_id, expired, now, rdm, file_id, bucket_name)

        plain_text = 'a=%s&k=%s&e=%d&t=%d&r=%d&f=%s&b=%s' % sign_tuple
        secret_key = config.cos_secret_key
        sha1_hmac = hmac.new(bytes(secret_key, 'utf-8'), bytes(plain_text, 'utf-8'), hashlib.sha1)
        hmac_digest = sha1_hmac.hexdigest()
        hmac_digest = binascii.unhexlify(hmac_digest)
        sign_hex = hmac_digest + bytes(plain_text, 'utf-8')
        sign_base64 = base64.b64encode(sign_hex)
        return sign_base64.decode('utf-8')

    @staticmethod
    def sign_once(bucket, cos_path):
        """单次签名(针对删除和更新操作)

        :param bucket: bucket名称
        :param cos_path: 要操作的cos路径, 以'/'开始
        :return: 签名字符串
        """
        return Auth.app_sign(bucket, cos_path, 0)

    @staticmethod
    def sign_more(bucket, cos_path, expired):
        """多次签名(针对上传文件，创建目录, 获取文件目录属性, 拉取目录列表)

        :param bucket: bucket名称
        :param cos_path: 要操作的cos路径, 以'/'开始
        :param expired: 签名过期时间, UNIX时间戳, 如想让签名在30秒后过期, 即可将expired设成当前时间加上30秒
        :return: 签名字符串
        """
        return Auth.app_sign(bucket, cos_path, expired)

    @staticmethod
    def sign_download(bucket, cos_path, expired):
        """下载签名(用于获取后拼接成下载链接，下载私有bucket的文件)

        :param bucket: bucket名称
        :param cos_path: 要下载的cos文件路径, 以'/'开始
        :param expired:  签名过期时间, UNIX时间戳, 如想让签名在30秒后过期, 即可将expired设成当前时间加上30秒
        :return: 签名字符串
        """
        return Auth.app_sign(bucket, cos_path, expired, False)
