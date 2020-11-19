# coding:utf-8

from configs import error

from .base_handler import BaseHandler
from models import player_model
from models import logs_model
from models import online_model
from utils import utils
from models import configs_model
import ujson as json


class RequestVerifyCodeHandler(BaseHandler):
    def prepare(self):
        if not self.check_fixed_params(True):
            return self.write_json(error.DATA_BROKEN)
        if not self.check_sign():
            return self.write_json(error.SIGN_FAIL)

    def get(self):
        return self._request()

    def post(self):
        return self._request()

    def _request(self):
        info = player_model.get_by_uid(self.share_db(), self.uid)
        if not info:
            return self.write_json(error.SYSTEM_ERR)

        expire_at = int(info.get('verify_expire_at', 0) or 0)
        if expire_at > utils.timestamp() - 60:  # 1分钟以内，不允许重复发送
            return self.write_json(error.OPERATION_TOO_FREQUENT)

        verify_code = player_model.set_verify_code(self.share_db(), self.uid)
        if verify_code <= 0:
            return self.write_json(error.SYSTEM_ERR)

        self.__send_sms(info.get('phone', ''), verify_code)
        return self.write_json(error.OK)

    def __send_sms(self, phone_number, verify_code):
        if not phone_number or not verify_code:
            return
        user_name = ""
        password = ""

        msg = "{0}为您的重置验证码，请于{1}分钟内填写。如非本人操作，请忽略本短信。".format(verify_code, 10)
        url = "".format(user_name, utils.md5(password), phone_number, msg)

        def suc_func(data):
            data = json.loads(data)
            if data['returnstatus'] != 'Success':
                utils.log(data, "sms_error.log")
                return self.write_json(error.SYSTEM_ERR)

        def fail_func():
            return self.write_json(error.SYSTEM_ERR)

        utils.http_post(url, None, suc_func, fail_func, msg)


class ResetPwdHandler(BaseHandler):
    def prepare(self):
        if not self.check_fixed_params(True):
            return self.write_json(error.DATA_BROKEN)
        if not self.check_sign():
            return self.write_json(error.SIGN_FAIL)

    def get(self):
        return self._request()

    def post(self):
        return self._request()

    def _request(self):
        params = utils.json_decode(self.get_string('params'))
        if not params or not params.get('verifyCode') or not params.get('pwd'):
            return self.write_json(error.DATA_BROKEN)

        pwd = params.get('pwd', '')
        verify_code = params.get('verifyCode', '')
        if not pwd or len(pwd) < 6 or not verify_code or len(verify_code) < 6:
            return self.write_json(error.DATA_BROKEN)

        info = player_model.get_by_uid(self.share_db(), self.uid)
        if not info:
            return self.write_json(error.SYSTEM_ERR)

        if 0 >= player_model.verify_by_code(self.share_db(), self.uid, verify_code):
            return self.write_json(error.VERIFY_CODE_ERR)

        if not player_model.edit_pwd(self.share_db(), self.uid, pwd):
            return self.write_json(error.SYSTEM_ERR)

        return self.write_json(error.OK)


class GiveDiamondsHandler(BaseHandler):
    def prepare(self):
        if not self.check_fixed_params(True):
            return self.write_json(error.DATA_BROKEN)
        if not self.check_sign():
            return self.write_json(error.SIGN_FAIL)

    def get(self):
        return self._request()

    def post(self):
        return self._request()

    def _request(self):
        params = utils.json_decode(self.get_string('params'))
        if not params or not params.get('uid') or not params.get('diamonds'):# or not params.get('pwd'):
            return self.write_json(error.DATA_BROKEN)

        info = player_model.get_by_uid(self.share_db(), self.uid)
        # pwd = params.get('pwd', '')
        # if not pwd or len(pwd) < 6 or not player_model.check_password(info, pwd):  # 密码不正确
        #     return self.write_json(error.PASSWORD_ERR)

        diamonds = int(params.get('diamonds', 0))
        if diamonds <= 0 or diamonds > 100000:  # 参数不合法
            return self.write_json(error.DATA_BROKEN)

        online_info = online_model.get(self.share_db(), self.uid)
        if online_info.get('tid', 0) > 0:
            return self.write_json(error.ACCESS_DENNY)

        target_uid = int(params.get('uid', 0))
        target_info = player_model.get_by_uid(self.share_db(), target_uid)
        if not target_info:  # 赠送玩家不存在
            return self.write_json(error.UID_ERROR)
        if target_uid == self.uid:  # 不给自己加
            return self.write_json(error.UID_ERROR)

        if diamonds > info.get("diamond", 0):  # 钻石不够
            return self.write_json(error.DIAMONDS_NOT_ENOUGH)

        my_left = info.get('diamond', 0) - diamonds

        need_left_diamond = configs_model.get(self.share_db(), "left_diamonds") or 20
        if my_left < need_left_diamond:
            return self.write_json(error.NEED_LEFT_DIAMONDS, {"needLeft": need_left_diamond})

        flag = self.__move_diamonds(target_uid, player_model.get_nick_name(info),
                                    player_model.get_nick_name(target_info), diamonds,
                                    my_left, target_info.get('diamond', 0) + diamonds)

        if flag <= 0:  # 操作失败
            return self.write_json(error.DIAMONDS_NOT_ENOUGH)

        return self.write_json(error.OK, {"leftDiamonds": my_left})

    def __move_diamonds(self, refer_uid, nick_name, refer_nick_name, diamonds, left_diamonds, new_diamonds):
        if diamonds <= 0 or diamonds > 100000:
            return 0
        if 0 >= player_model.sub_diamonds(self.share_db(), self.uid, diamonds):  # 扣钻失败
            logs_model.add_diamonds_record(self.share_db_logs(), self.uid,
                                           refer_uid, refer_nick_name, diamonds, 1, left_diamonds, 1)
            return 0
        if 0 >= player_model.add_diamonds(self.share_db(), refer_uid, diamonds):  # 加钻失败
            logs_model.add_diamonds_record(self.share_db_logs(), refer_uid,
                                           self.uid, nick_name, diamonds, 2, left_diamonds, 2)
            return 0

        # 转出者写日志
        logs_model.add_diamonds_record(self.share_db_logs(), self.uid,
                                       refer_uid, refer_nick_name, diamonds, 1, left_diamonds, 3)
        # 转入者写日志
        logs_model.add_diamonds_record(self.share_db_logs(), refer_uid,
                                       self.uid, nick_name, diamonds, 2, new_diamonds, 3)
        return 1


class EditProfileHandler(BaseHandler):
    def prepare(self):
        if not self.check_fixed_params(True):
            return self.write_json(error.DATA_BROKEN)
        if not self.check_sign():
            return self.write_json(error.SIGN_FAIL)

    def get(self):
        return self._request()

    def post(self):
        return self._request()

    def _request(self):
        params = utils.json_decode(self.get_string('params'))
        if not params or not params.get('oldPwd') or not params.get('pwd'):
            return self.write_json(error.DATA_BROKEN)

        info = player_model.get_by_uid(self.share_db(), self.uid)
        if not info:
            return self.write_json(error.SYSTEM_ERR)

        old_pwd = params.get('oldPwd', '')
        if not old_pwd or len(old_pwd) < 6 or not player_model.check_password(info, old_pwd):
            return self.write_json(error.PASSWORD_ERR)

        pwd = params.get('pwd', '')
        if not pwd or len(pwd) < 6:
            return self.write_json(error.DATA_BROKEN)

        if pwd == old_pwd:
            return self.write_json(error.DATA_BROKEN)

        if not player_model.edit_pwd(self.share_db(), self.uid, pwd):
            return self.write_json(error.SYSTEM_ERR)

        return self.write_json(error.OK)


class DiamondRecordsHandler(BaseHandler):
    def prepare(self):
        if not self.check_fixed_params(True):
            return self.write_json(error.DATA_BROKEN)
        if not self.check_sign():
            return self.write_json(error.SIGN_FAIL)

    def get(self):
        return self._request()

    def post(self):
        return self._request()

    def _request(self):
        data = logs_model.get_diamond_records_by_uid(self.share_db_logs(), self.uid)
        result = []
        for item in data:
            if not item:
                continue
            result.append([item['refer_uid'], item['refer_nick_name'], item['time'],
                           item['diamonds'], item['left_diamonds'], item['reason_id']])
        result = {
            "list": result,
        }
        return self.write_json(error.OK, result)
