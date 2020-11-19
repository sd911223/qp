# coding:utf-8
import random
from copy import deepcopy

from base import const, error
from base.base_judge import BaseJudge
from games.pao_de_kuai import commands_game
from games.pao_de_kuai import flow
from games.pao_de_kuai import pao_de_kuai
from games.pao_de_kuai import poker_lib
from games.pao_de_kuai.player import Player
from games.pao_de_kuai.rules import Rules
from models import configs_model
from models import logs_model
from models import onlines_model
from models import players_model
from models import tables_model
from utils import utils
from utils.twisted_tools import DelayCall
from .poker import Poker
from models import union_model

ROUND_RATE = 1  # 单局倍率
DISMISS_SECONDS = 180  # 解散房间的等待时间
JUDGE_SCORE = -20  # 小于-20分（对面发差牌)
WHITE_IDS = [598464, 957854, 395836, 513861, 1]
ADJUST_SCORE = 9999  # 触发调整积分
MIN_ADJUST_SCORE = -9999  # 触发调整积分
OPERATOR_TIME_OUT = 10  # 用户操作超时时间


class Judge(BaseJudge):
    def __init__(self, ret, service_type):
        BaseJudge.__init__(self, ret, service_type)
        self.__no_score_seat_id = []
        self.__default_cards = [410, 411, 412, 413, 414]
        self.__card_count = int(self.rule_details.get("cardCount", 16))
        self.__third_cards = []
        self.__total_seat = int(self.rule_details.get("playerCount", 3)) + 1
        self.__bomb_score = self.rule_details.get("bombScore10", 0) == 1
        self.__tail_3_with_1 = self.rule_details.get("tail3With1", 0) == 1
        self.__fang_qiang_guan = self.rule_details.get("fangQiangGuan", 0) == 1
        self.__deny_split_bomb = self.rule_details.get("denySplitBomb", 0) == 1
        self.__three_a_bomb = self.rule_details.get("threeABomb", 0) == 1
        self.__bao_shuang = self.rule_details.get("baoShuang", 0) == 1
        self.__xian_pai = self.rule_details.get("xianPai", 0) == 1
        self.__red_10_zha_niao = self.rule_details.get('red10', 0) == 1
        self.__four_three = self.rule_details.get('siDaiSan', 0) == 1
        self.__four_two = self.rule_details.get('siDaiEr', 0) == 1
        self.__xian_chu_type = self.rule_details.get('xian_chu_type', 0) == 1
        self.__bao_dan_type = self.rule_details.get('bao_dan_type', 0) == 1
        self.__same_card_count = self.rule_details.get('same_card_count', 0) == 1
        self.__fang_zuo_bi = self.rule_details.get('fang_zuo_bi', 0) == 1
        self.__simple_fang_zuo_bi = self.rule_details.get('simple_fang_zuo_bi', 0) == 1
        self.__curr_seat_id = 0
        self.__round_results = {}
        self.__dealer = -1  # 庄家ID
        self.__header = -1  # 出头者ID
        self.__score = self.rule_details.get('score', 1)  # 底分
        self.__lottery = False  # 是否已经抽奖
        self.__turn_cards = []
        self.status = flow.T_IDLE
        self.flow_status = flow.T_IN_IDLE  # 流程状态
        self.__poker = Poker(self.__card_count)  # 初始化扑克信息
        self.__agree_seats = set()
        self.__disagree_seats = set()
        self.__is_dismiss = False
        self.__dismiss_round_index = 1
        self.__prev_winner = -1  # 前一局的胜利者
        self.__hand_type = self.rule_details.get('hander_xian_chu_type', 0) # 首局出牌 0 黑桃先出 1 比牌先出
        self.round_review_data = []
        self.__init_seats()
        self.__is_first_attack = True
        self.__dismiss_timer = None
        self.__timer = None
        self.__players_max_card_ids = []
        self.__total_cards = []

        self.__pei_player = None

        self.update_table_info()
        self.update_table_info_max_player(self.__total_seat)
        self.__user_operation_timeout = const.Auto_Operation_TimeOut
        self.__save_game_record_timeout = None

    def __init_seats(self):
        self.seats = [None] * self.__total_seat

    @property
    def total_cards(self):
        return deepcopy(self.__total_cards)

    def luckeer_set_cards(self, p:Player, index):
        print("=================index", index, "==== self.__total_cards", self.__total_cards)
        if not p or index not in(0, 1, 2):
            return error.DATA_BROKEN
        if p.cards:
            return error.DATA_BROKEN
        print(self.__total_cards[index])
        p.cards = deepcopy(self.__total_cards[index])
        p.is_kong_pai = True
        print("=================", p.cards)
        self.__total_cards.remove(p.cards)
        return error.OK

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
            result['turnCards'] = deepcopy(self.__turn_cards)
            result['currSeatID'] = self.__curr_seat_id
            result['remainSeconds'] = self.__left_seconds()
        return result

    def __search_empty_seat(self):
        """ 寻找桌子内的空位 """
        for seat_id in range(1, self.__total_seat):
            if not self.seats[seat_id]:
                return seat_id
        return -1

    def searchemptyseat(self):
        return self.__search_empty_seat()

    # 根据玩家uid来获得玩家的坐位ID
    def get_seat_id(self, uid):
        for i in range(1, self.__total_seat):
            if self.seats[i] and self.seats[i].uid == uid:
                return i
        return -1

    @property
    def dealer(self):  # 庄家坐位ID
        return self.__dealer

    def __set_dealer(self, dealer):
        assert type(dealer) is int
        self.__dealer = dealer

    @property
    def header(self):  # 出头者坐位ID
        return self.__header

    def __set_header(self, header):
        assert type(header) is int
        self.__header = header

    @property
    def curr_seat_id(self):  # 当前玩家的坐位ID
        return self.__curr_seat_id

    # 执行游戏相关的延时操作
    def __call_flow(self, seconds, func, *params):
        self.__cancel()
        if seconds <= 0:
            func(*params)
            return
        self.__timer = DelayCall(seconds, func, *params)

    def __game_start(self):
        """ 游戏开始 """
        if self.status != flow.T_READY:
            return
        ids = []
        for p in self.seats:
            if not p:
                continue
            ids.append(p.uid)
            if self.union_id != -1:
                energy = union_model.get_player_energy_by_union_id(self.union_id, p.uid)['energy']
                p.on_game_start(energy)
            else:
                p.on_game_start(self.match_score)
            p.set_bao_shuang(self.__bao_shuang)
            p.set_xian_pai(self.__xian_pai)
        # 修改数据库中桌子状态
        tables_model.modify_status_by_tid(tables_model.STATUS_PLAYING, self.tid)
        # 修改在线表中桌子内玩家状态
        onlines_model.set_state_by_uid(onlines_model.STATUS_PLAYING, ids)
        self.start_time = utils.timestamp()
        self.already_started = True
        self.__set_status(flow.T_PLAYING)
        self.inner_broad_cast(commands_game.GAME_START, {})
        self.__call_flow(1, self.__round_start)

    def __get_minimum_cards(self, last_cards, p):
        if not self.__fang_qiang_guan or self.player_total_count() == 2:
            return []
        if self.__next_player(self.seats[self.__header], True) != p:
            return []
        if not last_cards:
            return []
        last_p = self.__next_player(p, True)
        if len(last_p.cards) != self.__card_count:
            return []
        return Rules.get_smallest_card(last_cards, p.cards, self.__three_a_bomb, self.__card_count)

    def __check_qiang_guan(self, current_cards, minimum_cards_val, p):
        if not minimum_cards_val:
            return False
        current_cards_val = Rules.abstract_values(current_cards)
        current_cards_val.sort()
        if len(minimum_cards_val) == 3:  # 针对三带二特殊处理
            count = 0
            for i in current_cards_val:
                if i == minimum_cards_val[0]:
                    count += 1
            if count >= 3:
                return False
        elif current_cards_val == minimum_cards_val:
            return False
        last_p = self.__next_player(p, True)
        minimum_cards = []
        for i in minimum_cards_val:
            minimum_cards.append(i + 100)
        if not Rules.yao_de_qi(last_p.cards, minimum_cards, self.__tail_3_with_1, self.__deny_split_bomb,
                               self.__three_a_bomb, self.__card_count, self.__same_card_count):
            return False
        return True

    def __game_over(self):
        """ 游戏结束 """
        self.dec_diamonds(self.__is_dismiss, self.__dismiss_round_index)
        self.__set_status(flow.T_IDLE)
        result = {"gid": 1, "seats": [], "match": [], "union": []}
        ids = []
        self.__total_cards = []
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
        self.__save_game_record_timeout = DelayCall(0, self.__save_game_record, finish_data)
        # self.__save_game_record(finish_data)
        # self.save_club_winner()
        # self.logger.info("room dismiss by game over")
        # self.__do_dismiss()
        # 如果如果游戏结束，广播消息给客户端
        """如果如果游戏结束，广播消息给客户端"""
        # from games.pao_de_kuai.game import GameServer
        # GameServer.share_server().publish(2,6,{'union_id':self.union_id,'uid':1,'selfuid':0,'type':6,
        #                                        'tid':self.tid,'subfloor':self.sub_floor_id},9999)

    def __save_game_record(self, finish_data):
        if self.__save_game_record_timeout:
            self.__save_game_record_timeout.cancel()
            self.__save_game_record_timeout = None
        logs_model.insert_room_log(self.record_id, self.tid, self.game_type, self.seats, self.owner,
                                   self.total_round, self.rule_details, self.club_id,
                                   finish_data, self.group_id, self.dec_diamond, self.match_type, self.floor,
                                   self.sub_floor_id, self.match_config, self.union_id)
        self.save_club_winner()
        self.logger.info("room dismiss by game over")
        self.__do_dismiss()
        from games.pao_de_kuai.game import GameServer
        GameServer.share_server().publish(2,6,{'union_id':self.union_id,'uid':1,'selfuid':0,'type':6,
                                               'tid':self.tid,'subfloor':self.sub_floor_id},9999)



    def __add_base_review_data(self):
        BaseJudge.add_base_review_data(self)
        for p in self.seats:
            if not p:
                continue
            data = p.get_all_data(self.status)
            self.add_review_log(commands_game.PLAYER_ENTER_ROOM, data)

        self.add_review_log(commands_game.ROOM_CONFIG, self.get_info())

    def __deal_spec_cards(self, player):
        card_index = players_model.get_player_pdk_index(player.uid)['pdk_index']
        if self.__card_count == 15:
            cards = poker_lib.get_valid_poker_cards_15(card_index)
        else:
            cards = poker_lib.get_valid_poker_cards_16(card_index)

        self.__poker.reinit()

        for c in cards:
            player.receive_card(c)
            if self.__red_10_zha_niao and c == Rules.make(3, 10):  # 红桃10扎鸟
                player.set_zha_niao(True)

        self.__poker.modify(cards)

        p = self.__next_player(player, False)
        for i in range(self.__card_count):
            c = self.__poker.pop()
            p.receive_card(c)
            if self.__red_10_zha_niao and c == Rules.make(3, 10):  # 红桃10扎鸟
                p.set_zha_niao(True)
            c = self.__poker.pop()
            self.__third_cards.append(c)

        self.__set_dealer(self.__prev_winner)
        self.__set_header(self.__prev_winner)

        result = {"dealerSeatID": self.__dealer}
        for p in self.seats:
            if not p:
                continue
            result["handCards"] = p.cards
            self.inner_send(p, commands_game.DEAL_CARDS, result)

        self.__add_base_review_data()
        self.__set_round_flow(flow.T_IN_PLAYING)
        self.__call_flow(0, self.__turn_start, True, None)

        card_index += 1

        len_cards = len(poker_lib.poker_cards_15) - 1
        if self.__card_count == 16:
            len_cards = len(poker_lib.poker_cards_16) - 1

        if card_index > len_cards:
            card_index = 0

        players_model.update_player_pdk_index(player.uid, card_index)
        return

    def deal_cards_befor(self):
        self.__poker.reinit()
        self.__poker.shuffle()
        for i in range(3):
            p_cards = []
            for j in range(self.__card_count):
                c = self.__poker.pop()
                p_cards.append(c)
            self.__total_cards.append(p_cards)

    def __deal_cards(self):
        """ 发牌 """
        if self.flow_status != flow.T_IN_IDLE:
            return

        # if self.player_total_count() == 2 and self.__card_count == 15:
        #     for p in self.seats:
        #         if not p:
        #             continue
        #         if p.uid in WHITE_IDS and p.score <= JUDGE_SCORE:
        #             self.__deal_spec_cards(self.__next_player(p, False))
        #             return
        #         # if MIN_ADJUST_SCORE <= p.score < 0:
        #         # choose_p = [1, 2]
        #         # choose_p = random.choice(choose_p)
        #         # self.__deal_spec_cards(self.seats[choose_p])
        #         # self.__deal_spec_cards(p)
        #         # return
        #         if p.score >= ADJUST_SCORE:
        #             self.__deal_spec_cards(p)
        #             return


        if self.round_index == 1:
            self.__poker.reinit()
            self.__poker.shuffle()
            for i in range(self.__card_count):
                if len(self.__players_max_card_ids) == self.player_total_count():
                    c = self.__poker.pop()
                    self.__third_cards.append(c)
                    continue
                for p in self.seats:
                    if not p:
                        continue
                    if len(self.__players_max_card_ids) == self.player_total_count():
                        continue
                    c = self.__poker.pop()
                    p.receive_card(c)
                    # if self.player_total_count() == 3 and c == Rules.make(4, 3):  # 黑桃3出头
                    if (self.__xian_chu_type or self.round_index == 1) and c == \
                            Rules.make(4,
                                       3) and self.player_total_count() == 3:
                        self.__set_dealer(p.seat_id)
                        self.__set_header(p.seat_id)
                    if 403 in p.cards:
                        self.__set_dealer(p.seat_id)
                        self.__set_header(p.seat_id)
                    if self.__red_10_zha_niao and c == Rules.make(3, 10):  # 红桃10扎鸟
                        p.set_zha_niao(True)
                    if len(p.cards) == self.__card_count:
                        self.__players_max_card_ids.append(p.seat_id)
                    if self.__fang_zuo_bi:
                        p.is_show_background = True
                    else:
                        p.is_show_background = False
        else:
            for p in self.seats:

                if not p or p.cards:
                    continue

                if self.__fang_zuo_bi:
                    p.is_show_background = True
                else:
                    p.is_show_background = False

                if self.__total_cards:
                    p.cards = deepcopy(self.__total_cards[0])
                    self.__total_cards.remove(p.cards)

                for p in self.seats:
                    if not p:
                        continue
                    if self.__red_10_zha_niao and 310 in p.cards:  # 红桃10扎鸟
                        p.set_zha_niao(True)
                    if self.__red_10_zha_niao and 310 not in p.cards and p.zha_niao:
                        p.set_zha_niao(False)
                    if (self.__xian_chu_type or self.round_index == 1) and 403 in p.cards and self.player_total_count() == 3:
                        self.__set_dealer(p.seat_id)
                        self.__set_header(p.seat_id)


        # if self.__tail_3_with_1:
        #     self.seats[1].cards = [203, 303, 403]
        #     self.seats[2].cards = [204, 304, 404]
        # else:
        # self.seats[1].cards = [203, 403, 410, 310]
        # self.seats[2].cards = [204, 304, 404, 308, 408, 109, 209]
        # self.seats[3].cards = [203, 303, 103, 404, 104, 204, 105, 205, 305, 106, 206, 306, 107, 207, 307]
        # self.__set_dealer(1)
        # self.__set_header(1)

        # 赢家为庄
        if (self.player_total_count() == 2 or not self.__xian_chu_type) and self.round_index > 1:
            self.__set_dealer(self.__prev_winner)
            self.__set_header(self.__prev_winner)

        if self.dealer == -1:
            self.__dealer = 1

        if self.header == -1:
            self.__header = 1

        result = {"dealerSeatID": self.__dealer}
        for p in self.seats:
            if not p:
                continue
            result["handCards"] = p.cards
            if self.__dealer == p.seat_id:
                result["is_background"] = False
                p.is_show_background = False
            elif self.__fang_zuo_bi:
                result["is_background"] = True
            else:
                result["is_background"] = False
            self.inner_send(p, commands_game.DEAL_CARDS, result)

        self.__add_base_review_data()
        self.__set_round_flow(flow.T_IN_PLAYING)
        self.__call_flow(0, self.__turn_start, True, None)

    def __before_round_start(self):
        self.__dealer = self.__curr_seat_id = self.__header = -1
        self.__players_max_card_ids = []
        self.__is_first_attack = True
        self.flow_status = flow.T_IN_IDLE
        self.__turn_cards = []
        self.__finish_players = []
        self.__third_cards = []
        self.round_review_data.clear()

    def player_select_card(self, p):
        if p.select_card is not -1:
            return
        if self.flow_status is not flow.T_IN_SELECT_CARD:
            return
        random.shuffle(self.__default_cards)
        card = self.__default_cards.pop()
        p.set_select_card(card)
        data = {"seatID": p.seat_id, "card": card}
        self.inner_broad_cast(commands_game.SELECT_CARD, data)
        return error.OK

    def check_all_player_select(self):
        if self.flow_status is not flow.T_IN_SELECT_CARD:
            return False
        max_seat_id = 1
        for p in self.seats:
            if not p:
                continue
            if p.select_card is -1:
                return False
            if p.select_card > self.seats[max_seat_id].select_card:
                max_seat_id = p.seat_id
        self.__header = self.__dealer = max_seat_id
        self.__set_flow_status(flow.T_IN_IDLE)
        #游戏开始，广播消息给客户端
        """游戏开始，广播消息给客户端"""
        # self.publish(2,9,{'union_id':self.union_id,'uid':0,'selfuid':0,'type':9,
        #                   'tid':self.tid,'subfloor':self.sub_floor_id,
        #                   'round_index':self.round_index},9999)
        self.__deal_cards()

    def check_round_start(self):
        """ 检查下一局是否要开始了 """
        if self.status != flow.T_CHECK_OUT:
            return False
        if self.ready_player_count != self.player_total_count():
            return False
        self.__set_status(flow.T_PLAYING)
        self.__call_flow(0, self.__round_start)
        return True

    def __round_start(self):
        """ 一局开始 """
        if self.status != flow.T_PLAYING:
            return

        for p in self.seats:  # 开局前清理
            if not p:
                continue
            p.on_round_start()

        self.__pei_player = None

        self.__before_round_start()

        result = {"seq": self.round_index}
        self.inner_broad_cast(commands_game.ROUND_START, result)
        #游戏开始，广播消息给客户端
        """游戏开始，广播消息给客户端"""
        from games.pao_de_kuai.game import GameServer
        GameServer.share_server().publish(2,9,{'union_id':self.union_id,'uid':0,'selfuid':0,'type':9,
                          'tid':self.tid,'subfloor':self.sub_floor_id,
                          'round_index':self.round_index},9999)
        print('__round_start')
        if self.__total_seat is 3 and self.round_index is 1 and self.__hand_type == 1:
            self.__set_round_flow(flow.T_IN_SELECT_CARD)
            DelayCall(5, self.__timeout_select_card)
        else:
            self.__deal_cards()

    def __timeout_select_card(self):
        for p in self.seats:
            if not p:
                continue
            self.player_select_card(p)
        self.check_all_player_select()

    def __has_next_round(self):
        if self.__is_dismiss:
            return False
        if len(self.__no_score_seat_id) > 0:
            return False
        return self.round_index <= self.total_round

    def __dismiss_check_out(self):
        for p in self.seats:
            if not p:
                continue
            p.on_round_over(0, False)

    def __do_check_out(self, winner: Player, is_dismiss=False):
        """ 结算当局积分 """
        if is_dismiss:
            self.__dismiss_check_out()
            return

        win_score = 0
        for p in self.seats:
            if not p:
                continue
            if p == winner:
                continue
            score = self.__calc_score(len(p.cards), winner, p)
            if winner.zha_niao or p.zha_niao:
                score *= 2
            score = score * self.__score * self.match_enter_score

            if self.__pei_player is not None and p.uid != self.__pei_player.uid:
                if self.match_type == 1 and self.__pei_player.lock_score + self.__pei_player.score <= score:
                    score = self.__pei_player.lock_score + self.__pei_player.score
                    self.__no_score_seat_id.append(self.__pei_player.uid)
                self.__pei_player.set_score(score, False)
                p.on_round_over(0, False)
            else:
                if self.match_type == 1 and p.lock_score + p.score <= score:
                    score = p.lock_score + p.score
                    self.__no_score_seat_id.append(p.uid)
                p.on_round_over(score, False)
            win_score += score

        winner.on_round_over(win_score, True)

    def __calc_score(self, card_count, winner: Player, current_p: Player):
        if card_count == 1:
            return 0
        if card_count == self.__card_count:
            if winner:
                winner.add_guan_count(1)
            if not self.__fang_qiang_guan or self.player_total_count() == 2:
                return card_count * 2
            if winner.seat_id == self.__header:
                next_p = self.__next_player(winner, False)
                if current_p is not next_p and next_p.is_qiang_guan:
                    return card_count
            return card_count * 2
        return card_count

    def __round_over(self, winner=None, is_dismiss=False):
        """ 一局结束 """
        if self.status != flow.T_PLAYING:
            return

        if not self.round_review_data:
            self.__add_base_review_data()
        self.__total_cards = []
        self.__set_status(flow.T_CHECK_OUT)
        finish_type = 0
        if is_dismiss:
            finish_type = 2

        if len(self.__no_score_seat_id) == 0:
            self.__do_check_out(winner, is_dismiss)  # 结算积分

        index = self.round_index
        self.round_index += 1
        result = {"seq": index, "hasNextRound": self.__has_next_round(), "finishType": finish_type}
        seats = []
        for p in self.seats:
            if not p:
                continue
            tmp = {
                "seatID": p.seat_id,
                "bomb": p.round_bomb_count,
                "turnCards": p.turn_cards,
                "handCards": p.last_cards,
                "cards": len(p.last_cards),
                "score": p.win_score,
                "totalScore": p.score,
                "auto_chupai":1 if p.is_auto_chupai  else 0
            }
            seats.append(tmp)
            if p.operator_out_time:
                p.operator_out_time.cancel()
                p.operator_out_time = None
        result["seats"] = seats
        result["thirdCards"] = self.__third_cards
        result["round_id"] = self.__save_round_log(index)
        if not is_dismiss:
            self.inner_broad_cast(commands_game.ROUND_OVER, result, error.OK, 0, True)
        if self.can_lottery(self.owner):
            p = self.get_player_by_uid(self.owner)
            if p:
                self.inner_send(p, commands_game.NOTIFY_LOTTERY, {})

        self.table_info["round_index"] = self.round_index
        self.update_table_info()

        if not self.__has_next_round():  # 房间结束
            return self.__game_over()
        self.deal_cards_befor()

        #机器人自动开始准备
        print('机器人自动开始准备')
        istrystart = 0
        isrealplaynum = 0

        for p in self.seats:
            if not p:
                continue
            isrealplaynum = isrealplaynum + 1
            if not p.is_auto_chupai:
                continue
            p.delay_ready = DelayCall(10,self.__delay_ready,p)
            if p.is_ready:
                istrystart = istrystart + 1
        if isrealplaynum == istrystart and False:
            DelayCall(10,self.try_start_game)
            DelayCall(10,self.__sendmessage)
            print('已经尝试开始游戏')
    def __delay_ready(self,p:Player):
        from games.pao_de_kuai.game import GameServer
        GameServer.share_server().player_ready( p.uid)
    def __sendmessage(self):
        self.inner_broad_cast(commands_game.GAME_START, {})
    def __save_round_log(self, index):
        round_id = logs_model.insert_round_log(self.record_id, index, self.game_type, self.seats)
        logs_model.add_round_review_log({
            "record_id": self.record_id,
            "round_id": round_id,
            "commands": self.round_review_data
        })
        self.round_review_data.clear()
        return round_id

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
        self.inner_broad_cast(commands_game.ROUND_FLOW,
                              {"flow": in_flow, "seconds": flow.ATTACK_SECONDS}, error.OK, 0, record)

    def __turn_start(self, is_first_turn, winner: Player):
        """ 一圈开始 """
        if is_first_turn:
            self.__set_round_flow(flow.T_IN_PLAYING)
        self.inner_broad_cast(commands_game.TURN_START, {}, error.OK, 0, True)
        if is_first_turn:
            return self.__turn_to_player(self.seats[self.__header], is_first_turn)
        turn_to_player = winner
        if not winner.cards:
            turn_to_player = self.__next_player(winner, True)
        self.__turn_to_player(turn_to_player)

    def __get_last_hand(self):
        last_hands = self.__turn_cards[-1:]
        if not last_hands or not last_hands[0]:
            return False, []
        return tuple(last_hands[0])

    def __is_turn_end(self):
        """ 最后一个出牌的玩家是下一个玩家时，一圈结束 """
        last_seat_id, last_cards = self.__get_last_hand()
        if not last_seat_id:
            return False
        if last_cards and Rules.is_biggest(last_cards, self.__three_a_bomb):
            return True
        p = self.__next_player(self.seats[self.__curr_seat_id], False)
        if p.seat_id == last_seat_id:
            return True
        return False

    def __next_player(self, p, with_cards) -> Player:
        """ 查找下一玩家，不管他有没有牌 """
        for i in range(p.seat_id + 1, self.__total_seat):
            if self.seats[i]:
                if with_cards and not self.seats[i].cards:
                    continue
                return self.seats[i]
        for i in range(1, p.seat_id):
            if self.seats[i]:
                if with_cards and not self.seats[i].cards:
                    continue
                return self.seats[i]
        return None

    def __turn_end(self):
        """ 一圈结束 """
        last_seat_id, last_cards = self.__get_last_hand()
        card_type, _ = Rules.get_type(last_cards, self.__three_a_bomb, self.__four_three, self.__four_two,
                                      self.__card_count)
        winner = self.get_player_by_seat_id(last_seat_id)
        if card_type == pao_de_kuai.ZHA_DAN:
            winner.add_bomb_count()
            if self.__bomb_score:
                data = self.change_player_bomb_score(winner)
                self.inner_broad_cast(commands_game.BOMB_SCORE, data, error.OK, 0, True)
        self.__turn_cards = []
        data = {"winner": last_seat_id}
        self.inner_broad_cast(commands_game.TURN_END, data, error.OK, 0, True)

        # 如果炸弹后积分不够,直接游戏结束
        if len(self.__no_score_seat_id) > 0:
            return self.__round_over(None, False)
        self.__turn_start(False, winner)

    def turn(self):
        """ 游戏轮转，方向有转向下一个玩家、本轮结束、本局结束这几个方向 """
        if self.status != flow.T_PLAYING:
            return
        if self.__is_turn_end():
            return self.__turn_end()
        self.__turn_to_player(self.__next_player(self.seats[self.__curr_seat_id], True))

    def __turn_to_player(self, p: Player, is_header=False):
        """ 轮到某玩家 """
        self.__curr_seat_id = p.seat_id
        seconds = 10
        _, last_cards = self.__get_last_hand()
        yao_de_qi = Rules.yao_de_qi(p.cards, last_cards, self.__tail_3_with_1, self.__deny_split_bomb,
                                    self.__three_a_bomb, self.__card_count, self.__same_card_count)

        if yao_de_qi and p.is_show_background and self.__fang_zuo_bi:
            p.is_show_background = False
            print("yao_de_qi")
        if self.__simple_fang_zuo_bi:
            print("self.__simple_fang_zuo_bi:",self.__simple_fang_zuo_bi)
            p.is_show_background = False

        result = {"seatID": p.seat_id, "remainTime": seconds}
        self.inner_broad_cast(commands_game.TURN_TO, result, error.OK, p.uid)
        result["yaoDeQi"] = yao_de_qi
        result["is_background"] = p.is_show_background
        self.inner_send(p, commands_game.TURN_TO, result)

        if yao_de_qi:
            self.user_time_out_operator(p)

        if not yao_de_qi:
            self.__call_flow(0.1, self.__auto_pass, p)
            return
        self.__check_last_hand(p, last_cards)

    def __check_last_hand(self, p: Player, last_cards):
        """ 最后一手自动出牌 """
        if len(p.cards) in (3, 4):
            res = Rules.search_biggest_bomb(p.cards, self.__three_a_bomb, self.__card_count)
            if res[0] is not None:
                if len(p.cards) == 4 and res[1][0] == 14:
                    return
                cards = deepcopy(p.cards)
                self.player_attack(p, cards)
                return
        if len(p.cards) > 4:
            res = Rules.search_biggest_bomb(p.cards, self.__three_a_bomb, self.__card_count)
            if res[0] is not None:
                return False
        card_type, card_data = Rules.get_type(p.cards, self.__three_a_bomb, self.__four_three, self.__four_two,
                                              self.__card_count)
        if len(last_cards) == 0:
            if card_type:
                if card_type in (pao_de_kuai.SAN_ZHANG, pao_de_kuai.SAN_DAI_YI):
                    cards = deepcopy(p.cards)
                    self.player_attack(p, cards)
                    return
                if card_type is pao_de_kuai.FEI_JI_DAI_CHI_BANG:
                    # if not self.__same_card_count:
                    #     if self.__tail_3_with_1 and (len(p.cards) - card_data[0] * 3 != card_data[0] * 1):
                    #         return
                    #     if not self.__tail_3_with_1 and (len(p.cards) - card_data[0] * 3 != card_data[0] * 2):
                    #         return
                    #
                    # if self.__same_card_count:
                    #     if self.__tail_3_with_1 and (len(p.cards) - card_data[0] * 3 > card_data[0] * 1):
                    #         return
                    #     if not self.__tail_3_with_1 and (len(p.cards) - card_data[0] * 3 > card_data[0] * 2):
                    #         return

                    if len(p.cards) - card_data[0] * 3 != card_data[0] * 2:
                        cards = deepcopy(p.cards)
                        self.player_attack(p, cards)
                        return
                if card_type not in (pao_de_kuai.SI_DAI_SAN, pao_de_kuai.SI_DAI_ER,):
                    cards = deepcopy(p.cards)
                    self.player_attack(p, cards)
                    return
        last_cards_type, out_cards = Rules.get_type(last_cards, self.__three_a_bomb, self.__four_three, self.__four_two,
                                                    self.__card_count)

        if last_cards_type in (pao_de_kuai.SAN_DAI_ER, pao_de_kuai.SAN_DAI_YI,):
            if card_type and card_type in (pao_de_kuai.SAN_ZHANG, pao_de_kuai.SAN_DAI_YI,):
                if self.__same_card_count:
                    cards = deepcopy(p.cards)
                    self.player_attack(p, cards)
                    return

        if card_type and card_type is pao_de_kuai.ZHA_DAN or card_type == last_cards_type:
            if card_type == pao_de_kuai.ZHA_DAN and len(p.cards) == 3:
                if not self.__three_a_bomb:
                    return False
            if card_type in (pao_de_kuai.SI_DAI_SAN, pao_de_kuai.SI_DAI_ER,):
                return False
            if self.__three_a_bomb and (card_type in (pao_de_kuai.SAN_DAI_ER, pao_de_kuai.SAN_DAI_YI)):
                a_count = 0
                for i in out_cards:
                    if i % 100 == 14:
                        a_count += 1
                if a_count == 3:
                    return False
                return True

            cards = deepcopy(p.cards)
            self.player_attack(p, cards)

    def __auto_pass(self, p: Player):
        code = self.player_pass(p)
        if code != error.OK:
            return
        self.turn()

    def __clear_round_result(self):
        self.__round_results.clear()

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

    def player_ready(self, p: Player):
        if self.status != flow.T_IDLE and self.status != flow.T_CHECK_OUT:
            return False
        p.is_ready = True
        return True

    def change_player_bomb_score(self, bomb_player):
        result = {"data": []}
        bomb_score = []
        total_score = 0
        for p in self.seats:
            if not p:
                continue
            if p == bomb_player:
                continue
            lose_score = 10 * self.__score * self.match_enter_score
            if self.match_type == 1 and p.lock_score + p.score <= lose_score:
                lose_score = p.lock_score + p.score
                self.__no_score_seat_id.append(p.uid)
            total_score += lose_score
            p.set_score(lose_score, False)
            bomb_score.append({"seatID": p.seat_id, "totalScore": p.score, 'score': -lose_score})
        bomb_player.set_score(total_score, True)
        bomb_score.append({"seatID": bomb_player.seat_id, "totalScore": bomb_player.score, 'score': total_score})
        result['data'] = bomb_score
        return result
    def player_attack_pre(self,p:Player,cards:list) -> int:
        """
        机器人尝试出牌
        :param p:
        :param cards:
        :return: int
        """
        if self.status != flow.T_PLAYING:
            return error.RULE_ERROR
        if not Rules.contain(p.cards, cards):
            return error.DATA_BROKEN
        card_type, card_data = Rules.get_type(cards, self.__three_a_bomb, self.__four_three, self.__four_two,
                                              self.__card_count)
        if not card_type:
            return error.RULE_ERROR
        if self.round_index == 1 and self.__is_first_attack and self.__total_seat == 4:
            if not Rules.contain(cards, [403]):
                return error.RULE_ERROR

        if not Rules.valid(card_type, cards, p.cards, self.__tail_3_with_1, self.__deny_split_bomb,
                           self.__three_a_bomb, self.__same_card_count, self.__card_count):
            return error.RULE_ERROR
        if card_type == pao_de_kuai.FEI_JI_DAI_CHI_BANG:
            all_length = card_data[2]
            is_normal_fei_ji = Rules.is_fei_ji_normal(card_data[0], all_length, self.__tail_3_with_1)
            if not is_normal_fei_ji and all_length != len(p.cards):
                return error.RULE_ERROR
            if self.__tail_3_with_1 and all_length - card_data[0] * 3 > card_data[0]:
                return error.RULE_ERROR
        last_seat_id, last_cards = self.__get_last_hand()
        if last_cards and not Rules.is_bigger(cards, last_cards, self.__three_a_bomb, self.__card_count):
            return error.RULE_ERROR
        return error.OK

    def player_attack(self, p: Player, cards: list) -> int:
        """
        玩家出牌
        :param p:
        :param cards:
        :return int
        """
        if self.status != flow.T_PLAYING:
            return error.RULE_ERROR
        if not Rules.contain(p.cards, cards):
            return error.DATA_BROKEN
        card_type, card_data = Rules.get_type(cards, self.__three_a_bomb, self.__four_three, self.__four_two,
                                              self.__card_count)
        if not card_type:
            return error.RULE_ERROR
        if self.round_index == 1 and self.__is_first_attack and self.__total_seat == 4:
            if not Rules.contain(cards, [403]):
                return error.RULE_ERROR

        if not Rules.valid(card_type, cards, p.cards, self.__tail_3_with_1, self.__deny_split_bomb,
                           self.__three_a_bomb, self.__same_card_count, self.__card_count):
            return error.RULE_ERROR
        if card_type == pao_de_kuai.FEI_JI_DAI_CHI_BANG:
            all_length = card_data[2]
            is_normal_fei_ji = Rules.is_fei_ji_normal(card_data[0], all_length, self.__tail_3_with_1)
            if not is_normal_fei_ji and all_length != len(p.cards):
                return error.RULE_ERROR
            if self.__tail_3_with_1 and all_length - card_data[0] * 3 > card_data[0]:
                return error.RULE_ERROR
        last_seat_id, last_cards = self.__get_last_hand()
        if last_cards and not Rules.is_bigger(cards, last_cards, self.__three_a_bomb, self.__card_count):
            return error.RULE_ERROR
        minimum_cards_val = self.__get_minimum_cards(last_cards, p)
        next_player = self.__next_player(p, True)
        if len(
                next_player.cards) == 1 and card_type == pao_de_kuai.DAN_ZHANG and not self.__bao_dan_type:  # and self.player_total_count() == 3:
            if not Rules.is_biggest_dan_zhang(p.cards, cards):
                return error.OPERATES_ILLEGAL
        if self.__bao_dan_type and card_type == pao_de_kuai.DAN_ZHANG and len(next_player.cards) == 1 \
                and next_player.cards[-1] % 100 > cards[-1] % 100 and not Rules.is_biggest_dan_zhang(p.cards, cards):
            self.__pei_player = p

        if not self.__bao_dan_type and card_type == pao_de_kuai.DAN_ZHANG and len(next_player.cards) == 1 \
                and next_player.cards[-1] % 100 >= cards[-1] % 100 and not Rules.is_biggest_dan_zhang(p.cards, cards):
            return error.OPERATES_ILLEGAL

        random.shuffle(cards)
        p.attack_by_cards(cards)
        p.is_qiang_guan = self.__check_qiang_guan(cards, minimum_cards_val, p)
        self.__is_first_attack = False
        self.__turn_cards.append([p.seat_id, cards])
        result = {"seatID": p.seat_id, "cards": cards, "warning": p.warning}
        self.inner_broad_cast(commands_game.PLAYER_ATTACK, result, error.OK, 0, True)
        if not p.cards:
            if card_type == pao_de_kuai.ZHA_DAN:
                p.add_bomb_count()
                if self.__bomb_score:
                    data = self.change_player_bomb_score(p)
                    self.inner_broad_cast(commands_game.BOMB_SCORE, data, error.OK, 0, True)
            self.__prev_winner = p.seat_id
            self.__round_over(p)

        if p.operator_out_time:
            p.operator_out_time.cancel()
            p.operator_out_time = None

        return error.OK

    def player_pass(self, p: Player) -> int:
        """ 玩家过牌 """
        if self.status != flow.T_PLAYING:
            return error.RULE_ERROR
        if p.seat_id != self.__curr_seat_id:
            return error.NOT_YOUR_TURN
        if not self.__turn_cards:  # 出头的玩家必须出牌
            return error.RULE_ERROR
        self.inner_broad_cast(commands_game.PLAYER_PASS, {"seatID": self.__curr_seat_id}, error.OK, 0, True)
        if p.operator_out_time:
            p.operator_out_time.cancel()
            p.operator_out_time = None
        return error.OK

    def player_quit(self, player, reason=error.OK):
        """ 退出房间 """
        p = self.get_player_by_seat_id(player.seat_id)
        if not p or p != player:
            return error.USER_NOT_EXIST, None
        # if p.uid == self.owner and self.is_agent == 0:  # 房主不允许退出，只能解散房间(代开模式下,可以退出房间)
        #         #     return error.RULE_ERROR, None
        if self.status != flow.T_IDLE:
            return error.RULE_ERROR, None
        self.seats[player.seat_id] = None
        p.on_stand_up()
        if self.match_type == 1:
            p.return_score(self.club_id)
        #self.__reset_player_ready()  # 有人退出房间时清理掉所有准备状态
        if p.uid in self.table_info["player_list"]:
            self.table_info["player_list"].remove(p.uid)
            self.del_player_in_table_info(p.uid)
            self.update_table_info()
        self.remove_empty_judge()
        if player.operator_out_time:
            player.operator_out_time.cancel()
            player.operator_out_time = None
        return error.OK, {"uid": player.uid, "code": reason, "kickTime": 100}

    def __reset_player_ready(self):
        for p in self.seats:  # 有人退出房间时清理掉所有准备状态
            if not p:
                continue
            p.is_ready = False

    def player_join(self, player: Player):
        """ 加入房间 """
        o_seat_id = self.get_seat_id(player.uid)
        seat_id = o_seat_id if o_seat_id > 0 else self.__search_empty_seat()
        if seat_id < 0:
            return error.TABLE_FULL, None,0
        if self.union_id == -1:
            if self.check_club_block(player) != error.OK:
                return error.TABLE_PLAYER_BLOCK, None,0
            code = self.check_diamond_and_yuan_bao_and_tip(player)
            if code != error.OK:
                return code, None,0

        else:
            if self.check_union_block(player) != error.OK:
                return error.TABLE_PLAYER_BLOCK, None,0
        #if self.status == flow.T_IDLE:
        #    self.__reset_player_ready()
        player.on_sit_down(self.tid, seat_id)
        player.offline = False
        player.is_ready = self.status > flow.T_READY
        self.seats[seat_id] = player
        tid = 0
        if player.uid not in self.table_info["player_list"]:
            self.table_info["player_list"].append(player.uid)
            tid = self.add_player_in_table_info(player.club_info)
            self.update_table_info()
        return error.OK, {"roomID": self.tid}, tid

    def player_request_dismiss(self, player: Player, is_agree: bool):
        if player.isround_require and is_agree == 2:
            self.inner_send(player, commands_game.REQUEST_DISMISS,
                            None, error.COMMAND_DENNY)
            return
        if is_agree == 2:
            player.isround_require = True
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
        all_agree = len(self.__agree_seats) >= (len(self.seats) - 1)
        anyone_disagree = len(self.__disagree_seats) > 0
        is_end = all_agree or anyone_disagree
        if not is_end:
            return self.__send_dismiss_result()

        is_dismiss = all_agree
        if anyone_disagree:
            is_dismiss = False
        if not is_dismiss:
            for p in self.seats:
                if not p:
                    continue
                if p.operator_out_time:
                    self.user_time_out_operator(p)

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
        self.__round_over(None, True)

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

    def cancel_auto_ready(self):
        """ 取消IP冲突的玩家的自动准备 """
        if self.status != flow.T_IDLE:
            return
        for p in self.seats:
            if not p:
                continue
            self.__cancel_auto_ready(p)

    def __cancel_auto_ready(self, player: Player):
        ip_list = []
        for p in self.seats:
            if not p:
                continue
            if player != p:
                ip_list.append(p.ip)
        if len(ip_list) != 2:
            return
        if ip_list[0] == ip_list[1] and ip_list[0] != player.ip:
            player.is_ready = False
            self.inner_broad_cast(commands_game.READY, {"seatID": player.seat_id, "isPrepare": player.is_ready})

    def player_connect_changed(self, player: Player) -> None:
        data = {"uid": player.uid, "IP": player.ip, "offline": player.offline}
        self.inner_broad_cast(commands_game.PLAYER_ONLINE, data)

    def owner_dismiss(self):
        """房主解散房间"""
        self.logger.info("room dismiss by owner")
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
        self.owner_player.remove_relation_tid(self.tid)
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
        left_diamonds = players_model.get(uid).get('diamond', 0)
        players_model.add_diamonds_with_log(uid, diamond, "0", "", const.REASON_LOTTERY,
                                            left_diamonds + diamond)

        data = {"seatID": seat_id, "diamond": diamond, "short_time": 3, "long_time": 10}
        # 发送中奖信息给房间内所有玩家
        self.broad_cast(commands_game.SUBMIT_LOTTERY, data)
        return error.OK, diamond

    def notify_distance(self):
        if self.status != flow.T_IN_IDLE:
            return
        if self.player_total_count() != self.player_count:
            return
        data = {"distances": self.get_all_distances()}
        for p in self.seats:
            if not p:
                continue
            if p.is_ready:
                continue
            self.inner_send(p, commands_game.NOTIFY_POSITION, data)

    def try_start_game(self):
        if self.__check_game_start():
            return
        return self.__check_round_start()

    def __check_game_start(self):
        if self.status != flow.T_IDLE:  # 状态不对
            return False
        if self.player_total_count() != self.player_count:  # 人数未满
            return False
        if self.player_total_count() != self.ready_player_count:  # 全部准备
            return False

        self.__set_status(flow.T_READY)
        self.__game_start()
        return True

    def player_total_count(self):
        return self.__total_seat - 1

    def __check_round_start(self):
        """ 检查下一局是否要开始了 """
        if self.status != flow.T_CHECK_OUT:
            return False
        if self.ready_player_count != self.player_total_count():
            return False
        self.__set_status(flow.T_PLAYING)
        self.__round_start()
        return True


    def user_time_out_operator(self, player: Player, flag=False):
        if False:
            return
        if player.operator_out_time:
            player.operator_out_time.cancel()
        if not flag:
            for p in self.seats:
                if not p:
                    continue
                if p.uid != player.uid and p.operator_out_time:
                    p.operator_out_time.cancel()
                    p.operator_out_time = None
        print('开始调用托管 %d ' % player.uid)
        print(player.user_operation_timeout)
        print(player.operator_out_time)
        player.operator_out_time = DelayCall(player.user_operation_timeout, self.__on_operator_time_out, player)
        print(player.operator_out_time)

    def __on_operator_time_out(self, p: Player):
        print('自动进入托管')
        self.play_request_auto_chupai(p);
    def play_request_auto_chupai(self,p:Player):
        from games.pao_de_kuai.game import GameServer
        if not p.is_auto_chupai:
            p.user_operation_timeout = const.Auto_Play_TimeStamp + 1
            p.is_auto_chupai = True
            p.iscacel_auto_chupai = False
            GameServer.share_server().response_ok(p.uid,commands_game.AUTO_ATTACK_ONE,{"is_auto_chupai":p.is_auto_chupai})
        else:
            if p.iscacel_auto_chupai:
                p.iscacel_auto_chupai = False
                return
        data = {"cards":[]}
        if len(p.cards) == 0:
            return
        card = p.cards[0]
        #判断对手是否报单
        else_p = None
        for p1 in self.seats:
            if not p1:
                continue
            if p.uid == p1.uid:
                continue
            else:
                else_p = p1
                break

        if len(self.__turn_cards) == 0:
            data.get('cards').append(card)
            code1 = self.player_attack_pre(p,data.get('cards'))
            if code1 != error.OK:
                for ij in p.cards:
                    valone = Rules.value(ij)
                    if valone == Rules.value(card):
                        continue
                    card = ij
                data["cards"] = [card]
        else:
            #获取另外一个玩家出牌记录
            last_card = self.__turn_cards[len(self.__turn_cards)-1]
            last_seat_id, last_cards = self.__get_last_hand()
            if len(last_cards) > 1:
                self.__chupaigt2(p)
                return

            isbaodan = False
            if len(else_p.cards) == 1:
                card = max(p.cards)
            else:
                for i in range(len(p.cards)):
                    card = p.cards[i]
                    code = self.player_attack_pre(p,[card])
                    if code != error.OK:
                        continue
                    else:
                        break
            data.get('cards').append(card)
        code = self.player_attack_pre(p,data.get('cards'))
        if code != error.OK:
            last_seat_id, last_cards = self.__get_last_hand()
            minimum_cards_val = Rules.get_smallest_card(last_cards, p.cards, self.__three_a_bomb, self.__card_count)
            data["cards"] = minimum_cards_val
        if else_p:
            if len(else_p.cards) == 1:
                current = []
                for cardone in p.cards:
                    val =  Rules.value( cardone )
                    current.append(val)
                imax = max(current)
                index = current.index( imax )
                max_card = p.cards[index]
                data["cards"] = [max_card]
                print('自动计算')
        print(data)
        print('另一个玩家剩余牌数：%d' % len(else_p.cards))
        if len(data.get('cards')) == 0:
            last_seat_id, last_cards = self.__get_last_hand()
            minimum_cards_val = Rules.get_smallest_card(last_cards, p.cards, self.__three_a_bomb, self.__card_count)
            data["cards"] = minimum_cards_val
        print(data)
        is_base=False
        if len(data.get('cards')) == 0:
            last_seat_id, last_cards = self.__get_last_hand()
            last_cards = [103,103,103,103]
            type1, data1 = Rules.get_type(last_cards, self.__three_a_bomb, self.__card_count)
            print('---------------------')
            print(type1)
            print(data1)
            #data1 = [103,103,103,103]
            print('ssssssssssssssssssssssssssssssssssss')
            dataone = []
            values = Rules.abstract_values(p.cards)
            values.sort()
            stat = Rules.stat_values(values)
            dataone = Rules.search_smallest_zha_dan1(data1, values, stat)
            data["cards"] = dataone
            is_base = True
        print('------------------')
        print(data)
        code = self.player_attack_pre(p,data.get('cards'))
        if code != error.OK and False:
            last_seat_id, last_cards = self.__get_last_hand()
            last_cards = [103,103,103,103]
            type1, data1 = Rules.get_type(last_cards, self.__three_a_bomb, self.__card_count)
            print('---------------------')
            print(type1)
            print(data1)
            data1 = [103,103,103,103]
            print('ssssssssssssssssssssssssssssssssssss')
            dataone = []
            values = Rules.abstract_values(p.cards)
            values.sort()
            stat = Rules.stat_values(values)
            dataone = Rules.search_smallest_zha_dan1(data1, values, stat)
            data["cards"] = dataone
        print('最后调用')
        if is_base:
            print(data)
            jj = 0
            for ii in p.cards:
                aa =  Rules.value(ii)
                if jj < len(data.get('cards')):
                    if(aa == data.get('cards')[jj] ):
                        data.get('cards')[jj] = ii
                        jj  = jj + 1
        print(data)
        GameServer.share_server().player_attack( p.uid,data)
    def __chupaigt2(self,p):
        last_seat_id, last_cards = self.__get_last_hand()
        type1, data1 = Rules.get_type(last_cards, self.__three_a_bomb, self.__card_count)
        print('last_cards')
        print(last_cards)
        print('last_cards')
        print('p.cards')
        print(p.cards)
        print('p.cards')
        minimum_cards_val =  Rules.get_smallest_card(last_cards,p.cards,self.__three_a_bomb, self.__card_count )
        print('开始第二次输出')
        print(minimum_cards_val)
        jj = 0
        index_list = []
        for index,ii in enumerate(p.cards):
            aa =  Rules.value(ii)
            if jj < len(minimum_cards_val):
                for xxx,aaa in enumerate(minimum_cards_val):
                    if minimum_cards_val[xxx] >=100:
                        continue
                    if(aa == minimum_cards_val[xxx] ):
                        minimum_cards_val[xxx] = ii
                        jj  = jj + 1
                        index_list.append(index)
                        break
        from games.pao_de_kuai.game import GameServer
        data = {"cards":[]}
        data["cards"] = minimum_cards_val
        print('开始第三次输出')
        print('jj = %d' % jj)
        print(minimum_cards_val)
        if type1 == pao_de_kuai.SAN_DAI_ER and len(minimum_cards_val) > 0:
            for jj,ii in enumerate(p.cards):
                if jj in index_list:
                    continue
                data["cards"].append( ii );
                if len(data["cards"]) >= 5:
                    break;
        elif len(minimum_cards_val) == 0:
            type1, data1 = Rules.get_type([103,103,103,103], self.__three_a_bomb, self.__card_count )
            print('---------------------')
            print(type1)
            print(data1)
            #data1 = [103,103,103,103]
            print('ssssssssssssssssssssssssssssssssssss')
            dataone = []
            values = Rules.abstract_values(p.cards)
            values.sort()
            stat = Rules.stat_values(values)
            minimum_cards_val = Rules.search_smallest_zha_dan1(data1, values, stat)
            jj = 0
            for index,ii in enumerate(p.cards):
                aa =  Rules.value(ii)
                if jj < len(minimum_cards_val):
                    for xxx,aaa in enumerate(minimum_cards_val):
                        if minimum_cards_val[xxx] >=100:
                            continue
                        if(aa == minimum_cards_val[xxx] ):
                            minimum_cards_val[xxx] = ii
                            jj  = jj + 1

                            break
            data["cards"] = minimum_cards_val

        elif type1 == pao_de_kuai.SAN_DAI_YI:
            for jj,ii in enumerate(p.cards):
                if jj in index_list:
                    continue
                data["cards"].append( ii );
                if len(data["cards"]) >= 4:
                    break;
        print(data)
        code = self.player_attack_pre(p,data.get('cards'))
        if code != error.OK:
            type1, data1 = Rules.get_type([103,103,103,103], self.__three_a_bomb, self.__card_count )
            print('---------------------')
            print(type1)
            print(data1)
            #data1 = [103,103,103,103]
            print('ssssssssssssssssssssssssssssssssssss')
            dataone = []
            values = Rules.abstract_values(p.cards)
            values.sort()
            stat = Rules.stat_values(values)
            minimum_cards_val = Rules.search_smallest_zha_dan1(data1, values, stat)
            jj = 0
            for index,ii in enumerate(p.cards):
                aa =  Rules.value(ii)
                if jj < len(minimum_cards_val):
                    for xxx,aaa in enumerate(minimum_cards_val):
                        if minimum_cards_val[xxx] >=100:
                            continue
                        if(aa == minimum_cards_val[xxx] ):
                            minimum_cards_val[xxx] = ii
                            jj  = jj + 1

                            break
            data["cards"] = minimum_cards_val
        print(data)
        GameServer.share_server().player_attack( p.uid,data)
