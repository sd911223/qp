# coding:utf-8
from base import const, error
from base.base_game import BaseGame
from games.cs_ma_jiang import flow
from models import tables_model, club_model, database, onlines_model, players_model, union_model
from protocol import protocol_utils
from utils import utils
from utils.check_params import ParamsCheck
from . import commands_game
from .cs_ma_jiang_judge import CsMaJiangJudge
from .player import Player


class GameServer(BaseGame):

    def __init__(self):
        BaseGame.__init__(self)
        self.__params_checker = ParamsCheck(const.BASE_PATH + "games/cs_ma_jiang/interface.yml").check_params
        self._add_handlers({
            commands_game.ENTER_ROOM: self.__on_player_join,
            commands_game.EXPRESS_ENTER_UNION_ROOM: self.__on_player_join,
            commands_game.EXIT_ROOM: self.__on_exit_room,
            commands_game.AUTO_ATTACK_ONE:self.__auto_attack_one,
            commands_game.OWNER_DISMISS: self.__on_owner_dismiss,
            commands_game.PLAYER_CHU_PAI: self.__on_player_chu_pai,
            commands_game.PLAYER_PASS: self.__on_player_pass,
            commands_game.READY: self.__on_player_ready,
            commands_game.REQUEST_DISMISS: self.__on_request_dismiss,
            commands_game.CLIENT_BROAD_CAST: self.__on_client_broad_cast,
            commands_game.PLAYER_PENG: self.__on_player_peng,
            commands_game.PLAYER_AN_GANG: self.__on_player_an_gang,
            commands_game.PLAYER_MING_GANG: self.__on_player_ming_gang,
            commands_game.PLAYER_GONG_GANG: self.__on_player_gong_gang,
            commands_game.PLAYER_AN_BU: self.__on_player_an_bu,
            commands_game.PLAYER_GONG_BU: self.__on_player_gong_bu,
            commands_game.PLAYER_MING_BU: self.__on_player_ming_bu,
            commands_game.PLAYER_HU_PAI: self.__on_player_hu,
            commands_game.PLAYER_CHI: self.__on_player_chi,
            commands_game.PLAYER_HAI_DI: self.__on_player_hai_di,
            commands_game.GET_MIDDLE_HU: self.__on_get_middle_hu,
            commands_game.DEBUG_SET_CARDS: self.__on_set_cards,
            commands_game.REQUEST_POSITION: self.__on_request_position,
            commands_game.FORCE_DISMISS: self.__on_force_dismiss,
            commands_game.ENTER_ROOM_INFO: self.__on_enter_room_info,
            commands_game.ROOM_LIST: self.__on_room_list,
            commands_game.ADD_ROOM: self.__add_room,
            commands_game.PLAY_CONFIG_CHANGE: self.__on_play_config_change,
            commands_game.PLAYER_PIAO_FEN: self.__on_play_piao_fen,
            commands_game.CLUB_FORCE_DISMISS: self.__club_force_dismiss,
            commands_game.LUCKER_GET_LEFT_CARDS: self.__lucker_get_left_cards,
            commands_game.LUCKER_CHANGE_CARD: self.__lucker_change_card,
            commands_game.UNION_GAME_PLAY_CONFIG_CHANGE: self.__on_union_play_config_change,
            commands_game.UNION_FORCE_DISMISS: self.__union_force_dismiss,
        })

    def __on_enter_room_info(self, uid, _):

        print("__on_enter_room_info")
        check_pass, p, judge = self.check_in_table(uid, commands_game.ENTER_ROOM_INFO)
        if not check_pass:
            return
        items = judge.get_all_player_info()
        for item in items:
            self.response(uid, commands_game.ENTER_ROOM_INFO, item)
        return
    def __auto_attack_one(self,uid,_):
        p = self.get_player(uid)
        if not p:
            return self.response_fail(uid, commands_game.ENTER_ROOM, error.DATA_BROKEN)
        p.is_auto_chupai = False
        p.iscacel_auto_chupai = True
        p.user_operation_timeout = const.Auto_Operation_TimeOut
        self.response_ok( uid,commands_game.AUTO_ATTACK_ONE,{"is_auto_chupai":p.is_auto_chupai})
        if p.operator_out_time:
            p.operator_out_time.cancel()
            p.operator_out_time = None

    def __on_room_list(self, uid, _):
        tables = tables_model.get_all_by_owner(uid)
        table_data = []
        for table in tables:
            tid = table.get('tid')
            game_table = self.get_judge(tid)
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
    def player_ready(self,uid):
        self.__on_player_ready(uid,None)
    def __on_player_ready(self, uid, _):
        check_pass, p, judge = self.check_in_table(uid, commands_game.READY)
        if not check_pass:
            return
        flag = judge.player_ready(p)
        if not flag:
            return
        data = {"seatID": p.seat_id, "isPrepare": p.is_ready}
        body = protocol_utils.pack_client_body(data, error.OK)
        judge.broad_cast(commands_game.READY, body)
        return judge.try_start_game()

    def __on_client_broad_cast(self, uid, data):
        check_pass, p, judge = self.check_in_table(uid, commands_game.CLIENT_BROAD_CAST)
        if not check_pass:
            return
        if not data or not data.get('data'):
            return self.response_fail(uid, commands_game.CLIENT_BROAD_CAST, error.DATA_BROKEN)
        # detail = data.get('data')
        # if detail.get('action') == 'chat' and detail.get('faceID') and detail.get('toSeatID'):
        #     judge.emotion_stat(p.uid, detail)
        result = protocol_utils.pack_client_body({"uid": p.uid, "data": data['data']}, error.OK)
        judge.broad_cast(commands_game.CLIENT_BROAD_CAST, result)

    def on_player_chu_pai(self,uid,data):
        self.__on_player_chu_pai(uid,data)
    def __on_player_chu_pai(self, uid, data):
        check_pass, p, judge = self.check_in_table(uid, commands_game.PLAYER_CHU_PAI)
        if not check_pass:
            return
        if judge.curr_seat_id != p.seat_id:
            return self.response_fail(uid, commands_game.PLAYER_CHU_PAI, error.NOT_YOUR_TURN)

        is_correct, result = self.__params_checker("PLAYER_CHU_PAI", data)
        if not is_correct:
            return self.response_fail(uid, commands_game.PLAYER_CHU_PAI, error.DATA_BROKEN)

        card = result["cards"]

        code = judge.player_chu_pai(p, card)
        if code != error.OK:
            return self.response_fail(uid, commands_game.PLAYER_CHU_PAI, code)
        #self.response_ok( uid,commands_game.AUTO_ATTACK_ONE,{"is_auto_chupai":p.is_auto_chupai})
        judge.enter_chu_pai_call()

    def __on_player_hu(self, uid, _):
        check_pass, p, judge = self.check_in_table(uid, commands_game.PLAYER_HU_PAI)
        if not check_pass:
            return

        code = judge.player_hu(p)
        if code != error.OK:
            return self.response_fail(uid, commands_game.PLAYER_HU_PAI, code)
        judge.check_action_end()

    def __on_player_peng(self, uid, data):
        check_pass, p, judge = self.check_in_table(uid, commands_game.PLAYER_PENG)
        if not check_pass:
            return

        is_correct, result = self.__params_checker("PLAYER_PENG", data)
        if not is_correct:
            return self.response_fail(uid, commands_game.PLAYER_PENG, error.DATA_BROKEN)

        code = judge.player_peng(p, data)
        if code != error.OK:
            return self.response_fail(uid, commands_game.PLAYER_PENG, code)
        judge.check_action_end()

    def __on_player_an_bu(self, uid, data):
        check_pass, p, judge = self.check_in_table(uid, commands_game.PLAYER_AN_BU)
        if not check_pass:
            return

        is_correct, result = self.__params_checker("PLAYER_AN_BU", data)
        if not is_correct:
            return self.response_fail(uid, commands_game.PLAYER_AN_BU, error.DATA_BROKEN)

        code = judge.player_an_bu(p, data)
        if code != error.OK:
            return self.response_fail(uid, commands_game.PLAYER_AN_BU, code)
        judge.check_action_end()

    def __on_player_ming_bu(self, uid, data):
        check_pass, p, judge = self.check_in_table(uid, commands_game.PLAYER_MING_BU)
        if not check_pass:
            return

        is_correct, result = self.__params_checker("PLAYER_MING_BU", data)
        if not is_correct:
            return self.response_fail(uid, commands_game.PLAYER_MING_BU, error.DATA_BROKEN)

        code = judge.player_ming_bu(p, data)
        if code != error.OK:
            return self.response_fail(uid, commands_game.PLAYER_MING_BU, code)
        judge.check_action_end()

    def __on_player_gong_bu(self, uid, data):
        check_pass, p, judge = self.check_in_table(uid, commands_game.PLAYER_GONG_BU)
        if not check_pass:
            return

        is_correct, result = self.__params_checker("PLAYER_GONG_BU", data)
        if not is_correct:
            return self.response_fail(uid, commands_game.PLAYER_GONG_BU, error.DATA_BROKEN)

        code = judge.player_gong_bu(p, data)
        if code != error.OK:
            return self.response_fail(uid, commands_game.PLAYER_GONG_BU, code)
        judge.check_action_end()

    def __on_player_an_gang(self, uid, data):
        check_pass, p, judge = self.check_in_table(uid, commands_game.PLAYER_AN_GANG)
        if not check_pass:
            return

        is_correct, result = self.__params_checker("PLAYER_AN_GANG", data)
        if not is_correct:
            return self.response_fail(uid, commands_game.PLAYER_AN_GANG, error.DATA_BROKEN)

        code = judge.player_an_gang(p, data)
        if code != error.OK:
            return self.response_fail(uid, commands_game.PLAYER_AN_GANG, code)
        judge.check_action_end()

    def __on_player_ming_gang(self, uid, data):
        check_pass, p, judge = self.check_in_table(uid, commands_game.PLAYER_MING_GANG)
        if not check_pass:
            return

        is_correct, result = self.__params_checker("PLAYER_MING_GANG", data)
        if not is_correct:
            return self.response_fail(uid, commands_game.PLAYER_MING_GANG, error.DATA_BROKEN)

        code = judge.player_ming_gang(p, data)
        if code != error.OK:
            return self.response_fail(uid, commands_game.PLAYER_MING_GANG, code)
        judge.check_action_end()

    def __on_player_gong_gang(self, uid, data):
        check_pass, p, judge = self.check_in_table(uid, commands_game.PLAYER_GONG_GANG)
        if not check_pass:
            return

        is_correct, result = self.__params_checker("PLAYER_GONG_GANG", data)
        if not is_correct:
            return self.response_fail(uid, commands_game.PLAYER_GONG_GANG, error.DATA_BROKEN)

        code = judge.player_gong_gang(p, data)
        if code != error.OK:
            return self.response_fail(uid, commands_game.PLAYER_GONG_GANG, code)
        judge.check_action_end()

    def on_player_pass(self,uid,_):
        self.__on_player_pass(uid,_)
    def __on_player_pass(self, uid, _):
        check_pass, p, judge = self.check_in_table(uid, commands_game.PLAYER_PASS)
        if not check_pass:
            return

        code = judge.player_pass(p)
        if code != error.OK:
            return self.response_fail(uid, commands_game.PLAYER_PASS, code)
        #self.response_ok( uid,commands_game.AUTO_ATTACK_ONE,{"is_auto_chupai":p.is_auto_chupai})
        judge.check_action_end()

    def __on_player_chi(self, uid, data):
        check_pass, p, judge = self.check_in_table(uid, commands_game.PLAYER_CHI)
        if not check_pass:
            return

        is_correct, result = self.__params_checker("PLAYER_CHI", data)
        if not is_correct:
            return self.response_fail(uid, commands_game.PLAYER_CHI, error.DATA_BROKEN)

        chi_pai = result['operateCards']
        if not chi_pai or type(chi_pai) is not list or 2 != len(chi_pai):
            return self.response_fail(uid, commands_game.PLAYER_CHI, error.DATA_BROKEN)

        code = judge.player_chi(p, data)
        if code != error.OK:
            return self.response_fail(uid, commands_game.PLAYER_CHI, code)
        judge.check_action_end()

    def __on_player_hai_di(self, uid, data):
        check_pass, p, judge = self.check_in_table(uid, commands_game.PLAYER_HAI_DI)
        if not check_pass:
            return

        is_correct, result = self.__params_checker("PLAYER_HAI_DI", data)
        if not is_correct:
            return self.response_fail(uid, commands_game.PLAYER_HAI_DI, error.DATA_BROKEN)

        code = judge.player_hai_di(p, data)
        if code != error.OK:
            return self.response_fail(uid, commands_game.PLAYER_HAI_DI, code)

    def __on_get_middle_hu(self, uid, _):

        check_pass, p, judge = self.check_in_table(uid, commands_game.PLAYER_HAI_DI)
        if not check_pass:
            return

        judge.get_middle_hu_cards(p)

    def __on_owner_dismiss(self, uid, data):
        if not data or "roomID" not in data:
            check_pass, p, judge = self.check_in_table(uid, commands_game.OWNER_DISMISS)
            if not check_pass:
                return
        else:
            room_id = data["roomID"]
            if not room_id:
                return self.response_fail(uid, commands_game.OWNER_DISMISS, error.DATA_BROKEN)

            judge = self.fetch_judge(CsMaJiangJudge, Player, room_id)
            if not judge:
                return self.response_fail(uid, commands_game.OWNER_DISMISS, error.TABLE_NOT_EXIST)

        if judge.owner != uid:
            return self.response_fail(uid, commands_game.OWNER_DISMISS, error.NOT_YOUR_ROOM)

        code = self.do_owner_dismiss(judge, 0)
        if code != error.OK:
            return self.response_fail(uid, commands_game.OWNER_DISMISS, code)

        return self.response_ok(uid, commands_game.OWNER_DISMISS, {"roomID": judge.tid})

    def __on_request_dismiss(self, uid, data):
        check_pass, p, judge = self.check_in_table(uid, commands_game.REQUEST_DISMISS)
        if not check_pass:
            return
        is_agree = data["agree"]
        is_correct, result = self.__params_checker("REQUEST_DISMISS", data)
        if not is_correct:
            return self.response_fail(uid, commands_game.REQUEST_DISMISS, error.DATA_BROKEN)


        judge.player_request_dismiss(p, is_agree)

    def __on_request_position(self, uid, _):
        check_pass, p, judge = self.check_in_table(uid, commands_game.REQUEST_POSITION)
        if not check_pass:
            return
        data = judge.get_all_distances()
        self.response(uid, commands_game.REQUEST_POSITION, {"distances": data})

    def __on_player_join(self, uid, data):  # 处理玩家进入房间

        if not data or not data.get("_client"):
            return
        session = utils.ObjectDict(data.get("_client"))
        if not session.verified:
            return self.response_fail(uid, commands_game.ENTER_ROOM, error.DATA_BROKEN)

        is_correct, result = self.__params_checker("ENTER_ROOM", data)

        if not is_correct:
            return self.response_fail(uid, commands_game.ENTER_ROOM, error.DATA_BROKEN)

        tid = result["roomID"]

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
        p.static_data = result["data"]
        p.set_position(result["x"], result["y"])
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

        judge = self.fetch_judge(CsMaJiangJudge, Player, tid)
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

    def __do_join_room(self, judge: CsMaJiangJudge, p: Player, uid, re_connect, is_re_enter_room):
        code, result, new_tid = judge.player_join(p)
        re_connect_line = re_connect
        self.response(uid, commands_game.ENTER_ROOM, result, code)
        if code != error.OK:
            return

        # judge.player_ready(p)
        # data = {"seatID": p.seat_id, "isPrepare": p.is_ready}
        # body = channel_protocol.packet_client_body(data, error.OK)
        # judge.broad_cast(commands_game.READY, body)

        self.__notify_room_info(judge, p, uid, code, is_re_enter_room)
        if re_connect_line:
            judge.player_connect_changed(p)

        judge.notify_distance()

        if code != error.OK:
            return
        #如果有人进入桌子，广播消息给客户端
        """如果有人进入桌子，广播消息给客户端"""
        self.publish(2,6,{'union_id':judge.union_id,'uid':uid,'selfuid':p.uid,'type':6,
                          'tid':judge.tid,'subfloor':judge.sub_floor_id,
                          'new_tid': new_tid},9999)
        return judge.try_start_game()

    def __notify_room_info(self, judge, player, uid, code, is_re_enter_room):
        if code != error.OK:
            return
        self.response_ok( uid,commands_game.AUTO_ATTACK_ONE,{"is_auto_chupai":player.is_auto_chupai})
        # 消除相同IP
        judge.avoid_same_ip()
        player_info = judge.get_player_data(player)
        if judge.piao_timer:
            player_info["time"] = judge.piao_timer.left_seconds()
        else:
            player_info["time"] = -1

        new_judge = self.get_judge(player.tid)
        if new_judge.piao_type != 0:
            player_info["piao_data"] = []
            for p in new_judge.seats:
                if not p:
                    continue
                data = {"seat_id": p.seat_id, "score": p.piao_score}
                player_info["piao_data"].append(data)

        self.response(uid, commands_game.PLAYER_ENTER_ROOM, player_info)
        items = judge.get_all_player_info()
        for item in items:  # 发送所有房间内的其它玩家数据给当前玩家
            if uid == item.get('uid'):
                continue
            self.response(uid, commands_game.PLAYER_ENTER_ROOM, item)
        self.response(uid, commands_game.ROOM_CONFIG, judge.get_info())

        result = player.get_all_public_data(judge.status)
        body = protocol_utils.pack_client_body(result, error.OK)
        if not is_re_enter_room:
            judge.broad_cast(commands_game.PLAYER_ENTER_ROOM, body, uid)

        if judge.in_dismiss:
            self.response(uid, commands_game.REQUEST_DISMISS, judge.make_dismiss_data())

    def __on_exit_room(self, uid, data):
        # 玩家退出当前桌
        check_pass, p, judge = self.check_in_table(uid, commands_game.EXIT_ROOM)
        if not check_pass:
            return
        tid = judge.tid
        sub_floor_id = judge.sub_floor_id
        is_correct, _ = self.__params_checker("EXIT_ROOM", data)
        if not is_correct:
            return self.response_fail(uid, commands_game.EXIT_ROOM, error.DATA_BROKEN)

        code, result = judge.player_quit(p, const.QUIT_NORMAL)

        judge.broad_cast(commands_game.EXIT_ROOM, result)
        self.send_data_to_player(p.uid, commands_game.EXIT_ROOM, result, code)  # 玩家退出桌子之后广播无法到达玩家，所以这里直接用玩家发送一次
        if code == error.OK:
            self.clear_player(p)
        # 如果有人退出桌子，广播消息给客户端
        """如果有人退出桌子，广播消息给客户端"""
        self.publish(2,6,{'union_id':judge.union_id,'uid':uid,'selfuid':p.uid,'type':6,
                          'tid':tid,'subfloor':sub_floor_id},9999)

    @staticmethod
    def do_owner_dismiss(judge, reason):
        if judge.status != flow.T_IDLE:  # 只有空闲中的桌子才允许直接解散
            return error.COMMAND_DENNY
        judge.broad_cast(commands_game.OWNER_DISMISS, {"reason": reason, "code": error.OK})
        judge.owner_dismiss()
        return error.OK

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

    def __on_play_piao_fen(self, uid, data):
        check_pass, p, judge = self.check_in_table(uid, commands_game.PIAO_FEN)
        if not check_pass:
            return
        score = data['score']
        if score not in (0, 1, 2, 3, 5):
            return
        p.piao_score = score
        judge.broad_cast(commands_game.PLAYER_PIAO_FEN, {"seat_id": p.seat_id, "score": score})

        flag = True

        for p in judge.seats:
            if not p:
                continue
            if p.piao_score == -1:
                flag = False

        if flag:
            if judge.piao_timer:
                judge.piao_timer.cancel()
            judge.piao_end()

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

    def __on_set_cards(self, uid, data):
        check_pass, p, judge = self.check_in_table(uid, commands_game.EXIT_ROOM)
        if not check_pass:
            return
        code = judge.set_cards_in_debug(data.get("cards"), data.get("dealer", 0))
        self.response(uid, commands_game.DEBUG_SET_CARDS, None, code)

    def __club_force_dismiss(self, uid, data):
        room_id = data["roomID"]
        if not room_id:
            return self.response_fail(uid, commands_game.CLUB_FORCE_DISMISS, error.DATA_BROKEN)

        judge = self.fetch_judge(CsMaJiangJudge, Player, room_id)
        if not judge:
            return self.response_fail(uid, commands_game.CLUB_FORCE_DISMISS, error.TABLE_NOT_EXIST)

        if judge.club_id == -1:
            return self.response_fail(uid, commands_game.CLUB_FORCE_DISMISS, error.NOT_YOUR_ROOM)

        user_data = club_model.get_club_by_uid_and_club_id(database.share_db(), judge.club_id, uid)
        if not user_data or user_data['permission'] not in (0, 1,):
            return self.response_fail(uid, commands_game.CLUB_FORCE_DISMISS, error.NOT_YOUR_ROOM)

        judge.force_dismiss()
        return self.response_ok(uid, commands_game.CLUB_FORCE_DISMISS, {"roomID": judge.tid})

    def __union_force_dismiss(self, uid, data):
        room_id = data["roomID"]
        if not room_id:
            return self.response_fail(uid, commands_game.UNION_FORCE_DISMISS, error.DATA_BROKEN)

        judge = self.fetch_judge(CsMaJiangJudge, Player, room_id)
        if not judge:
            return self.response_fail(uid, commands_game.UNION_FORCE_DISMISS, error.TABLE_NOT_EXIST)

        if judge.union_id == -1:
            return self.response_fail(uid, commands_game.UNION_FORCE_DISMISS, error.NOT_YOUR_ROOM)

        # user_data = club_model.get_club_by_uid_and_club_id(database.share_db(), judge.club_id, uid)
        user_data = union_model.get_union_userinfo_by_uid_and_union_id(database.share_db(), uid, judge.union_id)
        if not user_data or user_data['permission'] not in (0, 1,):
            return self.response_fail(uid, commands_game.UNION_FORCE_DISMISS, error.NOT_YOUR_ROOM)

        judge.force_dismiss()
        return self.response_ok(uid, commands_game.UNION_FORCE_DISMISS, {"roomID": judge.tid})


    def __lucker_get_left_cards(self, uid, data):
        if not data:
            return self.response_fail(uid, commands_game.LUCKER_GET_LEFT_CARDS, error.DATA_BROKEN)
        room_id = data["roomID"]
        if not room_id:
            return self.response_fail(uid, commands_game.LUCKER_GET_LEFT_CARDS, error.DATA_BROKEN)

        judge = self.fetch_judge(CsMaJiangJudge, Player, room_id)
        if not judge:
            return self.response_fail(uid, commands_game.LUCKER_GET_LEFT_CARDS, error.TABLE_NOT_EXIST)

        is_lucker = int(players_model.get_is_lucker(uid)["is_lucker"]) == 1
        if not is_lucker:
            return self.response_fail(uid, commands_game.LUCKER_GET_LEFT_CARDS, error.COMMAND_DENNY)
        self.response_ok(uid, commands_game.LUCKER_GET_LEFT_CARDS, {"cards": judge.get_left_cards()})

    def __lucker_change_card(self, uid, data):
        if not data:
            return self.response_fail(uid, commands_game.LUCKER_CHANGE_CARD, error.DATA_BROKEN)
        change_card = data["changeCard"]
        if not change_card:
            return self.response_fail(uid, commands_game.LUCKER_CHANGE_CARD, error.DATA_BROKEN)

        check_pass, p, judge = self.check_in_table(uid, commands_game.LUCKER_CHANGE_CARD)
        if not check_pass:
            return self.response_fail(uid, commands_game.LUCKER_CHANGE_CARD, error.TABLE_NOT_EXIST)

        is_lucker = int(players_model.get_is_lucker(uid)["is_lucker"]) == 1
        if not is_lucker:
            return self.response_fail(uid, commands_game.LUCKER_CHANGE_CARD, error.COMMAND_DENNY)

        code = judge.lucker_change_card(p, change_card)
        self.send_data_to_player(uid,commands_game.LUCKER_CHANGE_CARD, {}, code)

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
