# coding:utf-8

import ujson as json
from decimal import Decimal

from configs import error
from models import club_model, club_task_model
from utils import utils
from .comm_handler import CommHandler


def default(obj):
    if isinstance(obj, Decimal):
        return str(obj)
    raise TypeError


class GetClubTask(CommHandler):
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))
        if "clubID" not in params:
            return self.write_json(error.DATA_BROKEN)

        club_id = params['clubID']
        club_info = club_model.query_club_by_uid_and_club_id(self.share_db(), club_id, self.uid)
        if not club_info:
            return self.write_json(error.ACCESS_DENNY)

        club_task = club_task_model.get_club_tasks(self.share_db(), club_id)
        user_task = club_task_model.get_user_club_task(self.share_db(), club_id, self.uid)
        return self.write_json(error.OK, {"clubTask": club_task, "userTask": user_task})


class ModifyClubTask(CommHandler):
    def _request(self):
        params = utils.json_decode(self.get_string('params'))
        if "clubID" not in params:
            return self.write_json(error.DATA_BROKEN)

        club_id = params['clubID']
        club_info = club_model.query_club_by_uid_and_club_id(self.share_db(), club_id, self.uid)
        if not club_info or club_info["permission"] not in (0, 1):
            return self.write_json(error.ACCESS_DENNY)
        task_share = params['taskShare']
        task_today_game_round = params['taskTodayGameRound']
        if "8" not in task_today_game_round or "16" not in task_today_game_round:
            return self.write_json(error.DATA_BROKEN)
        club_task_model.update_club_task(self.share_db(), club_id, task_share, json.dumps(task_today_game_round))
        return self.write_json(error.OK)


class TaskClubShare(CommHandler):
    def _request(self):
        params = utils.json_decode(self.get_string('params'))
        if "clubID" not in params:
            return self.write_json(error.DATA_BROKEN)

        club_id = params['clubID']
        club_info = club_model.query_club_by_uid_and_club_id(self.share_db(), club_id, self.uid)
        if not club_info:
            return self.write_json(error.ACCESS_DENNY)
        club_task_model.modify_user_task_update_time(self.share_db(), club_id, self.uid)
        return self.write_json(error.OK)


class BonusClubTaskShare(CommHandler):
    def _request(self):
        params = utils.json_decode(self.get_string('params'))
        if "clubID" not in params:
            return self.write_json(error.DATA_BROKEN)

        club_id = params['clubID']
        club_info = club_model.query_club_by_uid_and_club_id(self.share_db(), club_id, self.uid)
        if not club_info:
            return self.write_json(error.ACCESS_DENNY)
        club_task = club_task_model.get_club_tasks(self.share_db(), club_id)
        user_task = club_task_model.get_user_club_task(self.share_db(), club_id, self.uid)

        if club_task['task_share'] == 0:
            return self.write_json(error.CLUB_TASK_NOT_OPEN)

        if user_task['bonus_share_time'] > utils.timestamp_today():
            return self.write_json(error.CLUB_TASK_ALREADY_RECEIVE)

        if user_task['share_time'] < utils.timestamp_today():
            return self.write_json(error.CLUB_TASK_NOT_FINISH)

        bonus_diamond = 2
        club_task_model.bonus_user(self.share_db(), self.uid, bonus_diamond)
        club_task_model.update_bonus_user_time(self.share_db(), club_id, self.uid)
        return self.write_json(error.OK, {"diamond": bonus_diamond})


class BonusClubTaskRound(CommHandler):
    def _request(self):
        params = utils.json_decode(self.get_string('params'))
        if "clubID" not in params:
            return self.write_json(error.DATA_BROKEN)

        club_id = params['clubID']
        club_info = club_model.query_club_by_uid_and_club_id(self.share_db(), club_id, self.uid)
        if not club_info:
            return self.write_json(error.ACCESS_DENNY)

        round_count_bonus = params['round']

        # 如果当前时间在今天0点2分内 (不可能达到目标) 直接返回错误
        if utils.timestamp() <= utils.timestamp_today() + 120:
            return self.write_json(error.CLUB_TASK_NOT_FINISH)

        club_task = club_task_model.get_club_tasks(self.share_db(), club_id)
        user_task = club_task_model.get_user_club_task(self.share_db(), club_id, self.uid)

        # 获取俱乐部配置
        club_game_round = json.loads(club_task['task_today_game_round'])
        round_count_list = []
        if str(round_count_bonus) in club_game_round and club_game_round[str(round_count_bonus)] == 1:
            round_count_list.append(str(round_count_bonus))

        player_game_round = json.loads(user_task['bonus_today_game_round'])
        if str(round_count_bonus) in player_game_round:
            return self.write_json(error.CLUB_TASK_ALREADY_RECEIVE)

        if str(round_count_bonus) not in round_count_list:
            return self.write_json(error.CLUB_TASK_NOT_OPEN)

        if user_task['today_game_round'] < round_count_bonus:
            return self.write_json(error.CLUB_TASK_NOT_FINISH)

        player_game_round[str(round_count_bonus)] = utils.timestamp()
        bonus_diamond = self._calc_bonus(round_count_bonus)
        club_task_model.update_user_today_game_round(self.share_db(), club_id, self.uid, json.dumps(player_game_round))
        club_task_model.bonus_user(self.share_db(), self.uid, bonus_diamond)
        return self.write_json(error.OK, {"round": round_count_bonus, "diamond": bonus_diamond})

    def _calc_bonus(self, round_count):
        if round_count >= 16:
            return 3
        if round_count >= 8:
            return 2
        return 1
