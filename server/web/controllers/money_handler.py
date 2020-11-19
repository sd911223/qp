# coding:utf-8

from configs import error, const
from .comm_handler import CommHandler
from utils import utils
from models import club_model
from models import money_model
import ujson as json


def default(obj):
    if isinstance(obj, Decimal):
        return str(obj)
    raise TypeError


class IncreaseDou(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)
        return

        params = utils.json_decode(self.get_string('params'))

        if "clubID" not in params or "uid" not in params or "count" not in params:
            return self.write_json(error.DATA_BROKEN)

        count = int(params["count"])

        # 最大赠送数量不能超过 100000
        if count > 100000 or count <= 0:
            return self.write_json(error.DOU_COUNT_ERROR)

        club_id = params["clubID"]
        club_info = club_model.query_club_by_uid_and_club_id(self.share_db(), club_id, self.uid)
        if not club_info or club_info["permission"] not in (0, 1):
            return self.write_json(error.ACCESS_DENNY)

        score = money_model.get_dou_by_uid_and_club_id(self.share_db(), params['clubID'], params['uid'])
        if not score:
            return self.write_json(error.DATA_BROKEN)

        # 此用户超过100万豆
        if score['score'] >= 1000000:
            return self.write_json(error.OVER_100W_DOU)

        money_model.transfer_dou(self.share_db(), params["clubID"], params["uid"], count)
        money_model.write_transfer_dou_log(self.share_db_logs(), params["clubID"], params['uid'],
                                           score['score'] + score['lock_score'], count,
                                           const.REASON_CLUB_ADD, self.uid)

        # 下发玩家目前的豆数量
        now_dou = count + int(score['score'])
        self.broad_cast_user([params['uid']],
                             {"type": const.USER_CHANGE_DOU,
                              "data":
                                  {"dou": count, "nowDou": now_dou, "clubId": params['clubID']}
                              })

        return self.write_json(error.OK)


class ReduceDou(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))

        if "clubID" not in params or 'count' not in params or 'uid' not in params:
            return self.write_json(error.DATA_BROKEN)

        club_info = club_model.query_club_by_uid_and_club_id(self.share_db(), params['clubID'], self.uid)
        if not club_info or club_info["permission"] not in (0, 1):
            return self.write_json(error.ACCESS_DENNY)

        score = money_model.get_dou_by_uid_and_club_id(self.share_db(), params['clubID'], params['uid'])
        if not score:
            return self.write_json(error.DATA_BROKEN)

        count = int(params['count'])

        # 减少豆之前需要检测是否超过当前积分以及锁定积分
        if count <= 0 or (int(score['score']) - int(score['lock_score'])) < count:
            return self.write_json(error.UPGRADE_COUNT_ERROR)

        res = money_model.reduce_player_dou(self.share_db(), params['clubID'], params['uid'], count)
        if res == 0:
            return self.write_json(error.UPGRADE_COUNT_ERROR)

        money_model.write_transfer_dou_log(self.share_db_logs(), params["clubID"], params['uid'],
                                           score['score'] + score['lock_score'], -count,
                                           const.REASON_CLUB_SUB, self.uid)

        # 下发玩家目前的豆数量
        now_dou = int(score['score']) - count
        self.broad_cast_user([params['uid']],
                             {"type": const.USER_CHANGE_DOU,
                              "data":
                                  {"dou": count, "nowDou": now_dou, "clubId": params['clubID']}
                              })
        return self.write_json(error.OK)


class QueryDou(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))

        if "clubID" not in params:
            return self.write_json(error.DATA_BROKEN)

        club_info = club_model.query_club_by_uid_and_club_id(self.share_db(), params['clubID'], self.uid)
        if not club_info:
            return self.write_json(error.ACCESS_DENNY)

        return self.write_json(error.OK, {'dou': club_info['score'], 'lock_score': club_info['lock_score']})


class QueryDouLogs(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))

        if "clubID" not in params:
            return self.write_json(error.DATA_BROKEN)

        data = club_model.query_dou_by_club_id_and_uid(self.share_db_logs(), params['clubID'], self.uid)
        return self.write_json(error.OK, data)


class RechargeConfig(CommHandler):
    def _request(self):
        data = money_model.get_recharge_config(self.share_db(), 2, 3)
        res = json.dumps(data)
        return self.write_json(error.OK, res)
