# coding:utf-8
import base64

import tornado.web
from tornado.options import options

from configs import config
from configs import const
from configs import error
from models import level_stat_model
from models import online_model
from models import player_model
from models import report_model
from models import server_model
from models import tables_model, activity_model
from models.base_redis import share_connect as redis_conn
from utils import utils, outer
from .base_handler import BaseHandler


def _get_token(db, uid, online_info):
    if not uid:
        return ''

    if online_info and online_info.get('token'):
        return online_info.get('token')

    inserts = online_model.insert(db, uid)
    return inserts['token']


def _find_room_info(db, result: dict, online_info):
    uid = 0
    ip, port = server_model.pick_one_gateway(db)

    result['server'] = {'host': ip, "port": port}
    if online_info and online_info.get('uid'):
        uid = online_info.get('uid')

    if online_info and online_info.get('tid') > 0:
        table_info = tables_model.get(db, online_info.get('tid'))
        if not table_info:
            online_model.clear_tid(db, uid, online_info.get('tid'))
        else:
            result['roomInfo'] = {"gameType": table_info['game_type'], "roomID": table_info.get('tid'), "inRoom": 1}
            return result

    tables_info = tables_model.get_all_tables_by_owner(db, uid)

    for table_info in tables_info:
        table_cache_data = tables_model.get_table_info(redis_conn(), table_info.get('tid')) or {
            "player_list": [],
            "players": [],
            "round_index": 1,
            "table_status": 0
        }

        #  处理玩家创建房间后为连上server的情况
        if table_info["is_agent"] == 0 and table_info["owner"] not in table_cache_data["player_list"]:
            table_cache_data["player_list"].append(table_info["owner"])

        in_room = int(uid in table_cache_data["player_list"])
        if table_info.get('tid') > 0 and in_room:
            result['roomInfo'] = {"gameType": table_info.game_type, "roomID": table_info.get('tid'), "inRoom": in_room}
            break

    return result


def _format_user_return(db, ip, params):
    online_info = online_model.get(db, params['uid'])
    nick_name = player_model.get_nick_name(params)
    ips = level_stat_model.get_ips_by_level(db, params['level'])['ips']
    idle_table_diamond = tables_model.get_total_idle_diamonds_by_uid(db, params['uid'])
    calc_diamond = int(params['diamond'] - idle_table_diamond)
    show_diamonds = max(0, calc_diamond)
    idle_match_table_diamond = tables_model.get_total_match_idle_diamonds_by_uid(db, params['uid'])
    show_la_jiao_dou = max(0, int(params['la_jiao_dou'] - idle_match_table_diamond))

    show_yuan_bao = params['yuan_bao']
    if calc_diamond < 0:
        show_yuan_bao = max(0, params['yuan_bao'] + calc_diamond)

    result = {
        'uid': params['uid'],
        'loginTime': params['login_time'],
        'sex': params['sex'],
        'nickname': nick_name,
        'avatar': params['avatar'] or '',
        'allowNiuNiu': params['allow_niu_niu'],
        'isLucker': params['is_lucker'],
        'diamond': show_diamonds,
        'yuanBao': show_yuan_bao,
        'laJiaoDou': show_la_jiao_dou,
        'roundCount': int(params['round_count']),
        'score': int(params['score']),  # 积分
        'signTime': int(params['sign_time']),  # 最后签到时间
        'signCount': int(params['sign_count']),  # 已签到次数
        'allowMatch': params['allow_match'],
        'rateScore': int(params['rate_score']),
        'IP': ip,
        'customType': params['custom_type'],
        'fatherId': params['father_id'],
        'agent': int(params.get('agent', 0)),
        'phone': utils.get_public_phone_number(params),
        'token': _get_token(db, params['uid'], online_info),
        'autoToken': params['auto_token'],
        'ips': str(base64.b64encode(bytes(str(ips), 'utf-8')), 'utf-8')
        # 'roomInfo': self._find_room_info(params['uid']),
    }
    return _find_room_info(db, result, online_info)


def _answer_by_user_info(handler: BaseHandler, user_info, params):
    """响应玩家BY玩家数据"""
    # 如果用户上次登录时间，小于今天0点，则插入活跃表
    if user_info.get('login_time') and user_info.get('login_time') < utils.timestamp_today():
        report_model.increase_player_login_statistics(handler.share_db_logs())
    player_model.update_login_info(handler.share_db(), user_info.get("uid"), params, handler.get_int_ip())
    activity_model.insert_spring_activity_user(handler.share_db(), user_info.get('uid'))
    if not config.in_white_list(user_info.get("uid"), handler.channel_id):
        return handler.write_error(error.SYSTEM_ERR, "登录被停止，请联系管理员开放！UID: " + str(user_info.get("uid")), {})
    return handler.write_json(error.OK, _format_user_return(handler.share_db(), handler.request.remote_ip, user_info))


class WeChatLoginHandler(BaseHandler):
    def prepare(self):
        if not self.check_fixed_params(False):
            return self.write_json(error.DATA_BROKEN)
        if not self.check_sign_no_token():
            return self.write_json(error.SIGN_FAIL)

    def get(self):
        return self._request()

    def post(self):
        return self._request()

    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))
        if not params or (not params.get('imei') and not params.get('mac')):
            return self.write_json(error.DATA_BROKEN)

        params["ip"] = self.get_int_ip()

        if params.get('code'):
            return self.__login_by_code(params)

        if params.get('autoToken'):
            return self.__login_by_auto_token(params.get('autoToken'))

        return self.write_json(error.DATA_BROKEN)

    def modify_unionid_to_openid(self, user_info):
        if not user_info or 'openid' not in user_info or 'unionid' not in user_info:
            return False
        openid = user_info.get('openid')
        unionid = user_info.get('unionid')
        openid_player = player_model.get_by_openid(self.share_db(), openid)
        if not openid_player:
            return
        unionid_player = player_model.get_by_unionid(self.share_db(), unionid)
        if not unionid_player:
            return
        if int(openid_player['uid']) != int(unionid_player['uid']):
            player_model.delete_union_id_and_modify_union_id_with_refer_info(self.share_db(), openid, unionid,
                                                                             unionid_player['refer_uid'],
                                                                             unionid_player['refer_time'])
        return

    @tornado.web.asynchronous
    def __after_get_token_by_code(self, auth_info, params, uid=None, db_user_info=None):
        token = auth_info.get('access_token')
        open_id = auth_info.get('openid')
        url = "https://api.weixin.qq.com/sns/userinfo?access_token={0}&openid={1}"
        url = url.format(token, open_id)

        def suc_func(data):
            user_info = utils.json_decode(data)
            self.modify_unionid_to_openid(user_info)  # 通过微信绑定的新用户,将绑定至之前客户端的用户中
            if uid:
                player_model.we_chat_refresh(self.share_db(), user_info, uid, auth_info)
                user_type = const.TYPE_LOGIN
                if db_user_info and db_user_info['openid'] is None:
                    player_model.update_auto_token_and_openid_and_bind_time(self.share_db(), uid, user_info['unionid'],
                                                                            user_info['openid'])
                    # 更新一些客户端登录时才会有的数据(openid,auto_token...)
                if db_user_info and db_user_info['bind_after_login_time'] == -1 and db_user_info['refer_uid'] != -1:
                    player_model.update_bind_after_login_time(self.share_db(), uid)
            else:
                user_type = const.TYPE_LOGIN
                player = player_model.get_by_openid(self.share_db(), user_info.get('openid'))
                if player and player['unionid'] is None:
                    player_model.we_chat_modify_union_id(self.share_db(), user_info)
                    if player['bind_after_login_time'] == -1 and player['refer_uid'] != -1:
                        player_model.update_bind_after_login_time(self.share_db(), player['uid'])
                else:
                    player_model.we_chat_sign_up(self.share_db(), params, self.get_fixed_params(), auth_info, user_info)
                    outer.register(self.share_db(), user_info.get('openid'))
                    user_type = const.TYPE_REG
            player_info = player_model.get_by_auth_info(self.share_db(), auth_info)
            if player_info:
                report_model.add_active_user_login_ip_logs(self.share_db_logs(), player_info['uid'],
                                                           self.get_int_ip(), user_type)
                # self.__recommend_with_diamond(user_type, player_info)
                return _answer_by_user_info(self, player_info, self.get_fixed_params())
            return self.write_json(error.SYSTEM_ERR)

        def fail_func():
            return self.write_json(error.SYSTEM_ERR)

        utils.http_get(url, suc_func, fail_func)

    @tornado.web.asynchronous
    def __login_by_code(self, params):
        if not self.share_db():
            return self.write_json(error.SYSTEM_ERR)

        code = params.get('code')
        url = "https://api.weixin.qq.com/sns/oauth2/access_token" \
              "?appid={0}&secret={1}&code={2}&grant_type=authorization_code"
        url = url.format(options.we_chat_app_id, options.we_chat_app_secret, code)

        def suc_func(data):
            auth_info = utils.json_decode(data)
            user_info = player_model.get_by_auth_info(self.share_db(), auth_info)
            if user_info:
                return self.__after_get_token_by_code(auth_info, params, user_info['uid'], user_info)
            return self.__after_get_token_by_code(auth_info, params)

        def fail_func():
            self.write_json(error.SYSTEM_ERR)

        utils.http_get(url, suc_func, fail_func)

    @tornado.web.asynchronous
    def __login_by_auto_token(self, auto_token):
        if not self.share_db():
            return self.write_json(error.SYSTEM_ERR)

        user_info = player_model.get_by_auto_token(self.share_db(), auto_token)
        if not user_info:
            return self.write_json(error.DATA_BROKEN)

        if not user_info['unionid']:
            return self.write_json(error.DATA_BROKEN)

        if user_info['login_time'] < utils.timestamp() - 7 * 24 * 60 * 60:
            return self.write_json(error.AUTO_TOKEN_EXPIRED)

        if user_info['bind_after_login_time'] == -1 and user_info['refer_uid'] != -1:
            player_model.update_bind_after_login_time(self.share_db(), user_info['uid'])

        report_model.add_active_user_login_ip_logs(self.share_db_logs(), user_info['uid'], self.get_int_ip(),
                                                   const.TYPE_LOGIN)
        return _answer_by_user_info(self, user_info, self.get_fixed_params())


class GuestLoginHandler(BaseHandler):
    def prepare(self):
        if not self.check_fixed_params(False):
            return self.write_json(error.DATA_BROKEN)
        if not self.check_sign_no_token():
            return self.write_json(error.SIGN_FAIL)

    def get(self):
        return self._request()

    def post(self):
        return self._request()

    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))
        if not params or (not params.get('imei') and not params.get('mac')):
            return self.write_json(error.DATA_BROKEN)

        if not self.share_db():
            return self.write_json(error.SYSTEM_ERR)


        params["ip"] = self.get_int_ip()
        user_info = player_model.get(self.share_db(), params)
        active_type = const.TYPE_LOGIN
        if not user_info:
            active_type = const.TYPE_REG
            player_model.insert_guest(self.share_db(), params, self.get_fixed_params())
            user_info = player_model.get(self.share_db(), params)
            if not user_info:
                return self.write_json(error.SYSTEM_ERR)

        report_model.add_active_user_login_ip_logs(self.share_db_logs(), user_info['uid'],
                                                   self.get_int_ip(), active_type)

        return _answer_by_user_info(self, user_info, self.get_fixed_params())
