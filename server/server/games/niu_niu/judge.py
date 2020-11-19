# coding:utf-8
from base.base_judge import BaseJudge

from base import error
from games.niu_niu import commands_game
from games.niu_niu import flow
from games.niu_niu.rules import Rules
from games.niu_niu.player import Player
from models import configs_model
from models import logs_model
from models import tables_model
from models import onlines_model
from protocol import channel_protocol
from utils import earth_position
from utils import utils
from utils.twisted_tools import DelayCall
from .poker import Poker
from copy import deepcopy
import random

ROUND_RATE = 1  # 单局倍率
DISMISS_SECONDS = 60  # 解散房间的等待时间
READY_TIME = 10  # 10秒自动开始准备
CALL_TIME = 10
DEALER_TIME = 10
WAITING_TIME = 15
# FAN_CARD_TIME = 10

NIU_NIU_SCORE = {
    1: [1, 2],
    2: [2, 4],
    3: [3, 6],
    4: [4, 8],
    5: [5, 10]
}


class Judge(BaseJudge):

    def __init__(self, ret, service):
        BaseJudge.__init__(self, ret, service)
        self.round_index = 1
        self.__no_score_seat_id = []
        self.__max_tui_zhu_times = 10
        self.__auto_show_card_timer = None
        self.__is_manual = True  # 手动开始游戏
        self.__prev_biggest_niu = 1
        self.__max_qiang = self.rule_details.get("maxQiang", 1)
        self.__total_seat = self.rule_details.get("playerCount", 2) + 1
        self.__base_score = self.rule_details.get("score", 1)
        self.__spec_type = self.rule_details.get("specType")
        self.__detail_type = self.rule_details.get("detailType", 1)
        self.__tui_zhu = bool(self.rule_details.get("tuiZhu", 0))
        self.__joker = bool(self.rule_details.get("joker", 0))
        self.__times = 1
        self.__zhuang_type = self.rule_details.get("zhuangType", 1)  # 1 固定庄，2 牛牛庄，3 顺序庄，4 明牌庄
        self.__prev_dealer = -1  # 上局庄家ID
        self.__dealer = -1  # 庄家ID
        self.__lottery = False  # 是否已经抽奖
        self.status = flow.T_IDLE
        self.flow_status = flow.T_IN_IDLE  # 流程状态
        self.__timer = None  # 游戏的定时器
        self.__dismiss_timer = None  # 解散房间定时器
        self.__poker = Poker(self.__detail_type, self.__joker)  # 初始化扑克信息
        self.__agree_seats = set()
        self.__disagree_seats = set()
        self.__is_dismiss = False
        self.__dismiss_round_index = 1
        self.__init_seats()
        # self.__owner_player = None

        self.update_table_info()
        self.update_table_info_max_player(self.__total_seat)

    @property
    def detail_type(self):
        return self.__detail_type

    def __send_player_card(self, cards, p: Player):
        result = {"handCards": cards}
        result["type"] = Rules.get_type(p.cards, self.__detail_type, self.__spec_type, self.__joker)[0]
        self.inner_send(p, commands_game.FAN_CARD, result)

    def fan_card(self, p: Player):
        if len(p.cards) != 5:
            c = self.__poker.pop()
            p.receive_card(c)
        self.__send_player_card(deepcopy(p.cards), p)

    @property
    def poker(self):
        return self.__poker

    @property
    def timer(self):
        return self.__timer

    def __init_seats(self):
        self.seats = [None] * self.__total_seat

    def default_call_score(self):
        return deepcopy(NIU_NIU_SCORE[self.__base_score])

    @property
    def max_qiang(self):
        return self.__max_qiang

    @property
    def in_dismiss(self):
        return len(self.__agree_seats) > 0

    def __set_status(self, status):
        # 设置桌子状态
        self.status = status
        if self.table_info["table_status"] != status:
            self.table_info["table_status"] = status
            self.update_table_info()

    def __set_flow_status(self, status):
        # 设置桌子状态
        self.flow_status = status

    def get_info(self):
        """ 获得房间基本信息 """
        result = BaseJudge.get_info(self)
        if self.status == flow.T_PLAYING:
            result['inFlow'] = self.flow_status
            result['dealer'] = self.__dealer
            result['remainSeconds'] = self.__left_seconds()
        return result

    def __search_empty_seat(self):
        """ 寻找桌子内的空位 """
        for seat_id in range(1, self.__total_seat):
            if not self.seats[seat_id]:
                return seat_id
        return -1

    # 根据玩家uid来获得玩家的坐位ID
    def get_seat_id(self, uid):
        for i in range(1, self.__total_seat):
            if self.seats[i] and self.seats[i].uid == uid:
                return i
        return -1

    def player_total_count(self):
        count = 0
        if self.__is_manual:
            for p in self.seats:
                if not p:
                    continue
                count += 1
        else:
            count = self.__total_seat - 1
        return count

    def player_total_count_in_config(self):
        return self.__total_seat - 1

    @property
    def dealer(self):  # 庄家坐位ID
        return self.__dealer

    def __set_dealer(self, dealer):
        assert type(dealer) is int
        self.__dealer = dealer

    def __game_start(self):
        """ 游戏开始 """
        if self.status != flow.T_READY:
            return
        ids = []
        for p in self.seats:
            if not p:
                continue
            ids.append(p.uid)
            p.on_game_start(self.match_score)
        self.start_time = utils.timestamp()
        # 修改数据库中桌子状态
        tables_model.modify_status_by_tid(tables_model.STATUS_PLAYING, self.tid)
        # 修改在线表中桌子内玩家状态
        onlines_model.set_state_by_uid(onlines_model.STATUS_PLAYING, ids)
        self.already_started = True
        self.__set_status(flow.T_PLAYING)
        self.inner_broad_cast(commands_game.GAME_START, {})
        self.__round_start()

    def __game_over(self):
        """ 游戏结束 """
        self.dec_diamonds(self.__is_dismiss, self.__dismiss_round_index)
        self.__set_status(flow.T_IDLE)
        result = {"gid": 1, "seats": [], "match": [], "union": []}
        ids = []
        for p in self.seats:
            if not p:
                continue
            ids.append(p.uid)
            result["seats"].append(p.game_over_data)
            result["match"].append(p.match_data(self.club_id, self.match_type))
            if self.union_id != -1:
                result["union"].append(p.union_energy_data(self.union_id))

        self.inner_broad_cast(commands_game.GAME_OVER, result)
        finish_data = self.get_game_finish_data()
        finish_data["isDismiss"] = self.__is_dismiss
        onlines_model.set_state_by_uid(onlines_model.STATUS_WAITING, ids)
        self.__save_game_record(finish_data)
        self.save_club_winner()
        self.__do_dismiss()

    def __save_game_record(self, finish_data):
        logs_model.insert_room_log(self.record_id, self.tid, self.game_type, self.seats, self.owner,
                                   self.total_round, self.rule_details, self.club_id,
                                   finish_data, self.group_id, self.dec_diamond, self.match_type, self.floor,
                                   self.sub_floor_id, self.match_config, self.union_id)

    def add_base_review_data(self):
        BaseJudge.add_base_review_data(self)

        for p in self.seats:
            if not p:
                continue
            data = p.get_all_data(self.detail_type)
            body = channel_protocol.packet_client_body(data, error.OK)
            self.add_review_log(commands_game.PLAYER_ENTER_ROOM, body)

        body = channel_protocol.packet_client_body(self.get_info(), error.OK)
        self.add_review_log(commands_game.ROOM_CONFIG, body)

    def __next_player(self, p) -> Player:
        """ 查找下一玩家 """
        for i in range(p.seat_id + 1, self.__total_seat):
            if self.seats[i]:
                return self.seats[i]
        for i in range(1, p.seat_id):
            if self.seats[i]:
                return self.seats[i]

    def __init_dealer(self):
        if not self.__joker:
            if self.__zhuang_type == 1:
                self.__dealer = 1
            elif self.__zhuang_type == 2:
                self.__dealer = self.__prev_biggest_niu
            elif self.__zhuang_type == 3:
                if self.round_index == 1:
                    self.__dealer = 1
                else:
                    next_dealer = self.__next_player(self.get_player_by_seat_id(self.__dealer))
                    self.__dealer = next_dealer.seat_id
        else:
            if self.round_index == 1:
                self.__dealer = 1
            else:
                next_dealer = self.__next_player(self.seats[self.__dealer])
                self.__dealer = next_dealer.seat_id

        result = {"dealer": self.__dealer}
        self.inner_broad_cast(commands_game.DING_ZHUANG, result)

    def __deal_four_cards(self):
        self.__poker.shuffle()
        for i in range(4):
            for p in self.seats:
                if not p:
                    continue
                c = self.__poker.pop()
                p.receive_card(c)

        result = dict()
        for p in self.seats:
            if not p:
                continue
            result["handCards"] = p.cards
            self.inner_send(p, commands_game.DEAL_CARDS, result)

        self.add_base_review_data()
        if not self.__joker:
            self.__set_round_flow(flow.T_IN_DEALER)

    def __deal_cards(self):
        self.__poker.shuffle()
        for i in range(5):
            for p in self.seats:
                if not p:
                    continue
                c = self.__poker.pop()
                p.receive_card(c)

        result = {"dealerSeatID": self.__dealer}
        for p in self.seats:
            if not p:
                continue
            result["handCards"] = p.cards
            result["type"] = Rules.get_type(p.cards, self.__detail_type, self.__spec_type, self.__joker)[0]
            self.inner_send(p, commands_game.DEAL_CARDS, result)

        self.add_base_review_data()
        self.__set_round_flow(flow.T_IN_KAI_PAI)

    def __before_round_start(self):
        if self.__zhuang_type == 4:
            self.__dealer = -1
        self.__times = 1
        self.flow_status = flow.T_IN_IDLE
        self.round_review_data.clear()

    def __round_start(self):
        """ 一局开始 """
        if self.status != flow.T_PLAYING:
            return

        for p in self.seats:  # 开局前清理
            if not p:
                continue
            p.on_round_start()

        self.__before_round_start()

        result = {"seq": self.round_index}
        self.inner_broad_cast(commands_game.ROUND_START, result)

        if self.__zhuang_type == 4:
            return self.__deal_four_cards()
        self.__init_dealer()

        if self.__joker:
            self.__deal_four_cards()

        self.__set_round_flow(flow.T_IN_CALL_SCORE)
        self.__init_call_score()

    def __init_call_score(self):
        for p in self.seats:
            if not p:
                continue
            score = self.default_call_score()
            if self.__dealer != p.seat_id:
                if self.__tui_zhu and self.round_index > 1 and p.prev_win_score != 0 and self.__prev_dealer != p.seat_id and \
                        p.tui_zhu is False:
                    last_score = score[-1]
                    all_score = last_score + p.prev_win_score
                    max_score = self.__max_tui_zhu_times * last_score
                    if all_score > max_score:
                        all_score = max_score
                    score.append(all_score)
                p.set_can_call_score(score)
                can_call_score = dict()
                can_call_score['score'] = p.can_call_score
                self.inner_send(p, commands_game.SCORE, can_call_score)

    def __has_next_round(self):
        if self.__is_dismiss:
            return False
        return self.round_index <= self.total_round

    def __dismiss_check_out(self):
        for p in self.seats:
            if not p:
                continue
            p.on_round_over(0, False)

    def __do_check_out(self, is_dismiss):
        """ 结算当局积分 """
        scores = {}

        prev_winner = self.__dealer

        if is_dismiss:
            return self.__dismiss_check_out()

        dealer = self.get_player_by_seat_id(self.__dealer)

        dealer_broke = False
        for p in self.seats:
            if not p:
                continue
            if p.seat_id == self.__dealer:
                continue
            if dealer_broke:
                break

            winner_id, times = Rules.get_winner(p, dealer, self.__detail_type, self.__spec_type, self.__joker)
            if self.__zhuang_type == 2 and times >= 4 and winner_id != prev_winner:
                prev_winner_player = self.get_player_by_seat_id(prev_winner)
                now_winner_player = self.get_player_by_seat_id(winner_id)
                prev_winner, _ = Rules.get_winner(prev_winner_player, now_winner_player, self.__detail_type,
                                                  self.__spec_type, self.__joker)

            score = p.call_score * times * self.__times * self.match_enter_score

            if self.match_type == 1 and self.club_id != -1:
                if p.seat_id == winner_id:
                    if dealer.lock_score + dealer.score <= score and dealer.uid != self.owner:
                        score = dealer.lock_score + dealer.score
                        self.__no_score_seat_id.append(self.__dealer)
                        dealer_broke = True
                else:
                    if p.lock_score + p.score <= score and p.uid != self.owner:
                        score = p.lock_score + p.score
                        self.__no_score_seat_id.append(p.seat_id)

            p.on_round_over(score, p.seat_id == winner_id, True)

            diff_score = score
            if p.seat_id != winner_id:
                diff_score = score * -1
            scores[p.seat_id] = diff_score

            dealer.on_round_over(score, dealer.seat_id == winner_id)

        self.__prev_biggest_niu = prev_winner
        self.inner_broad_cast(commands_game.PLAYER_SCORE_CHANGE, scores, error.OK, 0, True)
        return

    def __get_dealer_info(self):
        player = self.get_player_by_seat_id(self.__dealer)
        if not player or not player.cards:
            return {}
        cards = player.cards
        return {"cards": cards, "type": Rules.get_type(cards, self.__detail_type, self.__spec_type, self.__joker)[0]}

    def __round_over(self, is_dismiss=False):
        """ 一局结束 """
        if self.status != flow.T_PLAYING:
            return
        if not self.round_review_data:
            self.add_base_review_data()
        self.__set_status(flow.T_CHECK_OUT)
        finish_type = 0
        if is_dismiss:
            finish_type = 2
        self.__do_check_out(is_dismiss)

        if self.__timer:
            self.__timer.cancel()

        index = self.round_index
        self.round_index += 1
        result = {"seq": index, "hasNextRound": self.__has_next_round(), "finishType": finish_type,
                  "dealer": self.__get_dealer_info()}
        seats = []

        self.__save_round_log(index)

        for p in self.seats:
            if not p:
                continue
            tmp = {
                "seatID": p.seat_id,
                "cards": p.cards,
                "type": Rules.get_type(p.cards, self.__detail_type, self.__spec_type, self.__joker)[0],
                "totalScore": p.score,
                "score": p.current_score
            }
            seats.append(tmp)
            p.on_checkout_over()
        result["seats"] = seats
        self.inner_broad_cast(commands_game.ROUND_OVER, result, error.OK, 0, True)

        if len(self.__no_score_seat_id) > 0:
            return self.__game_over()

        self.__prev_dealer = self.__dealer

        # if self.can_lottery(self.owner):
        #     p = self.get_player_by_uid(self.owner)
        #     if p:
        #         self.inner_send(p, commands_game.NOTIFY_LOTTERY, {})

        self.table_info["round_index"] = self.round_index
        self.update_table_info()

        if not self.__has_next_round():  # 房间结束
            return self.__game_over()
        else:
            self.__timer = DelayCall(READY_TIME, self.__set_all_player_ready)

    def __all_player_round_detail(self):
        data = {"dealerSeatID": self.__dealer, "players": []}
        for p in self.seats:
            if not p:
                continue
            player_round_data = p.round_data
            player_round_data['cards'] = p.cards
            player_round_data['type'] = Rules.get_type(p.cards, self.__detail_type, self.__spec_type, self.__joker)[0]
            data['players'].append(deepcopy(player_round_data))
        return data

    def __save_round_log(self, index):
        round_id = logs_model.insert_round_log(self.record_id, index, self.game_type, self.seats,
                                               self.__all_player_round_detail())
        logs_model.add_round_review_log({
            "record_id": self.record_id,
            "round_id": round_id,
            "commands": self.round_review_data
        })
        self.round_review_data.clear()

    # 按优先顺序执行某函数
    def __seat_step(self, func):
        if not func:
            return
        for p in self.seats:
            if not p:
                continue
            func(p)

    def __set_round_flow(self, in_flow):
        self.__set_flow_status(in_flow)
        record = in_flow > flow.T_IN_IDLE

        if self.__timer:
            self.__timer.cancel()

        if in_flow == flow.T_IN_KAI_PAI:
            self.__timer = DelayCall(WAITING_TIME, self.__auto_kai_pai)
        elif in_flow == flow.T_IN_DEALER:
            self.__timer = DelayCall(DEALER_TIME, self.__auto_dealer)
        elif in_flow == flow.T_IN_CALL_SCORE:
            self.__timer = DelayCall(CALL_TIME, self.__auto_call_score)
        # elif in_flow == flow.T_IN_FAN_CARD:
        #    self.__timer = DelayCall(FAN_CARD_TIME, self.__auto_fan_card)
        self.inner_broad_cast(commands_game.ROUND_FLOW, {"flow": in_flow}, error.OK, 0, record)

    # def __auto_fan_card(self):
    #    for p in self.seats:
    #        if not p:
    #            continue
    #        if len(p.cards) != 5:
    #            c = self.__poker.pop()
    #            p.receive_card(c)
    #            self.__send_player_card(p)
    # self.__set_round_flow(flow.T_IN_KAI_PAI)

    def __auto_kai_pai(self):
        for p in self.seats:
            if not p:
                continue
            if p.is_show_cards:
                continue
            if len(p.cards) != 5:
                c = self.__poker.pop()
                p.receive_card(c)
            self.__send_player_card(deepcopy(p.cards), p)
            self.player_show_cards(p)
        self.check_all_show_cards()

    def __auto_call_score(self):
        for p in self.seats:
            if not p:
                continue
            if p.call_score != -1:
                continue
            self.player_call_score(p, self.default_call_score()[0])
        self.check_all_call_score()

    def __auto_dealer(self):
        for p in self.seats:
            if not p:
                continue
            if p.call_dealer != -1:
                continue
            self.player_call_dealer(p, 0)
        self.check_all_call_dealer()

    # 获得当前循环用户还剩余的时间,单位为秒
    def __left_seconds(self):
        if not self.__timer:
            return 0
        return int(round(self.__timer.left_seconds()))  # 浮点数取整

    # 取消定时器的定时操作
    def __cancel(self):
        if self.__timer:
            self.__timer.cancel()

    def cancel_by_pass(self):
        self.__cancel()

    # 游戏结算 输赢加减钱
    def check_out(self):
        if self.status != flow.T_PLAYING:
            return
        pass

    def player_ready(self, p: Player):
        if self.status != flow.T_IDLE and self.status != flow.T_CHECK_OUT:
            return False
        p.is_ready = True
        return True

    def __set_all_player_ready(self):
        for p in self.seats:
            if not p:
                continue
            p.is_ready = True
        return self.try_start_round()

    def player_call_score(self, p: Player, score) -> int:
        if p.call_score != -1:
            return error.RULE_ERROR
        if self.__dealer == p.seat_id:
            return error.RULE_ERROR
        if len(p.can_call_score) == 3 and score == p.can_call_score[-1]:
            p.tui_zhu = True
        else:
            p.tui_zhu = False
        p.call_score = score
        result = {"seatID": p.seat_id, "callScore": score}
        self.inner_broad_cast(commands_game.CALL_SCORE, result, error.OK, 0, True)
        return error.OK

    def player_call_dealer(self, p: Player, score) -> int:
        if p.call_dealer != -1:
            return error.RULE_ERROR
        p.call_dealer = score
        result = {"seatID": p.seat_id, "callScore": score}
        self.inner_broad_cast(commands_game.CALL_DEALER, result, error.OK, 0, True)
        return error.OK

    def check_all_call_dealer(self):
        all_call_dealer = True
        max_score = 0
        max_seats = []
        for p in self.seats:
            if not p:
                continue
            if p.call_dealer == -1:
                all_call_dealer = False
                break
            if p.call_dealer == max_score:
                max_seats.append(p.seat_id)
            elif p.call_dealer > max_score:
                max_seats = [p.seat_id]
                max_score = p.call_dealer

        if all_call_dealer:
            rnd = random.randint(1, len(max_seats))
            self.__times = 1 if max_score == 0 else max_score
            self.__init_manual_dealer(max_seats[rnd - 1])
            self.__set_round_flow(flow.T_IN_CALL_SCORE)
            self.__init_call_score()

    def __init_manual_dealer(self, seat_id):
        self.__dealer = seat_id
        result = {"dealer": self.__dealer}
        self.inner_broad_cast(commands_game.DING_ZHUANG, result)

    def __deal_manual_cards(self):
        for p in self.seats:
            if not p:
                continue
            card = self.__poker.pop()
            p.receive_card(card)
            result = dict()
            result["handCards"] = [card]
            result["type"] = Rules.get_type(p.cards, self.__detail_type, self.__spec_type, self.__joker)[0]
            self.inner_send(p, commands_game.DEAL_CARDS, result)
        self.__set_round_flow(flow.T_IN_KAI_PAI)

    def player_show_cards(self, p: Player) -> int:
        if len(p.cards) == 4:
            c = self.__poker.pop()
            p.receive_card(c)
        result = {"seatID": p.seat_id, "cards": p.cards,
                  "type": Rules.get_type(p.cards, self.__detail_type, self.__spec_type, self.__joker)[0]}
        p.is_show_cards = True
        self.inner_broad_cast(commands_game.SHOW_CARDS, result, error.OK, 0, True)
        return error.OK

    def check_all_show_cards(self):
        all_show_cards = True
        for p in self.seats:
            if not p:
                continue
            if not p.is_show_cards:
                all_show_cards = False
                break
        if all_show_cards:
            self.__round_over(False)

    def check_all_call_score(self):
        all_call_score = True
        for p in self.seats:
            if not p:
                continue
            if p.seat_id == self.__dealer:
                continue
            if p.call_score == -1:
                all_call_score = False
                break
        if all_call_score:
            if self.__zhuang_type != 4 and not self.__joker:
                self.__deal_cards()
            else:
                if self.__joker:
                    self.__set_round_flow(flow.T_IN_KAI_PAI)
                else:
                    self.__deal_manual_cards()

    def player_quit(self, player, reason=error.OK):
        """ 退出房间 """
        p = self.get_player_by_seat_id(player.seat_id)
        if not p or p != player:
            return error.USER_NOT_EXIST, None
        if p.uid == self.owner and self.is_agent == 0:  # 房主不允许退出，只能解散房间(代开模式下,可以退出房间)
            return error.RULE_ERROR, None
        if self.status != flow.T_IDLE:
            return error.RULE_ERROR, None
        self.seats[player.seat_id] = None
        p.on_stand_up()
        if self.match_type == 1:
            p.return_score(self.club_id)
        # self.__reset_player_ready()  # 有人退出房间时清理掉所有准备状态
        if p.uid in self.table_info["player_list"]:
            self.table_info["player_list"].remove(p.uid)
            self.del_player_in_table_info(p.uid)
            self.update_table_info()
        self.remove_empty_judge()
        return error.OK, {"uid": player.uid, "code": reason, "kickTime": 100}

    def __reset_player_ready(self):
        for p in self.seats:  # 有人退出房间时清理掉所有准备状态
            if not p:
                continue
            if not p.is_ready:
                continue

            p.is_ready = False
            data = {"seatID": p.seat_id, "isPrepare": p.is_ready}
            body = channel_protocol.packet_client_body(data, error.OK)
            self.broad_cast(commands_game.READY, body)

    def player_join(self, player: Player, is_re_enter_room=False):
        """ 加入房间 """
        o_seat_id = self.get_seat_id(player.uid)
        seat_id = o_seat_id if o_seat_id > 0 else self.__search_empty_seat()
        if seat_id < 0:
            return error.TABLE_FULL, None

        if self.union_id == -1:
            if self.check_club_block(player) != error.OK:
                return error.TABLE_PLAYER_BLOCK, None
            code = self.check_diamond_and_yuan_bao_and_tip(player)
            if code != error.OK:
                return code, None

        else:
            if self.check_union_block(player) != error.OK:
                return error.TABLE_PLAYER_BLOCK, None

        if not is_re_enter_room:
            if self.round_index > 1 or self.status != flow.T_IDLE:
                return error.TABLE_FULL, None
        player.on_sit_down(self.tid, seat_id)
        player.offline = False
        player.is_ready = self.status > flow.T_READY  # 游戏中坐下时自动准备
        self.seats[seat_id] = player
        if player.uid not in self.table_info["player_list"]:
            self.table_info["player_list"].append(player.uid)
            self.add_player_in_table_info(player.club_info)
            self.update_table_info()
        return error.OK, {"roomID": self.tid}

    def player_request_dismiss(self, player: Player, is_agree: bool):
        if self.status == flow.T_IDLE:
            return
        if is_agree and not self.__dismiss_timer:
            self.__dismiss_timer = DelayCall(DISMISS_SECONDS, self.__on_dismiss_time_out)
        if not self.__dismiss_timer:
            self.inner_send(player, commands_game.REQUEST_DISMISS, None, error.COMMAND_DENNY)
            return

        if is_agree:
            self.__agree_seats.add(player.seat_id)
        else:
            self.__disagree_seats.add(player.seat_id)
        all_agree = len(self.__agree_seats) >= self.player_total_count()
        anyone_disagree = len(self.__disagree_seats) > 0
        is_end = all_agree or anyone_disagree
        if not is_end:
            return self.__send_dismiss_result()

        is_dismiss = all_agree
        if anyone_disagree:
            is_dismiss = False

        self.__do_player_request_dismiss(is_dismiss)

    def __clean_dismiss(self):
        if self.__dismiss_timer:
            self.__dismiss_timer.cancel()
            self.__dismiss_timer = None
        self.__agree_seats.clear()
        self.__disagree_seats.clear()

    def __do_player_request_dismiss(self, is_dismiss):
        self.__send_dismiss_result(is_dismiss)
        if not is_dismiss:
            self.__clean_dismiss()
            return
        self.force_dismiss()

    def force_dismiss(self):
        """强制解散"""
        DelayCall(0.1, self.__clean_dismiss)
        self.__is_dismiss = True
        self.__dismiss_round_index = self.round_index
        if self.status != flow.T_PLAYING:
            return self.__game_over()
        self.__round_over(True)

    def make_dismiss_data(self, is_dismiss=None):
        left_seconds = DISMISS_SECONDS
        if self.__dismiss_timer:
            left_seconds = self.__dismiss_timer.left_seconds()
        data = {"configTime": DISMISS_SECONDS, "remainTime": left_seconds,
                "yesSeatIDs": list(self.__agree_seats), "noSeatIDs": list(self.__disagree_seats)}
        if not (is_dismiss is None):
            data['result'] = is_dismiss
        return data

    def __send_dismiss_result(self, is_dismiss=None):
        data = self.make_dismiss_data(is_dismiss)
        self.inner_broad_cast(commands_game.REQUEST_DISMISS, data)

    def __on_dismiss_time_out(self):
        self.__do_player_request_dismiss(True)

    def player_connect_changed(self, player: Player) -> None:
        data = {"uid": player.uid, "IP": player.ip, "offline": player.offline}
        self.inner_broad_cast(commands_game.PLAYER_ONLINE, data)

    def owner_dismiss(self):
        """房主解散房间"""
        self.__do_dismiss()

    def emotion_stat(self, uid, detail):
        to_uid = uid
        emotion_id = detail.get('faceID')
        if detail.get('messageType') == logs_model.EMOTION_TO_OTHER:
            p = self.get_player_by_seat_id(detail.get('toSeatID', 0))
            if p:
                to_uid = p.uid
        logs_model.add_emotion_log(uid, to_uid, emotion_id, detail.get('messageType'))

    def __do_dismiss(self):
        self.__cancel()
        self.__poker = None
        self.on_match_game_over()
        for p in self.seats:
            if not p:
                continue
            p.on_game_over()
        self.seats = []
        tables_model.remove(self.tid)
        self.share_service().on_table_game_over(self)
        # self.__owner_player.remove_relation_tid(self.__tid)
        self.update_table_info(True)

    def can_lottery(self, uid):
        if not configs_model.get("kai_fang_hong_bao_switch", True):
            return False
        if self.__lottery or self.owner != int(uid) or self.round_index != self.total_round:
            return False
        return True

    def player_lottery(self, uid):
        if not self.can_lottery(uid):
            return error.COMMAND_DENNY, 0

        self.__lottery = True
        diamond = self.share_service().do_lottery(self.total_round)
        seat_id = self.get_seat_id(uid)

        # 更改玩家钻石 & 写入钻石变动日志
        # left_diamonds = players_model.get(uid).get('diamond', 0)
        # players_model.add_diamonds_with_log(uid, diamond, "0", "", const.REASON_LOTTERY,
        #                                     left_diamonds + diamond)

        data = {"seatID": seat_id, "diamond": diamond, "short_time": 3, "long_time": 10}
        # 发送中奖信息给房间内所有玩家
        self.broad_cast(commands_game.SUBMIT_LOTTERY, data)
        return error.OK, diamond

    def get_all_distances(self):
        result = list()

        def __calc_distance(_p1, _p2):
            if not _p1 or not _p2:
                return earth_position.DISTANCE_UNKNOWN
            x1, y1 = _p1.position
            x2, y2 = _p2.position
            return earth_position.calc_earth_distance(x1, y1, x2, y2)

        p1 = self.get_player_by_seat_id(1)
        p2 = self.get_player_by_seat_id(2)
        p3 = self.get_player_by_seat_id(3)
        p4 = self.get_player_by_seat_id(4)
        p5 = self.get_player_by_seat_id(5)
        p6 = self.get_player_by_seat_id(6)
        p7 = self.get_player_by_seat_id(7)
        p8 = self.get_player_by_seat_id(8)
        p9 = self.get_player_by_seat_id(9)
        p10 = self.get_player_by_seat_id(10)

        result.append(__calc_distance(p1, p2))
        result.append(__calc_distance(p1, p3))
        result.append(__calc_distance(p1, p4))
        result.append(__calc_distance(p1, p5))
        result.append(__calc_distance(p1, p6))
        result.append(__calc_distance(p1, p7))
        result.append(__calc_distance(p1, p8))
        result.append(__calc_distance(p1, p9))
        result.append(__calc_distance(p1, p10))

        result.append(__calc_distance(p2, p3))
        result.append(__calc_distance(p2, p4))
        result.append(__calc_distance(p2, p5))
        result.append(__calc_distance(p2, p6))
        result.append(__calc_distance(p2, p7))
        result.append(__calc_distance(p2, p8))
        result.append(__calc_distance(p2, p9))
        result.append(__calc_distance(p2, p10))

        result.append(__calc_distance(p3, p4))
        result.append(__calc_distance(p3, p5))
        result.append(__calc_distance(p3, p6))
        result.append(__calc_distance(p3, p7))
        result.append(__calc_distance(p3, p8))
        result.append(__calc_distance(p3, p9))
        result.append(__calc_distance(p3, p10))

        result.append(__calc_distance(p4, p5))
        result.append(__calc_distance(p4, p6))
        result.append(__calc_distance(p4, p7))
        result.append(__calc_distance(p4, p8))
        result.append(__calc_distance(p4, p9))
        result.append(__calc_distance(p4, p10))

        result.append(__calc_distance(p5, p6))
        result.append(__calc_distance(p5, p7))
        result.append(__calc_distance(p5, p8))
        result.append(__calc_distance(p5, p9))
        result.append(__calc_distance(p5, p10))

        result.append(__calc_distance(p6, p7))
        result.append(__calc_distance(p6, p8))
        result.append(__calc_distance(p6, p9))
        result.append(__calc_distance(p6, p10))

        result.append(__calc_distance(p7, p8))
        result.append(__calc_distance(p7, p9))
        result.append(__calc_distance(p7, p10))

        result.append(__calc_distance(p8, p9))
        result.append(__calc_distance(p8, p10))

        result.append(__calc_distance(p9, p10))
        return result

    def notify_distance(self):
        if self.status != flow.T_IDLE:
            return
        if self.player_total_count() != self.player_count:
            return
        data = {"distances": []}
        for p in self.seats:
            if not p:
                continue
            if p.is_ready:
                continue
            self.inner_send(p, commands_game.NOTIFY_POSITION, data)

    def try_start_round(self):
        return self.__check_round_start()

    def try_start_game(self):
        return self.__check_game_start()

    def __check_game_start(self):
        if self.status != flow.T_IDLE:  # 状态不对
            return False
        if self.player_total_count() <= 1:
            return False
        if self.player_total_count() != self.ready_player_count:  # 全部准备
            return False

        self.__set_status(flow.T_READY)
        self.__game_start()
        return True

    def __check_round_start(self):
        """ 检查下一局是否要开始了 """
        if self.status != flow.T_CHECK_OUT:
            return False
        if self.ready_player_count != self.player_total_count():
            return False
        self.__set_status(flow.T_PLAYING)
        self.__round_start()
        return True
