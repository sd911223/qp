# coding:utf-8

import os
import tornado.web
from configs import error, config

from .base_handler import BaseHandler
from utils import utils
from models import base_redis


def _get_save_path(timestamp):
    path = os.path.join(config.sub_static_path, "aac", str(utils.time_format("%Y%m%d", timestamp)))
    return config.root_path, path


def _make_save_path(timestamp):
    path1, path2 = _get_save_path(timestamp)
    utils.make_dir(os.path.join(path1, path2))
    return path1, path2


class UploadAACHandler(BaseHandler):

    def prepare(self):
        if not self.check_fixed_params(True):
            return self.write_json(error.DATA_BROKEN)
        if not self.check_sign():
            return self.write_json(error.SIGN_FAIL)

    @tornado.web.asynchronous
    def post(self):
        return self._request()

    def __gen_url(self, file_path):
        protocol = self.request.protocol
        host = self.request.host
        return protocol + "://" + host + "/fetchAAC/" + file_path

    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))
        if not params or not params.get('roomID'):
            return self.write_json(error.DATA_BROKEN)

        room_id = int(params.get('roomID'))
        timestamp = utils.timestamp()
        random_id = utils.get_random_num(4)
        sound_id = "{0}_{1}_{2}".format(room_id, timestamp, random_id)
        # save_file_name = sound_id + ".aac"

        if not self.request.files or not self.request.files.get("aac"):
            return self.write_json(error.DATA_BROKEN)

        upload_file = self.request.files.get("aac")
        if not upload_file or not type(upload_file) is list or len(upload_file) != 1:
            return self.write_json(error.DATA_BROKEN)

        upload_file = upload_file[0]
        # save_root_path, save_sub_path = _make_save_path(timestamp)
        # abs_file_name = os.path.join(save_root_path, save_sub_path, save_file_name)
        base_redis.save(sound_id, upload_file["body"])
        # with open(abs_file_name, "wb") as up:
        #     redis_base.save(sound_id, upload_file["body"])
        #     up.write(upload_file["body"])

        # relative_file_name = os.path.join(save_sub_path, save_file_name)
        url = self.__gen_url(sound_id)
        return self.write_json(error.OK, {"soundID": sound_id, "url": url})


class GetAACHandler(BaseHandler):

    @tornado.web.asynchronous
    def get(self, file_name):
        """
        HTTP/1.1 200 OK
        Server: nginx/1.11.7
        Date: Tue, 10 Jan 2017 14:25:50 GMT
        Content-Type: application/octet-stream
        Content-Length: 3104
        Last-Modified: Tue, 10 Jan 2017 11:52:20 GMT
        Connection: keep-alive
        ETag: "5874caf4-c20"
        Expires: Wed, 11 Jan 2017 14:25:50 GMT
        Cache-Control: max-age=86400
        Accept-Ranges: bytes
        :param file_name:
        :return:
        """
        data = base_redis.fetch(file_name)
        if not data:
            return self.send_error(404)
        self.add_header("Content-Type", "application/octet-stream")
        self.finish(chunk=data)
