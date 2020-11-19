# coding:utf-8

import logging
import random
from decimal import Decimal
import datetime
import pydash as _

from configs import error, const
from controllers.room_handler import CreateRoomHandler
from models import union_model, player_model, room_config_model, tables_model, game_room_model, logs_model, base_redis
from models.base_redis import share_connect as redis_conn
from utils import utils
from .comm_handler import CommHandler


def default(obj):
    if isinstance(obj, Decimal):
        return str(obj)
    raise TypeError


UNION_MANAGER = 0
UNION_SEC_MANAGER = 1
UNION_SMALL_MANAGER = 10
UNION_PARTNER = 11

MAX_FLOOR_COUNT = 5
MAX_SUB_FLOOR_COUNT = 6

MODIFY_FLOOR = 1
MODIFY_SUB_FLOOR = 2
DEL_FLOOR = 3
DEL_SUB_FLOOR = 4

SMALL_UNION = 0
BIG_UNION = 1


def calc_sub_floor_diamonds(share_db, round_count: int, game_type):
    data = room_config_model.get_room_config(share_db, game_type)
    diamonds = utils.json_decode(data['data'])
    for i in diamonds["diamondInfo"]:
        if i['count'] == round_count:
            return i['diamond']
    return -1


def create_sub_floor_room(share_db, params, union, auto_room_count, floor, sub_floor, match_config):
    rules = params.get("rules") or params.get("ruleDetails")
    game_type = params["gameType"]
    sid = game_room_model.get_best_server_sid(share_db, redis_conn(), game_type)
    if not sid:
        logging.error("create_sub_floor_room -- no server exist")
        return error.DATA_BROKEN

    consume_type = params.get('consumeType')
    total_round = int(params["totalRound"])
    rule_type = params["ruleType"]
    diamonds = calc_sub_floor_diamonds(share_db, total_round, game_type)

    logging.info(f"create_sub_floor_room -- {auto_room_count}")
    tid = 0
    for i in range(auto_room_count):
        while True:
            tid = base_redis.spop_table_id() or utils.get_random_num(6)
            try:
                tables_model.insert(share_db, sid, game_type, int(tid), union['uid'], 1, total_round,
                                    diamonds, rule_type, -1, rules, floor=floor, consume_type=consume_type,
                                    match_type=1, sub_floor=sub_floor, match_config=match_config, union_id=union['id'])
                logging.info(f"create_sub_floor_room {union['id']}  floor {floor} sub_floor {sub_floor}")
            except Exception as data:
                logging.error(f"insert union table error: {union['id']} {data}")
                continue
            break
    return error.OK,tid


# 显示所有小盟主
class QueryAllSmallUnionManager(CommHandler):
    def _request(self):
        # 检测自己的权限
        union_user_info = union_model.get_union_userinfo_by_uid(self.share_db(), self.uid)
        if not union_user_info:
            return self.write_json(error.DATA_BROKEN)
        if union_user_info['permission'] not in (UNION_MANAGER, UNION_SEC_MANAGER,):
            return self.write_json(error.ACCESS_DENNY)

        union_id = union_user_info['union_id']
        managers = union_model.query_all_small_union_manager(self.share_db(), union_id)
        sub_floor = union_model.query_energy_config_by_uid(self.share_db(), union_id, self.uid)
        for data in managers:
            data['profit'] = union_model.query_small_union_profit(self.share_db(), union_id, data['uid'])
        return self.write_json(error.OK, {"data": managers, "subFloorEnergy": sub_floor})


# 查看小盟主详情(显示小盟主的所有下级合伙人和玩家)
class QuerySmallUnionUsers(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))
        if "uid" not in params:
            return self.write_json(error.DATA_BROKEN)

        union_user_info = union_model.get_union_userinfo_by_uid(self.share_db(), self.uid)
        if not union_user_info:
            return self.write_json(error.DATA_BROKEN)
        if union_user_info['permission'] not in (UNION_MANAGER, UNION_SEC_MANAGER,):
            return self.write_json(error.ACCESS_DENNY)

        union_id = union_user_info['union_id']
        uid = params['uid']

        #small_union = union_model.get_small_union_by_owner_id_and_union_id(self.share_db(), uid, union_id)

        data = union_model.query_small_union_users1(self.share_db(), union_id,uid)
        return self.write_json(error.OK, data)


# 显示所有合伙人(小盟主使用)
class QueryUnionPartner(CommHandler):
    def _request(self):
        union_user_info = union_model.get_union_userinfo_by_uid(self.share_db(), self.uid)
        if not union_user_info:
            return self.write_json(error.DATA_BROKEN)
        if union_user_info['permission'] not in (UNION_MANAGER, UNION_SMALL_MANAGER,):
            return self.write_json(error.ACCESS_DENNY)

        union_id = union_user_info['union_id']
        managers = union_model.query_all_small_union_partner(self.share_db(), union_id, self.uid)
        sub_floor = union_model.query_energy_config_by_uid(self.share_db(), union_id, self.uid)
        for data in managers:
            data['profit'] = union_model.query_small_union_profit(self.share_db(), union_id, data['uid'])
        return self.write_json(error.OK, {"data": managers, "subFloorEnergy": sub_floor})


# 查看合伙人下级详情
class QueryUnionPartnerUsers(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))
        if "uid" not in params:
            return self.write_json(error.DATA_BROKEN)

        union_user_info = union_model.get_union_userinfo_by_uid(self.share_db(), self.uid)
        if not union_user_info:
            return self.write_json(error.DATA_BROKEN)
        if union_user_info['permission'] not in (UNION_MANAGER, UNION_SEC_MANAGER, UNION_SMALL_MANAGER, UNION_PARTNER):
            return self.write_json(error.ACCESS_DENNY)

        union_id = union_user_info['union_id']
        uid = params['uid']
        #partner_user_info = union_model.get_union_userinfo_by_uid(self.share_db(), uid)
        #small_union_id = partner_user_info['union_small_id']

        # if not partner_user_info or partner_user_info['union_user_id'] != self.uid:
        #     return self.write_json(error.ACCESS_DENNY)

        #partner = union_model.get_union_partner_by_id(self.share_db(), uid, union_id, small_union_id)
        partner_id = 0 #partner['id']
        data = union_model.query_union_partner_users(self.share_db(), union_id, uid, partner_id)
        return self.write_json(error.OK, data)


# 设置小盟主分成比例
class SetSmallUnionProfit(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))
        if "uid" not in params or 'subFloor' not in params or 'percent' not in params:
            return self.write_json(error.DATA_BROKEN)

        percent = params['percent']
        sub_floor = params['subFloor']
        uid = params['uid']
        if percent < 0 or percent > 100:
            return self.write_json(error.DATA_BROKEN)

        union_user_info = union_model.get_union_userinfo_by_uid(self.share_db(), self.uid)
        if not union_user_info:
            return self.write_json(error.DATA_BROKEN)
        if union_user_info['permission'] not in (UNION_MANAGER, UNION_SEC_MANAGER,):
            return self.write_json(error.ACCESS_DENNY)

        refer_user = union_model.get_union_userinfo_by_uid(self.share_db(), uid)
        if refer_user['permission'] is not UNION_SMALL_MANAGER:
            return self.write_json(error.ACCESS_DENNY)

        union_model.set_small_union_profit(self.share_db(), self.uid, union_user_info['union_id'], uid, sub_floor,
                                           percent)
        return self.write_json(error.OK)


# 设置合伙人分成比例
class SetUnionPartnerProfit(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))
        if "uid" not in params or 'subFloor' not in params or 'percent' not in params:
            return self.write_json(error.DATA_BROKEN)

        percent = params['percent']
        sub_floor = params['subFloor']
        uid = params['uid']
        if percent < 0 or percent > 100:
            return self.write_json(error.DATA_BROKEN)

        union_user_info = union_model.get_union_userinfo_by_uid(self.share_db(), self.uid)
        if not union_user_info:
            return self.write_json(error.DATA_BROKEN)
        if union_user_info['permission'] not in (UNION_MANAGER, UNION_SEC_MANAGER, UNION_SMALL_MANAGER,):
            return self.write_json(error.ACCESS_DENNY)

        refer_user = union_model.get_union_userinfo_by_uid(self.share_db(), uid)
        if refer_user['permission'] is not UNION_PARTNER or refer_user['union_user_id'] != self.uid:
            return self.write_json(error.ACCESS_DENNY)

        union_model.set_small_union_profit(self.share_db(), self.uid, union_user_info['union_id'], uid, sub_floor,
                                           percent)
        return self.write_json(error.OK)


# 所有联盟管理员信息
class QueryUnionManagerInfo(CommHandler):
    def _request(self):
        union_user_info = union_model.get_union_userinfo_by_uid(self.share_db(), self.uid)
        if not union_user_info:
            return self.write_json(error.DATA_BROKEN)
        data = union_model.query_all_union_manager(self.share_db(), union_user_info['union_id'])
        return self.write_json(error.OK, data)


# 获取楼层
class GetUnionFloor(CommHandler):
    def _request(self):
        union_user_info = union_model.get_union_userinfo_by_uid(self.share_db(), self.uid)
        if not union_user_info:
            return self.write_json(error.DATA_BROKEN)
        data = union_model.get_floor_by_union_id(self.share_db(), union_user_info['union_id'])
        return self.write_json(error.OK, {"data": data})


# 删除楼层
class DelUnionFloor(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))

        if "floor" not in params or 'gameType' not in params:
            return self.write_json(error.DATA_BROKEN)

        union_user_info = union_model.get_union_userinfo_by_uid(self.share_db(), self.uid)
        if not union_user_info or union_user_info['permission'] not in (UNION_MANAGER, UNION_SEC_MANAGER,):
            return self.write_json(error.DATA_BROKEN)

        union_id = union_user_info['union_id']

        count = union_model.del_union_floor(self.share_db(), union_id, params['floor'], params['gameType'])
        if count == 0:
            return self.write_json(error.DATA_BROKEN)

        count = union_model.del_union_sub_floor(self.share_db(), params['floor'])
        if count > 0:
            data = union_model.get_sub_floor_by_floor(self.share_db(), params['floor'])
            for i in data:
                base_redis.remove_union_sub_floor_count(union_id, i['id'])
            self.publish_to_service(const.UNION_GAME_PLAY_CONFIG_CHANGE, 1,
                                    {"unionID": union_id,
                                     "floor": params['floor'],
                                     "type": DEL_FLOOR}, params['gameType'])
        return self.write_json(error.OK, {"floor": params['floor']})


# 编辑楼层游戏
class EditUnionFloor(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))

        if "floor" not in params or "gameType" not in params:
            return self.write_json(error.DATA_BROKEN)

        union_user_info = union_model.get_union_userinfo_by_uid(self.share_db(), self.uid)
        if not union_user_info or union_user_info['permission'] not in (UNION_MANAGER, UNION_SEC_MANAGER,):
            return self.write_json(error.DATA_BROKEN)

        union_id = union_user_info['union_id']
        floor = union_model.get_union_floor(self.share_db(), union_id, params['floor'])
        if not floor:
            return self.write_json(error.ACCESS_DENNY)

        if floor['game_type'] == params['gameType']:
            return self.write_json(error.OK)

        count = union_model.edit_union_floor(self.share_db(), params['floor'], params['gameType'])
        if count == 0:
            return self.write_json(error.DATA_BROKEN)

        count = union_model.del_union_sub_floor(self.share_db(), params['floor'])
        # 编辑楼层游戏时，删掉该楼层下所有桌子
        del_count = union_model.del_union_floor_table(self.share_db(), params['floor'], union_id)

        if count > 0 and del_count > 0:
            data = union_model.get_sub_floor_by_floor(self.share_db(), params['floor'])
            for i in data:
                base_redis.remove_union_sub_floor_count(union_id, i['id'])
            self.publish_to_service(const.GAME_PLAY_CONFIG_CHANGE, 1,
                                    {"unionID": union_id,
                                     "floor": params['floor'],
                                     "type": MODIFY_FLOOR}, params['gameType'])

        return self.write_json(error.OK, {"floor": params['floor']})


# 新增楼层
class AddUnionFloor(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))

        if "gameType" not in params:
            return self.write_json(error.DATA_BROKEN)

        union_user_info = union_model.get_union_userinfo_by_uid(self.share_db(), self.uid)
        if not union_user_info or union_user_info['permission'] not in (UNION_MANAGER, UNION_SEC_MANAGER,):
            return self.write_json(error.DATA_BROKEN)

        union_id = union_user_info['union_id']

        data = union_model.query_union_floor_count_by_union_id(self.share_db(), union_id)
        if data and data['count'] >= MAX_FLOOR_COUNT:
            return self.write_json(error.OVER_FLOOR)

        floor = union_model.add_union_floor(self.share_db(), union_id, params['gameType'])
        if floor == 0:
            return self.write_json(error.DATA_BROKEN)

        return self.write_json(error.OK)


# 获取子楼层
class GetUnionSubFloor(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))

        if "floor" not in params:
            return self.write_json(error.DATA_BROKEN)

        data = union_model.get_sub_floor_by_floor(self.share_db(), int(params['floor']))
        return self.write_json(error.OK, {"data": data, "floor": params['floor']})


# 获取全部子楼层
class GetUnionAllSubFloor(CommHandler):
    def _request(self):
        union_user_info = union_model.get_union_userinfo_by_uid(self.share_db(), self.uid)
        if not union_user_info:
            return self.write_json(error.DATA_BROKEN)

        union_id = union_user_info['union_id']
        data = union_model.get_sub_floor_by_union_id(self.share_db(), union_id)
        return self.write_json(error.OK, data)


# 删除子楼层下桌子
class DelUnionSubFloor(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))

        # xingxing or "gameType" not in params
        if "subFloor" not in params  or "unionID" not in params:
            return self.write_json(error.DATA_BROKEN)

        union_user_info = union_model.get_union_userinfo_by_uid(self.share_db(), self.uid)
        if not union_user_info or union_user_info['permission'] not in (UNION_MANAGER, UNION_SEC_MANAGER,):
            return self.write_json(error.DATA_BROKEN)

        union_id = union_user_info['union_id']
        count = union_model.del_sub_floor_by_sub_floor_and_union_id_and_game_type(self.share_db(), params['subFloor'],
                                                                                  union_id, 0)# xingxing params['gameType']

        # 删除子楼层桌子数据库操作
        del_count,deltids = union_model.del_table_by_sub_floor_and_union_id_and_game_type(self.share_db(), params['subFloor'],
                                                                                  union_id, 0) # xingxing params['gameType']

        if count == 0 or del_count == 0:
            return self.write_json(error.ACCESS_DENNY)

        base_redis.remove_union_sub_floor_count(union_id, params['subFloor'])
        self.publish_to_service(const.GAME_PLAY_CONFIG_CHANGE, 1,
                                {"unionID": union_id,
                                 "floor": params['subFloor'],
                                 "type": DEL_SUB_FLOOR}, 0) # xingxing params['gameType']
        #广播给联盟内所有的玩家
        unionuser = union_model.query_all_union_users( self.share_db(),union_id)
        user_list = list()

        for urs in unionuser:
            user_list.append(urs['uid'])

        self.broad_cast_user(user_list, {"type": const.UNION_SUBFLOOR_REMOVE_NOTICE, "data": {"uid": self.uid}})
        # 如果有人关闭玩法，广播消息给客户端
        """如果有人关闭玩法，广播消息给客户端"""
        self.publish(2,6,{'union_id':union_id,'uid':self.uid,'selfuid':self.uid,'type':6,
                          'tid':-9,'subfloor':params['subFloor'],'deltids':deltids},9999)
        return self.write_json(error.OK, {"subFloor": params['subFloor']})

class QueryUnionCSLog(CommHandler):
    """
    查询提取记录
    """
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)
        params = utils.json_decode(self.get_string('params'))
        if 'union_id' not in params or 'datetime' not in params:
            return self.write_json(error.DATA_BROKEN)
        union_id = params['union_id']
        datetime = params['datetime']
        data = union_model.query_cs_log(self.share_db(),union_id,self.uid,datetime)
        self.write_json(error.OK,data)



#保存提取记录
class SaveUnionCSLog(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)
        params = utils.json_decode(self.get_string('params'))
        if 'union_id' not in params or 'score' not in params or\
                "queryid" not in params:
            return self.write_json(error.DATA_BROKEN)
        union_id = params["union_id"]
        score = params["score"]
        queryid = params["queryid"]
        effects = union_model.save_cs_log(self.share_db(),union_id,self.uid,score,queryid)
        if effects == 0:
            return self.write_json(error.DATA_BROKEN)
        return self.write_json(error.OK)

#获取保险箱抽水详情
class GetSafeBoxFaxList(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)
        params = utils.json_decode(self.get_string('params'))
        if 'union_id' not in params or 'datetime' not in params:
            return self.write_json(error.DATA_BROKEN)
        union_id = params["union_id"]
        datetime = params['datetime']
        data = union_model.querysaftboxlist(self.share_db(),self.uid,union_id,datetime)
        num = union_model.queryroundandamountbytoday(self.share_db(),self.uid,union_id )
        arr = dict()
        datalist = list()
        if num:
            if len(num) == 2:
                datalist.append({'num':num[0]['num'],'amount':num[1]['num']})

        for item in data:
            play_config = utils.json_decode(item["play_config"])
            enterScore = play_config["matchConfig"]["enterScore"]
            game_type = item["game_type"]
            from_userid = item["from_userid"]
            item["enterScore"] = enterScore
            item.pop('play_config')
            datalist.append(item)
        self.write_json( error.OK,datalist)

# 编辑子楼层
class EditUnionSubFloor(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))

        if 'subFloor' not in params or 'ruleDetails' not in params:
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

        union_user_info = union_model.get_union_userinfo_by_uid(self.share_db(), self.uid)
        if not union_user_info or union_user_info['permission'] not in (UNION_MANAGER, UNION_SEC_MANAGER,):
            return self.write_json(error.DATA_BROKEN)

        union_id = union_user_info['union_id']

        floor = params['subFloor']
        floor_config = union_model.get_union_sub_floor_config(self.share_db(), union_id, floor)

        if not floor or not floor_config:
            return self.write_json(error.DATA_BROKEN)

        play_config = utils.json_decode(floor_config['play_config'])
        origin_service_type = int(play_config['gameType'])

        game_type = params.get("gameType")
        if game_type != floor_config['game_type']:
            return self.write_json(error.DATA_BROKEN)

        if params.get('consumeType') != const.PAY_TYPE_CREATOR:
            return self.write_json(error.DATA_BROKEN)

        rules = CreateRoomHandler.make_rule_details(game_type, game_config['ruleDetails'])

        params["ruleDetails"] = rules
        # sub_floor = params['subFloor']
        auto_count = params['maxAutoCreateRoom']

        params['tip'] = tip
        params['tipLimit'] = tip_limit
        params['tipPaymentMethod'] = tip_payment_method

        params['ruleDetails']['tip'] = tip
        params['ruleDetails']['tipLimit'] = tip_limit
        params['ruleDetails']['tipPaymentMethod'] = tip_payment_method

        params.pop("floor", None)
        params.pop("subFloor", None)
        params.pop("maxAutoCreateRoom", None)
        params.pop("isAgent", None)

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
        # if limit_score not in (0, 50, 100, 200, 300,):
        #     return self.write_json(error.DATA_BROKEN)
        limit_rate = match_config['limitRate']
        # if limit_rate not in (1, 2, 3, 4, 5,):
        #     return self.write_json(error.DATA_BROKEN)

        total_round = int(params["totalRound"])
        diamonds = calc_sub_floor_diamonds(self.share_db(), total_round, game_type)
        if diamonds == -1:
            return self.write_json(error.DATA_BROKEN, {"subFloor": floor})

        union = union_model.get_union_info(self.share_db(), union_id)
        user = player_model.get_by_uid(self.share_db(), union['uid'])
        idle_match_table_diamond = tables_model.get_total_match_idle_diamonds_by_uid(self.share_db(), union['uid'])
        if user.get('diamond', 0) < room_count * diamonds + idle_match_table_diamond:
            return self.write_json(error.DIAMONDS_CLUB_NOT_ENOUGH, {"subFloor": floor})



        union_model.update_sub_floor_play_config(self.share_db(), union_id, utils.json_encode(params), floor,
                                                 auto_count, utils.json_encode(match_config), tip, tip_limit,
                                                 tip_payment_method)



        # # 修改table表中关于桌子的游戏配置
        # union_model.update_table_play_config(self.share_db(), union_id, utils.json_encode(rules), floor, game_type)




        # base_redis.remove_union_sub_floor_count(union_id, sub_floor)
        if origin_service_type != -1:
            self.publish_to_service(const.UNION_GAME_PLAY_CONFIG_CHANGE, 1,
                                    {"unionID": union_id,
                                     "floor": floor,
                                     "type": MODIFY_SUB_FLOOR}, origin_service_type)

        return self.write_json(error.OK, {"subFloor": floor})


# 新增子楼层
class AddUnionSubFloor(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))

        # floor 改成 unionID
        #if "floor" not in params  or 'ruleDetails' not in params or "maxAutoCreateRoom" not in params or 'matchType' not in params:
        if "unionID" not in params  or 'ruleDetails' not in params or "maxAutoCreateRoom" not in params or 'matchType' not in params:
            return self.write_json(error.DATA_BROKEN)

        if params['matchType'] is not const.MATCH_ROOM:
            return self.write_json(error.DATA_BROKEN)

        union_user_info = union_model.get_union_userinfo_by_uid(self.share_db(), self.uid)
        if not union_user_info or union_user_info['permission'] not in (UNION_MANAGER, UNION_SEC_MANAGER,):
            return self.write_json(error.DATA_BROKEN)
        union_id = union_user_info['union_id']

        #floor = union_model.get_union_floor(self.share_db(), union_id, params['floor'])
        #if not floor:
        #   return self.write_json(error.ACCESS_DENNY)

        data = union_model.query_union_sub_floor_count_by_union_id(self.share_db(), union_id )# floor 改成 union_id
        # if data and data['count'] > MAX_SUB_FLOOR_COUNT:
        #     return self.write_json(error.OVER_FLOOR)

        room_count = params['maxAutoCreateRoom']
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
        if consume_type != const.PAY_TYPE_CREATOR:
            return self.write_json(error.DATA_BROKEN)

        rules = CreateRoomHandler.make_rule_details(game_type, params['ruleDetails'])

        params["ruleDetails"] = rules

        floor = 0#params['floor']
        max_count = params['maxAutoCreateRoom']

        params['tip'] = tip
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
        # if limit_score not in (0,  100, 200, 300,500):
        #     return self.write_json(error.DATA_BROKEN)
        limit_rate = match_config['limitRate']
        # if limit_rate not in (2, 3, 4, 5,7):
        #     return self.write_json(error.DATA_BROKEN)

        total_round = int(params["totalRound"])
        diamonds = calc_sub_floor_diamonds(self.share_db(), total_round, game_type)
        if diamonds == -1:
            return self.write_json(error.DATA_BROKEN, {"subFloor": floor})

        union = union_model.get_union_info(self.share_db(), union_id)
        user = player_model.get_by_uid(self.share_db(), union['uid'])
        idle_match_table_diamond = tables_model.get_total_match_idle_diamonds_by_uid(self.share_db(), union['uid'])
        if user.get('diamond', 0) < room_count * diamonds + idle_match_table_diamond:
            return self.write_json(error.DIAMONDS_CLUB_NOT_ENOUGH, {"subFloor": floor})

        auto_count = max_count
        union_model.update_sub_floor_play_config(self.share_db(), union_id, utils.json_encode(params), 0,
                                                 auto_count, utils.json_encode(match_config), tip, tip_limit,
                                                 tip_payment_method)

        count = union_model.insert_sub_floor_play_config(self.share_db(), union_id, 0, utils.json_encode(params),
                                                         max_count, game_type, utils.json_encode(match_config), tip,
                                                         tip_limit, tip_payment_method)
        if count == 0:
            return self.write_json(error.DATA_BROKEN, {"subFloor": floor})

        floor_id = union_model.get_max_sub_floor_by_floor(self.share_db(), floor)['id']

        code,tid = create_sub_floor_room(self.share_db(), params, union, room_count, floor, floor_id, match_config)
        if code == error.OK:
            union_users = union_model.query_all_uids_by_union_id(self.share_db(), union_id) or list()
            broad_user = list()
            for user in union_users:
                broad_user.append(user["uid"])
            self.broad_cast_user(broad_user, {"type": const.UNION_SUBFLOOR_REMOVE_NOTICE})

            # 如果新增玩法，广播消息给客户端
            """如果新增玩法，广播消息给客户端"""
            self.publish(2,6,{'union_id':union_id,'uid':self.uid,'selfuid':self.uid,'type':6,
                              'tid':tid,'subfloor':floor_id},9999)

        return self.write_json(code, {"floor": floor})


# 创建联盟
class CreateUnion(CommHandler):
    def _can_create_union(self, user):
        return True

    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))
        if "text" not in params:
            return self.write_json(error.DATA_BROKEN)

        union_name = params["text"]
        union_id = utils.get_random_num(6)
        wechat = params['wechat']
        player = player_model.get_by_uid(self.share_db(), self.uid)
        if not self._can_create_union(player):
            return self.write_json(error.SYSTEM_ERR)

        union_user_info = union_model.get_union_userinfo_by_uid(self.share_db(), self.uid)
        if union_user_info:
            return self.write_json(error.DATA_BROKEN)

        count = union_model.create_union(self.share_db(), union_id, self.uid, union_name, "健康游戏，严禁赌博。", 1, 0, wechat)
        if count == 0:
            return self.write_json(error.SYSTEM_ERR)

        union_model.join_union(self.share_db(), self.uid, union_id, self.uid, self.uid, permission=0)
        return self.write_json(error.OK, ({"union_id": union_id}))


# 编辑联盟公告
class EditUnionNotice(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))
        if "text" not in params:
            return self.write_json(error.DATA_BROKEN)

        union_user_info = union_model.get_union_userinfo_by_uid(self.share_db(), self.uid)
        if not union_user_info:
            return self.write_json(error.DATA_BROKEN)
        if union_user_info['permission'] not in (0, 1):
            return self.write_json(error.ACCESS_DENNY)

        union_model.update_union_notice(self.share_db(), union_user_info['union_id'], params['text'])
        return self.write_json(error.OK)


# 编辑联盟名称
class EditUnionName(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))
        if "text" not in params:
            return self.write_json(error.DATA_BROKEN)

        union_user_info = union_model.get_union_userinfo_by_uid(self.share_db(), self.uid)
        if not union_user_info:
            return self.write_json(error.DATA_BROKEN)
        if union_user_info['permission'] not in (0, 1):
            return self.write_json(error.ACCESS_DENNY)

        union_model.update_union_name(self.share_db(), union_user_info['union_id'], params['text'])
        return self.write_json(error.OK)


# 联盟钻石消耗
class GetUnionDiamondInfo(CommHandler):
    def _request(self):
        union_user_info = union_model.get_union_userinfo_by_uid(self.share_db(), self.uid)
        if not union_user_info:
            return self.write_json(error.DATA_BROKEN)
        union_id = union_user_info['union_id']

        data = dict()
        data['todayDiamond'] = union_model.get_union_consume_diamond_by_time(self.share_db_logs(), union_id,
                                                                             utils.timestamp_today(),
                                                                             utils.timestamp())
        data['yesterdayDiamond'] = union_model.get_union_consume_diamond_by_time(self.share_db_logs(),
                                                                                 union_id,
                                                                                 utils.timestamp_yesterday(),
                                                                                 utils.timestamp_today() - 1)
        data['monthDiamond'] = union_model.get_union_consume_diamond_by_time(self.share_db_logs(),
                                                                             union_id,
                                                                             utils.timestamp_month_start(),
                                                                             utils.timestamp_month_end())
        data['totalDiamond'] = union_model.get_union_consume_diamond_by_time(self.share_db_logs(),
                                                                             union_id,
                                                                             1,
                                                                             utils.timestamp())
        union_player = player_model.get_by_uid(self.share_db(), union_user_info['uid'] )
        data["leftDiamond"] = 0
        if union_player:
            data["leftDiamond"] = union_player["diamond"]
        return self.write_json(error.OK, data)


class QueryUnionDirectUsers(CommHandler):
    """根据上级用户的编号查看下级用户能量情况"""
    def _request(self):
        # union_user_info = union_model.get_union_userinfo_by_uid(self.share_db(), self.uid)
        # if not union_user_info:
        #     return self.write_json(error.DATA_BROKEN)
        # union_id = union_user_info['union_id']
        params = utils.json_decode(self.get_string('params'))
        if "union_id" not in params or "uid" not in params:
            return self.write_json(error.DATA_BROKEN)
        is_all = False
        union_id = params['union_id']
        uid = params["uid"]
        data = []
        data = union_model.query_union_users_by_union_id1(self.share_db(), union_id,uid,is_all)

        return self.write_json(error.OK, data)


# 联盟内下级用户列表
class QueryUnionUsers(CommHandler):
    def _request(self):
        union_id = self.share_redis().hget('unionid',self.uid )
        if not union_id:
            union_user_info = union_model.get_union_userinfo_by_uid(self.share_db(), self.uid)
            if not union_user_info:
                return self.write_json(error.DATA_BROKEN)
            union_id = union_user_info['union_id']
        else:
            union_id = int(union_id)
        # params = utils.json_decode(self.get_string('params'))
        # if "union_id" not in params or "uid" not in params:
        #     return self.write_json(error.DATA_BROKEN)
        #is_all = params['uid'] == self.uid and params['union_id'] == union_id
        #union_id = params['union_id']
        uid = self.uid
        data = []
        data = union_model.query_union_users_by_union_id1(self.share_db(), union_id,uid,False)
        # if union_user_info['permission'] in (UNION_MANAGER, UNION_SEC_MANAGER,):
        #     data = union_model.query_union_users_by_union_id1(self.share_db(), union_id,uid,False)
        # elif union_user_info['permission'] in (UNION_SMALL_MANAGER,):
        #     data = union_model.query_union_users_by_small_manager_id1(self.share_db(), union_id, uid,False)
        # elif union_user_info['permission'] in (UNION_PARTNER,):
        #     # small_union_id = union_user_info['union_small_id']
        #     # partner = union_model.get_union_partner_by_id(self.share_db(), self.uid, union_id, small_union_id)
        #     # if not partner and False:
        #     #     return self.write_json(error.DATA_BROKEN)
        #     data = union_model.query_union_users_by_partner_id1(self.share_db(), union_id, uid, 0,False)
        data = [x for x in data if x['uid'] != self.uid]
        # for i in data:
        #     i['online'] = True if i['login_time'] and i['login_time'] > utils.timestamp() - 9 * 60 else False
        return self.write_json(error.OK, data)



class SetUnionPlayerPermission(CommHandler):
    def _request(self):
        # 设置联盟玩家权限
        # 0 盟主
        # 1 副盟主
        # 10 小盟主
        # 11 小盟主的合伙人
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode((self.get_string('params')))

        if "uid" not in params or "permission" not in params or params["permission"] not in (
                UNION_SEC_MANAGER, UNION_SMALL_MANAGER, UNION_PARTNER,):
            return self.write_json(error.DATA_BROKEN)

        uid = params["uid"]
        permission = params["permission"]

        if uid == self.uid:  # 防止创建人更改自己权限
            return self.write_json(error.ACCESS_DENNY)

        info = union_model.get_union_userinfo_by_uid(self.share_db(), self.uid)
        if params["permission"] <= info["permission"]:
            return self.write_json(error.ACCESS_DENNY)

        # 如果是小联盟，则不能设置小盟主
        union = union_model.get_union_info(self.share_db(), info['union_id'])
        if not union or union['union_type'] == SMALL_UNION and params['permission'] == UNION_SMALL_MANAGER:
            return self.write_json(error.ACCESS_DENNY)

        count = union_model.update_permission_by_uid_and_union_id(self.share_db(), uid, info['union_id'], permission)
        if count == 0:
            return self.write_json(error.SYSTEM_ERR)
        # 如果是设置合伙人
        if params['permission'] == UNION_PARTNER:
            union_model.update_union_user_id(self.share_db(), info['union_id'], uid, self.uid)
        if permission == 99:
            union_model.modify_union_tag_uid_to_owner_uid(self.share_db(), info['union_id'], uid)
        return self.write_json(error.OK)


# 标记玩家归属(注入功能)
class TagUnionUser(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))
        if "ids" not in params or 'tagUid' not in params:
            return self.write_json(error.DATA_BROKEN)

        tag_uid = params['tagUid']
        ids = params['ids']

        info = union_model.get_union_userinfo_by_uid(self.share_db(), self.uid)
        if not info or info["permission"] not in (UNION_MANAGER, UNION_SEC_MANAGER, UNION_SMALL_MANAGER,):
            return self.write_json(error.ACCESS_DENNY)

        tag_user = player_model.get_by_uid(self.share_db(), tag_uid)
        if not tag_user:
            return self.write_json(error.ACCESS_DENNY)
        tag_info = union_model.get_union_userinfo_by_uid(self.share_db(), tag_uid)

        # 对方权限必须是合伙人
        if tag_info['permission'] is not UNION_PARTNER:
            return self.write_json(error.ACCESS_DENNY)

        count = 0
        for i in ids:
            if info['permission'] == UNION_SMALL_MANAGER:
                count = union_model.modify_union_user_tag(self.share_db(), info['union_id'], i, tag_uid,
                                                          tag_user['nick_name'],
                                                          self.uid)
            else:
                count = union_model.modify_union_user_tag(self.share_db(), info['union_id'], i, tag_uid,
                                                          tag_user['nick_name'])

        if count > 0:
            return self.write_json(error.OK)
        return self.write_json(error.ACCESS_DENNY)


# 增加能量
class AddEnergy(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))

        if "uid" not in params or "count" not in params:
            return self.write_json(error.DATA_BROKEN)

        count = int(params["count"])
        if count <= 0:
            return self.write_json(error.DOU_COUNT_ERROR)

        info = union_model.get_union_userinfo_by_uid(self.share_db(), self.uid)
        if not info or info["permission"] not in (
                UNION_MANAGER, UNION_SEC_MANAGER, UNION_SMALL_MANAGER, UNION_PARTNER,):
            return self.write_json(error.ACCESS_DENNY)

        available_energy = int(info['energy'] - info['lock_energy'])
        if count > available_energy:
            return self.write_json(error.DOU_COUNT_ERROR)

        # 不能给自己增加能量
        if params['uid'] == self.uid:
            return self.write_json(error.DATA_BROKEN)

        refer_user = union_model.get_union_userinfo_by_uid(self.share_db(), params['uid'])
        if not refer_user or refer_user['union_id'] != info['union_id']:
            return self.write_json(error.DATA_BROKEN)

        union_id = refer_user['union_id']

        # 检测上下级关系
        # 如果转移对象是副管理员，[我]必须是管理员
        # 如果转移对象是小盟主,[我]必须是管理员或者副管理员
        # 如果转移对象是合伙人，[我]必须是对应的小盟主或者管理员及副管理员
        # 如果转移对象是普通玩家，[我]则必须是管理员或副管理员，或者关联上的小盟主，或关联上的合伙人
        # if refer_user['permission'] == UNION_SEC_MANAGER:
        #     if info['permission'] != UNION_MANAGER:
        #         return self.write_json(error.ACCESS_DENNY)
        # elif refer_user['permission'] == UNION_SMALL_MANAGER:
        #     if info['permission'] not in (UNION_MANAGER, UNION_SEC_MANAGER,):
        #         return self.write_json(error.ACCESS_DENNY)
        # elif refer_user['permission'] == UNION_PARTNER:
        #     if info['permission'] not in (UNION_MANAGER, UNION_SEC_MANAGER, UNION_SMALL_MANAGER,):
        #         return self.write_json(error.ACCESS_DENNY)
        #     if info['permission'] == UNION_PARTNER and refer_user['union_user_id'] != self.uid:
        #         return self.write_json(error.ACCESS_DENNY)
        # else:
        #     if info['permission'] in (UNION_PARTNER, UNION_SMALL_MANAGER,):
        #         if refer_user['union_user_id'] != self.uid and refer_user['tag_uid'] != self.uid:
        #             return self.write_json(error.ACCESS_DENNY)

        # 减少自己能量，增加别人能量
        ret_count = union_model.reduce_energy(self.share_db(), union_id, self.uid, count)
        if ret_count == 0:
            return self.write_json(error.DOU_COUNT_ERROR)
        union_model.add_energy(self.share_db(), union_id, params['uid'], count)

        # 能量记录
        union_model.write_energy_log(self.share_db_logs(), union_id, self.uid,
                                     refer_user['energy'] + refer_user['lock_energy'], count,
                                     const.REASON_UNION_ADD, params['uid'],count + int(refer_user['energy']) + int(refer_user['lock_energy']) )

        now_dou = count + int(refer_user['energy']) + int(refer_user['lock_energy'])
        self.broad_cast_user([params['uid']],
                             {"type": const.USER_CHANGE_DOU,
                              "data":
                                  {"dou": count, "nowDou": now_dou, "byUid": self.uid}
                              })

        self.publish(2,3,{'union_id':union_id,'uid':params['uid'],'selfuid':self.uid,'type':3},9999)

        data_my_en = union_model.get_my_energy1(self.share_db(), union_id, self.uid, params['uid'])

        return self.write_json(error.OK,data_my_en)


# 减少能量
class ReduceEnergy(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))

        if "uid" not in params or "count" not in params:
            return self.write_json(error.DATA_BROKEN)

        count = int(params["count"])
        if count <= 0:
            return self.write_json(error.DOU_COUNT_ERROR)

        info = union_model.get_union_userinfo_by_uid(self.share_db(), self.uid)
        if not info or info["permission"] not in (
                UNION_MANAGER, UNION_SEC_MANAGER, UNION_SMALL_MANAGER, UNION_PARTNER,):
            return self.write_json(error.ACCESS_DENNY)

        available_energy = int(info['energy'] - info['lock_energy'])
        # if count > available_energy:
        #     return self.write_json(error.DOU_COUNT_ERROR)

        # 不能给自己减少能量
        if params['uid'] == self.uid:
            return self.write_json(error.DATA_BROKEN)

        refer_user = union_model.get_union_userinfo_by_uid(self.share_db(), params['uid'])
        if not refer_user or refer_user['union_id'] != info['union_id']:
            return self.write_json(error.DATA_BROKEN)

        union_id = refer_user['union_id']
        ifexists = False
        #检查是否在对局，在游戏中不能下分
        room_info_list = union_model.get_table_by_union_id1(self.share_db(), union_id)
        for room_info in room_info_list:
            table_cache_data = tables_model.get_table_info(redis_conn(), room_info["tid"]) or {"player_list": [],
                                                                                               "players": [],
                                                                                               "round_index": 1,
                                                                                               "table_status": 0}
            player_list = table_cache_data["player_list"]
            if not player_list:
                continue
            if params['uid'] not in player_list:
                continue
            else:
                ifexists = True
                break
        if ifexists:
            return self.write_json(-66)
        # 检测上下级关系
        # 如果转移对象是副管理员，[我]必须是管理员
        # 如果转移对象是小盟主,[我]必须是管理员或者副管理员
        # 如果转移对象是合伙人，[我]必须是对应的小盟主或者管理员及副管理员
        # 如果转移对象是普通玩家，[我]则必须是管理员或副管理员，或者关联上的小盟主，或关联上的合伙人
        # if refer_user['permission'] == UNION_SEC_MANAGER:
        #     if info['permission'] != UNION_MANAGER:
        #         return self.write_json(error.ACCESS_DENNY)
        # elif refer_user['permission'] == UNION_SMALL_MANAGER:
        #     if info['permission'] not in (UNION_MANAGER, UNION_SEC_MANAGER,):
        #         return self.write_json(error.ACCESS_DENNY)
        # elif refer_user['permission'] == UNION_PARTNER:
        #     if info['permission'] not in (UNION_MANAGER, UNION_SEC_MANAGER, UNION_SMALL_MANAGER,):
        #         return self.write_json(error.ACCESS_DENNY)
        #     if info['permission'] == UNION_PARTNER and refer_user['union_user_id'] != self.uid:
        #         return self.write_json(error.ACCESS_DENNY)
        # else:
        #     if info['permission'] in (UNION_PARTNER, UNION_SMALL_MANAGER,):
        #         if refer_user['union_user_id'] != self.uid and refer_user['tag_uid'] != self.uid:
        #             return self.write_json(error.ACCESS_DENNY)

        # 减少别人能量，增加自己能量
        ret_count = union_model.reduce_energy(self.share_db(), union_id, params['uid'], count)
        if ret_count == 0:
            return self.write_json(error.DOU_COUNT_ERROR)
        union_model.add_energy(self.share_db(), union_id, self.uid, count)

        # 能量记录
        union_model.write_energy_log(self.share_db_logs(), union_id, self.uid,
                                     refer_user['energy'] + refer_user['lock_energy'], count,
                                     const.REASON_UNION_SUB, params['uid'],int(refer_user['energy']) + int(refer_user['lock_energy']) - count)

        now_dou = int(refer_user['energy']) + int(refer_user['lock_energy']) - count
        self.broad_cast_user([params['uid']],
                             {"type": const.USER_CHANGE_DOU,
                              "data":
                                  {"dou": count, "nowDou": now_dou, "byUid": self.uid}
                              })
        self.publish(2,3,{'union_id':union_id,'uid':params['uid'],'selfuid':self.uid,'type':3},9999)
        data_my_en = union_model.get_my_energy1(self.share_db(), union_id, self.uid, params['uid'])

        return self.write_json(error.OK, data_my_en)


# 能量记录(最近100条)
class QueryEnergyLogs(CommHandler):
    def _request(self):
        union_user_info = union_model.get_union_userinfo_by_uid(self.share_db(), self.uid)
        if not union_user_info:
            return self.write_json(error.DATA_BROKEN)
        union_id = union_user_info['union_id']
        data = union_model.query_energy_logs(self.share_db_logs(), union_id, self.uid)
        return self.write_json(error.OK, data)


# 能量转移
class TransferEnergy(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))

        if "uid" not in params or "count" not in params:
            return self.write_json(error.DATA_BROKEN)

        count = int(params["count"])
        if count <= 0:
            return self.write_json(error.DOU_COUNT_ERROR)

        info = union_model.get_union_userinfo_by_uid(self.share_db(), self.uid)
        # 任何权限都可以转移
        if not info:
            return self.write_json(error.ACCESS_DENNY)

        available_energy = int(info['energy'] - info['lock_energy'])
        if count > available_energy:
            return self.write_json(error.DOU_COUNT_ERROR)

        # 不能给自己增加能量
        if params['uid'] == self.uid:
            return self.write_json(error.DATA_BROKEN)

        refer_user = union_model.get_union_userinfo_by_uid(self.share_db(), params['uid'])

        # 只确定两人是否在同一联盟中
        if not refer_user or refer_user['union_id'] != info['union_id']:
            return self.write_json(error.DATA_BROKEN)

        union_id = refer_user['union_id']

        # 减少自己能量，增加别人能量
        ret_count = union_model.reduce_energy(self.share_db(), union_id, self.uid, count)
        if ret_count == 0:
            return self.write_json(error.DOU_COUNT_ERROR)
        union_model.add_energy(self.share_db(), union_id, params['uid'], count)

        # 能量记录
        union_model.write_energy_log(self.share_db_logs(), union_id, self.uid,
                                     refer_user['energy'] + refer_user['lock_energy'], count,
                                     const.REASON_UNION_TRANSFER, params['uid'], count + int(refer_user['energy']) + int(refer_user['lock_energy']))

        now_dou = count + int(refer_user['energy']) + int(refer_user['lock_energy'])
        self.broad_cast_user([params['uid']],
                             {"type": const.USER_CHANGE_DOU,
                              "data":
                                  {"dou": count, "nowDou": now_dou, "byUid": self.uid}
                              })

        return self.write_json(error.OK)


# 能量转移记录(最近100条)
class QueryTransferEnergyLogs(CommHandler):
    def _request(self):
        union_user_info = union_model.get_union_userinfo_by_uid(self.share_db(), self.uid)
        if not union_user_info:
            return self.write_json(error.DATA_BROKEN)
        union_id = union_user_info['union_id']
        data = union_model.query_transfer_energy_logs(self.share_db_logs(), union_id, self.uid)
        return self.write_json(error.OK, data)


# 同桌提醒设置
class SetUnionBlock(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode((self.get_string('params')))
        if "uid1" not in params or "uid2" not in params or 'status' not in params:
            return self.write_json(error.DATA_BROKEN)

        uid1 = int(params["uid1"])
        uid2 = int(params["uid2"])
        status = int(params["status"])

        if 'blockStatus' not in params:
            block_status = 0
        else:
            block_status = int(params['blockStatus'])  # 0 = 永久 # 1 = 24 小时

        info = union_model.get_union_userinfo_by_uid(self.share_db(), self.uid)
        if not info or info["permission"] not in (UNION_MANAGER, UNION_SEC_MANAGER,):
            return self.write_json(error.ACCESS_DENNY)

        union_id = info['union_id']
        try:
            if status == 1:
                count = union_model.add_union_block_list(self.share_db(), union_id, uid1, uid2, block_status)
            else:
                count = union_model.remove_union_block_list(self.share_db(), union_id, uid1, uid2)
        except Exception as e:
            return self.write_json(error.OK, {"status": 0})
        return self.write_json(error.OK, {"status": count})


# 获取同桌提醒设置
class QueryUnionBlock(CommHandler):
    def _request(self):
        union_user_info = union_model.get_union_userinfo_by_uid(self.share_db(), self.uid)
        if not union_user_info:
            return self.write_json(error.DATA_BROKEN)
        union_id = union_user_info['union_id']
        data = union_model.query_union_block_list(self.share_db(), union_id)
        return self.write_json(error.OK, {"data": data})


# 加入联盟（普通玩家)
class JoinUnion(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode((self.get_string('params')))
        if "promo" not in params:
            return self.write_json(error.DATA_BROKEN)
        promo = int(params["promo"])
        info = union_model.get_union_userinfo_by_uid(self.share_db(), self.uid)
        if info:
            return self.write_json(error.CLUB_IS_JOIN)

        union_id = 0
        # 根据邀请码判断是什么用户邀请的
        if promo >= 100000 and promo < 199999:
            # 大盟主邀请
            union_id = promo
        elif promo >= 200000 and promo < 299999:
            # 小盟主邀请
            small_union = union_model.get_small_union_by_id(self.share_db(), promo)
            if not small_union:
                return self.write_json(error.DATA_BROKEN)
            union_id = small_union["union_id"]
        elif promo >= 300000 and promo < 499999:
            # 合伙人邀请
            #partner = union_model.get_union_partner_by_partner_id(self.share_db(), promo)
            partner = union_model.get_union_partner_by_partner_id1(self.share_db(),promo)
            if not partner and False:
                return self.write_json(error.DATA_BROKEN)
            union_id = partner["union_id"] #partner["union_id"]
        if union_id == 0:
            return self.write_json(error.DATA_BROKEN)

        union_info = union_model.get_union_info(self.share_db(), union_id)
        if union_info is None:
            return self.write_json(error.CLUB_STATUS_IS_ERROR)

        if union_model.get_verify_list_by_uid(self.share_db(), union_id, self.uid, -2):
            return self.write_json(error.OK)

        count = union_model.update_user_verify(self.share_db(), self.uid, union_id, promo, 0, verify_type=0)
        if count == 0:
            self.write_json(error.SYSTEM_ERR)
        admin_list = union_model.query_all_union_manager(self.share_db(), union_id) or list()
        user_list = list()
        for user_info in admin_list:
            user_list.append(user_info["uid"])
        self.broad_cast_user(user_list, {"type": const.USER_APPLY_JOIN_UNION, "data": {"uid": self.uid}})
        return self.write_json(error.OK)


# 获取联盟信息
class GetUnionInfo(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))
        if "union_id" not in params:
            return self.write_json(error.DATA_BROKEN)
        union_id = int(params.get('union_id'))
        info = union_model.get_union_info(self.share_db(), union_id)
        if not info:
            return self.write_json(error.DATA_BROKEN)
        return self.write_json(error.OK, info)


class GetOnlineUnionCount(CommHandler):
    def _request(self):
        union_user_info = self.share_redis().hget('unionid',self.uid)
        union_id = 0
        if not union_user_info:
            union_user_info = union_model.get_union_userinfo_by_uid(self.share_db(), self.uid)
            if not union_user_info:
                return self.write_json(error.DATA_BROKEN)
            else:
                union_id = union_user_info['union_id']
                self.share_redis().hset('unionid',self.uid,union_id)
        else:
            union_id = int(union_user_info)
        info = union_model.get_my_union_info11(self.share_db(), union_id, self.uid)
        if not info:
            return self.write_json(error.DATA_BROKEN)
        info["onlinenum"] = int(redis_conn().hget('onlinenum',1)) + random.randint(30,30)
        # room_info_list = union_model.get_table_by_union_id1(self.share_db(), union_user_info['union_id'])
        isstartnum = 0
        iswaitnum = 0
        # for room_info in room_info_list:
        #     table_cache_data = tables_model.get_table_info(redis_conn(), room_info["tid"]) or {"player_list": [],
        #                                                                                        "players": [],
        #                                                                                        "round_index": 1,
        #                                                                                        "table_status": 0}
        #     if 'players' not in table_cache_data:
        #         table_cache_data['players'] = []
        #     player_list = table_cache_data["player_list"]
        #     if len(player_list) == 0:
        #         continue
        #     if len(player_list) == 1:
        #         iswaitnum = iswaitnum + 1
        #     else:
        #         isstartnum = isstartnum + 1
        info["startnum"] = isstartnum
        info["waitnum"] = iswaitnum
        return self.write_json(error.OK, info)



# 获取自己联盟信息
class GetMyUnionInfo(CommHandler):
    def _request(self):
        unionid = self.share_redis().hget('unionid',self.uid )
        if not unionid:
            union_user_info = union_model.get_union_userinfo_by_uid(self.share_db(), self.uid)
            if not union_user_info:
                return self.write_json(error.DATA_BROKEN)
            unionid = int(union_user_info['union_id'])
            self.share_redis().hset('unionid', self.uid,unionid )
        else:
            unionid = int(unionid)
        info = self.share_redis().hget(unionid,self.uid)
        if not info:
            info = union_model.get_my_union_info(self.share_db(), unionid, self.uid)
            if not info:
                return self.write_json(error.DATA_BROKEN)
            self.share_redis().hset(unionid, self.uid, utils.json_encode(info) )
        else:
            info = utils.json_decode(info)
            #获取实时能量值
            myenergy = union_model.get_my_energy( self.share_db(),unionid,self.uid )
            if myenergy:
                info['energy'] = myenergy['energy']
                info['permission'] = myenergy['permission']
        # 增加邀请码
        if info["permission"] == UNION_MANAGER:
            info["promo"] = int(unionid) #union_user_info['union_id']
        elif info["permission"] == UNION_SMALL_MANAGER:
            small_union = union_model.get_small_union_by_owner_id(self.share_db(), self.uid)
            info["promo"] = small_union['promo']
        elif info["permission"] == UNION_PARTNER:
            #partner = union_model.get_union_partner_by_id(self.share_db(), self.uid,
            #                                           union_user_info['union_id'], union_user_info['union_small_id'])
            info["promo"] = self.uid#union_user_info['union_id']
        else:
            info["promo"] = 0
        #通知用户状态
        #self.publish(2,3,{'union_id':unionid,'uid':801012,'selfuid':801012},9999)
        return self.write_json(error.OK, info)


# 退出联盟（需要清空能量)
class QuitUnion(CommHandler):
    def _request(self):
        union_user_info = union_model.get_union_userinfo_by_uid(self.share_db(), self.uid)
        if not union_user_info:
            return self.write_json(error.DATA_BROKEN)
        union_id = union_user_info['union_id']

        # 检测能量是否为空
        if union_user_info['energy'] != 0 or union_user_info['lock_energy'] != 0:
            return self.write_json(error.DATA_BROKEN)
        # 检测自身权限
        if union_user_info['permission'] == UNION_MANAGER:
            return self.write_json(error.DATA_BROKEN)

        union = union_model.get_union_info(self.share_db(), union_id)
        # 如果自己是小盟主，则将全部旗下用户绑定至盟主，合伙人绑定至盟主
        if union_user_info['permission'] == UNION_SMALL_MANAGER:
            union_model.modify_union_user_id(self.share_db(), union_id, self.uid, union['uid'])
        # 如果自己是合伙人，则将全部旗下用户绑定至小盟主
        elif union_user_info['permission'] in (UNION_PARTNER, UNION_SEC_MANAGER,):
            # to_union_user_id = union_user_info['union_user_id']
            # if union_user_info['union_user_id'] == -1:
            #     to_union_user_id = union['uid']
            union_model.modify_union_user_id(self.share_db(), union_id, self.uid, union['uid'])
            #union_model.modify_union_tag_id(self.share_db(), union_id, self.uid, to_union_user_id)
        union_model.remove_union_user_by_uid(self.share_db(), union_id, self.uid)
        union_model.add_user_count(self.share_db(), union_id, -1)
        self.share_redis().hdel('unionid', self.uid)
        self.share_redis().hdel('union_player_online', self.uid)
        return self.write_json(error.OK)


# 获取最近的游戏类型
class GetUnionGamePlay(CommHandler):
    def _request(self):
        union_user_info = union_model.get_union_userinfo_by_uid(self.share_db(), self.uid)
        if not union_user_info:
            return self.write_json(error.DATA_BROKEN)
        union_id = union_user_info['union_id']
        union_game = union_model.get_union_floor_config(self.share_db(), union_id)
        data = []
        for game_type in union_game:
            data.append(game_type["game_type"])
        union_game_for_logs = union_model.get_union_game_by_logs_table(self.share_db_logs(), union_id)
        if union_game_for_logs:
            for game_type in union_game_for_logs:
                if game_type["game_type"] not in data:
                    data.append(game_type["game_type"])
        return self.write_json(error.OK, data)


# 获取联盟楼层桌子
class QueryUnionRoomsByFloor(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))
        if "floor" not in params:
            return self.write_json(error.DATA_BROKEN)

        union_user_info = union_model.get_union_userinfo_by_uid(self.share_db(), self.uid)
        if not union_user_info:
            return self.write_json(error.DATA_BROKEN)
        union_id = union_user_info['union_id']

        # 获取联盟楼层下桌子信息
        room_info_list = union_model.get_table_by_union_id_and_floor(self.share_db(), union_id, params['floor'])

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

#查询用户头像
class QueryUserHead(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)
        params = utils.json_decode(self.get_string('params'))
        if "uid" not in params:
            return self.write_json(error.DATA_BROKEN)
        union_user_info = union_model.get_union_userinfo_by_uid(self.share_db(), params["uid"])


class NoticeUnionMessage(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))
        if "union_id" not in params or "uid" not in params or "type" not in params:
            return self.write_json(error.DATA_BROKEN)
        union_id = params['union_id']
        uid = params['uid']
        type = params['type']
        if type == 1:#获取总能量
            self.publish(2,2,{'union_id':union_id,'uid':uid,'selfuid':self.uid,'type':type},9999)
            return self.write_json(error.OK, {})
        elif type == 2:#获取查找用户的能量
            self.publish(2,3,{'union_id':union_id,'uid':uid,'selfuid':self.uid,'type':type},9999)
            return self.write_json(error.OK, {})
        elif type == 5:#获取联盟所有的桌子
            """获取联盟桌子"""
            self.publish(2,type,{'union_id':union_id,'uid':uid,'selfuid':self.uid,'type':type},9999)
            """记录玩家登录联盟大厅"""
            key = "union_player_online"
            self.share_redis().hset(key,self.uid, union_id)
            return self.write_json(error.OK, {})


#根据联盟和subfloor获取桌子
class QueryUnionRoomsBySubFloor(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))
        if "subfloor" not in params:
            return self.write_json(error.DATA_BROKEN)

        union_user_info = union_model.get_union_userinfo_by_uid(self.share_db(), self.uid)
        if not union_user_info:
            return self.write_json(error.DATA_BROKEN)
        union_id = union_user_info['union_id']

        # 获取联盟楼层下桌子信息
        room_info_list = union_model.get_table_by_union_id_and_subfloor1(self.share_db(), union_id, params['subfloor'])

        result = list()
        for room_info in room_info_list:
            table_cache_data = tables_model.get_table_info(redis_conn(), room_info["tid"]) or {"player_list": [],
                                                                                               "players": [],
                                                                                               "round_index": 1,
                                                                                               "table_status": 0}
            if 'players' not in table_cache_data:
                table_cache_data['players'] = []
            rules = room_info["rules"] or room_info["ruleDetails"]
            players = table_cache_data['players']
            nicknamelst = list()
            for ply in players:
                if not ply:
                    continue
                nicknamelst.append(ply['nickName'])
            client_room_info = {"playerList": table_cache_data["player_list"],
                                "nickname":nicknamelst,
                                "roundIndex": table_cache_data["round_index"],
                                #"matchConfig": room_info["match_config"],
                                #"matchType": room_info['match_type'],
                                #"floor": room_info['floor'],
                                "subFloor": room_info['sub_floor'],
                                "status": table_cache_data["table_status"],
                                #"players": table_cache_data['players'],
                                "totalRound": room_info["round_count"],
                                #"gameType": room_info["game_type"],
                                #"ruleType": room_info["rule_type"],
                                #"owner": room_info["owner"],
                                "tid": room_info["tid"],
                                #"ruleDetails": rules
                                "sortbyid": 2 if len(table_cache_data["player_list"]) == 1 else 1 if len(table_cache_data["player_list"]) == 2 else 0
                                }
            result.append(client_room_info)

        #添加机器人

        tablesubfloor = union_model.querysubfloortable(self.share_db(),union_id)
        d_time = datetime.datetime.strptime(str(datetime.datetime.now().date())+'9:30', '%Y-%m-%d%H:%M')
        d_time1 =  datetime.datetime.strptime(str(datetime.datetime.now().date())+'23:57', '%Y-%m-%d%H:%M')
        n_time = datetime.datetime.now()
        ishas = False
        if n_time > d_time and n_time<d_time1:
            ishas = True
        else:
            ishas = False
        if len(tablesubfloor) >= 1 and ishas:
            ids = self.share_redis().hget('android',union_id)
            if ids != None:
                ids = utils.json_decode(str(ids,encoding='utf8') )
            if not ids or len(ids) == 0:
                start = 0
                last = 0
                if union_id == 10000:
                    start = 21
                    last = 20
                elif union_id == 100000:
                    start = 0
                    last = 20
                else:
                    start = 0
                    last = 0
                ids = union_model.queryandroid(self.share_db(),start,last)
                random.shuffle(ids)
                for i,id in  enumerate( ids ):
                    id['roundIndex'] = random.randint(0,5)
                    id['jointime'] = utils.timestamp() + random.randint(10,60)
                    id['tid'] = tablesubfloor[(i + 1) % len(tablesubfloor)]['tid']
                    id['subfloorid'] = tablesubfloor[(i + 1) % len(tablesubfloor)]['sub_floor']
                self.share_redis().hset('android',union_id,utils.json_encode(ids))
            else:
                autotime = random.randint(2,10) * 60
                roundtime = random.randint(30,50)
                if isinstance(ids,str):
                    ids = utils.json_decode(ids)
                round_person = random.randint(0,len(ids)-1)
                resultone = utils.timestamp() - ids[round_person]['jointime']
                if resultone > autotime or ids[round_person]['roundIndex'] >= 8:
                    random.shuffle(ids)
                    for i,id in  enumerate( ids ):
                        if id['roundIndex'] >= 8:
                            id['roundIndex'] = 1
                            id['jointime'] = utils.timestamp() + random.randint(10,60)
                            id['tid'] = tablesubfloor[(i + 1) % len(tablesubfloor)]['tid']
                            id['subfloorid'] = tablesubfloor[(i + 1) % len(tablesubfloor)]['sub_floor']
                    self.share_redis().hset('android',union_id,utils.json_encode(ids))
                if True:
                    roundnum = random.randint(3,7)
                    #random.shuffle(ids)
                    for i,id in  enumerate( ids ):
                        resultone = utils.timestamp() - id['jointime']
                        if resultone < roundtime:
                            continue
                        if i >= roundnum and roundnum % 2 == 0:
                            break
                        id['jointime'] = utils.timestamp() + random.randint(10,60)
                        id['roundIndex'] = id['roundIndex'] + random.randint(1,4)
                        if id['roundIndex'] > 8:
                            id['roundIndex'] = 8
                    self.share_redis().hset('android',union_id,utils.json_encode(ids))


            arr = []
            ids = sorted(ids, key=lambda x: x['subfloorid'],reverse=True)
            for i , j in enumerate(ids):
                if params['subfloor'] != j['subfloorid']:
                    continue
                if len(arr) == 1:
                    arr.append(j)
                    if params['subfloor'] != arr[0]['subfloorid']:
                        continue
                    keyval = {'sortbyid':1,"playerList":[arr[0]['uid'],arr[1]['uid']],"nickname":[arr[0]['nickname'],arr[1]['nickname']],"roundIndex":arr[0]['roundIndex'],"subFloor":arr[0]['subfloorid'],"status":10,"totalRound":"8","tid":arr[0]['tid']}
                    result.append(keyval)
                    arr.clear()
                else:
                    arr.append(j)

        # 排序
        result1 = sorted(result, key=lambda x: x['sortbyid'],reverse=True)
        for item in result1:
            item.pop('sortbyid')
        return self.write_json(error.OK, result1)


# 获取联盟全部桌子 大厅模式请求数据
class QueryUnionAllRooms(CommHandler):
    def _request(self):
        union_id = self.share_redis().hget('unionid',self.uid )
        if not union_id:
            union_user_info = union_model.get_union_userinfo_by_uid(self.share_db(), self.uid)
            if not union_user_info:
                return self.write_json(error.DATA_BROKEN)
            union_id = union_user_info['union_id']
        else:
            union_id = int(union_id)

        room_info_list = None
        room_info_list = self.share_redis().hgetall('autotable')
        #room_info_list = union_model.get_table_by_union_id1(self.share_db(), union_id)
        room_info_list = union_model.get1(union_id)
        """
        if not room_info_list:
            
            for kv in room_info_list:
                tid = kv['tid']
                sub_floor = kv['sub_floor']
                round_count = kv['round_count']
                self.share_redis().hset('autotable',tid,utils.json_encode({'subfloor':sub_floor,'round_count':round_count}))
        else:
            data_left = list()
            for iv in room_info_list.items():
                tid = int(iv[0])
                dv = utils.json_decode(str(iv[1], encoding = "utf8"))
                dv['tid'] = tid
                data_left.append(dv)
            room_info_list = data_left
"""
        result = list()

        for room_info in room_info_list:
            table_cache_data = tables_model.get_table_info(redis_conn(), room_info["tid"]) or {"player_list": [],
                                                                                               "players": [],
                                                                                               "round_index": 1,
                                                                                               "table_status": 0}
            if 'players' not in table_cache_data:
                table_cache_data['players'] = []
            #rules = room_info["rules"] or room_info["ruleDetails"]
            players = table_cache_data['players']
            nicknamelst = list()
            for ply in players:
                if not ply:
                    continue
                nicknamelst.append(ply['nickName'])
            client_room_info = {"playerList": table_cache_data["player_list"],
                                "nickname":nicknamelst,
                                "roundIndex": table_cache_data["round_index"],
                                #"matchConfig": room_info["match_config"],
                                #"matchType": room_info['match_type'],
                                "subFloor": room_info['sub_floor'],
                                #"floor": room_info['floor'],
                                "status": table_cache_data["table_status"],
                                #"players": table_cache_data['players'],
                                "totalRound": room_info["round_count"],
                                #"gameType": room_info["game_type"],
                                #"ruleType": room_info["rule_type"], "owner": room_info["owner"],
                                "tid": room_info["tid"],
                                #"ruleDetails": rules
                                "sortbyid": 2 if len(table_cache_data["player_list"]) == 1 else 1 if len(table_cache_data["player_list"]) == 2 else 0
                                }
            result.append(client_room_info)
        #添加机器人

        tablesubfloor = union_model.querysubfloortable(self.share_db(),union_id)
        d_time = datetime.datetime.strptime(str(datetime.datetime.now().date())+'9:30', '%Y-%m-%d%H:%M')
        d_time1 =  datetime.datetime.strptime(str(datetime.datetime.now().date())+'23:57', '%Y-%m-%d%H:%M')
        n_time = datetime.datetime.now()
        ishas = False
        if n_time > d_time and n_time<d_time1:
            ishas = True
        else:
            ishas = False
        if len(tablesubfloor) >= 1 and ishas:
            ids = self.share_redis().hget('android',union_id)
            if ids != None:
                ids = utils.json_decode(str(ids,encoding='utf8') )
            if not ids or len(ids) == 0:
                start = 0
                last = 0
                if union_id == 10000:
                    start = 21
                    last = 20
                elif union_id == 100000:
                    start = 0
                    last = 20
                else:
                    start = 0
                    last = 0
                ids = union_model.queryandroid(self.share_db(),start,last)
                random.shuffle(ids)
                for i,id in  enumerate( ids ):
                    id['roundIndex'] = random.randint(0,5)
                    id['jointime'] = utils.timestamp() + random.randint(10,60)
                    id['tid'] = tablesubfloor[(i + 1) % len(tablesubfloor)]['tid']
                    id['subfloorid'] = tablesubfloor[(i + 1) % len(tablesubfloor)]['sub_floor']
                self.share_redis().hset('android',union_id,utils.json_encode(ids))
                print(ids)
            else:
                autotime = random.randint(2,10) * 60
                roundtime = random.randint(30,50)
                if isinstance(ids,str):
                    ids = utils.json_decode(ids)
                round_person = random.randint(0,len(ids)-1)
                resultone = utils.timestamp() - ids[round_person]['jointime']
                if resultone > autotime or ids[round_person]['roundIndex'] >= 8:
                    random.shuffle(ids)
                    for i,id in  enumerate( ids ):
                        if id['roundIndex'] >= 8:
                            id['roundIndex'] = 1
                            id['jointime'] = utils.timestamp() + random.randint(10,60)
                            id['tid'] = tablesubfloor[(i + 1) % len(tablesubfloor)]['tid']
                            id['subfloorid'] = tablesubfloor[(i + 1) % len(tablesubfloor)]['sub_floor']
                    self.share_redis().hset('android',union_id,utils.json_encode(ids))
                if True:
                    roundnum = random.randint(3,7)
                    #random.shuffle(ids)
                    for i,id in  enumerate( ids ):
                        resultone = utils.timestamp() - id['jointime']
                        if resultone < roundtime:
                            continue
                        if i >= roundnum and roundnum % 2 == 0:
                            break
                        id['jointime'] = utils.timestamp() + random.randint(10,60)
                        id['roundIndex'] = id['roundIndex'] + random.randint(0,5)
                        if id['roundIndex'] > 8:
                            id['roundIndex'] = 8
                    self.share_redis().hset('android',union_id,utils.json_encode(ids))


            arr = []
            ids = sorted(ids, key=lambda x: x['tid'],reverse=True)
            for i , j in enumerate(ids):
                if len(arr) == 1:
                    arr.append(j)
                    keyval = {'sortbyid':1,"playerList":[arr[0]['uid'],arr[1]['uid']],"nickname":[arr[0]['nickname'],arr[1]['nickname']],"roundIndex":arr[0]['roundIndex'],"subFloor":arr[0]['subfloorid'],"status":10,"totalRound":"8","tid":arr[0]['tid']}
                    result.append(keyval)
                    arr.clear()
                else:
                    arr.append(j)

        #排序
        result1 = sorted(result, key=lambda x: x['sortbyid'],reverse=True)
        for item in result1:
            item.pop('sortbyid')
        return self.write_json(error.OK, result1)


# 备注联盟玩家名称
class RemarkUnionUser(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode((self.get_string('params')))
        if "uid" not in params or "remark" not in params:
            return self.write_json(error.DATA_BROKEN)

        uid = params["uid"]
        remark = params["remark"]

        union_user_info = union_model.get_union_userinfo_by_uid(self.share_db(), self.uid)
        if not union_user_info:
            return self.write_json(error.DATA_BROKEN)
        union_id = union_user_info['union_id']

        if union_user_info['permission'] not in (UNION_MANAGER, UNION_SEC_MANAGER,):
            return self.write_json(error.ACCESS_DENNY)

        refer_user_info = union_model.get_union_userinfo_by_uid(self.share_db(), self.uid)
        if not refer_user_info:
            return self.write_json(error.DATA_BROKEN)

        count = union_model.update_remark_by_uid_and_union_id(self.share_db(), uid, union_id, remark)
        if count == 0:
            return self.write_json(error.OK, params)
        return self.write_json(error.OK, params)


# 踢出联盟玩家
class KickUnionUser(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode((self.get_string('params')))
        if "uid" not in params:
            return self.write_json(error.DATA_BROKEN)
        union_user_info = union_model.get_union_userinfo_by_uid(self.share_db(), self.uid)
        if not union_user_info:
            return self.write_json(error.DATA_BROKEN)
        union_id = union_user_info['union_id']

        if union_user_info['permission'] not in (UNION_MANAGER, UNION_SEC_MANAGER , UNION_SMALL_MANAGER,):
            return self.write_json(error.ACCESS_DENNY)

        uid = params["uid"]
        union_id_from_client = params['union_id']
        refer_user_info = union_model.get_union_userinfo_by_uid1(self.share_db(), uid,union_id_from_client)
        if not refer_user_info:
            return self.write_json(error.DATA_BROKEN)

        # 检测能量是否为空
        if refer_user_info['energy'] != 0 or refer_user_info['lock_energy'] != 0:
            return self.write_json(error.DATA_BROKEN)

        # 检测自身权限
        if refer_user_info['permission'] in( UNION_MANAGER ,UNION_SMALL_MANAGER):
            return self.write_json(error.DATA_BROKEN)

        #判断是否是直属玩家
        if refer_user_info['union_user_id'] != self.uid:
            return self.write_json(error.ACCESS_DENNY)
        union = union_model.get_union_info(self.share_db(), union_id)

        # 如果是小盟主，则将全部旗下用户绑定至盟主，合伙人绑定至盟主
        if refer_user_info['permission'] == UNION_SMALL_MANAGER:
            union_model.modify_union_user_id(self.share_db(), union_id, uid, union['uid'])
            pass
        # 如果自己是合伙人，则将全部旗下用户绑定至小盟主
        elif refer_user_info['permission'] in (UNION_PARTNER, UNION_SEC_MANAGER,):
            # to_union_user_id = refer_user_info['union_user_id']
            # if refer_user_info['union_user_id'] == -1:
            #     to_union_user_id = union['uid']
            union_model.modify_union_user_id(self.share_db(), union_id, uid, union['uid'])
            #union_model.modify_union_tag_id(self.share_db(), union_id, uid, to_union_user_id)
            pass
        union_model.remove_union_user_by_uid(self.share_db(), union_id, uid)
        union_model.add_user_count(self.share_db(), union_id, -1)
        self.share_redis().hdel('unionid', uid)
        self.share_redis().hdel('union_player_online', uid)
        return self.write_json(error.OK)


# 添加玩家至联盟
class AddPlayerToUnion(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)
        params = utils.json_decode((self.get_string('params')))
        if "uid" not in params:
            return self.write_json(error.DATA_BROKEN)
        uid = params["uid"]
        union_user_info = union_model.get_union_userinfo_by_uid(self.share_db(), self.uid)
        if not union_user_info:
            return self.write_json(error.DATA_BROKEN)
        if union_user_info['permission'] not in (UNION_MANAGER, UNION_SMALL_MANAGER,UNION_PARTNER):
            return self.write_json(error.ACCESS_DENNY)

        union_id = union_user_info['union_id']
        refer_user_info = union_model.get_union_userinfo_by_uid(self.share_db(), uid)
        if refer_user_info:
            return self.write_json(error.DATA_BROKEN)

        union_model.join_union(self.share_db(), uid, union_id, union_user_id=self.uid)
        union_model.add_user_count(self.share_db(), union_id, 1)
        self.broad_cast_user([uid],
                             {"type": const.ADD_USER_TO_UNION, "data": {"unionID": union_id}})
        return self.write_json(error.OK)


# 小联盟申请并入大联盟
class RequestMergeUnion(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)
        params = utils.json_decode((self.get_string('params')))
        if "union_id" not in params:
            return self.write_json(error.DATA_BROKEN)
        union_user_info = union_model.get_union_userinfo_by_uid(self.share_db(), self.uid)
        if not union_user_info:
            return self.write_json(error.DATA_BROKEN)
        if union_user_info['permission'] not in (UNION_MANAGER,):
            return self.write_json(error.ACCESS_DENNY)

        union_id = int(params["uid"])
        owner_union_id = union_user_info['union_id']

        owner_union = union_model.get_union_info(self.share_db(), owner_union_id)
        if owner_union['type'] == 1:
            return self.write_json(error.OWNER_BIG_UNION)
        union = union_model.get_union_info(self.share_db(), union_id)
        if not union or union['type'] == 0:
            return self.write_json(error.NOT_UNION)

        count = union_model.get_not_empty_energy_count_by_union_id(self.share_db(), owner_union_id)['count']
        if count != 0:
            return self.write_json(error.ENERGY_NOT_EMPTY)

        # 插入审核表
        # union_model.update_user_verify(self.share_db(), self.uid, union_id, 0, 0, ref_union_id=owner_union_id,
        #                               verify_type=1)
        return self.write_json(error.OK)


# 获取申请列表
class QueryUnionRequestJoinList(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode((self.get_string('params')))
        union_user_info = union_model.get_union_userinfo_by_uid(self.share_db(), self.uid)
        if not union_user_info:
            return self.write_json(error.DATA_BROKEN)
        if union_user_info['permission'] not in (UNION_MANAGER, UNION_SEC_MANAGER, UNION_SMALL_MANAGER, UNION_PARTNER):
            return self.write_json(error.ACCESS_DENNY)

        union_id = union_user_info['union_id']
        type = 0
        if "type" in params:
            type = int(params['type'])

        promo = 0
        if union_user_info['permission'] == UNION_MANAGER:
            promo = union_id
        elif union_user_info['permission'] == UNION_SMALL_MANAGER:
            small_union = union_model.get_small_union_by_owner_id(self.share_db(), self.uid)
            if not small_union:
                return self.write_json(error.DATA_BROKEN)
            promo = small_union["promo"]
        elif union_user_info['permission'] == UNION_PARTNER:
            #small_union_id = union_user_info['union_small_id']
            #partner = union_model.get_union_partner_by_id(self.share_db(), self.uid, union_id, small_union_id)
            #if not partner:
            #    return self.write_json(error.DATA_BROKEN)
            promo = union_user_info["uid"]#partner["promo"]

        result = {}
        result["type"] = type
        if type == 1:
            status = params.get("status") or 0
            # result['data'] = union_model.query_verify_list_left_join_player_left_join_union(self.share_db(), union_id,
            #                                                                                 status)
            result['data'] = union_model.query_verify_list_left_join_player_by_promo(self.share_db(), promo, status)
        elif type == 2:
            # apply_record_list = union_model.query_verify_list_record_join_player_join_union(self.share_db(), union_id)
            apply_record_list = union_model.query_verify_list_record_by_promo(self.share_db(), promo)
            result["data"] = apply_record_list
        return self.write_json(error.OK, result)


# 处理申请
class VerifyUnionRequestJoin(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)
        params = utils.json_decode((self.get_string('params')))
        if "id" not in params or 'status' not in params:
            return self.write_json(error.DATA_BROKEN)
        status = params['status']
        v_id = params['id']
        if status not in (1, -1,):
            return self.write_json(error.DATA_BROKEN)

        union_user_info = union_model.get_union_userinfo_by_uid(self.share_db(), self.uid)
        if not union_user_info:
            return self.write_json(error.DATA_BROKEN)
        if union_user_info['permission'] not in (UNION_MANAGER, UNION_SEC_MANAGER, UNION_SMALL_MANAGER, UNION_PARTNER):
            return self.write_json(error.ACCESS_DENNY)

        curr_union_id = union_user_info['union_id']
        # 检测权限
        verify = union_model.get_verify_by_id(self.share_db(), v_id)
        if verify['union_id'] != curr_union_id:
            return self.write_json(error.ACCESS_DENNY)

        uid = verify['uid']
        union_id = verify['union_id']

        if status == 1:
            # 玩家加入
            if verify['type'] == 0:
                refer_user = union_model.get_union_userinfo_by_uid(self.share_db(), verify['uid'])
                if refer_user:
                    return self.write_json(error.UID_ERROR)

                promo = int(verify['promo'])

                small_union_id = 0
                union_partner_id = 0

                if promo >= 200000 and promo < 299999:
                    small_union_id = promo
                elif promo >= 300000 and promo < 499999:
                    #partner = union_model.get_union_partner_by_partner_id(self.share_db(), promo)
                    if False:
                        return self.write_json(error.DATA_BROKEN)

                    small_union_id = 0#partner["union_small_id"]
                    union_partner_id = promo

                union_model.join_union(self.share_db(), uid, union_id, union_user_id=self.uid,
                                       small_union_id=small_union_id, partner_id=union_partner_id)
                union_model.add_user_count(self.share_db(), union_id, 1)
            # 小联盟加入
            # elif verify['type'] == 1:
            #     refer_union = union_model.get_union_info(self.share_db(), verify['ref_union_id'])
            #     if not refer_union or refer_union['dismiss_time'] != 0:
            #         return self.write_json(error.ENERGY_NOT_EMPTY)
            #     count = union_model.get_not_empty_energy_count_by_union_id(self.share_db(),
            #                                                                verify['ref_union_id'])['count']
            #     if count != 0:
            #         return self.write_json(error.ENERGY_NOT_EMPTY)
            #     union_model.merge_union_adjust_permission(self.share_db(), verify['ref_union_id'])
            #     count = union_model.merge_union_id(self.share_db(), verify['ref_union_id'], union_id, verify['uid'])
            #     union_model.add_user_count(self.share_db(), union_id, count)
            #     union_model.update_dismiss_time(self.share_db(), verify['ref_union_id'])

        admin_info = player_model.get_by_uid(self.share_db(), self.uid)
        nick_name = admin_info['nick_name']
        count = union_model.update_user_verify_by_id(self.share_db(), v_id, status, nick_name, self.uid,
                                                     union_id=union_id)
        if count == 0:
            return self.write_json(error.SYSTEM_ERR)

        self.broad_cast_user([verify['uid']],
                             {"type": const.PASS_JOIN_GROUP,
                              "data": {"status": status, "unionID": verify['union_id']}})

        return self.write_json(error.OK, params)


# 获取联盟战绩 (自己以及自己下级的战绩，盟主和副盟主，则是全部)
class QueryUnionScoreList(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode((self.get_string('params')))
        # if "isOwner" not in params:
        #     return self.write_json(error.DATA_BROKEN)
        if "uid" not in params:
            return self.write_json(error.DATA_BROKEN)

        uid = params['uid']#self.uid if int(params['isOwner']) == 1 else 0
        union_user_info = union_model.get_union_userinfo_by_uid(self.share_db(), self.uid)
        if not union_user_info:
            return self.write_json(error.DATA_BROKEN)
        union_id = union_user_info['union_id']

        info = []
        if uid == 0:
            if union_user_info['permission'] in (UNION_MANAGER, UNION_SEC_MANAGER,):
                info = union_model.get_union_room_list(self.share_db_logs(), union_id, uid)
            elif union_user_info['permission'] == UNION_SMALL_MANAGER:
                origin_info = union_model.get_union_room_list(self.share_db_logs(), union_id, uid)
                info = []
                if origin_info:
                    all_uids = union_model.query_small_union_users_only_id(self.share_db(), union_id, self.uid)
                    all_uids = set(_.pluck(all_uids, 'uid'))
                    for i in origin_info:
                        if i['uid1'] not in all_uids and i['uid2'] not in all_uids and i['uid3'] not in \
                                all_uids and i['uid4'] not in all_uids:
                            continue
                        info.append(i)
            elif union_user_info['permission'] == UNION_PARTNER:
                origin_info = union_model.get_union_room_list(self.share_db_logs(), union_id, uid)
                info = []
                if origin_info:
                    all_uids = union_model.query_small_union_partner_users_only_id(self.share_db(), union_id, self.uid)
                    all_uids = set(_.pluck(all_uids, 'uid'))
                    for i in origin_info:
                        if i['uid1'] not in all_uids and i['uid2'] not in all_uids and i['uid3'] not in \
                                all_uids and i['uid4'] not in all_uids:
                            continue
                        info.append(i)
        else:
            info = union_model.get_union_room_list(self.share_db_logs(), union_id, uid)
        result = []
        for row in info:
            result.append(
                {"recordID": row.record_id, "roomID": row.room_id, "time": row.finish_time, "owner": row.owner,
                 "matchType": row.match_type,
                 "roundIndex": logs_model.get_last_round_index_by_record_id(self.share_db_logs(), row.record_id)[
                                   'seq'] or 1,
                 "totalRound": row.round_count,
                 "gameType": row.game_type, "ruleType": row.rule_type,
                 "users": [[row.name1, row.score1, row.uid1, row.avatar1], [row.name2, row.score2, row.uid2, row.avatar2],
                           [row.name3, row.score3, row.uid3, row.avatar3], [row.name4, row.score4, row.uid4, row.avatar4],
                           [row.name5, row.score5, row.uid5, row.avatar5], [row.name6, row.score6, row.uid6, row.avatar6],
                           [row.name7, row.score7, row.uid7, row.avatar7], [row.name8, row.score8, row.uid8, row.avatar8],
                           [row.name9, row.score9, row.uid9, row.avatar9], [row.name10, row.score10, row.uid10, row.avatar10],
                           ], })
            data = result[len(result)-1]
            users = data.get('users')
            maxuser = max(users,key=self.get_max_val)
            users.remove(maxuser)
            users.insert(0,maxuser)
            result[len(result)-1]['users'] = users

        return self.write_json(error.OK, result)

    def get_max_val(self, k):
        return k[1]


class QueryUnionGameLogs(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))
        if 'beginTime' not in params or 'endTime' not in params:
            return self.write_json(error.DATA_BROKEN)

        union_user_info = union_model.get_union_userinfo_by_uid(self.share_db(), self.uid)
        if not union_user_info:
            return self.write_json(error.DATA_BROKEN)
        union_id = union_user_info['union_id']
        start_time = params['beginTime']
        end_time = params['endTime']

        data = []
        if union_user_info['permission'] in (UNION_MANAGER, UNION_SEC_MANAGER,):
            data = union_model.get_union_game_logs(self.share_db_logs(), union_id, start_time, end_time)
        elif union_user_info['permission'] == UNION_SMALL_MANAGER:
            data = union_model.get_union_game_logs(self.share_db_logs(), union_id, start_time, end_time)

            if not data:
                return self.write_json(error.OK, [])
            all_uids = union_model.query_small_union_users_only_id(self.share_db(), union_id, self.uid)
            all_uids.append({"uid":self.uid})
            all_uids = set(_.pluck(all_uids, 'uid'))
            ret_data = []
            for i in data:
                if i['uid1'] not in all_uids and i['uid2'] not in all_uids and i['uid3'] not in \
                        all_uids and i['uid4'] not in all_uids:
                    continue
                ret_data.append(i)
            return self.write_json(error.OK, ret_data)
        elif union_user_info['permission'] == UNION_PARTNER:
            data = union_model.get_union_game_logs(self.share_db_logs(), union_id, start_time, end_time)
            if not data:
                return self.write_json(error.OK, [])
            all_uids = union_model.query_small_union_partner_users_only_id(self.share_db(), union_id, self.uid)
            all_uids = set(_.pluck(all_uids, 'uid'))
            ret_data = []
            for i in data:
                if i['uid1'] not in all_uids and i['uid2'] not in all_uids and i['uid3'] not in \
                        all_uids and i['uid4'] not in all_uids:
                    continue
                ret_data.append(i)
            return self.write_json(error.OK, ret_data)
        return self.write_json(error.OK, data)


class QueryUnionAllUsers(CommHandler):
    def _request(self):
        union_user_info = union_model.get_union_userinfo_by_uid(self.share_db(), self.uid)
        if not union_user_info:
            return self.write_json(error.DATA_BROKEN)
        union_id = union_user_info['union_id']
        data = union_model.query_all_union_users(self.share_db(), union_id)
        return self.write_json(error.OK, data)


class GetUnionGameCountLogs(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode((self.get_string('params')))
        union_user_info = union_model.get_union_userinfo_by_uid(self.share_db(), self.uid)
        if not union_user_info:
            return self.write_json(error.DATA_BROKEN)

        union_id = union_user_info['union_id']
        if union_user_info['permission'] not in (UNION_MANAGER, UNION_SEC_MANAGER,):
            return self.write_json(error.ACCESS_DENNY)

        status = params.get("status") or 0
        apply_list = union_model.query_union_game_count_logs(self.share_db_logs(), union_id, status)
        return self.write_json(error.OK, {"data": apply_list, "status": status})


class SetUnionGameCountLogs(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode((self.get_string('params')))
        union_user_info = union_model.get_union_userinfo_by_uid(self.share_db(), self.uid)
        if not union_user_info:
            return self.write_json(error.DATA_BROKEN)

        union_id = union_user_info['union_id']
        msg_id = int(params["msgID"])
        if union_user_info['permission'] not in (UNION_MANAGER, UNION_SEC_MANAGER,):
            return self.write_json(error.ACCESS_DENNY)

        status = 1
        count = union_model.set_union_game_count_logs(self.share_db_logs(), union_id, msg_id, status)
        return self.write_json(error.OK, {"isFinish": count})


# 将联盟玩家设置为小盟主
class SetUnionPlayerAsSubManager(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode((self.get_string('params')))

        if "uid" not in params or "union_id" not in params:
            return self.write_json(error.DATA_BROKEN)

        uid = params["uid"]
        union_id = params["union_id"]

        if uid == self.uid:  # 不能自己设置自己为小盟主
            return self.write_json(error.ACCESS_DENNY)

        info = union_model.get_union_userinfo_by_uid_and_union_id(self.share_db(), self.uid, union_id)
        if UNION_SMALL_MANAGER <= info["permission"]:
            return self.write_json(error.ACCESS_DENNY)

        union = union_model.get_union_info(self.share_db(), union_id)
        if not union:
            return self.write_json(error.ACCESS_DENNY)

        count = union_model.update_permission_by_uid_and_union_id(self.share_db(), uid, union_id, UNION_SMALL_MANAGER)
        if count == 0:
            return self.write_json(error.SYSTEM_ERR)

        # 创建一个小联盟
        small_union_id = utils.get_random_small_union_id()
        # 检查小联盟ID是否已经被占用
        while True:
            tmp = union_model.get_small_union_by_id(self.share_db(), small_union_id)
            if not tmp:
                break
            else:
                small_union_id = utils.get_random_small_union_id()

        name = str(uid)
        promo = small_union_id  # utils.get_random_num(6)
        divide = 0
        remark = ""
        count = union_model.create_small_union(self.share_db(), small_union_id, name, "健康游戏，严禁赌博。", 0, 1,
                                               union_id, promo, uid, divide, remark)
        if count == 0:
            return self.write_json(error.SYSTEM_ERR)
        else:
            self.share_redis().hdel(union_id,uid)

        return self.write_json(error.OK)


# 将联盟玩家设置为合伙人
class SetUnionPlayerAsPartner(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode((self.get_string('params')))

        if "uid" not in params or "union_id" not in params:
            return self.write_json(error.DATA_BROKEN)





        uid = params["uid"]
        union_id = params["union_id"]
        small_union_id = 0

        if uid == self.uid:  # 不能自己设置自己为合伙人
            return self.write_json(error.ACCESS_DENNY)
        # 获取操作者信息
        info = union_model.get_union_userinfo_by_uid_and_union_id(self.share_db(), self.uid, union_id)

        if UNION_PARTNER < info["permission"]:
            return self.write_json(error.ACCESS_DENNY)

        small_union_id = info["union_small_id"]

        if info["permission"] == UNION_SMALL_MANAGER:
            # 小盟主设置合伙人
            small_union = union_model.get_small_union_by_owner_id(self.share_db(), self.uid)
            if not small_union:
                return self.write_json(error.DATA_BROKEN)
            small_union_id = small_union['id']
        elif info["permission"] == UNION_PARTNER:
            # 合伙人设置下级合伙人
            #partner = union_model.get_union_partner_by_id(self.share_db(), self.uid, union_id, small_union_id)
            if False:
                return self.write_json(error.DATA_BROKEN)
            small_union_id = 0 #partner['union_small_id']

        # 设置权限
        count = union_model.update_permission_by_uid_and_union_id(self.share_db(), uid, union_id, UNION_PARTNER)
        if count == 0:
            return self.write_json(error.SYSTEM_ERR)
        if True:
            return self.write_json(error.OK)
        # 创建合伙人记录
        partner_id = utils.get_random_union_partner_id()
        # 检查partner_id 是否已经使用
        while True:
            tmp = union_model.get_union_partner_by_partner_id(self.share_db(), partner_id)
            if not tmp:
                break
            else:
                partner_id = utils.get_random_union_partner_id()

        name = ""
        parent_id = -1
        promo = partner_id
        divide = 0
        remark = ""
        notice = ""

        if info['permission'] == UNION_PARTNER:
            # 获取合伙人ID
            partner_info = union_model.get_union_partner_by_id(self.share_db(), uid, union_id, small_union_id)
            if partner_info:
                parent_id = partner_info['id']

        count = union_model.create_union_partner(self.share_db(), partner_id, name, uid, union_id, small_union_id,
                                                 parent_id, promo, divide, remark, notice, 1)
        if count == 0:
            return self.write_json(error.SYSTEM_ERR)
        else:
            self.share_redis().hdel(union_id,uid)

        return self.write_json(error.OK)

class SetUnionUserPlayerDivide(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)
        params = utils.json_decode((self.get_string('params')))
        if "uid" not in params or "union_id" not in params or "divide" not in params \
                or "subfloorid" not in params:
            return self.write_json(error.DATA_BROKEN)
        uid = params["uid"]
        union_id = params["union_id"]
        divide = params["divide"]
        subfloorid = params["subfloorid"]
        count = union_model.set_subfloorplaydivide(self.share_db(),union_id,uid,subfloorid,divide,self.uid)
        if count == 0:
            return self.write_json(error.SYSTEM_ERR)

        return self.write_json(error.OK)

# 设置小盟主分成比例
class SetSmallUnionDivide(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode((self.get_string('params')))

        if "uid" not in params or "union_id" not in params or "divide" not in params:
            return self.write_json(error.DATA_BROKEN)

        uid = params["uid"]
        union_id = params["union_id"]
        # small_union_id = params["small_union_id"]
        divide = params["divide"]
        small_union = union_model.get_small_union_by_owner_id(self.share_db(), uid)
        if not small_union:
            return self.write_json(error.DATA_BROKEN)
        small_union_id = small_union['id']

        # 设置小联盟分成比例
        count = union_model.set_small_union_divide(self.share_db(), union_id, small_union_id, divide,uid)
        if count == 0:
            return self.write_json(error.SYSTEM_ERR)

        return self.write_json(error.OK)


# 设置合伙人分成比例
class SetUnionPartnerDivide(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode((self.get_string('params')))
        if "uid" not in params or "union_id" not in params or "divide" not in params:
            return self.write_json(error.DATA_BROKEN)

        uid = params["uid"]
        union_id = params["union_id"]
        # small_union_id = params["small_union_id"]
        divide = params["divide"]

        union_user_info = union_model.get_union_userinfo_by_uid_and_union_id(self.share_db(), uid, union_id)
        if not union_user_info:
            return self.write_json(error.DATA_BROKEN)
        else:
            small_union_id = union_user_info['union_small_id']

        partner_info = union_model.get_union_partner_by_id(self.share_db(), uid, union_id, small_union_id)

        # if not partner_info:
        #     return self.write_json(error.DATA_BROKEN)

        #partner_id = partner_info['id']

        count = union_model.set_small_union_divide(self.share_db(), union_id,uid,divide,uid)
        #count = union_model.set_union_partner_divide(self.share_db(), uid, divide)
        if count == 0:
            return self.write_json(error.SYSTEM_ERR)

        return self.write_json(error.OK)

#获取盟主指定玩家玩法比例分成
class GetUnionUserDive(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))
        if "uid" not in params or "union_id" not in params:
            return self.write_json(error.DATA_BROKEN)

        uid = params['uid']
        union_id = params['union_id']
        data = union_model.get_union_wf(self.share_db(), uid, union_id,self.uid)
        permission = union_model.getpermission(self.share_db(),self.uid,union_id)
        for item in data:
            config = utils.json_decode(item["play_config"])
            if permission:
                if permission["permission"] == 0:
                    item["limitRate"] = config["matchConfig"]["limitRate"]
            item["enterScore"] = config["matchConfig"]["enterScore"]
            item.pop('play_config')
        return self.write_json(error.OK, data)

# 获取联盟中指定玩家分成比例
class GetUnionUserDivide(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))
        if "uid" not in params or "union_id" not in params:
            return self.write_json(error.DATA_BROKEN)

        uid = params['uid']
        union_id = params['union_id']
        union_user_info = union_model.get_union_userinfo_by_uid_and_union_id(self.share_db(), uid, union_id)
        if not union_user_info:
            return self.write_json(error.DATA_BROKEN)
        if union_user_info['permission'] not in (UNION_MANAGER, UNION_SEC_MANAGER,UNION_SMALL_MANAGER, UNION_PARTNER):
            return self.write_json(error.ACCESS_DENNY)

        if union_user_info['permission'] == UNION_SMALL_MANAGER:
            small_union = union_model.get_small_union_by_owner_id(self.share_db(), uid)
            data = {}
            if small_union and len(small_union) > 0:
                data = {"divide": small_union['divide'], "uid": uid}
            else:
                data = {"divide": 0, "uid": uid}
            return self.write_json(error.OK, data)
        elif union_user_info['permission'] == UNION_PARTNER:
            small_union_id = union_user_info["union_small_id"]
            partner = union_model.get_union_partner_by_id(self.share_db(), uid, union_id, small_union_id)
            d = union_model.get_small_union_by_owner_id1(self.share_db(), uid,union_id)
            data = None
            if d:
                data = {"divide": d['divide'], "uid": uid}
            elif partner:
                data = {"divide": partner['divide'], "uid": uid}
            else:
                data = {"divide": 0, "uid": uid}
            return self.write_json(error.OK, data)
        elif union_user_info['permission'] == UNION_MANAGER:
            data = {"divide": 0, "uid": uid}
            return self.write_json(error.OK, data)

        data = {"divide": 0, "uid": uid}
        return self.write_json(error.OK, data)

# 查询指定id直属小盟主和合伙人总抽水情况
class QueryUserExtraList(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))
        if "union_id" not in params:
            return self.write_json(error.DATA_BROKEN)
        union_id = params["union_id"]
        union_user_info = union_model.get_union_userinfo_by_uidone(self.share_db(), self.uid,union_id)
        return self.write_json(error.OK, union_user_info)


# 获取直属有分成的用户
class QuerySubManagerOrPartnerUsers(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))
        if "uid" not in params:
            return self.write_json(error.DATA_BROKEN)

        union_user_info = union_model.get_union_userinfo_by_uid(self.share_db(), self.uid)
        if not union_user_info:
            return self.write_json(error.DATA_BROKEN)
        if union_user_info['permission'] not in (UNION_MANAGER, UNION_SEC_MANAGER,UNION_SMALL_MANAGER, UNION_PARTNER):
            return self.write_json(error.ACCESS_DENNY)

        union_id = union_user_info['union_id']
        small_union_id = union_user_info['union_small_id']
        partner_id = union_user_info['partner_id']
        if small_union_id is None:
            small_union_id = 0
        if partner_id is None:
            partner_id = 0

        if union_user_info['permission'] == UNION_MANAGER:
            small_union_id = 0
            partner_id = 0
        elif union_user_info['permission'] == UNION_SMALL_MANAGER:
            small_union = union_model.get_small_union_by_owner_id(self.share_db(), self.uid)
            if small_union is None:
                return self.write_json(error.ACCESS_DENNY)
            small_union_id = small_union['id']
            partner_id = 0
        elif union_user_info['permission'] == UNION_PARTNER:
            # partner = union_model.get_union_partner_by_id(self.share_db(), self.uid, union_id, small_union_id)
            # if not partner:
            #     return self.write_json(error.ACCESS_DENNY)
            partner_id = 0 #partner['id']
        else:
            return self.write_json(error.ACCESS_DENNY)

        uid = self.uid
        data = None
        if union_user_info['permission'] == 10:
            data = union_model.get_sub_manager_or_partner_by_id1(self.share_db(), union_id,uid)
        else:
            data = union_model.get_sub_manager_or_partner_by_id1(self.share_db(), union_id, uid )

        return self.write_json(error.OK, data)

# 快速加入房间
class SpeedJoinUnionRoom(CommHandler):
    def _request(self):
        print('fwfe')
        #self.publish_to_service(1,871349,{},1 )


#查询保险箱抽水记录
class QueryUnionSafeBoxBalance(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))

        unionid = int(params["unionid"])
        uid = int(params["uid"])

        info = union_model.get_union_userinfo_by_uid1(self.share_db(),uid,unionid)

        if not info:
            return self.write_json(error.ACCESS_DENNY)

        #查询保险箱抽水余额
        data = union_model.query_union_safebox(self.share_db(),uid,unionid)
        return self.write_json(error.OK, data)


#提取抽水
class FetchUnionSafeBoxBalance(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))

        unionid = int(params["unionid"])
        uid = int(params["uid"])

        info = union_model.get_union_userinfo_by_uid1(self.share_db(),uid,unionid)
        if not info:
            return self.write_json(error.ACCESS_DENNY)
        queryid = params["queryid"]
        if not queryid:
            return self.write_json(error.ACCESS_DENNY)

        score = union_model.query_union_safebox_by_queryid(self.share_db(),uid,unionid,queryid)
        data = union_model.fetch_union_safebox(self.share_db(),uid,unionid,queryid )

        if score:
            score = score['score']
        else:
            score = 0
        if score == 0:
            data['energy'] = 0
            data['effects'] = 1
            return self.write_json(error.OK, data)
        score = 0 if not score else score
        count = union_model.save_cs_log( self.share_db(),unionid,uid,score,queryid )
        print('提取抽水记录%d' % count)
        return self.write_json(error.OK, data)

from controllers import base_handler
class TestOK(base_handler.BaseHandler):

    def prepare(self):
        pass

    def get(self):
        return self._request()

    def post(self):
        return self._request()

    def _request(self):
        # self.publish(2,1,{'gettables':100},9999)
        #self.publish(2,2,{'union_id':10000,'uid':801012,'selfuid':801012},9999)
        self.publish(2,5,{'union_id':10000,'uid':801012,'selfuid':801012,'type':5},9999)
        return self.write('ok')


#查询抽水排行榜
class QueryUnionCSList(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))

        unionid = int(params["unionid"])
        uid = int(params["uid"])
        valdiff = int(params["valdiff"]) or 0
        info = union_model.get_union_userinfo_by_uid(self.share_db(), self.uid)
        if not info or info["permission"] not in (
                UNION_MANAGER,):
            return self.write_json(error.ACCESS_DENNY)
        data = union_model.query_union_cs_list(self.share_db(),unionid,valdiff)

        return self.write_json(error.OK, data)


# 大盟主增加自己能量
class UnionManagerAddEnergy(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))

        if "count" not in params:
            return self.write_json(error.DATA_BROKEN)

        count = int(params["count"])
        if count <= 0:
            return self.write_json(error.DOU_COUNT_ERROR)

        info = union_model.get_union_userinfo_by_uid(self.share_db(), self.uid)
        if not info or info["permission"] not in (
                UNION_MANAGER, ):
            return self.write_json(error.ACCESS_DENNY)

        #
        union_id = info['union_id']
        union_model.add_energy(self.share_db(), union_id, self.uid, count)

        # 能量记录
        union_model.write_energy_log(self.share_db_logs(), union_id, self.uid,
                                     info['energy'] + info['lock_energy'], count,
                                     const.REASON_UNION_ADD, self.uid, count + int(info['energy']) + int(info['lock_energy']))

        now_dou = count + int(info['energy']) + int(info['lock_energy'])
        self.broad_cast_user([self.uid],
                             {"type": const.USER_CHANGE_DOU,
                              "data":
                                  {"dou": count, "nowDou": now_dou, "byUid": self.uid}
                              })

        return self.write_json(error.OK)
