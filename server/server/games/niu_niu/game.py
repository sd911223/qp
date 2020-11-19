# coding:utf-8
import random

from base import const
from base import error
from base.base_game import BaseGame
from games.niu_niu import commands_game
from games.niu_niu import flow
from games.niu_niu.judge import Judge
from games.niu_niu.player import Player
from models import club_model, database, onlines_model
from models import configs_model
from models import lottery_model
from models import tables_model
from protocol import channel_protocol
from utils import utils


class GameServer(BaseGame):
    def __init__(self):
        BaseGame.__init__(self)
        self.__lottery_8 = []  # 8局红包集合
        self.__lottery_16 = []  # 16局红包集合
        self._add_handlers({
            commands_game.ENTER_ROOM: self.__on_player_join,
            commands_game.EXIT_ROOM: self.__on_exit_room,
            commands_game.OWNER_DISMISS: self.__on_owner_dismiss,
            commands_game.READY: self.__on_player_ready,
            commands_game.GAME_START: self.__on_player_game_start,
            commands_game.CALL_DEALER: self.__on_player_call_dealer,
            commands_game.CALL_SCORE: self.__on_player_call_score,
            commands_game.SHOW_CARDS: self.__on_player_show_cards,
            commands_game.REQUEST_DISMISS: self.__on_request_dismiss,
            commands_game.CLIENT_BROAD_CAST: self.__on_client_broad_cast,
            commands_game.SUBMIT_LOTTERY: self.__on_submit_lottery,
            commands_game.REQUEST_POSITION: self.__on_request_position,
            commands_game.FORCE_DISMISS: self.__on_force_dismiss,
            commands_game.ROOM_LIST: self.__on_room_list,
            commands_game.ADD_ROOM: self.__add_room,
            commands_game.PLAY_CONFIG_CHANGE: self.__on_play_config_change,
            commands_game.PLAYER_FAN_CARD: self.__fan_card,
            commands_game.CLUB_FORCE_DISMISS: self.__club_force_dismiss,
            commands_game.UNION_GAME_PLAY_CONFIG_CHANGE: self.__on_union_play_config_change,
        })

    def __on_submit_lottery(self, uid, _):
        check_pass, p, judge = self.check_in_table(uid, commands_game.SUBMIT_LOTTERY)
        if not check_pass:
            return
        code, diamond = judge.player_lottery(uid)
        if code != error.OK:
            return self.response_fail(uid, commands_game.SUBMIT_LOTTERY, code)
        if diamond >= configs_model.get("broadcast_diamond_count", 18):
            # 当大于等于指定数量时，进行全局广播
            data = {"uid": uid, "nickname": p.nick_name, "diamond": diamond, "short_time": 3,
                    "long_time": 10, "type": const.BROAD_CAST_LOTTERY}
            from hall import system
            self.broad_cast(system.BROAD_CAST, data, const.SERVICE_SYSTEM)

    def __on_client_broad_cast(self, uid, data):
        check_pass, p, judge = self.check_in_table(uid, commands_game.CLIENT_BROAD_CAST)
        if not check_pass:
            return
        if not data or not data.get('data'):
            return self.response_fail(uid, commands_game.CLIENT_BROAD_CAST, error.DATA_BROKEN)
        # detail = data.get('data')
        # if detail.get('action') == 'chat' and detail.get('faceID') and detail.get('toSeatID'):
        #     judge.emotion_stat(p.uid, detail)
        result = channel_protocol.packet_client_body({"uid": p.uid, "data": data['data']}, error.OK)
        judge.broad_cast(commands_game.CLIENT_BROAD_CAST, result)

    def __on_player_ready(self, uid, _):
        check_pass, p, judge = self.check_in_table(uid, commands_game.READY)
        if not check_pass:
            return
        flag = judge.player_ready(p)
        if not flag:
            return
        data = {"seatID": p.seat_id, "isPrepare": p.is_ready}
        body = channel_protocol.packet_client_body(data, error.OK)
        judge.broad_cast(commands_game.READY, body)
        return judge.try_start_round()

    def __on_player_call_score(self, uid, data):
        check_pass, p, judge = self.check_in_table(uid, commands_game.CALL_SCORE)
        if not check_pass:
            return
        if judge.flow_status != flow.T_IN_CALL_SCORE:
            return self.response_fail(uid, commands_game.CALL_SCORE, error.NOT_YOUR_TURN)
        score = data["score"]
        if not score or p.in_can_call_score(score) is False:
            return self.response_fail(uid, commands_game.CALL_SCORE, error.DATA_BROKEN)
        code = judge.player_call_score(p, score)
        if code != error.OK:
            return self.response_fail(uid, commands_game.CALL_SCORE, code)
        judge.check_all_call_score()

    def __on_player_call_dealer(self, uid, data):
        check_pass, p, judge = self.check_in_table(uid, commands_game.CALL_DEALER)
        if not check_pass:
            return
        if judge.flow_status != flow.T_IN_DEALER:
            return self.response_fail(uid, commands_game.CALL_DEALER, error.NOT_YOUR_TURN)
        score = data["score"]
        if score < 0 or score > judge.max_qiang:
            return self.response_fail(uid, commands_game.CALL_DEALER, error.DATA_BROKEN)
        code = judge.player_call_dealer(p, score)
        if code != error.OK:
            return self.response_fail(uid, commands_game.CALL_DEALER, code)
        judge.check_all_call_dealer()

    def __on_player_game_start(self, uid, _):
        check_pass, p, judge = self.check_in_table(uid, commands_game.GAME_START)
        if not check_pass:
            return
        if judge.status != flow.T_IDLE:
            return self.response_fail(uid, commands_game.GAME_START, error.NOT_YOUR_TURN)
        # if p.seat_id != 1:
        #     return self.response_fail(uid, commands_game.GAME_START, error.NOT_YOUR_TURN)
        return judge.try_start_game()

    def __on_player_show_cards(self, uid, _):
        check_pass, p, judge = self.check_in_table(uid, commands_game.SHOW_CARDS)
        if not check_pass:
            return
        if judge.flow_status != flow.T_IN_KAI_PAI:
            return self.response_fail(uid, commands_game.SHOW_CARDS, error.NOT_YOUR_TURN)
        if p.is_show_cards:
            return self.response_fail(uid, commands_game.SHOW_CARDS, error.DATA_BROKEN)
        code = judge.player_show_cards(p)
        if code != error.OK:
            return self.response_fail(uid, commands_game.SHOW_CARDS, code)
        judge.check_all_show_cards()

    def __on_owner_dismiss(self, uid, data):
        if not data or "roomID" not in data:
            check_pass, p, judge = self.check_in_table(uid, commands_game.OWNER_DISMISS)
            if not check_pass:
                return
        else:
            room_id = data["roomID"]
            if not room_id:
                return self.response_fail(uid, commands_game.OWNER_DISMISS, error.DATA_BROKEN)

            judge = self.fetch_judge(Judge, Player, room_id)
            if not judge:
                return self.response_fail(uid, commands_game.OWNER_DISMISS, error.TABLE_NOT_EXIST)

        if judge.owner != uid:
            return self.response_fail(uid, commands_game.OWNER_DISMISS, error.NOT_YOUR_ROOM)

        code = self.do_owner_dismiss(judge, 0)
        if code != error.OK:
            return self.response_fail(uid, commands_game.OWNER_DISMISS, code)

        return self.response_ok(uid, commands_game.OWNER_DISMISS, {"roomID": judge.tid})

    def __on_force_dismiss(self, uid, data):
        room_id = data.get('roomID')
        if not room_id:
            return self.response_fail(uid, commands_game.FORCE_DISMISS, error.DATA_BROKEN)

        judge = self.get_judge(room_id)
        if not judge:
            return self.response_fail(uid, commands_game.FORCE_DISMISS, error.TABLE_NOT_EXIST)

        if judge.owner != uid:
            return self.response_fail(uid, commands_game.FORCE_DISMISS, error.NOT_YOUR_ROOM)

        judge.force_dismiss()
        return self.response_ok(uid, commands_game.FORCE_DISMISS, {"roomID": judge.tid})

    def __on_room_list(self, uid, _):
        tables = tables_model.get_all_by_owner(uid)
        table_data = []
        for table in tables:
            tid = table.get('tid')
            game_table = self.__get_judge(tid)
            cache_data = tables_model.get_table_info(tid) or {
                "player_list": [],
                "round_index": 1,
                "table_status": flow.T_IDLE
            }
            if not cache_data and not game_table:
                continue
            table.update(cache_data)
            table_data.append(table)

        return self.response_ok(uid, commands_game.ROOM_LIST, {"tables": table_data})

    def __add_room(self, uid, data):
        if not data:
            return self.response_fail(uid, commands_game.ADD_ROOM, error.DATA_BROKEN)

        room_id = data["roomID"]
        if not room_id:
            return self.response_fail(uid, commands_game.ADD_ROOM, error.DATA_BROKEN)

        table = tables_model.get(room_id)
        if not table:
            return self.response_fail(uid, commands_game.ADD_ROOM, error.TABLE_NOT_EXIST)

        cache_data = tables_model.get_table_info(room_id) or {
            "is_del": 0,
            "player_list": [],
            "round_index": 1,
            "table_status": flow.T_IDLE
        }

        table.update(cache_data)

        return self.response_ok(uid, commands_game.ADD_ROOM, {"tables": {room_id: table}})

    def __on_request_dismiss(self, uid, data):
        check_pass, p, judge = self.check_in_table(uid, commands_game.REQUEST_DISMISS)
        if not check_pass:
            return
        is_agree = bool(data.get('agree'))
        judge.player_request_dismiss(p, is_agree)

    def __on_player_join(self, uid, data):  # 处理玩家进入房间
        if not data or not data.get("_client"):
            return
        session = utils.ObjectDict(data.get("_client"))
        if not session.verified:
            return self.response_fail(uid, commands_game.ENTER_ROOM, error.DATA_BROKEN)

        tid = int(data.get('roomID'))
        if not tid or 0 >= tid:  # 玩家没有待处理的进入操作
            return self.response_fail(uid, commands_game.ENTER_ROOM, error.DATA_BROKEN)

        online = onlines_model.get_by_uid(uid)
        if online and online['tid'] != 0 and online['tid'] != tid:
            return self.response_fail(uid, commands_game.ENTER_ROOM, error.IN_OTHER_ROOM)

        info = tables_model.get_by_server(self.server_id, tid)
        if not info:
            return

        p = self.get_player(uid)
        re_connect = False
        if not p:
            p = Player(uid)
            self.save_player(p)
        else:
            re_connect = True
        p.session = session
        p.static_data = data.get('data')
        p.set_position(data.get('x'), data.get('y'))
        is_re_enter_room = p.tid > 0 and p.tid == tid

        if not is_re_enter_room and info['club_id'] != -1:
            user_data = club_model.get_club_by_uid_and_club_id(database.share_db(), info['club_id'], uid)
            if not user_data:
                return self.response_fail(uid, commands_game.ENTER_ROOM, error.NOT_CLUB_MEMBER)

            club = club_model.get_club(database.share_db(), info['club_id'])
            if club and club['lock_status'] is 1:
                return self.response_fail(uid, commands_game.ENTER_ROOM, error.SYSTEM_ERROR)

        if p.tid > 0 and p.tid != tid:  # 玩家已经在其它房间中
            return self.response_fail(uid, commands_game.ENTER_ROOM, error.IN_OTHER_ROOM)

        judge = self.fetch_judge(Judge, Player, tid)
        if not judge:
            return self.response_fail(uid, commands_game.ENTER_ROOM, error.TABLE_NOT_EXIST)

        if info['club_id'] != -1 and info['match_type'] == 1:
            code = judge.enter_match_score(p, info['club_id'])
            if code is not error.OK:
                return self.response_fail(uid, commands_game.ENTER_ROOM, code)

        if info['union_id'] != -1:
            code = judge.enter_union_energy(p, info['union_id'])
            if code is not error.OK:
                return self.response_fail(uid, commands_game.ENTER_ROOM, code)

        self.__do_join_room(judge, p, uid, re_connect, is_re_enter_room)

    def __on_request_position(self, uid, _):
        check_pass, p, judge = self.check_in_table(uid, commands_game.REQUEST_POSITION)
        if not check_pass:
            return
        data = []
        self.response(uid, commands_game.REQUEST_POSITION, {"distances": data})

    def __do_join_room(self, judge: Judge, p: Player, uid, re_connect, is_re_enter_room):
        offline = p.offline
        code, result = judge.player_join(p, is_re_enter_room)
        re_connect_line = re_connect and offline != p.offline
        self.response(uid, commands_game.ENTER_ROOM, result, code)
        if code != error.OK:
            return
        self.response(uid, commands_game.PLAYER_COUNT, {'totalSeat': judge.player_total_count_in_config()}, 0)
        self.__notify_room_info(judge, p, uid, code, is_re_enter_room)
        if re_connect_line:
            judge.player_connect_changed(p)
        if code != error.OK:
            return
        judge.notify_distance()
        return judge.try_start_game()

    def __notify_room_info(self, judge, player, uid, code, is_re_enter_room):
        if code != error.OK:
            return

        data = player.get_all_data(judge.detail_type)
        self.response(uid, commands_game.PLAYER_ENTER_ROOM, data)

        items = judge.get_all_player_info()
        for item in items:  # 发送所有房间内的其它玩家数据给当前玩家
            if uid == item.get('uid'):
                continue
            self.response(uid, commands_game.PLAYER_ENTER_ROOM, item)

        data = player.get_all_public_data(judge.detail_type)
        body = channel_protocol.packet_client_body(data, error.OK)
        if not is_re_enter_room:
            judge.broad_cast(commands_game.PLAYER_ENTER_ROOM, body, uid)

        self.response(uid, commands_game.ROOM_CONFIG, judge.get_info())
        if judge.in_dismiss:
            self.response(uid, commands_game.REQUEST_DISMISS, judge.make_dismiss_data())

    def __get_judge(self, tid: int) -> Judge:
        """ 查找桌子 """
        return self.judges.get(tid)

    def __del_judge(self, judge: Judge):
        """ 删除桌子 """
        try:
            del self.judges[judge.tid]
        except Exception as ex:
            print(ex)
        for k, v in list(self.judges.items()):
            if v == judge or not v:
                del self.judges[k]

    def __on_exit_room(self, uid, _):
        # 玩家退出当前桌
        check_pass, p, judge = self.check_in_table(uid, commands_game.EXIT_ROOM)
        if not check_pass:
            return

        code, result = judge.player_quit(p, const.QUIT_NORMAL)

        judge.broad_cast(commands_game.EXIT_ROOM, result)
        self.send_data_to_player(p.uid, commands_game.EXIT_ROOM, result, code)  # 玩家退出桌子之后广播无法到达玩家，所以这里直接用玩家发送一次
        if code == error.OK:
            self.__clear_player(p)

    def __on_play_config_change(self, uid, data):
        if uid is not 1:
            return
        if 'clubID' not in data or 'type' not in data or 'floor' not in data:
            return
        change_type = data['type']
        club_id = data['clubID']
        floor = data['floor']

        tables = []
        if change_type in (const.MODIFY_FLOOR, const.DEL_FLOOR,):
            tables = tables_model.query_table_with_not_start_and_floor(floor)
        elif change_type in (const.DEL_SUB_FLOOR, const.MODIFY_SUB_FLOOR,):
            tables = tables_model.query_table_with_not_start_and_sub_floor(floor)

        for t in tables:
            tables_model.remove(t['tid'])
            judge = self.get_judge(t['tid'])
            if judge:
                judge.change_config = True
                self.do_owner_dismiss(judge, 0)
        self.club_auto_create_table_by_count(floor, False)
        self.club_room_change_broad_cast(club_id)
        return

    def __fan_card(self, uid, _):
        if not uid:
            return
        p = self.get_player(uid)
        if not p:
            return
        judge = self.get_judge(p.tid)
        if not judge:
            return

        judge.fan_card(p)

    def on_player_connection_change(self, uid, offline):
        """ 玩家断线时的响应 """
        if not uid:
            return
        p = self.get_player(uid)
        if not p:
            return
        if p.tid <= 0:
            self.del_player(p)
        is_offline = offline == 1
        if p.offline == is_offline:
            return
        p.offline = is_offline
        judge = self.get_judge(p.tid)
        if not judge:
            return
        judge.player_connect_changed(p)

    def do_lottery(self, total_round):
        if total_round == 8:
            if len(self.__lottery_8) == 0:
                self.__lottery_8 = lottery_model.make_lottery(8)
            lotteries = self.__lottery_8
        else:
            if len(self.__lottery_16) == 0:
                self.__lottery_16 = lottery_model.make_lottery(16)
            lotteries = self.__lottery_16
        rnd = random.randint(0, len(lotteries) - 1)
        diamond = lotteries[rnd]
        del lotteries[rnd]
        return diamond

    # 玩家退出房间时清理
    def __clear_player(self, p):
        if not p or not self.players.get(p.uid):
            return
        p.tid = 0  # 清除桌子数据
        if p.offline:
            self.del_player(p)

    @staticmethod
    def do_owner_dismiss(judge, reason):
        if judge.status != flow.T_IDLE:  # 只有空闲中的桌子才允许直接解散
            return error.COMMAND_DENNY
        judge.broad_cast(commands_game.OWNER_DISMISS, {"reason": reason, "code": error.OK})
        judge.owner_dismiss()
        return error.OK

    def __club_force_dismiss(self, uid, data):
        room_id = data["roomID"]
        if not room_id:
            return self.response_fail(uid, commands_game.CLUB_FORCE_DISMISS, error.DATA_BROKEN)

        judge = self.fetch_judge(Judge, Player, room_id)
        if not judge:
            return self.response_fail(uid, commands_game.CLUB_FORCE_DISMISS, error.TABLE_NOT_EXIST)

        if judge.club_id == -1:
            return self.response_fail(uid, commands_game.CLUB_FORCE_DISMISS, error.NOT_YOUR_ROOM)

        user_data = club_model.get_club_by_uid_and_club_id(database.share_db(), judge.club_id, uid)
        if not user_data or user_data['permission'] not in (0, 1,):
            return self.response_fail(uid, commands_game.CLUB_FORCE_DISMISS, error.NOT_YOUR_ROOM)

        judge.force_dismiss()
        return self.response_ok(uid, commands_game.CLUB_FORCE_DISMISS, {"roomID": judge.tid})

    def __on_union_play_config_change(self, uid, data):
        print("__on_union_play_config_change")
        if uid is not 1:
            return
        if 'unionID' not in data or 'type' not in data or 'floor' not in data:
            return
        change_type = data['type']
        union_id = data['unionID']
        floor = data['floor']

        tables = []
        if change_type in (const.MODIFY_FLOOR, const.DEL_FLOOR,):
            tables = tables_model.query_table_with_not_start_and_floor(floor)
        elif change_type in (const.DEL_SUB_FLOOR, const.MODIFY_SUB_FLOOR,):
            tables = tables_model.query_table_with_not_start_and_sub_floor(floor)

        for t in tables:
            tables_model.remove(t['tid'])
            judge = self.get_judge(t['tid'])
            if judge:
                judge.change_config = True
                self.do_owner_dismiss(judge, 0)
        self.union_auto_create_table_by_count(floor, False)
        self.union_room_change_broad_cast(union_id)
        return

    @staticmethod
    def share_server():
        return GameServer()
