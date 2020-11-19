# coding:utf-8

from .comm_handler import CommHandler
from models import activity_model
from utils import utils
import base64


class ClubsDataHandler(CommHandler):
    def prepare(self):
        pass

    def get(self):
        return self._request()

    def post(self):
        return self._request()

    def _request(self):

        start_time = self.get_int('startTime') or 1521475200  # 2018-01-31 00:00:00
        end_time = self.get_int('endTime') or 1522339199  # 2018-02-08 23:59:59
        data = activity_model.get_club_room_rank_over_100(self.share_db_logs(), start_time, end_time)
        uid = 0
        try:
            uid = int(base64.b64decode(self.get_string('u')).decode('utf-8'))
        except Exception as e:
            print(e)
        game_room = 0
        if uid is not 0:
            res = activity_model.get_club_room_playing_count_by_uid(self.share_db_logs(), start_time, end_time, uid)
            if res and res['room_count']:
                game_room = res['room_count']
        rank = -1
        count = 1
        bonus = ['<b>588元+412钻石</b>', '<b>488元+312钻石</b>', '288元+312钻石', '188元+212钻石', '168元+132钻石']

        while len(data) > 5:
            data.pop()

        for i in data:
            if i['uid'] == uid:
                rank = count
                continue
            count += 1

        outputs = dict()
        outputs['data'] = data
        outputs['rank'] = rank
        outputs['bonus'] = bonus
        outputs['game_room'] = game_room
        outputs['zhu_shou'] = "ooS"
        self.render('club_rank.html', **outputs)
