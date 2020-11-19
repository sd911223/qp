# coding:utf-8

from copy import deepcopy

from base.base_player import BasePlayer
from games.niu_niu.rules import Rules
from models import onlines_model

# 玩家状态标志
IN_IDLE = 0  # 空闲中
IN_WAITING = 1  # 等待中(新玩家加入后等待中)
IN_PLAYING = 2  # 游戏中

DEFAULT_SCORE = 0


class Player(BasePlayer):
    def __init__(self, uid):
        BasePlayer.__init__(self, uid)
        self.__current_score = 0
        self.__tui_zhu = False  # 已经推注
        self.__cards = []  # 手牌
        self.__call_score = -1
        self.__call_dealer = -1
        self.__is_show_cards = False
        self.__score = DEFAULT_SCORE
        self.__win_score = 0
        self.__can_call_score = []
        self.__prev_win_score = 0

        self.__win_count = 0
        self.__lose_count = 0
        self.__lock_score = 0

    @property
    def lock_score(self):
        return self.__lock_score

    @property
    def tui_zhu(self):
        return self.__tui_zhu

    @tui_zhu.setter
    def tui_zhu(self, is_tui_zhu):
        self.__tui_zhu = is_tui_zhu

    @property
    def prev_win_score(self):
        return self.__prev_win_score

    def set_can_call_score(self, score):
        self.__can_call_score = deepcopy(score)

    @property
    def current_score(self):
        return self.__current_score

    @property
    def call_dealer(self):
        return self.__call_dealer

    @call_dealer.setter
    def call_dealer(self, call_dealer):
        self.__call_dealer = call_dealer

    @property
    def call_score(self):
        return self.__call_score

    @call_score.setter
    def call_score(self, call_score):
        self.__call_score = call_score

    @property
    def score(self):
        return self.__score

    @property
    def is_show_cards(self):
        return self.__is_show_cards

    @is_show_cards.setter
    def is_show_cards(self, flag):
        self.__is_show_cards = flag

    # 接收扑克牌
    def receive_card(self, card):
        self.__cards.append(card)

    @property
    def round_data(self):
        return {
            "seatID": self.seat_id,
            "callScore": self.__call_score,
            "callDealer": self.__call_dealer,
            "currentScore": self.__current_score,
            "score": self.__score,
        }

    def __clear_cards(self):
        """ 清除所有牌 """
        self.__cards = []

    # 获取玩家的扑克牌
    @property
    def cards(self):
        return self.__cards

    @property
    def game_over_data(self):
        return {
            "seatID": self.seat_id,
            "totalScore": self.score,
        }

    @property
    def in_playing(self):
        return self.status == IN_PLAYING

    @property
    def can_call_score(self):
        return self.__can_call_score

    def in_can_call_score(self, score):
        return score in self.__can_call_score

    def set_cards(self, cards):
        self.__cards = cards

    def get_all_public_data(self, detail_type):
        result = {
            'uid': self.uid,
            'data': self.static_data,
            'score': self.__score,
            'IP': self.session.ip,
            'seatID': self.seat_id,
            'isPrepare': self.is_ready,
            'status': self.status,
            'offline': self.offline,
            'callScore': self.__call_score,
            'canCallScore': self.__can_call_score,
            'showCards': self.__is_show_cards,
            'callDealer': self.__call_dealer
        }
        if self.in_playing and self.__is_show_cards:
            result['cards'] = deepcopy(self.__cards)
            result["type"] = Rules.get_type(self.__cards, detail_type)[0]
        return result

    def get_all_data(self, detail_type):
        result = self.get_all_public_data(detail_type)
        if self.in_playing:
            result['cards'] = deepcopy(self.__cards)
            result["type"] = Rules.get_type(self.__cards, detail_type)[0]
        return result

    def __set_score(self, score, is_add):
        """ 设置玩家积分，只修改内存中的数据，不改数据库 """
        assert score >= 0
        if is_add:
            self.__score += score
            self.__current_score += score
        else:
            self.__score -= score
            self.__current_score -= score

    def on_stand_up(self):
        """ 玩家站起响应 """
        self.tid = 0
        self.seat_id = -1
        self.status = IN_IDLE
        self.__score = DEFAULT_SCORE
        self.__can_call_score = []
        onlines_model.set_tid(self.uid, 0)

    def on_sit_down(self, tid, seat_id):
        """ 玩家坐下响应 """
        self.tid = tid
        if self.status != IN_PLAYING:
            self.__clear_cards()
            self.status = IN_WAITING
        self.offline = False
        self.is_ready = True  # 坐下时自动准备
        self.seat_id = seat_id
        onlines_model.set_tid(self.uid, tid)

    def on_game_start(self, match_score):
        """ 房间开始前的清理 """
        self.__lock_score = match_score
        self.__clear_game_data()

    def on_game_over(self):
        self.__clear_round_data()
        self.__clear_game_data()
        self.__lock_score = 0
        self.on_stand_up()

    def __clear_game_data(self):
        self.__win_count = self.__lose_count = 0
        self.__tui_zhu = False
        self.__call_score = -1
        self.__prev_win_score = 0

    def __clear_round_data(self):
        self.__clear_cards()
        self.__can_call_score = []
        self.__call_score = -1
        self.__call_dealer = -1

    def on_checkout_over(self):
        self.__clear_cards()

    def on_round_start(self):
        """ 开局前的清理 """
        self.__clear_round_data()
        self.__call_score = -1
        self.__is_show_cards = False
        self.__current_score = 0
        self.status = IN_PLAYING

    def on_round_over(self, score, is_win, calc=False):
        """ 一局结束结算 """
        if calc and is_win:
            self.__prev_win_score = score
        else:
            self.__prev_win_score = 0
        self.__set_score(score, is_win)
        self.is_ready = False  # 一局结束后取消准备
