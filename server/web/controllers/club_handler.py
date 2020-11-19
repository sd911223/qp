# coding:utf-8

import logging
import time
import ujson as json
from decimal import Decimal

import pydash as _

import configs.const as const
from configs import error
from controllers.room_handler import CreateRoomHandler
from models import base_redis
from models import club_configs_model
from models import club_model
from models import game_room_model
from models import logs_model, club_rank_model
from models import player_model
from models import room_config_model, money_model
from models import tables_model
from models.base_redis import share_connect as redis_conn
from utils import utils
from .comm_handler import CommHandler


def default(obj):
    if isinstance(obj, Decimal):
        return str(obj)
    raise TypeError


def get_base_club(club_info):
    client_club_info = dict()
    key_map = dict(club_id="clubID", name="name", notice="notice", join_time="joinTime", auto_room="autoRoomCount",
                   max_player_count="maxPlayerCount", level="level", now_player_count="nowPlayerCount",
                   dismiss_time="dismissTime", avatar="avatar", price="price", )

    for key, value in club_info.items():
        if key not in key_map:
            continue

        client_club_info[key_map[key]] = value

    return client_club_info


def get_base_player(club_info):
    client_player_info = dict()
    key_map = dict(avatar="avatar", nick_name="name", sex="sex", uid="uid", remark="remark", permission="permission", )

    for key, value in club_info.items():
        if key not in key_map:
            continue

        client_player_info[key_map[key]] = value

    return client_player_info


class SetClubAutoRoomHandler(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))
        if "clubID" not in params or "maxAutoCreateRoom" not in params or "floor" not in params:
            return self.write_json(error.DATA_BROKEN)

        club_id = params['clubID']
        floor = params['floor']
        club_user = club_model.query_club_by_uid_and_club_id(self.share_db(), club_id, self.uid)
        if not club_user:
            return self.write_json(error.DATA_BROKEN)
        room_count = int(params['maxAutoCreateRoom'])
        if room_count < 0:
            return self.write_json(error.DATA_BROKEN)
        club_model.update_club_auto_room_count(self.share_db(), club_id, room_count, floor)
        club = club_model.get_club(self.share_db(), club_id)
        if club['dismiss_time'] != 0:
            return self.write_json(error.OK)
        res = self._create_room(club, room_count, floor)
        if res is error.OK:
            return self.write_json(error.OK)

    def __calc_diamonds(self, round_count: int, game_type):
        data = room_config_model.get_room_config(self.share_db(), game_type)
        diamonds = utils.json_decode(data['data'])
        for i in diamonds["diamondInfo"]:
            if i['count'] == round_count:
                return i['diamond']
        return -1

    def __calc_diamonds_with_player_count(self, round_count: int, game_type: int, player_count: int):
        data = room_config_model.get_room_config(self.share_db(), game_type)
        diamonds = utils.json_decode(data['data'])
        for i in diamonds["diamondInfo"]:
            if i['count'] == round_count and i['playerCount'] == player_count:
                return i['diamond']
        return -1

    def _create_room(self, club, auto_room_count, floor):
        current_room_count = tables_model.get_count_by_club_id_and_floor(self.share_db(), club['id'], floor)[
            'room_count']
        if auto_room_count <= current_room_count:
            return 0

        floor_config = club_model.get_club_floor_config_by_floor(self.share_db(), club['id'], floor)
        params = utils.json_decode(floor_config['play_config'])
        if not params or not params.get('gameType') or not params.get('totalRound'):
            return self.write_json(error.CLUB_AUTO_ROOM_NEED_CONFIG)
        rules = params.get("rules") or params.get("ruleDetails")

        game_type = params["gameType"]
        sid = game_room_model.get_best_server_sid(self.share_db(), redis_conn(), game_type)
        if not sid:
            return self.write_json(error.DATA_BROKEN)

        total_round = int(params["totalRound"])
        rule_type = params["ruleType"]

        if game_type in const.CALC_DIAMOND_WITH_PLAYER_NUM:
            diamonds = self.__calc_diamonds_with_player_count(total_round, game_type, rules.get("totalSeat"))
        else:
            diamonds = self.__calc_diamonds(total_round, game_type)

        if diamonds == -1:
            return self.write_json(error.DATA_BROKEN)

        user = player_model.get_by_uid(self.share_db(), club['uid'])
        if not user:
            return self.write_json(error.DATA_BROKEN)
        diff_count = auto_room_count - current_room_count

        idle_table_diamond = tables_model.get_total_idle_diamonds_by_uid(self.share_db(), user['uid'])
        if user.get('diamond', 0) + user.get('yuan_bao', 0) < diff_count * diamonds + idle_table_diamond:
            return self.write_json(error.DIAMONDS_CLUB_NOT_ENOUGH)

        consume_type = int(params.get('consumeType', 0))
        if consume_type not in (0, 1, 2):
            consume_type = 0

        for i in range(diff_count):
            tid = base_redis.spop_table_id() or utils.get_random_num(6)
            try:
                tables_model.insert(self.share_db(), sid, game_type, int(tid), club['uid'], 1, total_round,
                                    diamonds, rule_type, club["id"], rules, floor=floor, consume_type=consume_type)
            except Exception as data:
                logging.error(f"insert club table error: {club['id']} {data}")

        club_users = club_model.query_all_data_by_club_id(self.share_db(), club['id']) or list()
        broad_user = list()
        for user in club_users:
            broad_user.append(user["uid"])
        self.broad_cast_user(broad_user, {"type": const.AUTO_ROOM_CHANGE})
        return error.OK


class SetClubModeHandler(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))

        if "clubID" not in params:
            return self.write_json(error.DATA_BROKEN)

        game_config = params
        origin_service_type = -1

        club_info = club_model.query_club_by_uid_and_club_id(self.share_db(), params['clubID'], self.uid)
        if not club_info or club_info["permission"] not in (0, 1):
            return self.write_json(error.ACCESS_DENNY)

        floor = params['floor']

        floor_config = club_model.get_club_floor_config_by_floor(self.share_db(), params['clubID'], floor)
        play_config = utils.json_decode(floor_config['play_config'])

        if 'gameType' in play_config:
            origin_service_type = int(play_config['gameType'])

        if not game_config.get('gameType') or not game_config.get('totalRound') or not game_config.get('ruleType'):
            return self.write_json(error.DATA_BROKEN)

        game_type = params.get("gameType")
        consume_type = params.get('consumeType')
        if consume_type not in (1, 2):
            return self.write_json(error.DATA_BROKEN)

        rules = CreateRoomHandler.make_rule_details(game_type, game_config['ruleDetails'])

        params["ruleDetails"] = rules
        club_id = params["clubID"]
        del params["clubID"]

        club_model.update_club_play_config(self.share_db(), club_id, utils.json_encode(params), floor)

        if origin_service_type is not -1:
            self.publish_to_service(const.GAME_PLAY_CONFIG_CHANGE, 1, {"clubID": club_id, "floor": floor},
                                    origin_service_type)

        return self.write_json(error.OK)


class CreateClubHandler(CommHandler):
    @staticmethod
    def _default_play_config():
        play_config = {}
        return utils.json_encode(play_config)

    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))
        if "text" not in params:
            return self.write_json(error.DATA_BROKEN)

        club_name = params["text"]

        player_info = player_model.get_by_uid(self.share_db(), self.uid)

        if player_info["diamond"] < club_configs_model.get(self.share_db(), "min_diamond"):
            return self.write_json(error.CREATE_CLUB_ERROR_DIAMOND)

        club_list = club_model.get_club_by_owner(self.share_db(), self.uid) or []
        if len(club_list) >= club_configs_model.get(self.share_db(), "max_club_count", True):
            return self.write_json(error.CLUB_COUNT_IS_MAX)

        club_create_consume = utils.json_decode(club_configs_model.get(self.share_db(), "club_create_diamond", True))
        if len(club_create_consume) < (len(club_list)):
            return self.write_json(error.SYSTEM_ERR)

        consume = club_create_consume[len(club_list)]
        if consume > 0:
            if consume > player_info.get('diamond'):
                return self.write_json(error.DIAMONDS_NOT_ENOUGH)

        club_id = utils.get_random_num(6)
        play_config = self._default_play_config()
        wet_chat = params['wet_chat']
        count = club_model.create_club(self.share_db(), club_id, self.uid, club_name, "健康游戏，严禁赌博。", 1, 0, 0, 0,
                                       play_config, wet_chat)
        if count == 0:
            return self.write_error(error.SYSTEM_ERR)
        elif consume > 0:
            count = player_model.sub_diamonds(self.share_db(), self.uid, consume)
            if count == 0:
                return self.write_json(error.UID_ERROR)

        club_model.join_club(self.share_db(), self.uid, club_id, self.uid, 0)
        level_info = club_model.get_club_level_config(self.share_db(), 2)
        price = level_info and level_info["price"] or -1
        club_model.update_club_player_count(self.share_db(), club_id, 1)

        return self.write_json(error.OK, get_base_club(
            {"avatar": player_info["avatar"], "club_id": club_id, "name": club_name, "price": price}))


class DismissClubHandler(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))
        if "clubID" not in params:
            return self.write_json(error.DATA_BROKEN)

        club_id = params["clubID"]

        club_info = club_model.query_club_by_uid_and_club_id(self.share_db(), club_id, self.uid)
        if not club_info or club_info["permission"] not in (0,):
            return self.write_json(error.ACCESS_DENNY)

        club_info = club_model.get_club(self.share_db(), club_id)
        if club_info["dismiss_time"] != 0:
            return self.write_json(error.CLUB_STATUS_IS_ERROR)

        count = club_model.dismiss_club(self.share_db(), club_id)
        if count == 0:
            return self.write_json(error.SYSTEM_ERR)

        # 解散房间时清除全部空闲桌子
        tables_model.remove_idle_table_by_club_id(self.share_db(), club_id)

        return self.write_json(error.OK)


class GetClubHandler(CommHandler):
    def _request(self):
        club_id_list = club_model.query_club_by_uid(self.share_db(), self.uid)

        club_list = list()
        for club_id_info in club_id_list:
            club_info = club_model.get_club(self.share_db(), club_id_info["club_id"])
            if not club_info:
                continue

            if len(club_info) == 0:
                continue

            if club_info["status"] == -1:
                continue

            if 0 < club_info["dismiss_time"]:
                delay_time = int(club_configs_model.get(self.share_db(), "delete_delay_time", True))
                if (club_info["dismiss_time"] + delay_time) < time.time():
                    club_model.delete_club(self.share_db(), club_id_info["club_id"])
                    continue

            level_info = club_model.get_club_level_config(self.share_db(), club_info["level"])
            club_info["max_player_count"] = level_info["limit"]
            club_info["now_player_count"] = club_info["count"]
            club_info["club_id"] = club_info["id"]

            player_info = player_model.get_by_uid(self.share_db(), club_info["uid"])
            club_info["avatar"] = player_info["avatar"]

            club_game_info = club_model.get_club_floor_config(self.share_db(), club_id_info["club_id"])

            club = get_base_club(club_info)
            club['permission'] = club_id_info['permission']
            if club_id_info['permission'] in (0, 1,):
                verify_data = club_model.get_need_verify_data(self.share_db(), club_info['id'])
                club['review'] = 1 if verify_data else 0
            else:
                club['review'] = 0
            club["uid"] = club_info['uid']
            club["nick_name"] = player_info["nick_name"]
            club["wet_chat"] = club_info["wet_chat"]
            club["game_type"] = club_game_info
            club_list.append(club)

        return self.write_json(error.OK, club_list)


class SetUserRemark(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode((self.get_string('params')))
        if "uid" not in params or "clubID" not in params or "remark" not in params:
            return self.write_json(error.DATA_BROKEN)

        uid = params["uid"]
        club_id = params["clubID"]
        remark = params["remark"]

        club_relationship = club_model.query_club_by_uid_and_club_id(self.share_db(), club_id, self.uid)
        if club_relationship["permission"] not in (0, 1):
            return self.write_json(error.ACCESS_DENNY)

        club_relationship = club_model.query_club_by_uid_and_club_id(self.share_db(), club_id, uid)
        if not club_relationship:
            return self.write_json(error.ACCESS_DENNY)

        count = club_model.update_remark_by_uid_and_club_id(self.share_db(), uid, club_id, remark)
        if count == 0:
            return self.write_json(error.OK, params)

        return self.write_json(error.OK, params)

# permission
# 0 创始人
# 1 副馆长
# 2 一级管理员
# 3 二级管理员
# 99 普通成员
class SetUserPermission(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode((self.get_string('params')))

        if "uid" not in params or "clubID" not in params or "permission" not in params or params["permission"] not in (
                0, 1, 2, 3, 99):
            return self.write_json(error.DATA_BROKEN)

        uid = params["uid"]
        permission = params["permission"]
        club_id = params["clubID"]

        if uid == self.uid:  # 防止创建人更改自己权限
            return self.write_json(error.ACCESS_DENNY)

        club_relationship = club_model.query_club_by_uid_and_club_id(self.share_db(), club_id, self.uid)

        if params["permission"] <= club_relationship["permission"]:
            return self.write_json(error.ACCESS_DENNY)

        count = club_model.update_permission_by_uid_and_club_id(self.share_db(), uid, club_id, permission)
        if count == 0:
            return self.write_json(error.SYSTEM_ERR)

        if permission == 99:
            club = club_model.get_club(self.share_db(), club_id)
            if club:
                club_model.modify_club_tag_uid_to_owner_uid(self.share_db(), club_id, uid, club['uid'])

        return self.write_json(error.OK, params)


class QuitClubHandler(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode((self.get_string('params')))
        if "clubID" not in params:
            return self.write_json(error.DATA_BROKEN)

        club_id = params["clubID"]
        club_info = club_model.query_club_by_uid_and_club_id(self.share_db(), club_id, self.uid)
        if not club_info or club_info["permission"] not in (99,):  # 管理员不允许直接退出
            return self.write_json(error.ACCESS_DENNY)

        result = club_model.set_quit_club(self.share_db(), club_id, self.uid)
        if result > 0:
            club_model.update_club_player_count(self.share_db(), club_id, -1)
            return self.write_json(error.OK, {})
        else:
            return self.write_json(error.DATA_BROKEN)


class VerifyClubUserHandler(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode((self.get_string('params')))
        if "clubID" not in params or "uid" not in params or "status" not in params:
            return self.write_json(error.DATA_BROKEN)

        club_id = int(params["clubID"])
        uid = int(params["uid"])
        status = int(params["status"])

        if status not in (1, -1, -2):
            return self.write_json(error.DATA_BROKEN)

        club_info = club_model.query_club_by_uid_and_club_id(self.share_db(), club_id, uid)
        if club_info:
            return self.write_json(error.CLUB_IS_JOIN)

        club_info = club_model.query_club_by_uid_and_club_id(self.share_db(), club_id, self.uid)
        if not club_info or club_info["permission"] not in (0, 1):
            return self.write_json(error.ACCESS_DENNY)

        club_info = club_model.get_club(self.share_db(), club_id)
        if not club_info or club_info["dismiss_time"] != 0:
            return self.write_json(error.CLUB_STATUS_IS_ERROR)

        if status == 1:
            level_info = club_model.get_club_level_config(self.share_db(), club_info["level"])
            if club_info["count"] >= level_info.get('limit', 0):
                return self.write_json(error.CLUB_IS_FULL)

            count = club_model.join_club(self.share_db(), uid, club_id, club_info['uid'], 99)
            if count == 0:
                return self.write_json(error.SYSTEM_ERR)

            count = club_model.update_club_player_count(self.share_db(), club_id, 1)
            if count == 0:
                return self.write_json(error.SYSTEM_ERR)
        admin_info = player_model.get_by_uid(self.share_db(), self.uid)

        nick_name = admin_info['nick_name']
        count = club_model.update_user_verify(self.share_db(), uid, club_id, status, nick_name)
        if count == 0:
            return self.write_json(error.SYSTEM_ERR)

        self.broad_cast_user([uid], {"type": const.PASS_USER_JOIN_CLUB, "data": {"status": status, "clubID": club_id}})

        return self.write_json(error.OK, params)


# 申请加入俱乐部
class ApplyClubHandler(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode((self.get_string('params')))
        if "clubID" not in params:
            return self.write_json(error.DATA_BROKEN)

        club_id = int(params["clubID"])

        club_info = club_model.query_club_by_uid_and_club_id(self.share_db(), club_id, self.uid)
        if club_info:
            return self.write_json(error.CLUB_IS_JOIN)

        club_info = club_model.get_club(self.share_db(), club_id)
        if not club_info or club_info["dismiss_time"] != 0:
            return self.write_json(error.CLUB_STATUS_IS_ERROR)

        level_info = club_model.get_club_level_config(self.share_db(), club_info["level"])
        if club_info["count"] >= level_info.get('limit', 0):
            return self.write_json(error.CLUB_IS_FULL)

        if club_model.get_verify_list_by_uid(self.share_db(), club_id, self.uid, -2):
            return self.write_json(error.OK)

        count = club_model.update_user_verify(self.share_db(), self.uid, club_id, 0)

        if count == 0:
            self.write_json(error.SYSTEM_ERR)

        admin_list = club_model.get_club_admin(self.share_db(), club_id) or list()
        user_list = list()
        for user_info in admin_list:
            user_list.append(user_info["uid"])

        self.broad_cast_user(user_list,
                             {"type": const.USER_APPLY_JOIN_CLUB, "data": {"uid": self.uid, "clubID": club_id}})

        return self.write_json(error.OK)


# 添加进入俱乐部
class AgreeClubHandler(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode((self.get_string('params')))
        if "clubID" not in params or "uid" not in params:
            return self.write_json(error.DATA_BROKEN)

        club_id = int(params["clubID"])
        uid = int(params["uid"])

        if player_model.get_by_uid(self.share_db(), uid) is None:
            return self.write_json(error.ACCESS_DENNY)

        club_info = club_model.query_club_by_uid_and_club_id(self.share_db(), club_id, uid)
        if club_info:
            return self.write_json(error.CLUB_IS_JOIN)

        club_info = club_model.query_club_by_uid_and_club_id(self.share_db(), club_id, self.uid)
        if not club_info or club_info["permission"] not in (0, 1):
            return self.write_json(error.ACCESS_DENNY)

        club_info = club_model.get_club(self.share_db(), club_id)
        if not club_info or club_info["dismiss_time"] != 0:
            return self.write_json(error.CLUB_STATUS_IS_ERROR)

        level_info = club_model.get_club_level_config(self.share_db(), club_info["level"])
        if club_info["count"] >= level_info.get('limit', 0):
            return self.write_json(error.CLUB_IS_FULL)

        count = club_model.join_club(self.share_db(), uid, club_id, self.uid, 99)
        if count == 0:
            return self.write_json(error.SYSTEM_ERR)
        admin_info = player_model.get_by_uid(self.share_db(), self.uid)

        nick_name = admin_info['nick_name']

        count = club_model.update_user_verify(self.share_db(), uid, club_id, 1, nick_name)
        if count == 0:
            return self.write_json(error.SYSTEM_ERR)

        count = club_model.update_club_player_count(self.share_db(), club_id, 1)
        if count == 0:
            return self.write_json(error.SYSTEM_ERR)

        club_info = club_model.get_club(self.share_db(), club_id)
        self.broad_cast_user([uid],
                             {"type": const.ADD_USER_TO_CLUB, "data": {"clubID": club_id, "name": club_info["name"]}})

        return self.write_json(error.OK)


class GetVerifyListClubHandler(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode((self.get_string('params')))
        if "clubID" not in params:
            return self.write_json(error.DATA_BROKEN)

        club_id = int(params["clubID"])

        club_relation = club_model.query_club_by_uid_and_club_id(self.share_db(), club_id, self.uid)
        if not club_relation or club_relation["permission"] not in (0, 1):
            return self.write_json(error.ACCESS_DENNY)
        type = 0
        if "type" in params:
            type = int(params['type'])
        result = {}
        result["type"] = type
        if type == 1:
            status = params.get("status") or 0
            apply_list = club_model.get_verify_list(self.share_db(), club_id, status)

            player_list = list()
            for info in apply_list:
                player_info = player_model.get_by_uid(self.share_db(), info["uid"])
                if not player_info:
                    continue

                if player_info["model"] == "nomobile" and player_info["nick_name"] == "":
                    player_info["nick_name"] = "nomobile"

                player_info = get_base_player(player_info)
                player_info["requestTime"] = info['time']
                player_info["remark"] = info.get('remark', "")
                player_list.append(player_info)
            result["data"] = player_list
            return self.write_json(error.OK, result)
        elif type == 2:
            apply_record_list = club_model.get_verify_list_record(self.share_db(), club_id)
            result["data"] = apply_record_list
            return self.write_json(error.OK, result)


class KickUserHandler(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode((self.get_string('params')))
        if "clubID" not in params and 'uid' not in params:
            return self.write_json(error.DATA_BROKEN)

        club_id = int(params["clubID"])
        uid = int(params["uid"])

        club_relation = club_model.query_club_by_uid_and_club_id(self.share_db(), club_id, self.uid)
        if not club_relation or club_relation["permission"] not in (0, 1):
            return self.write_json(error.ACCESS_DENNY)

        club_relation = club_model.query_club_by_uid_and_club_id(self.share_db(), club_id, uid)
        if not club_relation or club_relation["permission"] in (0, 1):
            return self.write_json(error.ONLY_KICK_COMM_USER)

        count = club_model.delete_user(self.share_db(), club_id, uid)
        if count == 0:
            return self.write_json(error.SYSTEM_ERR)

        count = club_model.update_club_player_count(self.share_db(), club_id, -1)
        if count == 0:
            return self.write_json(error.SYSTEM_ERR)

        club = club_model.get_club(self.share_db(), club_id)
        club_model.update_club_tag_id(self.share_db(), club_id, uid, club['uid'])

        return self.write_json(error.OK, params)


class UpdateClubNameHandler(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode((self.get_string('params')))
        if "clubID" not in params or "text" not in params:
            return self.write_json(error.DATA_BROKEN)

        club_id = params["clubID"]
        club_info = club_model.query_club_by_uid_and_club_id(self.share_db(), club_id, self.uid)
        if not club_info or club_info["permission"] not in (0, 1):
            return self.write_json(error.ACCESS_DENNY)

        count = club_model.update_club_name(self.share_db(), club_id, params["text"])
        if count == 0:
            return self.write_json(error.SYSTEM_ERR)

        return self.write_json(error.OK, params)


class UpdateClubNoticeHandler(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode((self.get_string('params')))
        if "clubID" not in params or "notice" not in params:
            return self.write_json(error.DATA_BROKEN)

        club_id = params["clubID"]
        club_info = club_model.query_club_by_uid_and_club_id(self.share_db(), club_id, self.uid)
        if not club_info or club_info["permission"] not in (0, 1):
            return self.write_json(error.ACCESS_DENNY)

        count = club_model.update_club_notice(self.share_db(), club_id, params["notice"])
        if count == 0:
            return self.write_json(error.SYSTEM_ERR)

        return self.write_json(error.OK, params)


class UpgradeClubHandler(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode((self.get_string('params')))
        if "clubID" not in params:
            return self.write_json(error.DATA_BROKEN)

        club_id = params["clubID"]
        club_info = club_model.get_club(self.share_db(), club_id)
        if not club_info or club_info["status"] != 0:
            return self.write_json(error.CLUB_STATUS_IS_ERROR)

        club_info["level"] = int(club_info["level"]) + 1
        level_info = club_model.get_club_level_config(self.share_db(), club_info["level"])
        if not level_info:
            return self.write_json(error.CLUB_LEVEL_IS_MAX)

        info = player_model.get_by_uid(self.share_db(), self.uid)
        consume = level_info["price"]
        if consume > 0:
            if consume > info.get('diamond'):
                return self.write_json(error.DIAMONDS_NOT_ENOUGH)

        count = club_model.update_club_level(self.share_db(), club_id, int(club_info["level"]))
        if count == 0:
            return self.write_error(error.SYSTEM_ERR)
        else:
            if consume != 0:
                count = player_model.sub_diamonds(self.share_db(), self.uid, consume)
                if count == 0:
                    return self.write_json(error.UID_ERROR)

        club_info["max_player_count"] = level_info["limit"]
        level_info = club_model.get_club_level_config(self.share_db(), club_info["level"] + 1)
        club_info["price"] = level_info and level_info["price"] or -1

        owner = club_model.get_club_owner(self.share_db(), club_info["id"])
        player_info = player_model.get_by_uid(self.share_db(), owner["uid"])
        club_info["avatar"] = player_info["avatar"]

        return self.write_json(error.OK, get_base_club(club_info))


class GetClubUserHandler(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode((self.get_string('params')))
        if "clubID" not in params:
            return self.write_json(error.DATA_BROKEN)

        club_id = params["clubID"]

        club_relation = club_model.query_club_by_uid_and_club_id(self.share_db(), club_id, self.uid)
        if not club_relation:
            return self.write_json(error.ACCESS_DENNY)

        user_list = club_model.query_club_user_data_and_online_time_by_club_id(self.share_db(), club_id)
        user_info_list = []
        for info in user_list:
            data = get_base_player(info)
            data['loginTime'] = info['login_time']
            data['online'] = True if info['login_time'] and info['login_time'] > utils.timestamp() - 9 * 60 else False
            data['tagName'] = info['tag_name']
            data['tagUid'] = info['tag_uid']
            user_info_list.append(data)

        return self.write_json(error.OK, user_info_list)


class GetClubScoreListHandler(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode((self.get_string('params')))
        if "clubID" not in params or "isOwner" not in params:
            return self.write_json(error.DATA_BROKEN)

        # if int(params['isOwner']) != 1:
        #     club_id = params["clubID"]
        #     club_info = club_model.query_club_by_uid_and_club_id(self.share_db(), club_id, self.uid)
        #     if not club_info or club_info["permission"] not in (0, 1):
        #         result = []
        #         return self.write_json(error.OK, result)

        uid = self.uid if int(params['isOwner']) == 1 else 0
        match_type = None
        if "matchType" in params:
            match_type = int(params['matchType'])

        info = logs_model.get_club_room_list(self.share_db_logs(), params['clubID'], uid, match_type=match_type)
        result = []
        for row in info:
            result.append(
                {"recordID": row.record_id, "roomID": row.room_id, "time": row.finish_time, "owner": row.owner,
                 "matchType": row.match_type,
                 "roundIndex": logs_model.get_last_round_index_by_record_id(self.share_db_logs(), row.record_id)[
                                   'seq'] or 1,
                 "totalRound": row.round_count,
                 "gameType": row.game_type, "ruleType": row.rule_type,
                 "users": [[row.name1, row.score1, row.uid1], [row.name2, row.score2, row.uid2],
                           [row.name3, row.score3, row.uid3], [row.name4, row.score4, row.uid4],
                           [row.name5, row.score5, row.uid5], [row.name6, row.score6, row.uid6],
                           [row.name7, row.score7, row.uid7], [row.name8, row.score8, row.uid8],
                           [row.name9, row.score9, row.uid9], [row.name10, row.score10, row.uid10],
                           ], })
        return self.write_json(error.OK, result)


class GetClubScoreListByGameTypeAndTime(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode((self.get_string('params')))
        if "clubID" not in params or "isOwner" not in params or 'gameType' not in \
                params or "startTime" not in params or "endTime" not in params:
            return self.write_json(error.DATA_BROKEN)

        uid = self.uid if int(params['isOwner']) == 1 else 0
        match_type = None
        if "matchType" in params:
            match_type = int(params['matchType'])

        game_type = int(params['gameType'])
        start_time = int(params['startTime'])
        end_time = int(params['endTime'])

        info = logs_model.get_club_room_list_by_time_and_game_type(self.share_db_logs(), params['clubID'], uid,
                                                                   limit=1000, match_type=match_type,
                                                                   game_type=game_type,
                                                                   start_time=start_time, end_time=end_time)
        result = []
        for row in info:
            result.append(
                {"recordID": row.record_id, "roomID": row.room_id, "time": row.finish_time, "owner": row.owner,
                 "matchType": row.match_type,
                 "roundIndex": logs_model.get_last_round_index_by_record_id(self.share_db_logs(), row.record_id)[
                                   'seq'] or 1,
                 "totalRound": row.round_count,
                 "gameType": row.game_type, "ruleType": row.rule_type,
                 "users": [[row.name1, row.score1, row.uid1], [row.name2, row.score2, row.uid2],
                           [row.name3, row.score3, row.uid3], [row.name4, row.score4, row.uid4],
                           [row.name5, row.score5, row.uid5], [row.name6, row.score6, row.uid6],
                           [row.name7, row.score7, row.uid7], [row.name8, row.score8, row.uid8],
                           [row.name9, row.score9, row.uid9], [row.name10, row.score10, row.uid10],
                           ], })
        return self.write_json(error.OK, result)


class GetClubScoreByUid(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode((self.get_string('params')))
        if "clubID" not in params:
            return self.write_json(error.DATA_BROKEN)

        club_info = club_model.get_club(self.share_db(), params['clubID'])
        if not club_info:
            return self.write_json(error.DATA_BROKEN)

        match_type = None
        if "matchType" in params:
            match_type = int(params['matchType'])

        data = logs_model.get_club_week_and_day_info(self.share_db_logs(), params['clubID'], params['uid'],
                                                     match_type=match_type)
        return self.write_json(error.OK, data)


class GetClubInfoHandler(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode((self.get_string('params')))
        if "clubID" not in params:
            return self.write_json(error.DATA_BROKEN)

        club_info = club_model.get_club(self.share_db(), params['clubID'])
        if not club_info:
            return self.write_json(error.DATA_BROKEN)

        club_info["now_player_count"] = club_info["count"]
        club_info["club_id"] = club_info["id"]

        player_info = player_model.get_by_uid(self.share_db(), club_info["uid"])
        club_info["avatar"] = player_info["avatar"]

        club = get_base_club(club_info)

        club_user = club_model.query_club_by_uid_and_club_id(self.share_db(), club_info["id"], self.uid)
        club['join_time'] = club_user['join_time'] if club_user else 0

        score = money_model.get_dou_by_uid_and_club_id(self.share_db(), params['clubID'], self.uid)
        if score:
            club['dou'] = int(score['score'] or 0)
        else:
            club['dou'] = 0
        club['ownerName'] = player_info['nick_name']
        club['uid'] = club_info['uid']
        club['isOwner'] = 1 if self.uid == club_info['uid'] else 0
        club['permission'] = club_user['permission'] if club_user else 99
        club['gameConfig'] = club_model.get_club_floor_config(self.share_db(), params['clubID'])
        club['allowMatch'] = player_info['allow_match']
        club['queryWinnerScore'] = club_info['query_winner_score']

        return self.write_json(error.OK, club)


class GetClubWinnerList(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode((self.get_string('params')))
        if "clubID" not in params:
            return self.write_json(error.DATA_BROKEN)

        club_id = params["clubID"]
        club_info = club_model.query_club_by_uid_and_club_id(self.share_db(), club_id, self.uid)
        if not club_info or club_info["permission"] not in (0, 1):
            return self.write_json(error.ACCESS_DENNY)

        if club_info['uid'] != self.uid:
            return self.write_json(error.DATA_BROKEN)

        data = logs_model.get_club_winner_list(self.share_db_logs(), params['clubID'])
        return self.write_json(error.OK, data)


class SetClubWinnerList(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode((self.get_string('params')))
        if "clubID" not in params or 'ids' not in params:
            return self.write_json(error.DATA_BROKEN)

        club_id = params["clubID"]
        club_info = club_model.query_club_by_uid_and_club_id(self.share_db(), club_id, self.uid)
        if not club_info or club_info["permission"] not in (0, 1):
            return self.write_json(error.ACCESS_DENNY)

        if club_info['uid'] != self.uid:
            return self.write_json(error.DATA_BROKEN)

        data = logs_model.set_club_winner_list(self.share_db_logs(), params['clubID'], params["ids"])
        return self.write_json(error.OK, data)


class GetClubWinnerRank(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode((self.get_string('params')))
        if "clubID" not in params or 'beginTime' not in params or 'endTime' not in params:
            return self.write_json(error.DATA_BROKEN)

        club_info = club_model.query_club_by_uid_and_club_id(self.share_db(), params['clubID'], self.uid)
        if not club_info:
            return self.write_json(error.ACCESS_DENNY)

        start_time = params['beginTime']
        end_time = params['endTime']
        if start_time == -1:
            start_time = utils.timestamp_today()
            end_time = utils.timestamp()
        data = logs_model.get_club_winner_rank(self.share_db_logs(), params['clubID'], start_time, end_time)
        res = json.dumps(data)
        return self.write_json(error.OK, res)


class TransferClub(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode((self.get_string('params')))
        if "clubID" not in params or 'uid' not in params:
            return self.write_json(error.DATA_BROKEN)

        # 检测是否 Owner
        club = club_model.get_club_by_owner_and_club_id(self.share_db(), self.uid, params['clubID'])
        if not club:
            return self.write_json(error.ACCESS_DENNY)

        # 检测玩家是否在俱乐部列表
        club_info = club_model.query_club_by_uid_and_club_id(self.share_db(), params['clubID'], params['uid'])
        if not club_info:
            return self.write_json(error.ACCESS_DENNY)

        # 重新设置俱乐部 Owner
        count = club_model.set_club_owner(self.share_db(), params['clubID'], params['uid'])
        if count == 0:
            return self.write_json(error.ACCESS_DENNY)

        # 调整权限
        club_model.update_permission_by_uid_and_club_id(self.share_db(), params['uid'], params['clubID'], 0)
        club_model.update_permission_by_uid_and_club_id(self.share_db(), self.uid, params['clubID'])

        # Table

        return self.write_json(error.OK)


class GetClubOwnerRoomInfo(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode((self.get_string('params')))
        if "clubID" not in params:
            return self.write_json(error.DATA_BROKEN)

        club_info = club_model.get_club(self.share_db(), params['clubID'])
        if not club_info:
            return self.write_json(error.DATA_BROKEN)

        data = logs_model.get_club_week_and_day_info_by_owner(self.share_db_logs(), params['clubID'],
                                                              club_info["uid"])
        return self.write_json(error.OK, data)


class GetClubOwnerInfo(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode((self.get_string('params')))
        if "clubID" not in params:
            return self.write_json(error.DATA_BROKEN)

        club_info = club_model.get_club(self.share_db(), params['clubID'])
        if not club_info:
            return self.write_json(error.DATA_BROKEN)

        data = dict()
        data['todayDiamond'] = player_model.get_consume_diamond_by_time(self.share_db_logs(), self.uid,
                                                                        params['clubID'],
                                                                        utils.timestamp_today(), utils.timestamp())
        data['yesterdayDiamond'] = player_model.get_consume_diamond_by_time(self.share_db_logs(), self.uid,
                                                                            params['clubID'],
                                                                            utils.timestamp_yesterday(),
                                                                            utils.timestamp_today() - 1)
        data['monthDiamond'] = player_model.get_consume_diamond_by_time(self.share_db_logs(), self.uid,
                                                                        params['clubID'],
                                                                        utils.timestamp_month_start(),
                                                                        utils.timestamp_month_end())
        data['totalDiamond'] = player_model.get_consume_diamond_by_time(self.share_db_logs(), self.uid,
                                                                        params['clubID'], 1,
                                                                        utils.timestamp())
        user = player_model.get_by_uid(self.share_db(), self.uid)
        idle_table_diamond = tables_model.get_total_idle_diamonds_by_uid(self.share_db(), self.uid)
        show_diamonds = max(0, int(user['diamond'] - idle_table_diamond))
        data['leftDiamond'] = show_diamonds
        return self.write_json(error.OK, data)


class GetClubDiamondInfo(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode((self.get_string('params')))
        if "clubID" not in params:
            return self.write_json(error.DATA_BROKEN)

        club_info = club_model.get_club(self.share_db(), params['clubID'])
        if not club_info:
            return self.write_json(error.DATA_BROKEN)

        data = dict()
        data['todayDiamond'] = club_model.get_club_consume_diamond_by_time(self.share_db_logs(), params['clubID'],
                                                                           utils.timestamp_today(),
                                                                           utils.timestamp())
        data['yesterdayDiamond'] = club_model.get_club_consume_diamond_by_time(self.share_db_logs(),
                                                                               params['clubID'],
                                                                               utils.timestamp_yesterday(),
                                                                               utils.timestamp_today() - 1)
        data['monthDiamond'] = club_model.get_club_consume_diamond_by_time(self.share_db_logs(),
                                                                           params['clubID'],
                                                                           utils.timestamp_month_start(),
                                                                           utils.timestamp_month_end())
        data['totalDiamond'] = club_model.get_club_consume_diamond_by_time(self.share_db_logs(),
                                                                           params['clubID'], 1,
                                                                           utils.timestamp())
        return self.write_json(error.OK, data)


class GetClubUserRank(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode((self.get_string('params')))
        if "clubID" not in params or 'beginTime' not in params or 'endTime' not in params:
            return self.write_json(error.DATA_BROKEN)

        club_id = params['clubID']
        start_time = params['beginTime']
        end_time = params['endTime']
        if start_time == -1:
            data = club_rank_model.get_club_user_rank_today_without_game_type(self.share_db_logs(), club_id)
        else:
            data = club_rank_model.get_club_user_rank_without_game_type(self.share_db_logs(), club_id, start_time,
                                                                        end_time)
        res = json.dumps(data)
        return self.write_json(error.OK, res)


class GetClubUserRoomInfo(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode((self.get_string('params')))
        if "clubID" not in params or 'beginTime' not in params or 'endTime' not in params or 'gameType' not in params:
            return self.write_json(error.DATA_BROKEN)

        club_id = params['clubID']
        start_time = params['beginTime']
        end_time = params['endTime']
        game_type = params['gameType']
        data = club_rank_model.get_club_user_room_info(self.share_db_logs(), club_id, game_type, start_time, end_time)
        res = json.dumps(data)
        return self.write_json(error.OK, res)


class GetClubQuickRoom(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode((self.get_string('params')))
        if "clubID" not in params:
            return self.write_json(error.DATA_BROKEN)

        datas = club_model.get_club_waiting_table(self.share_db(), params["clubID"]) or []
        rooms = []
        for data in datas:
            table_cache_data = tables_model.get_table_info(redis_conn(), data["tid"]) or {"player_list": [],
                                                                                          "players": [],
                                                                                          "round_index": 1,
                                                                                          "table_status": 0}
            if 'max_player' not in table_cache_data:
                rooms.append({"tid": data["tid"], "left_player_count": 10})
            else:
                left_player_count = int(table_cache_data['max_player']) - len(table_cache_data['player_list'])
                if left_player_count <= 0:
                    continue
                rooms.append({"tid": data["tid"], "left_player_count": left_player_count})

        calc_rooms = _.order_by(rooms, ['left_player_count'])
        ids = []
        for i in calc_rooms:
            ids.append(i['tid'])
        ret = {"roomID": ids}
        return self.write_json(error.OK, ret)


class CopyClubHandler(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode((self.get_string('params')))
        if "clubID" not in params:
            return self.write_json(error.DATA_BROKEN)

        club_info = club_model.get_club(self.share_db(), params["clubID"])
        if club_info['uid'] != self.uid:
            return self.write_json(error.SYSTEM_ERR)

        club_list = club_model.get_club_by_owner(self.share_db(), self.uid) or []
        if len(club_list) >= club_configs_model.get(self.share_db(), "max_club_count", True):
            return self.write_json(error.CLUB_COUNT_IS_MAX)

        club_create_consume = utils.json_decode(club_configs_model.get(self.share_db(), "club_create_diamond", True))
        if len(club_create_consume) < (len(club_list)):
            return self.write_json(error.SYSTEM_ERR)

        consume = club_create_consume[len(club_list)]

        # 计算创建 & 升级钻石
        upgrade_club_config = club_model.get_all_club_level_config(self.share_db())
        for i in upgrade_club_config:
            if i['level'] <= club_info['level']:
                consume += int(i['price'])

        info = player_model.get_by_uid(self.share_db(), self.uid)
        if consume > 0:
            if consume > info.get('diamond'):
                return self.write_json(error.DIAMONDS_NOT_ENOUGH)

        club_id = utils.get_random_num(6)
        count = club_model.create_club(self.share_db(), club_id, self.uid, club_info['name'], club_info['notice'],
                                       club_info['level'], club_info['count'], club_info['status'], 0, '')
        if count == 0:
            return self.write_error(error.SYSTEM_ERR)
        else:
            if consume != 0:
                count = player_model.sub_diamonds(self.share_db(), self.uid, consume)
                if count == 0:
                    return self.write_json(error.UID_ERROR)

        # 玩家映射表复制 & 加入时间刷新
        users = club_model.query_all_data_by_club_id(self.share_db(), club_info['id'])
        club_model.insert_user_with_copy_club(self.share_db(), club_id, users)

        return self.write_json(error.OK, get_base_club({"club_id": club_id}))


class GetClubRoomHandler(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode((self.get_string('params')))
        if "clubID" not in params or "floor" not in params:
            return self.write_json(error.DATA_BROKEN)

        club_id = params["clubID"]
        club_relationship = club_model.query_club_by_uid_and_club_id(self.share_db(), club_id, self.uid)
        if not club_relationship:
            return self.write_json(error.ACCESS_DENNY)

        room_info_list = tables_model.get_table_by_club_id_and_floor(self.share_db(), club_id, params['floor'])

        result = list()

        for room_info in room_info_list:
            table_cache_data = tables_model.get_table_info(redis_conn(), room_info["tid"]) or {"player_list": [],
                                                                                               "players": [],
                                                                                               "round_index": 1,
                                                                                               "table_status": 0}
            if 'players' not in table_cache_data:
                table_cache_data['players'] = []
            rules = room_info["rules"] or room_info["ruleDetails"]
            client_room_info = {"playerList": table_cache_data["player_list"],
                                "roundIndex": table_cache_data["round_index"],
                                "matchConfig": room_info["match_config"],
                                "matchType": room_info['match_type'],
                                "floor": room_info['floor'],
                                "subFloor": room_info['sub_floor'],
                                "status": table_cache_data["table_status"],
                                "players": table_cache_data['players'],
                                "totalRound": room_info["round_count"], "gameType": room_info["game_type"],
                                "ruleType": room_info["rule_type"], "owner": room_info["owner"],
                                "tid": room_info["tid"], "ruleDetails": rules}
            result.append(client_room_info)

        return self.write_json(error.OK, result)


class GetClubRoomByMatchTypeHandler(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode((self.get_string('params')))
        if "clubID" not in params or "matchType" not in params:
            return self.write_json(error.DATA_BROKEN)

        club_id = params["clubID"]

        club_relationship = club_model.query_club_by_uid_and_club_id(self.share_db(), club_id, self.uid)
        if not club_relationship:
            return self.write_json(error.ACCESS_DENNY)

        room_info_list = tables_model.get_table_by_club_id_and_match_type(self.share_db(), club_id,
                                                                          params['matchType'])

        result = list()

        for room_info in room_info_list:
            table_cache_data = tables_model.get_table_info(redis_conn(), room_info["tid"]) or {"player_list": [],
                                                                                               "players": [],
                                                                                               "round_index": 1,
                                                                                               "table_status": 0}
            if 'players' not in table_cache_data:
                table_cache_data['players'] = []
            rules = room_info["rules"] or room_info["ruleDetails"]
            client_room_info = {"playerList": table_cache_data["player_list"],
                                "roundIndex": table_cache_data["round_index"],
                                "matchConfig": room_info["match_config"],
                                "matchType": room_info['match_type'],
                                "subFloor": room_info['sub_floor'],
                                "floor": room_info['floor'],
                                "status": table_cache_data["table_status"],
                                "players": table_cache_data['players'],
                                "totalRound": room_info["round_count"], "gameType": room_info["game_type"],
                                "ruleType": room_info["rule_type"], "owner": room_info["owner"],
                                "tid": room_info["tid"], "ruleDetails": rules}
            result.append(client_room_info)

        return self.write_json(error.OK, result)


class GetClubConfig(CommHandler):
    def _request(self):
        return self.write_json(error.OK, club_configs_model.get_all_config_items(self.share_db()))


class GetClubGamePlay(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode((self.get_string('params')))
        if "clubID" not in params:
            return self.write_json(error.DATA_BROKEN)

        club_id = params['clubID']
        club_game = club_model.get_club_floor_config(self.share_db(), club_id)
        data = []
        for game_type in club_game:
            data.append(game_type["game_type"])
        club_game_for_logs = club_model.get_club_game_by_logs_table(self.share_db_logs(), club_id)
        if club_game_for_logs:
            for game_type in club_game_for_logs:
                if game_type["game_type"] not in data:
                    data.append(game_type["game_type"])
        return self.write_json(error.OK, data)


class TransferClubUser(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))
        if "fromClubID" not in params or "toClubID" not in params or "uids" not in params:
            return self.write_json(error.DATA_BROKEN)

        from_club_id = params['fromClubID']
        to_club_id = params["toClubID"]
        uids = params['uids']
        if not uids:
            return self.write_json(error.DATA_BROKEN)

        club_info = club_model.query_club_by_uid_and_club_id(self.share_db(), from_club_id, self.uid)
        if not club_info or club_info["permission"] not in (0,):
            return self.write_json(error.ACCESS_DENNY)

        to_club = club_model.get_club(self.share_db(), to_club_id)
        if not to_club:
            return self.write_json(error.ACCESS_DENNY)

        # 检测权限
        club_info = club_model.query_club_by_uid_and_club_id(self.share_db(), from_club_id, self.uid)
        if not club_info or club_info["permission"] not in (0, 1,):
            return self.write_json(error.CLUB_STATUS_IS_ERROR)

        count = 0
        if uids[0] == -1:
            club_users = club_model.query_all_data_by_club_id(self.share_db(), from_club_id) or list()
            for i in club_users:

                #创始人也可以转移
                #if i['uid'] == self.uid:
                #    continue
                try:
                    club_model.insert_user_in_club(self.share_db(), to_club_id, i['uid'], self.uid)
                    count += 1
                except Exception as data:
                    utils.log(str(data), "transfer_club.txt")
                    continue
        else:
            for i in uids:
                user_info = club_model.query_club_by_uid_and_club_id(self.share_db(), from_club_id, i)
                if not user_info:
                    continue
                #if i == self.uid:
                #    continue
                try:
                    club_model.insert_user_in_club(self.share_db(), to_club_id, i, self.uid)
                    count += 1
                except Exception as data:
                    utils.log(str(data), "transfer_club.txt")
                    continue

        club_model.update_club_player_count(self.share_db(), to_club_id, count)
        return self.write_json(error.OK)


class GetClubBaseInfo(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))
        if "clubID" not in params:
            return self.write_json(error.DATA_BROKEN)

        club_id = int(params['clubID'])
        club = club_model.get_club(self.share_db(), club_id)
        if not club:
            return self.write_json(error.DATA_BROKEN)

        player = player_model.get_by_uid(self.share_db(), club['uid'])
        if not player:
            return self.write_json(error.DATA_BROKEN)

        club['ownerNickName'] = player['nick_name']
        club['ownerAvatar'] = player['avatar']

        return self.write_json(error.OK, club)


class TagClubUser(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))
        if "clubID" not in params or "ids" not in params or 'tagUid' not in params:
            return self.write_json(error.DATA_BROKEN)
        club_id = params['clubID']
        tag_uid = params['tagUid']
        ids = params['ids']
        club_info = club_model.query_club_by_uid_and_club_id(self.share_db(), club_id, self.uid)
        if not club_info or club_info["permission"] not in (0,):
            return self.write_json(error.ACCESS_DENNY)
        tag_user = player_model.get_by_uid(self.share_db(), tag_uid)
        if not tag_user:
            return self.write_json(error.ACCESS_DENNY)
        for i in ids:
            club_model.modify_club_user_tag(self.share_db(), club_id, i, tag_uid, tag_user['nick_name'])
        return self.write_json(error.OK)


class GetClubTagUserRoomInfo(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))
        if "clubID" not in params or 'beginTime' not in params or 'endTime' not in params:
            return self.write_json(error.DATA_BROKEN)

        club_id = params['clubID']
        start_time = params['beginTime']
        end_time = params['endTime']
        data = club_rank_model.get_club_tag_user_room_info(self.share_db_logs(), club_id, start_time, end_time)
        ret_data = []
        for i in data:
            p = player_model.get_by_uid(self.share_db(), i['tag_uid'])
            i['nick_name'] = "未知用户" if not p else p['nick_name']
            t = club_model.count_by_club_id_and_tag_id(self.share_db(), club_id, i['tag_uid'])
            i['club_user_count'] = t['count']
            ret_data.append(i)
        res = json.dumps(ret_data)
        return self.write_json(error.OK, res)


class GetClubGameLogs(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))
        if "clubID" not in params or 'beginTime' not in params or 'endTime' not in params:
            return self.write_json(error.DATA_BROKEN)

        club_id = params['clubID']
        start_time = params['beginTime']
        end_time = params['endTime']
        data = club_rank_model.get_club_game_logs(self.share_db_logs(), club_id, start_time, end_time)
        return self.write_json(error.OK, data)


class SetClubQueryWinnerScore(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))
        if "clubID" not in params or 'score' not in params:
            return self.write_json(error.DATA_BROKEN)

        club_id = params['clubID']
        score = int(params['score'])
        club_info = club_model.query_club_by_uid_and_club_id(self.share_db(), club_id, self.uid)
        if not club_info or club_info["permission"] not in (0, 1,):
            return self.write_json(error.ACCESS_DENNY)

        club_model.modify_club_winner_score(self.share_db(), club_id, score)
        return self.write_json(error.OK)
