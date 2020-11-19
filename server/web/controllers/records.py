# coding:utf-8

import tornado

from configs import error
from models import base_redis
from models import logs_model
from models import player_model
from models import qcloud_cos
from utils import utils
from .base_handler import BaseHandler


class RePlayDetailsHandler(BaseHandler):
    def prepare(self):
        if not self.check_fixed_params(True):
            return self.write_json(error.DATA_BROKEN)
        if not self.check_sign():
            return self.write_json(error.SIGN_FAIL)

    def get(self):
        return self._request()

    def post(self):
        return self._request()

    @tornado.web.asynchronous
    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))
        if not params or not params.get('roundID'):
            return self.write_json(error.DATA_BROKEN)

        if not self.share_db_logs():
            return self.write_json(error.SYSTEM_ERR)

        round_id = int(params.get('roundID', 0))
        info = logs_model.get_round_log(self.share_db_logs(), round_id)
        resource_path = info.get("resource_path", "")
        if info and resource_path:
            url = qcloud_cos.make_down_url(resource_path)

            def suc_func(response):
                data = utils.json_decode(response)
                return self.write_json(error.OK, {"details": data.get('commands'),
                                                  "gameType": info.get("game_type", 0)})

            def fail_func():
                return self.write_json(error.OK, {"details": []})

            if url:
                utils.http_get(url, suc_func, fail_func)
                return

        details = self.__get_round_details_in_redis(round_id)
        return self.write_json(error.OK, {"details": details, "gameType": info.get("game_type", 0)})

    @staticmethod
    def __get_round_details_in_redis(round_id):
        if not round_id:
            return []
        all_data = base_redis.get_all_play_details()
        if not all_data:
            return []
        for item in all_data:
            data = utils.json_decode(item)
            if not data:
                continue
            if data.get('round_id', 0) == round_id:
                return data.get('commands')
        return []


class MakeReviewCodeHandler(BaseHandler):
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
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))
        if not params or not params.get('roundID'):
            return self.write_json(error.DATA_BROKEN)

        if not self.share_db_logs():
            return self.write_json(error.SYSTEM_ERR)

        round_id = int(params.get('roundID', 0))
        round_info = logs_model.get_round_log(self.share_db_logs(), round_id)
        if not round_info:
            return self.write_json(error.DATA_BROKEN)
        share_code = round_info.get("share_code", 0) or 0
        if share_code <= 0:
            share_code = int(utils.get_random_num(6))
            logs_model.set_round_share_code(self.share_db_logs(), round_id, share_code)
        return self.write_json(error.OK, {"reviewCode": share_code})


class GetDetailsResultHandler(BaseHandler):
    def prepare(self):
        if not self.check_fixed_params(True):
            return self.write_json(error.DATA_BROKEN)
        if not self.check_sign():
            return self.write_json(error.SIGN_FAIL)

    def get(self) -> object:
        return self._request()

    def post(self):
        return self._request()

    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))
        if not params or not params.get('recordId'):
            return self.write_json(error.DATA_BROKEN)

        if not self.share_db_logs():
            return self.write_json(error.SYSTEM_ERR)

        record_id = params.get('recordId')
        data = logs_model.get_game_finish_data_by_record_id(self.share_db_logs(), record_id)

        if not data:
            # 此处数据为空 经常报系统错误
            # return self.write_json(error.SYSTEM_ERR)
            return self.write_json(error.OK, data)
        return self.write_json(error.OK, data)


class GetByReviewCodeHandler(BaseHandler):
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
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))
        if not params or not params.get('reviewCode'):
            return self.write_json(error.DATA_BROKEN)

        if not self.share_db_logs():
            return self.write_json(error.SYSTEM_ERR)

        share_code = int(params.get('reviewCode', 0))
        round_info = logs_model.get_round_log_by_share_code(self.share_db_logs(), share_code)
        if not round_info:
            return self.write_json(error.SHARE_CODE_NOT_EXIST)
        room_info = logs_model.get_room_log(self.share_db_logs(), round_info.get('record_id', ''))
        if not room_info:
            return self.write_json(error.SYSTEM_ERR)

        uid1, uid2, uid3, uid4, uid5, uid6, uid7, uid8, uid9, uid10 = room_info.get('uid1', 0), \
                                                                      room_info.get('uid2', 0), \
                                                                      room_info.get('uid3', 0), \
                                                                      room_info.get('uid4', 0), \
                                                                      room_info.get('uid5', 0), \
                                                                      room_info.get('uid6', 0), \
                                                                      room_info.get('uid7', 0), \
                                                                      room_info.get('uid8', 0), \
                                                                      room_info.get('uid9', 0), \
                                                                      room_info.get('uid10', 0)
        name1, name2, name3, name4, name5, name6, name7, name8, name9, name10 = room_info.get('name1', ''), \
                                                                                room_info.get('name2', ''), \
                                                                                room_info.get('name3', ''), \
                                                                                room_info.get('name4', ''), \
                                                                                room_info.get('name5', ''), \
                                                                                room_info.get('name6', ''), \
                                                                                room_info.get('name7', ''), \
                                                                                room_info.get('name8', ''), \
                                                                                room_info.get('name9', ''), \
                                                                                room_info.get('name10', '')
        score1, score2, score3, score4, score5, score6, score7, score8, score9, score10 = round_info.get("score1", 0), \
                                                                                          round_info.get("score2", 0), \
                                                                                          round_info.get("score3", 0), \
                                                                                          round_info.get("score4", 0), \
                                                                                          round_info.get("score5", 0), \
                                                                                          round_info.get("score6", 0), \
                                                                                          round_info.get("score7", 0), \
                                                                                          round_info.get("score8", 0), \
                                                                                          round_info.get("score9", 0), \
                                                                                          round_info.get("score10", 0)
        result = {"roundID": round_info.get("round_id", 0), "gameType": round_info.get("game_type", 0),
                  "seq": round_info.get("seq", 0),
                  "users": [[name1, score1, uid1], [name2, score2, uid2], [name3, score3, uid3], [name4, score4, uid4],
                            [name5, score5, uid5],
                            [name6, score6, uid6],
                            [name7, score7, uid7],
                            [name8, score8, uid8],
                            [name9, score9, uid9],
                            [name10, score10, uid10],
                            ],
                  "time": round_info.get("finish_time", 0), }
        return self.write_json(error.OK, result)


class PlayRoomListHandler(BaseHandler):
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
        if not self.share_db_logs():
            return self.write_json(error.SYSTEM_ERR)

        params = utils.json_decode(self.get_string('params'))
        if not params:
            return self.write_json(error.DATA_BROKEN)

        club_id = params.get('clubID')
        if not club_id:
            club_id = -1

        info = logs_model.get_room_list(self.share_db_logs(), self.uid, club_id)
        result = {"rooms": []}
        for row in info:
            result['rooms'].insert(0, {"recordID": row.record_id, "isAgent": row.is_agent,
                                       "agentName": row.agent_name,
                                       "roomID": row.room_id, "gameType": row.game_type, "time": row.finish_time,
                                       "users": [[row.name1, row.score1, row.uid1, row.avatar1 or ""],
                                                 [row.name2, row.score2, row.uid2, row.avatar2 or ""],
                                                 [row.name3, row.score3, row.uid3, row.avatar3 or ""],
                                                 [row.name4, row.score4, row.uid4, row.avatar4 or ""],
                                                 [row.name5, row.score5, row.uid5, row.avatar5 or ""],
                                                 [row.name6, row.score6, row.uid6, row.avatar6 or ""],
                                                 [row.name7, row.score7, row.uid7, row.avatar7 or ""],
                                                 [row.name8, row.score8, row.uid8, row.avatar8 or ""],
                                                 [row.name9, row.score9, row.uid9, row.avatar9 or ""],
                                                 [row.name10, row.score10, row.uid10, row.avatar10 or ""],
                                                 ], })
        return self.write_json(error.OK, result)


class PlayRoomListWithClubAndTimeHandler(BaseHandler):
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
        if not self.share_db_logs():
            return self.write_json(error.SYSTEM_ERR)

        params = utils.json_decode(self.get_string('params'))
        if not params:
            return self.write_json(error.DATA_BROKEN)

        club_id = params.get('clubID')
        uid = params.get('uid')
        if not club_id or not uid:
            return self.write_json(error.DATA_BROKEN)

        start_time = utils.timestamp_today()
        end_time = utils.timestamp_tomorrow() - 1
        info = logs_model.get_room_list_with_club_id_and_time(self.share_db_logs(), uid, club_id, start_time, end_time)
        result = {"rooms": []}
        for row in info:
            result['rooms'].insert(0, {"recordID": row.record_id, "isAgent": row.is_agent,
                                       "agentName": row.agent_name,
                                       "roomID": row.room_id, "gameType": row.game_type, "time": row.finish_time,
                                       "users": [[row.name1, row.score1, row.uid1, row.avatar1 or ""],
                                                 [row.name2, row.score2, row.uid2, row.avatar2 or ""],
                                                 [row.name3, row.score3, row.uid3, row.avatar3 or ""],
                                                 [row.name4, row.score4, row.uid4, row.avatar4 or ""],
                                                 [row.name5, row.score5, row.uid5, row.avatar5 or ""],
                                                 [row.name6, row.score6, row.uid6, row.avatar6 or ""],
                                                 [row.name7, row.score7, row.uid7, row.avatar7 or ""],
                                                 [row.name8, row.score8, row.uid8, row.avatar8 or ""],
                                                 [row.name9, row.score9, row.uid9, row.avatar9 or ""],
                                                 [row.name10, row.score10, row.uid10, row.avatar10 or ""],
                                                 ], })
        return self.write_json(error.OK, result)


class RoundListHandler(BaseHandler):
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
        if not params or not params.get('recordID'):
            return self.write_json(error.DATA_BROKEN)

        if not self.share_db_logs():
            return self.write_json(error.SYSTEM_ERR)

        record_id = params.get('recordID')
        info = logs_model.get_round_list(self.share_db_logs(), record_id)
        result = {"rounds": []}
        score1 = 0
        score2 = 0
        score3 = 0
        score4 = 0
        score5 = 0
        score6 = 0
        score7 = 0
        score8 = 0
        score9 = 0
        score10 = 0
        uids = dict()
        for row in info:
            score1 = row.score1 - score1
            score2 = row.score2 - score2
            score3 = row.score3 - score3
            score4 = row.score4 - score4
            score5 = row.score5 - score5
            score6 = row.score6 - score6
            score7 = row.score7 - score7
            score8 = row.score8 - score8
            score9 = row.score9 - score9
            score10 = row.score10 - score10
            maxscorelst = [score1,score2,score3,score4,score5,score6,score7,score8,score9,score10]
            for i,uidone in enumerate(maxscorelst):
                if i not in uids:
                    uids[i] = 0
                    uids[i] = uidone
                else:
                    uids[i] = uids[i] + uidone
            # maxscore = max(maxscorelst)
            # maxscorelst.remove(maxscore)
            # maxscorelst.insert(0,maxscore)
            result["rounds"].append(
                {"roundID": row.round_id, "seq": row.seq,
                 "detail": row.round_detail,
                 "scores": maxscorelst ,
                 "time": row.finish_time, })
            game_type = row['game_type']
            if game_type == 66 or game_type == 42:
                score1 = 0
                score2 = 0
                score3 = 0
                score4 = 0
                score5 = 0
                score6 = 0
                score7 = 0
                score8 = 0
                score9 = 0
                score10 = 0
            else:
                score1 = row.score1
                score2 = row.score2
                score3 = row.score3
                score4 = row.score4
                score5 = row.score5
                score6 = row.score6
                score7 = row.score7
                score8 = row.score8
                score9 = row.score9
                score10 = row.score10
        max_value = -99999
        max_index = 0
        for i in uids:
            if uids[i] > max_value:
                max_value = uids[i]
                max_index = i

        for j in result["rounds"]:
            val = j['scores'][max_index]
            j['scores'].pop(max_index)
            j['scores'].insert(0, val)

        return self.write_json(error.OK, result)


class RoundRankHandler(BaseHandler):
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
        if not self.share_db_logs():
            return self.write_json(error.SYSTEM_ERR)

        sql = "SELECT * FROM round_rank_logs ORDER BY count DESC LIMIT 100"
        my_rank = 0
        info = self.share_db_logs().query(sql)
        result = {"list": []}
        rank = 0
        for row in info:
            rank += 1
            if rank <= 20:
                result["list"].append([row.get('uid'), row.get('nickname'), row.get('count')])
            if row.get('uid') == self.uid:
                my_rank = rank
        result["myRank"] = my_rank
        player = player_model.get_by_uid(self.share_db(), self.uid)
        result["phone"] = utils.get_public_phone_number(player)
        return self.write_json(error.OK, result)


class SetPhoneHandler(BaseHandler):
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
        if not self.share_db():
            return self.write_json(error.SYSTEM_ERR)

        params = utils.json_decode(self.get_string('params'))
        if not params or not params.get('phone'):
            return self.write_json(error.DATA_BROKEN)

        phone = params.get('phone', "")
        if len(phone) != 11 or phone[0:1] != "1":
            return self.write_json(error.DATA_BROKEN)

        player_model.set_phone_number(self.share_db(), self.uid, phone)
        return self.write_json(error.OK)
