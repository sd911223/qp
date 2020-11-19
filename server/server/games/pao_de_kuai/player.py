# coding:utf-8

import random
from copy import deepcopy
from base import const

from models import onlines_model
from base.base_player import BasePlayer

# 玩家状态标志
IN_IDLE = 0  # 空闲中
IN_WAITING = 1  # 等待中(新玩家加入后等待中)
IN_PLAYING = 2  # 游戏中

DEFAULT_SCORE = 0


class Player(BasePlayer):
    def __init__(self, uid):
        BasePlayer.__init__(self, uid)
        self.__select_card = -1
        self.__cards = []  # 手牌
        self.__turn_cards = []  # 出牌记录
        self.__score = DEFAULT_SCORE
        self.__win_score = 0
        self.__zha_niao = False
        self.__is_qiang_guan = False  # 是否强关
        self.__bomb_count = 0  # 炸弹次数
        self.__guan_count = 0  # 关笼次数
        self.__win_count = 0
        self.__lose_count = 0
        self.__max_score = 0
        self.__round_bomb_count = 0
        self.__bao_shuang = False
        self.__xian_pai = False
        self.__last_cards = []  # 用于结算显示的牌
        self.__operator_out_time = None  # 用户操作超时定时器对象
        self.__delay_ready = None  # 用户自动托管延迟准备
        self.__is_show_background = True  # 盖牌
        self.__lock_score = 0
        self.__is_kong_pai = False
        self.__is_auto_chupai = False #是否自动出牌
        self.__user_operation_timeout = const.Auto_Operation_TimeOut #自动出牌等待时间
        self.__iscacel_auto_chupai = False #客户端是否取消自动托管
        self.__isround_require = False #小局是否已经申请解散

    @property
    def isround_require(self):
        return self.__isround_require
    @isround_require.setter
    def isround_require(self,val):
        self.__isround_require = val
    @property
    def iscacel_auto_chupai(self):
        return  self.__iscacel_auto_chupai
    @iscacel_auto_chupai.setter
    def iscacel_auto_chupai(self, iscacel):
        self.__iscacel_auto_chupai = iscacel
    @property
    def is_kong_pai(self):
        return  self.__is_kong_pai

    @is_kong_pai.setter
    def is_kong_pai(self, is_kong):
        self.__is_kong_pai = is_kong
    @property
    def is_auto_chupai(self):
        return  self.__is_auto_chupai
    @is_auto_chupai.setter
    def is_auto_chupai(self,isauto):
        self.__is_auto_chupai = isauto
    @property
    def user_operation_timeout(self):
        return self.__user_operation_timeout
    @user_operation_timeout.setter
    def user_operation_timeout(self,timeout):
        self.__user_operation_timeout = timeout
    @property
    def lock_score(self):
        return self.__lock_score

    @property
    def last_cards(self):
        return self.__last_cards
    @property
    def delay_ready(self):
        return self.__delay_ready

    @delay_ready.setter
    def delay_ready(self, delay):
        if not self.is_auto_chupai:
            self.__delay_ready = delay
    @property
    def select_card(self):
        return self.__select_card

    @property
    def is_show_background(self):
        return self.__is_show_background

    @is_show_background.setter
    def is_show_background(self, is_show_background):
        self.__is_show_background = is_show_background

    @property
    def is_qiang_guan(self):
        return self.__is_qiang_guan

    @is_qiang_guan.setter
    def is_qiang_guan(self, is_qiang_guan):
        self.__is_qiang_guan = is_qiang_guan

    def set_select_card(self, card):
        self.__select_card = card

    @property
    def operator_out_time(self):
        return self.__operator_out_time

    @operator_out_time.setter
    def operator_out_time(self, delay):
        print('个人定时器在被调用')
        if not self.is_auto_chupai:
            self.__operator_out_time = delay
        print('个人定时器在被调用')
        print(delay)
        print('afwefwfwe')

    @property
    def zha_niao(self):
        return self.__zha_niao

    def set_zha_niao(self, zha_niao):
        self.__zha_niao = zha_niao

    def set_xian_pai(self, xian_pai):
        self.__xian_pai = xian_pai

    def set_score(self, score, is_add=True):
        self.__set_score(score, is_add)

    def set_bao_shuang(self, bao_shuang):
        self.__bao_shuang = bao_shuang

    @property
    def score(self):
        return self.__score

    @property
    def win_score(self):
        return self.__win_score

    @property
    def warning(self):
        if self.__xian_pai:
            return len(self.__cards)
        cards = [1]
        if self.__bao_shuang:
            cards = [1, 2]
        if len(self.__cards) in cards:
            return len(self.__cards)
        return -1

    @property
    def turn_cards(self):
        return self.__turn_cards

    # 接收扑克牌
    def receive_card(self, card):
        self.__cards.append(card)

    def __clear_cards(self):
        """ 清除所有牌 """
        self.__select_card = -1
        self.__cards = []
        self.__turn_cards = []

    # 获取玩家的扑克牌
    @property
    def cards(self):
        return self.__cards

    @cards.setter
    def cards(self, card):
        self.__cards = deepcopy(card)

    def shuffle_cards(self):
        random.shuffle(self.__cards)

    @property
    def round_bomb_count(self):
        return self.__round_bomb_count

    @property
    def game_over_data(self):
        return {
            "seatID": self.seat_id,
            "totalScore": self.score,
            "winCount": self.__win_count,
            "loseCount": self.__lose_count,
            "bombCount": self.__bomb_count,
            "guanCount": self.__guan_count,
            "maxScore": self.__max_score,
            "auto_chupai":1 if self.__is_auto_chupai else 0
        }

    def add_bomb_count(self, count=1):
        self.__round_bomb_count += count
        self.__bomb_count += count

    def add_guan_count(self, count=1):
        self.__guan_count += count

    @property
    def in_playing(self):
        return self.status == IN_PLAYING

    def get_all_public_data(self, _):
        result = {
            'uid': self.uid,
            'data': self.static_data,
            'score': self.__score,
            'IP': self.ip,
            'seatID': self.seat_id,
            'isPrepare': self.is_ready,
            'status': self.status,
            'offline': self.offline,
            'warning': self.warning,
            'select_card': self.select_card
        }

        # 更新static数据中IP
        tmp_data = result['data'].replace(self.session.ip, self.ip)
        result['data'] = tmp_data

        return result

    def get_all_data(self, judge_status):
        result = self.get_all_public_data(judge_status)
        if self.in_playing:
            result['shouPai'] = deepcopy(self.__cards)
        return result

    # 移除手上的牌
    def attack_by_cards(self, cards):
        self.__turn_cards.append(deepcopy(cards))
        for card in cards:
            if card in self.__cards:
                self.__cards.remove(card)

    def __set_score(self, score, is_add):
        """ 设置玩家积分，只修改内存中的数据，不改数据库 """
        assert score >= 0
        if is_add:
            self.__score += score
            self.__win_score += score
            if self.__win_score > self.__max_score:
                self.__max_score = self.win_score
        else:
            self.__score -= score
            self.__win_score -= score

    def on_stand_up(self):
        """ 玩家站起响应 """
        self.tid = 0
        self.seat_id = -1
        self.status = IN_IDLE
        self.__score = DEFAULT_SCORE
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
        self.__zha_niao = self.__bao_shuang = False
        self.__max_score = self.__bomb_count \
            = self.__guan_count = self.__win_count = self.__lose_count = 0
        self.__last_cards = []
        self.__is_auto_chupai = False
        self.__user_operation_timeout = const.Auto_Operation_TimeOut
        self.__iscacel_auto_chupai = False
        if self.__delay_ready:
            self.__delay_ready.cacel()
            self.__delay_ready = None

    def __clear_round_data(self):
        self.__clear_cards()
        self.__round_bomb_count = 0
        self.__is_qiang_guan = False
        self.__zha_niao = False
        self.__is_kong_pai = False
        self.__isround_require = False #小局是否已经申请解散
        if self.__delay_ready:
            self.__delay_ready.cacel()
            self.__delay_ready = None


    def on_round_start(self):
        """ 开局前的清理 """
        if not self.__is_kong_pai:
            self.__clear_round_data()
        self.__win_score = 0
        self.status = IN_PLAYING

    def on_round_over(self, score, is_win):
        """ 一局结束结算 """
        self.__set_score(score, is_win)
        self.is_ready = False  # 一局结束后取消准备
        self.__stat_data(is_win, score)
        self.__last_cards = deepcopy(self.cards)
        self.__clear_cards()

    def __stat_data(self, is_win, _):
        if is_win:
            self.__win_count += 1
        else:
            self.__lose_count += 1

    def set_cards(self, cards):
        self.__cards = cards
