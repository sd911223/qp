# coding:utf-8

import logging

import configs.const as const
from configs import error
from controllers.room_handler import CreateRoomHandler
from models import base_redis
from models import club_model
from models import game_room_model
from models import player_model
from models import room_config_model, floor_model
from models import tables_model
from models.base_redis import share_connect as redis_conn
from utils import utils
from .comm_handler import CommHandler

MAX_FLOOR_COUNT = 5
MAX_SUB_FLOOR_COUNT = 6

MODIFY_FLOOR = 1
MODIFY_SUB_FLOOR = 2
DEL_FLOOR = 3
DEL_SUB_FLOOR = 4


def calc_sub_floor_diamonds(share_db, round_count: int, game_type):
    data = room_config_model.get_room_config(share_db, game_type)
    diamonds = utils.json_decode(data['data'])
    for i in diamonds["diamondInfo"]:
        if i['count'] == round_count:
            return i['diamond']
    return -1


def create_sub_floor_room(share_db, params, club, auto_room_count, floor, sub_floor, match_config):
    rules = params.get("rules") or params.get("ruleDetails")
    game_type = params["gameType"]
    sid = game_room_model.get_best_server_sid(share_db, redis_conn(), game_type)
    if not sid:
        return error.DATA_BROKEN

    consume_type = params.get('consumeType')
    total_round = int(params["totalRound"])
    rule_type = params["ruleType"]
    diamonds = calc_sub_floor_diamonds(share_db, total_round, game_type)
    match_type = params.get("matchType")

    for i in range(auto_room_count):
        while True:
            tid = base_redis.spop_table_id() or utils.get_random_num(6)
            try:
                tables_model.insert(share_db, sid, game_type, int(tid), club['uid'], 1, total_round,
                                    diamonds, rule_type, club["id"], rules, floor=floor, consume_type=consume_type,
                                    match_type=match_type, sub_floor=sub_floor, match_config=match_config)
            except Exception as data:
                logging.error(f"insert club table error: {club['id']} {data}")
                continue
            break
    return error.OK


class EditFloorHandler(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))

        if "clubID" not in params or "floor" not in params or "gameType" not in params:
            return self.write_json(error.DATA_BROKEN)

        club_info = club_model.query_club_by_uid_and_club_id(self.share_db(), params['clubID'], self.uid)
        if not club_info or club_info["permission"] not in (0, 1):
            return self.write_json(error.ACCESS_DENNY)

        floor = floor_model.get_club_floor(self.share_db(), params['clubID'], params['floor'])
        if not floor:
            return self.write_json(error.ACCESS_DENNY)

        if floor['game_type'] == params['gameType']:
            return self.write_json(error.OK)

        count = floor_model.edit_club_floor(self.share_db(), params['floor'], params['gameType'])
        if count == 0:
            return self.write_json(error.DATA_BROKEN)

        count = floor_model.del_club_sub_floor(self.share_db(), params['floor'])
        if count > 0:
            data = floor_model.get_sub_floor_by_floor(self.share_db(), params['floor'])
            for i in data:
                base_redis.remove_club_sub_floor_count(params['clubID'], i['id'])
            self.publish_to_service(const.GAME_PLAY_CONFIG_CHANGE, 1,
                                    {"clubID": params['clubID'],
                                     "floor": params['floor'],
                                     "type": MODIFY_FLOOR}, params['gameType'])

        return self.write_json(error.OK, {"floor": params['floor']})


class EditSubFloorHandler(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))

        if "clubID" not in params or 'subFloor' not in params or 'ruleDetails' not in params:
            return self.write_json(error.DATA_BROKEN)
        game_config = params
        if not game_config.get('gameType') or not game_config.get('totalRound') or not game_config.get(
                'ruleType') or not game_config.get("maxAutoCreateRoom"):
            return self.write_json(error.DATA_BROKEN)

        room_count = params['maxAutoCreateRoom']
        if room_count <= 0 or room_count > 6:
            return self.write_json(error.DATA_BROKEN)

        tip = 0
        tip_limit = 0
        tip_payment_method = 0
        if "tip" in params:
            tip = params['tip']
        if "tipLimit" in params:
            tip_limit = params['tipLimit']
        if "tipPaymentMethod" in params:
            tip_payment_method = params['tipPaymentMethod']

        tip = int(tip)
        tip_limit = int(tip_limit)
        tip_payment_method = int(tip_payment_method)

        if tip < 0 or tip > 100:
            return self.write_json(error.DATA_BROKEN)

        club_info = club_model.query_club_by_uid_and_club_id(self.share_db(), params['clubID'], self.uid)
        if not club_info or club_info["permission"] not in (0, 1):
            return self.write_json(error.ACCESS_DENNY)

        floor = params['subFloor']
        floor_config = floor_model.get_club_sub_floor_config(self.share_db(), params['clubID'], floor)

        if not floor or not floor_config:
            return self.write_json(error.DATA_BROKEN)

        play_config = utils.json_decode(floor_config['play_config'])
        origin_service_type = int(play_config['gameType'])

        game_type = params.get("gameType")
        if game_type != floor_config['game_type']:
            return self.write_json(error.DATA_BROKEN)

        consume_type = params.get('consumeType')
        if floor_config['match_type'] == const.DIAMOND_ROOM and \
                consume_type not in (const.PAY_TYPE_WINNER, const.PAY_TYPE_AA, const.PAY_TYPE_CREATOR,):
            return self.write_json(error.DATA_BROKEN)
        elif floor_config['match_type'] == const.MATCH_ROOM and consume_type != const.PAY_TYPE_CREATOR:
            return self.write_json(error.DATA_BROKEN)

        rules = CreateRoomHandler.make_rule_details(game_type, game_config['ruleDetails'])

        params["ruleDetails"] = rules
        club_id = params["clubID"]
        sub_floor = params['subFloor']
        auto_count = params['maxAutoCreateRoom']

        params['tip'] = tip
        params['tipLimit'] = tip_limit
        params['tipPaymentMethod'] = tip_payment_method

        params['ruleDetails']['tip'] = tip
        params['ruleDetails']['tipLimit'] = tip_limit
        params['ruleDetails']['tipPaymentMethod'] = tip_payment_method

        params.pop("clubID", None)
        params.pop("floor", None)
        params.pop("subFloor", None)
        params.pop("maxAutoCreateRoom", None)
        params.pop("isAgent", None)

        match_config = {}
        if floor_config['match_type'] == const.MATCH_ROOM:
            if 'matchConfig' not in params:
                return self.write_json(error.DATA_BROKEN)
            match_config = params['matchConfig']
            if "score" not in match_config or "enterScore" not in match_config or "limitType" \
                    not in match_config or "limitScore" not in match_config or "limitRate" not in match_config:
                return self.write_json(error.DATA_BROKEN)
            score = match_config['score']
            if score < 50 or score > 5000:
                return self.write_json(error.DATA_BROKEN)
            enter_score = match_config['enterScore']
            if enter_score < 1 or enter_score > 200:
                return self.write_json(error.DATA_BROKEN)
            if match_config['limitType'] not in (1, 2, 3,):
                return self.write_json(error.DATA_BROKEN)
            limit_score = match_config['limitScore']
            if limit_score not in (0, 50, 100, 200, 300,):
                return self.write_json(error.DATA_BROKEN)
            limit_rate = match_config['limitRate']
            if limit_rate not in (1, 2, 3, 4, 5,):
                return self.write_json(error.DATA_BROKEN)

        total_round = int(params["totalRound"])
        diamonds = calc_sub_floor_diamonds(self.share_db(), total_round, game_type)
        if diamonds == -1:
            return self.write_json(error.DATA_BROKEN, {"subFloor": floor})

        club = club_model.get_club(self.share_db(), club_id)
        match_type = params.get("matchType")
        user = player_model.get_by_uid(self.share_db(), club['uid'])
        if match_type == const.DIAMOND_ROOM and consume_type == const.PAY_TYPE_CREATOR:
            idle_table_diamond = tables_model.get_total_idle_diamonds_by_uid(self.share_db(), club['uid'])
            if user.get('diamond', 0) + user.get('yuan_bao', 0) < room_count * diamonds + idle_table_diamond:
                return self.write_json(error.DIAMONDS_CLUB_NOT_ENOUGH, {"subFloor": floor})
        elif match_type == const.MATCH_ROOM:
            idle_match_table_diamond = tables_model.get_total_match_idle_diamonds_by_uid(self.share_db(), club['uid'])
            if user.get('la_jiao_dou', 0) < room_count * diamonds + idle_match_table_diamond:
                return self.write_json(error.LA_JIAO_DOU_NOT_ENOUGH, {"subFloor": floor})

        floor_model.update_sub_floor_play_config(self.share_db(), club_id, utils.json_encode(params), floor,
                                                 auto_count, utils.json_encode(match_config), tip, tip_limit,tip_payment_method)

        # base_redis.remove_club_sub_floor_count(club_id, sub_floor)
        if origin_service_type != -1:
            self.publish_to_service(const.GAME_PLAY_CONFIG_CHANGE, 1,
                                    {"clubID": club_id,
                                     "floor": floor,
                                     "type": MODIFY_SUB_FLOOR}, origin_service_type)

        return self.write_json(error.OK, {"subFloor": floor})


class GetFloorHandler(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))

        if "clubID" not in params or "matchType" not in params:
            return self.write_json(error.DATA_BROKEN)

        data = floor_model.get_floor_by_club_id_and_match_type(self.share_db(), params['clubID'], params['matchType'])
        return self.write_json(error.OK, {"data": data, "matchType": params['matchType']})


class DelFloorHandler(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))

        if "floor" not in params or "clubID" not in params or "gameType" not in params:
            return self.write_json(error.DATA_BROKEN)

        club_info = club_model.query_club_by_uid_and_club_id(self.share_db(), params['clubID'], self.uid)
        if not club_info or club_info["permission"] not in (0, 1):
            return self.write_json(error.ACCESS_DENNY)

        count = floor_model.del_club_floor(self.share_db(), params['clubID'], params['floor'], params['gameType'])
        if count == 0:
            return self.write_json(error.DATA_BROKEN)

        count = floor_model.del_club_sub_floor(self.share_db(), params['floor'])
        if count > 0:
            data = floor_model.get_sub_floor_by_floor(self.share_db(), params['floor'])
            for i in data:
                base_redis.remove_club_sub_floor_count(params['clubID'], i['id'])
            self.publish_to_service(const.GAME_PLAY_CONFIG_CHANGE, 1,
                                    {"clubID": params['clubID'],
                                     "floor": params['floor'],
                                     "type": DEL_FLOOR}, params['gameType'])
        return self.write_json(error.OK, {"floor": params['floor']})


class AddFloorHandler(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))

        if "clubID" not in params or "matchType" not in params or "gameType" not in params:
            return self.write_json(error.DATA_BROKEN)

        if params['matchType'] not in (const.DIAMOND_ROOM, const.MATCH_ROOM,):
            return self.write_json(error.DATA_BROKEN)

        club_info = club_model.query_club_by_uid_and_club_id(self.share_db(), params['clubID'], self.uid)
        if not club_info or club_info["permission"] not in (0, 1):
            return self.write_json(error.ACCESS_DENNY)

        data = floor_model.query_club_floor_count_by_club_id_and_match_type(self.share_db(),
                                                                            params['clubID'],
                                                                            params['matchType'])
        if data and data['count'] >= MAX_FLOOR_COUNT:
            return self.write_json(error.OVER_FLOOR)

        floor = floor_model.add_club_floor(self.share_db(), params['clubID'], params['matchType'], params['gameType'])
        if floor == 0:
            return self.write_json(error.DATA_BROKEN)

        return self.write_json(error.OK)


class GetSubFloorHandler(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))

        if "floor" not in params:
            return self.write_json(error.DATA_BROKEN)

        data = floor_model.get_sub_floor_by_floor(self.share_db(), int(params['floor']))
        return self.write_json(error.OK, {"data": data, "floor": params['floor']})


class GetSubFloorByMatchTypeHandler(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))

        if "clubID" not in params or "matchType" not in params:
            return self.write_json(error.DATA_BROKEN)

        data = floor_model.get_sub_floor_by_match_type(self.share_db(), int(params['clubID']), int(params['matchType']))
        return self.write_json(error.OK, {"data": data, "clubID": params['clubID'], "matchType": params['matchType']})


class DelSubFloorHandler(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))

        if "subFloor" not in params or "clubID" not in params or "gameType" not in params:
            return self.write_json(error.DATA_BROKEN)

        club_info = club_model.query_club_by_uid_and_club_id(self.share_db(), params['clubID'], self.uid)
        if not club_info or club_info["permission"] not in (0, 1):
            return self.write_json(error.ACCESS_DENNY)

        count = floor_model.del_sub_floor_by_sub_floor_and_club_id_and_game_type(self.share_db(), params['subFloor'],
                                                                                 params['clubID'], params['gameType'])
        if count == 0:
            return self.write_error(error.ACCESS_DENNY)

        base_redis.remove_club_sub_floor_count(params['clubID'], params['subFloor'])
        self.publish_to_service(const.GAME_PLAY_CONFIG_CHANGE, 1,
                                {"clubID": params['clubID'],
                                 "floor": params['subFloor'],
                                 "type": DEL_SUB_FLOOR}, params['gameType'])

        return self.write_json(error.OK, {"subFloor": params['subFloor']})


class AddSubFloorHandler(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))

        if "floor" not in params or 'clubID' not in params or 'ruleDetails' not in params or 'matchType' not in \
                params or "maxAutoCreateRoom" not in params:
            return self.write_json(error.DATA_BROKEN)

        club_info = club_model.query_club_by_uid_and_club_id(self.share_db(), params['clubID'], self.uid)
        if not club_info or club_info["permission"] not in (0, 1):
            return self.write_json(error.ACCESS_DENNY)

        floor = floor_model.get_club_floor(self.share_db(), params['clubID'], params['floor'])
        if not floor:
            return self.write_json(error.ACCESS_DENNY)

        match_type = int(floor['match_type'])
        data = floor_model.query_club_sub_floor_count_by_club_id_and_match_type(self.share_db(), params['floor'],
                                                                                match_type)
        if data and data['count'] > MAX_SUB_FLOOR_COUNT:
            return self.write_json(error.OVER_FLOOR)

        # room_count = params['maxAutoCreateRoom']
        # if room_count <= 0 or room_count > 6:
        #     return self.write_json(error.DATA_BROKEN)

        tip = 0
        tip_limit = 0
        tip_payment_method = 0
        if "tip" in params:
            tip = params['tip']
        if "tipLimit" in params:
            tip_limit = params['tipLimit']
        if "tipPaymentMethod" in params:
            tip_payment_method = params['tipPaymentMethod']

        tip = int(tip)
        tip_limit = int(tip_limit)
        tip_payment_method = int(tip_payment_method)

        if tip < 0 or tip > 100:
            return self.write_json(error.DATA_BROKEN)

        game_type = params.get("gameType")

        consume_type = params.get('consumeType')
        if match_type == const.DIAMOND_ROOM and consume_type not in (
                const.PAY_TYPE_AA, const.PAY_TYPE_WINNER, const.PAY_TYPE_CREATOR,):
            return self.write_json(error.DATA_BROKEN)
        elif match_type == const.MATCH_ROOM and consume_type != const.PAY_TYPE_CREATOR:
            return self.write_json(error.DATA_BROKEN)

        rules = CreateRoomHandler.make_rule_details(game_type, params['ruleDetails'])

        params["ruleDetails"] = rules

        club_id = params["clubID"]
        floor = params['floor']
        max_count = params['maxAutoCreateRoom']

        params['tip'] = tip
        params.pop("clubID", None)
        params.pop("floor", None)
        params.pop("subFloor", None)
        params.pop("maxAutoCreateRoom", None)
        params.pop("isAgent", None)

        params['tip'] = tip
        params['tipLimit'] = tip_limit
        params['tipPaymentMethod'] = tip_payment_method
        params['ruleDetails']['tip'] = tip
        params['ruleDetails']['tipLimit'] = tip_limit
        params['ruleDetails']['tipPaymentMethod'] = tip_payment_method

        match_config = {}
        if match_type == const.MATCH_ROOM:
            if 'matchConfig' not in params:
                return self.write_json(error.DATA_BROKEN)
            match_config = params['matchConfig']
            if "score" not in match_config or "enterScore" not in match_config or "limitType" \
                    not in match_config or "limitScore" not in match_config or "limitRate" not in match_config:
                return self.write_json(error.DATA_BROKEN)
            score = match_config['score']
            if score < 50 or score > 5000:
                return self.write_json(error.DATA_BROKEN)
            enter_score = match_config['enterScore']
            if enter_score < 1 or enter_score > 200:
                return self.write_json(error.DATA_BROKEN)
            if match_config['limitType'] not in (1, 2, 3,):
                return self.write_json(error.DATA_BROKEN)
            limit_score = match_config['limitScore']
            if limit_score not in (0, 100, 200, 300,500):
                return self.write_json(error.DATA_BROKEN)
            limit_rate = match_config['limitRate']
            if limit_rate not in (1, 2, 3, 4, 5,):
                return self.write_json(error.DATA_BROKEN)

        total_round = int(params["totalRound"])
        diamonds = calc_sub_floor_diamonds(self.share_db(), total_round, game_type)
        if diamonds == -1:
            return self.write_json(error.DATA_BROKEN, {"subFloor": floor})

        club = club_model.get_club(self.share_db(), club_id)
        match_type = params.get("matchType")
        user = player_model.get_by_uid(self.share_db(), club['uid'])
        if match_type == const.DIAMOND_ROOM and consume_type == const.PAY_TYPE_CREATOR:
            idle_table_diamond = tables_model.get_total_idle_diamonds_by_uid(self.share_db(), club['uid'])
            if user.get('diamond', 0) + user.get('yuan_bao', 0) < room_count * diamonds + idle_table_diamond:
                return self.write_json(error.DIAMONDS_CLUB_NOT_ENOUGH, {"subFloor": floor})
        elif match_type == const.MATCH_ROOM:
            idle_match_table_diamond = tables_model.get_total_match_idle_diamonds_by_uid(self.share_db(), club['uid'])
            if user.get('diamond', 0) < room_count * diamonds + idle_match_table_diamond:
                return self.write_json(error.DIAMONDS_CLUB_NOT_ENOUGH, {"subFloor": floor})
            # if user.get('la_jiao_dou', 0) < room_count * diamonds + idle_match_table_diamond:
            #     return self.write_json(error.LA_JIAO_DOU_NOT_ENOUGH, {"subFloor": floor})

        count = floor_model.insert_sub_floor_play_config(self.share_db(), club_id, floor, utils.json_encode(params),
                                                         max_count, game_type, match_type,
                                                         utils.json_encode(match_config), tip,tip_limit,tip_payment_method)
        if count == 0:
            return self.write_json(error.DATA_BROKEN, {"subFloor": floor})

        floor_id = floor_model.get_max_sub_floor_by_floor(self.share_db(), floor)['id']
        code = create_sub_floor_room(self.share_db(), params, club, room_count, floor, floor_id, match_config)
        if code == error.OK:
            club_users = club_model.query_all_data_by_club_id(self.share_db(), club_id) or list()
            broad_user = list()
            for user in club_users:
                broad_user.append(user["uid"])
            self.broad_cast_user(broad_user, {"type": const.AUTO_ROOM_CHANGE})

        return self.write_json(code, {"floor": floor})

class ClubDouLogs(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))

        if 'clubID' not in params:
            return self.write_json(error.DATA_BROKEN)

        club_info = club_model.query_club_by_uid_and_club_id(self.share_db(), params['clubID'], self.uid)
        if not club_info or club_info["permission"] not in (0, 1):
            return self.write_json(error.ACCESS_DENNY)

        data = {}
        # TODO 需要确认统计条件
        data['today'] = \
            int(club_model.query_consume_diamond_by_club_id(self.share_db_logs(), params['clubID'],
                                                            utils.timestamp_today(),
                                                            utils.timestamp())['diamond'] or 0)
        data['yesterday'] = \
            int(club_model.query_consume_diamond_by_club_id(self.share_db_logs(), params['clubID'],
                                                            utils.timestamp_yesterday(),
                                                            utils.timestamp_today() - 1)['diamond'] or 0)
        data['month'] = \
            int(club_model.query_consume_diamond_by_club_id(self.share_db_logs(), params['clubID'],
                                                            utils.timestamp_month_start(),
                                                            utils.timestamp())['diamond'] or 0)
        data['total'] = \
            int(club_model.query_consume_diamond_by_club_id(self.share_db_logs(), params['clubID'], 1,
                                                            utils.timestamp())[
                    'diamond'] or 0)
        idle_table_diamond = int(tables_model.get_total_idle_diamonds_by_uid(self.share_db(), self.uid))
        data['left'] = player_model.get_by_uid(self.share_db(), self.uid)['diamond'] + idle_table_diamond
        return self.write_json(error.OK, data)


class ClubUserDouLogs(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))

        if 'clubID' not in params:
            return self.write_json(error.DATA_BROKEN)

        club_info = club_model.query_club_by_uid_and_club_id(self.share_db(), params['clubID'], self.uid)
        if not club_info or club_info["permission"] not in (0, 1):
            return self.write_json(error.ACCESS_DENNY)

        total_score = int(club_model.query_club_total_dou(self.share_db(), params['clubID'])['score'] or 0)
        total_limit_score = int(
            club_model.query_club_total_limit_dou(self.share_db_logs(), params['clubID'], utils.timestamp_yesterday(),
                                                  utils.timestamp_today() - 1)['score'] or 0)
        data = {"totalScore": total_score, "totalLimitScore": total_limit_score, "players": []}
        users = club_model.query_user_info_by_club_id(self.share_db(), params['clubID'])
        for i in users:
            u = {"nickName": i['nick_name'], "uid": i['uid'], "round": i['game_round'], "limitScore": i['limit_score'],
                 "score": i['score']}
            data['players'].append(u)
        return self.write_json(error.OK, data)


class ClubUserDetailDouLogs(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))

        if 'clubID' not in params:
            return self.write_json(error.DATA_BROKEN)

        club_info = club_model.query_club_by_uid_and_club_id(self.share_db(), params['clubID'], self.uid)
        if not club_info or club_info["permission"] not in (0, 1):
            return self.write_json(error.ACCESS_DENNY)

        users = club_model.query_user_info_by_club_id(self.share_db(), params['clubID'])
        data = []
        for i in users:
            yesterday_score = int(club_model.get_user_score_by_time(self.share_db_logs(), params['clubID'], i['uid'],
                                                                    utils.timestamp_yesterday(),
                                                                    utils.timestamp_today() - 1)['score'] or 0)
            u = {"nickName": i['nick_name'], "uid": i['uid'], "yesterdayScore": yesterday_score,
                 "score": i['game_score'], "totalAddScore": i['add_score'], "totalMinusScore": i['minus_score'],
                 "recentAddTime": i['add_time'], 'recentMinusTime': i['minus_time']}
            data.append(u)
        return self.write_json(error.OK, data)


class QueryDouOperLogs(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))

        if "clubID" not in params:
            return self.write_json(error.DATA_BROKEN)

        data = club_model.query_dou_oper_by_club_id(self.share_db_logs(), params['clubID'])
        return self.write_json(error.OK, data)


class GetGameCountLogs(CommHandler):
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

        status = params.get("status") or 0
        apply_list = club_model.query_game_count_logs(self.share_db_logs(), club_id, status)
        return self.write_json(error.OK, {"data": apply_list, "status": status})


class SetGameCountLogs(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode((self.get_string('params')))
        if "clubID" not in params:
            return self.write_json(error.DATA_BROKEN)

        club_id = int(params["clubID"])
        msg_id = int(params["msgID"])

        club_relation = club_model.query_club_by_uid_and_club_id(self.share_db(), club_id, self.uid)
        if not club_relation or club_relation["permission"] not in (0, 1):
            return self.write_json(error.ACCESS_DENNY)

        status = 1
        count = club_model.set_club_game_count_logs(self.share_db_logs(), club_id, msg_id, status)
        return self.write_json(error.OK, {"isFinish": count})


class QueryClubBlockHandler(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))
        if "clubID" not in params:
            return self.write_json(error.DATA_BROKEN)

        club_id = int(params["clubID"])
        data = club_model.query_club_block_list(self.share_db(), club_id)
        return self.write_json(error.OK, {"data": data})


class SetClubBlockHandler(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode((self.get_string('params')))
        if "clubID" not in params or "uid1" not in params or "uid2" not in params or 'status' not in params:
            return self.write_json(error.DATA_BROKEN)

        club_id = int(params["clubID"])
        uid1 = int(params["uid1"])
        uid2 = int(params["uid2"])
        status = int(params["status"])
        if 'blockStatus' not in params:
            block_status = 0
        else:
            block_status = int(params['blockStatus'])  # 0 = 永久 # 1 = 24 小时

        club_relation = club_model.query_club_by_uid_and_club_id(self.share_db(), club_id, self.uid)
        if not club_relation or club_relation["permission"] not in (0, 1):
            return self.write_json(error.ACCESS_DENNY)

        try:
            if status == 1:
                count = club_model.add_club_block_list(self.share_db(), club_id, uid1, uid2, block_status)
            else:
                count = club_model.remove_club_block_list(self.share_db(), club_id, uid1, uid2)
        except Exception as e:
            return self.write_json(error.OK, {"status": 0})
        return self.write_json(error.OK, {"status": count})
