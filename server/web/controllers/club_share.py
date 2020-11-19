# coding:utf-8

from .comm_handler import CommHandler
from models import club_model, player_model

VERIFY = 0
CAN_JOIN_CLUB = 1
ALREADY_JOIN_CLUB = 2
NO_CLUB_OR_NO_USER = 3


class ClubShareHandler(CommHandler):
    def prepare(self):
        pass

    def get(self):
        return self._request()

    def post(self):
        return self._request()

    def _request(self):
        union = self.get_string('u') or ""
        club_info = self.get_string('c') or ""
        club_id = ""
        club_name = ""
        club_config = ""
        club_host = ""
        host_img = ""

        status = NO_CLUB_OR_NO_USER

        db_player = False
        player_login = False

        club = player = None

        if club_info:
            club = club_model.get_club(self.share_db(), club_info)
            if club:
                club_id = club['id']
                club_name = club['name']
                club_config = club['play_config']
                host = player_model.get_by_uid(self.share_db(), club['uid'])  # 群主
                club_host = host['nick_name']
                host_img = host['avatar']

        # 检测是否有 unionid
        if union:
            player = player_model.get_by_unionid(self.share_db(), union)
            if player:  # 检测是否有用户
                db_player = True
                player_login = (player['login_time'] != 0)  # 检测用户是否登录过

        # 检测是否在俱乐部 & 俱乐部审核
        if club and player:
            already = club_model.get_club_by_uid_and_club_id(self.share_db(), player['uid'], club['id'])
            if already:
                status = ALREADY_JOIN_CLUB
            else:
                verify_data = club_model.get_verify_list_by_uid(self.share_db(), club['id'], player['uid'])
                if verify_data and len(verify_data) > 0:
                    status = VERIFY
                else:
                    status = CAN_JOIN_CLUB

        if self.request.path.endswith('.json'):
            if status == CAN_JOIN_CLUB:
                club_model.update_user_verify(self.share_db(), player['uid'], club['id'], 0)  # 添加一条申请记录
            self.redirect("/clubShare?u=" + union + "&c=" + club_info)
        else:
            outputs = dict()
            outputs['player'] = db_player
            outputs['player_login'] = player_login
            outputs['status'] = status
            outputs['host_img'] = host_img
            outputs['club_host'] = club_host
            outputs['club_id'] = club_id
            outputs['club_name'] = club_name
            outputs['club_config'] = club_config
            outputs['token'] = union
            self.render('club_share.html', **outputs)
