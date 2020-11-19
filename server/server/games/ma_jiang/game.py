# coding:utf-8
from base import const
from base import error
from base.base_game import BaseGame
from games.ma_jiang import flow
from models import club_model, database, onlines_model, union_model
from models import logs_model
from models import tables_model
from protocol import protocol_utils
from utils import utils
from utils.check_params import ParamsCheck
from . import commands_game
from .player import Player
from .zz_ma_jiang_judge import ZzMaJiangJudge


class GameServer(BaseGame):
    def __init__(self):
        BaseGame.__init__(self)
        self.__params_checker = ParamsCheck(const.BASE_PATH + "configs/ma_jiang_interface.yml").check_params
        self._add_handlers({
            commands_game.ENTER_ROOM: self.__on_player_join,
            commands_game.EXPRESS_ENTER_UNION_ROOM: self.__on_player_join,
            commands_game.EXIT_ROOM: self.__on_exit_room,
            commands_game.OWNER_DISMISS: self.__on_owner_dismiss,
            commands_game.AUTO_ATTACK_ONE:self.__auto_attack_one,
            commands_game.PLAYER_CHU_PAI: self.__on_player_chu_pai,
            commands_game.PLAYER_PASS: self.__on_player_pass,
            commands_game.READY: self.__on_player_ready,
            commands_game.REQUEST_DISMISS: self.__on_request_dismiss,
            commands_game.CLIENT_BROAD_CAST: self.__on_client_broad_cast,
            commands_game.PLAYER_PENG: self.__on_player_peng,
            commands_game.PLAYER_GANG: self.__on_player_gang,
            commands_game.PLAYER_BU: self.__on_player_bu,
            commands_game.PLAYER_HU_PAI: self.__on_player_hu,
            commands_game.PLAYER_CHI: self.__on_player_chi,
            commands_game.PLAYER_CHUI: self.__on_player_chui,
            commands_game.DEBUG_SET_CARDS: self.__on_set_cards,
            commands_game.REQUEST_POSITION: self.__on_request_position,
            commands_game.ROOM_LIST: self.__on_room_list,
            commands_game.ADD_ROOM: self.__add_room,
            commands_game.PLAY_CONFIG_CHANGE: self.__on_play_config_change,
            commands_game.FORCE_DISMISS: self.__on_force_dismiss,
            commands_game.ENTER_ROOM_INFO: self.__on_enter_room_info,
            commands_game.DEBUG_CARDS_INFO: self.__on_debug_card_info,
            commands_game.DEBUG_PLAYERS_INFO: self.__on_debug_players_info,
            commands_game.CLUB_FORCE_DISMISS: self.__club_force_dismiss,
            commands_game.CHANGE_SIT: self.__change_sit,
            commands_game.UNION_GAME_PLAY_CONFIG_CHANGE: self.__on_union_play_config_change,
            commands_game.UNION_FORCE_DISMISS: self.__union_force_dismiss,
        })
        self.__stop_timer = None

    def __on_enter_room_info(self, uid, _):
        check_pass, p, judge = self.__check_in_table(uid, commands_game.ENTER_ROOM_INFO)
        if not check_pass:
            return
        items = judge.get_all_player_info()
        for item in items:
            self.response(uid, commands_game.ENTER_ROOM_INFO, item)
        return

    def __on_debug_card_info(self, uid, data):
        if not data or uid >= 7:
            return
        room_id = data["roomID"]
        from_idx = data['fromIdx']
        to_idx = data['toIdx']
        judge = self.__get_judge(room_id)
        if not judge or not from_idx or not to_idx:
            return
        judge.debug_cards(str(uid), from_idx, to_idx)

    def __on_debug_players_info(self, uid, data):
        if not data or uid >= 7:
            return
        room_id = data["roomID"]
        judge = self.__get_judge(room_id)
        if not judge:
            logs_model.delete_redis_data(room_id)
            return
        logs_model.modify_redis_data(room_id, judge.debug_get_players())

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
    def __auto_attack_one(self,uid,_):
        p = self.get_player(uid)
        if not p:
            return self.response_fail(uid, commands_game.ENTER_ROOM, error.DATA_BROKEN)
        p.is_auto_chupai = False
        p.iscacel_auto_chupai = True
        p.user_operation_timeout = const.Auto_Operation_TimeOut
        if p.operator_out_time:
            p.operator_out_time.cancel()
            p.operator_out_time = None
        self.response_ok( uid,commands_game.AUTO_ATTACK_ONE,{"is_auto_chupai":p.is_auto_chupai})
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

    def __on_set_cards(self, uid, data):
        check_pass, p, judge = self.__check_in_table(uid, commands_game.DEBUG_SET_CARDS)
        if not check_pass:
            return
        code = judge.set_cards_in_debug(data.get("cards"), data.get("dealer", 0))
        self.response(uid, commands_game.DEBUG_SET_CARDS, None, code)

    def __on_client_broad_cast(self, uid, data):
        check_pass, p, judge = self.__check_in_table(uid, commands_game.CLIENT_BROAD_CAST)
        if not check_pass:
            return

        is_correct, result = self.__params_checker("CLIENT_BROAD_CAST", data)
        if not is_correct:
            return self.response_fail(uid, commands_game.CLIENT_BROAD_CAST, error.DATA_BROKEN)

        result = protocol_utils.pack_client_body({"uid": p.uid, "data": result['data']}, error.OK)
        judge.broad_cast(commands_game.CLIENT_BROAD_CAST, result)

    def __on_player_ready(self, uid, _):
        check_pass, p, judge = self.__check_in_table(uid, commands_game.READY)
        if not check_pass:
            return
        flag = judge.player_ready(p)
        if not flag:
            return
        data = {"seatID": p.seat_id, "isPrepare": p.is_ready}
        body = protocol_utils.pack_client_body(data, error.OK)
        judge.broad_cast(commands_game.READY, body)
        return judge.try_start_game()
    def on_player_chu_pai(self,uid,data):
        self.__on_player_chu_pai(uid,data)
    def __on_player_chu_pai(self, uid, data):
        check_pass, p, judge = self.__check_in_table(uid, commands_game.PLAYER_CHU_PAI)
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
        check_pass, p, judge = self.__check_in_table(uid, commands_game.PLAYER_HU_PAI)
        if not check_pass:
            return

        code = judge.player_hu(p)
        if code != error.OK:
            return self.response_fail(uid, commands_game.PLAYER_HU_PAI, code)
        judge.check_action_end()

    def __on_player_peng(self, uid, data):
        check_pass, p, judge = self.__check_in_table(uid, commands_game.PLAYER_PENG)
        if not check_pass:
            return

        is_correct, result = self.__params_checker("PLAYER_PENG", data)
        if not is_correct:
            return self.response_fail(uid, commands_game.PLAYER_PENG, error.DATA_BROKEN)

        code = judge.player_peng(p, data)
        if code != error.OK:
            return self.response_fail(uid, commands_game.PLAYER_PENG, code)
        judge.check_action_end()

    def __on_player_bu(self, uid, data):
        check_pass, p, judge = self.__check_in_table(uid, commands_game.PLAYER_BU)
        if not check_pass:
            return

        is_correct, result = self.__params_checker("PLAYER_BU", data)
        if not is_correct:
            return self.response_fail(uid, commands_game.PLAYER_BU, error.DATA_BROKEN)

        code = judge.player_bu(p, data)
        if code != error.OK:
            return self.response_fail(uid, commands_game.PLAYER_BU, code)
        judge.check_action_end()

    def __on_player_gang(self, uid, data):
        check_pass, p, judge = self.__check_in_table(uid, commands_game.PLAYER_GANG)
        if not check_pass:
            return

        is_correct, result = self.__params_checker("PLAYER_GANG", data)
        if not is_correct:
            return self.response_fail(uid, commands_game.PLAYER_GANG, error.DATA_BROKEN)

        code = judge.player_gang(p, data)
        if code != error.OK:
            return self.response_fail(uid, commands_game.PLAYER_GANG, code)
        judge.check_action_end()
    def on_player_pass(self,uid,_):
        self.__on_player_pass(uid,_)
    def __on_player_pass(self, uid, _):
        check_pass, p, judge = self.__check_in_table(uid, commands_game.PLAYER_PASS)
        if not check_pass:
            return

        code = judge.player_pass(p)
        if code != error.OK:
            return self.response_fail(uid, commands_game.PLAYER_PASS, code)
        #self.response_ok( uid,commands_game.AUTO_ATTACK_ONE,{"is_auto_chupai":p.is_auto_chupai})
        judge.check_action_end()
    def player_ready(self,uid):
        self.__on_player_ready(uid,None)
    def __on_player_chi(self, uid, data):
        check_pass, p, judge = self.__check_in_table(uid, commands_game.PLAYER_CHI)
        if not check_pass:
            return

        is_correct, result = self.__params_checker("PLAYER_CHI", data)
        if not is_correct or "cards" not in result:
            return self.response_fail(uid, commands_game.PLAYER_CHI, error.DATA_BROKEN)

        chi_pai = result['cards']
        if not chi_pai or type(chi_pai) is not list or 3 != len(chi_pai):
            return self.response_fail(uid, commands_game.PLAYER_CHI, error.DATA_BROKEN)

        code = judge.player_chi(p, chi_pai)
        if code != error.OK:
            return self.response_fail(uid, commands_game.PLAYER_CHI, code)
        judge.check_action_end()

    def __on_player_chui(self, uid, data):
        check_pass, p, judge = self.__check_in_table(uid, commands_game.PLAYER_CHUI)
        if not check_pass:
            return

        is_correct, result = self.__params_checker("PLAYER_CHUI", data)
        if not is_correct:
            return self.response_fail(uid, commands_game.PLAYER_CHUI, error.DATA_BROKEN)

        chui = result['chui']
        if not hasattr(judge, "player_chui_call"):
            return self.response_fail(uid, commands_game.PLAYER_CHUI, error.RULE_ERROR)

        code = judge.player_chui_call(p, chui)
        if code != error.OK:
            return self.response_fail(uid, commands_game.PLAYER_CHUI, error.RULE_ERROR)

    def __on_request_dismiss(self, uid, data):
        check_pass, p, judge = self.__check_in_table(uid, commands_game.REQUEST_DISMISS)
        if not check_pass:
            return
        is_agree = data["agree"]
        is_correct, result = self.__params_checker("REQUEST_DISMISS", data)
        if not is_correct:
            return self.response_fail(uid, commands_game.REQUEST_DISMISS, error.DATA_BROKEN)


        judge.player_request_dismiss(p, is_agree)

    def __on_request_position(self, uid, _):
        check_pass, p, judge = self.__check_in_table(uid, commands_game.REQUEST_POSITION)
        if not check_pass:
            return
        data = judge.get_all_distances()
        self.response(uid, commands_game.REQUEST_POSITION, {"distances": data})

    def __check_in_table(self, uid, cmd, with_notify=False) -> (int, Player, ZzMaJiangJudge):
        p = self.get_player(uid)
        if not p:
            if with_notify:
                self.response_fail(uid, cmd, error.USER_NOT_EXIST)
            return False, None, None
        judge = self.__get_judge(p.tid)
        if not judge:
            if with_notify:
                self.response_fail(uid, cmd, error.TABLE_NOT_EXIST)
            return False, None, None
        return True, p, judge

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

        judge = self.fetch_judge(ZzMaJiangJudge, Player, tid)
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

    def __do_join_room(self, judge: ZzMaJiangJudge, p: Player, uid, re_connect, is_re_enter_room):
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
        self.response(uid, commands_game.PLAYER_ENTER_ROOM, judge.get_player_data(player))
        items = judge.get_all_player_info()
        for item in items:  # 发送所有房间内的其它玩家数据给当前玩家
            if uid == item.get('uid'):
                continue
            self.response(uid, commands_game.PLAYER_ENTER_ROOM, item)
        self.response(uid, commands_game.ROOM_CONFIG, judge.get_info())

        data = player.get_all_public_data(judge.status)
        body = protocol_utils.pack_client_body(data, error.OK)
        if not is_re_enter_room:
            judge.broad_cast(commands_game.PLAYER_ENTER_ROOM, body, uid)

        if judge.in_dismiss:
            self.response(uid, commands_game.REQUEST_DISMISS, judge.make_dismiss_data())

    def __get_judge(self, tid: int):
        """ 查找桌子 """
        return self.judges.get(tid)

    def __del_judge(self, judge):
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
        tid = judge.tid
        sub_floor_id = judge.sub_floor_id
        code, result = judge.player_quit(p, const.QUIT_NORMAL)

        judge.broad_cast(commands_game.EXIT_ROOM, result)
        self.send_data_to_player(p.uid, commands_game.EXIT_ROOM, result, code)  # 玩家退出桌子之后广播无法到达玩家，所以这里直接用玩家发送一次
        if code == error.OK:
            self.__clear_player(p)
        # 如果有人退出桌子，广播消息给客户端
        """如果有人退出桌子，广播消息给客户端"""
        self.publish(2,6,{'union_id':judge.union_id,'uid':uid,'selfuid':p.uid,'type':6,
                          'tid':tid,'subfloor':sub_floor_id},9999)

    @staticmethod
    def __do_owner_dismiss(judge, reason):
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

    def __on_owner_dismiss(self, uid, data):
        if not data or "roomID" not in data:
            check_pass, p, judge = self.__check_in_table(uid, commands_game.OWNER_DISMISS)
            if not check_pass:
                return
        else:
            room_id = data["roomID"]
            if not room_id:
                return self.response_fail(uid, commands_game.OWNER_DISMISS, error.DATA_BROKEN)

            judge = self.fetch_judge(ZzMaJiangJudge, Player, room_id)
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

    def __club_force_dismiss(self, uid, data):
        room_id = data["roomID"]
        if not room_id:
            return self.response_fail(uid, commands_game.CLUB_FORCE_DISMISS, error.DATA_BROKEN)

        judge = self.fetch_judge(ZzMaJiangJudge, Player, room_id)
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

        judge = self.fetch_judge(ZzMaJiangJudge, Player, room_id)
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

    def __change_sit(self,uid, _):
        if not uid:
            return
        ret, p, judge = self.check_in_table(uid, commands_game.CHANGE_SIT)
        if not ret or not p or not judge:
            return
        code = judge.change_seat(p)
        if code < 0:
            return self.response_fail(uid, commands_game.CHANGE_SIT, code)

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
