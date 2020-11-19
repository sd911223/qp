# coding:utf-8

from copy import deepcopy

from base import const
from base.base_player import BasePlayer
from games.hong_zhong_ma_jiang import ma_jiang, flow
from models import logs_model
from models import onlines_model
from models import players_model, floor_model, club_model
from utils import earth_position
from utils import utils

# 玩家状态标志
IN_IDLE = 0  # 空闲中
IN_WAITING = 1  # 等待中(新玩家加入后等待中)
IN_PLAYING = 2  # 游戏中

DEFAULT_SCORE = 0
OVER_WIN_COUNT = 3


class Player(BasePlayer):
    def __init__(self, uid):
        BasePlayer.__init__(self, uid)
        self.__tid = 0
        self.__uid = int(uid) or 0

        self.__cards = []  # 手牌
        self.__relation_tid_set = set()
        self.__chu_cards = []  # 出牌记录
        self.__seat_id = -1
        self.__is_quit = False
        self.__is_ready = False
        self.__diamond = 0
        self.__score = DEFAULT_SCORE
        self.__mo_card = 0
        self.__mo_card1 = 0 # 发牌前的摸牌
        self.__win_score = 0
        self.__piao_score = 0
        self.__status = 0
        self.__offline = False
        self.__nick_name = ""
        self.__avatar = ""
        self.__judge_info = {}

        self.__is_lock = False
        self.__chui = -1

        self.__zhuang_count = 0
        self.__win_count = 0
        self.__lose_count = 0
        self.__yuan_bao = 0
        self.__load_details()

        self.__zhuo_pai = []  # 玩家桌牌
        self.__chou_peng_pai = set()  # 臭碰牌
        self.__chou_chi_pai = set()  # 臭吃牌
        self.__chou_hu_pai = set()
        self.__chou_gang_pai = set()  # 臭杠牌
        self.__is_lou_hu = False
        self.__operates = []  # 能做的操作
        self.__zi_mo_count = 0
        self.__ming_gang_count = 0
        self.__an_gang_count = 0
        self.__gong_gang_count = 0
        self.__ming_tang_count = 0
        self.__ren_pai_times = 0  # 忍牌次数
        self.__has_qi_shou_ti = False  # 有没有起手提
        self.__sex = 1

        self.__max_round_score = 0  # 单局最高得分
        self.__ming_tang_dict = dict()
        self.__x = earth_position.X_NA  # 玩家经度
        self.__y = earth_position.Y_NA  # 玩家纬度
        self.__qi_shou_ti_cards = []  # 起手提的牌
        self.__operator_out_time = None  # 用户操作超时定时器对象
        self.__lock_score = 0

        self.__gang_peng_cards = []
        self.__change_card = None  # 标记牌
        self.__is_auto_chupai = False #是否自动出牌
        self.__user_operation_timeout = const.Auto_Operation_TimeOut #自动出牌等待时间
        self.__isround_require = False #小局是否已经申请解散
        self.__iscacel_auto_chupai = False #客户端是否取消自动托管
    @property
    def iscacel_auto_chupai(self):
        return  self.__iscacel_auto_chupai
    @iscacel_auto_chupai.setter
    def iscacel_auto_chupai(self, iscacel):
        self.__iscacel_auto_chupai = iscacel
    @property
    def isround_require(self):
        return self.__isround_require
    @isround_require.setter
    def isround_require(self,val):
        self.__isround_require = val
    def set_change_card(self, card):
        self.__change_card = card

    def remove_change_card(self):
        self.__change_card = None
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
    def get_change_card(self):
        return self.__change_card

    @property
    def yuan_bao(self):
        return self.__yuan_bao

    @property
    def lock_score(self):
        return self.__lock_score

    def __load_details(self):
        """ 加载玩家的游戏数据 """
        info = players_model.get(self.__uid)
        if not info:
            return False

        self.__diamond = int(info.diamond)
        self.__avatar = info.avatar
        self.__yuan_bao = int(info.yuan_bao)
        self.__nick_name = info.nick_name or info.model
        self.__sex = int(info.sex)
        return True

    def is_over_win(self):
        return self.__win_count >= OVER_WIN_COUNT

    @property
    def avatar(self):
        return self.__avatar

    def can_del(self):
        # TODO
        if self.__tid > 0:
            return False

        return True

    def get_cheng_pai_count_by_action(self):
        cheng_pai_count = {}
        for cheng_pai in self.__get_cheng_pai():
            if cheng_pai[0] not in cheng_pai_count:
                cheng_pai_count[cheng_pai[0]] = 0

            cheng_pai_count[cheng_pai[0]] += 1

        return cheng_pai_count

    @property
    def uid(self):
        return self.__uid

    @property
    def nick_name(self):
        return self.__nick_name

    @property
    def score(self):
        return self.__score

    @property
    def chui(self):
        return self.__chui

    @chui.setter
    def chui(self, chui):
        if chui not in (1, 2):
            return

        self.__chui = chui

    @property
    def lock(self):
        return self.__is_lock

    @lock.setter
    def lock(self, is_lock):
        self.__is_lock = is_lock

    @property
    def piao_score(self):
        return self.__piao_score

    @property
    def win_score(self):
        return self.__win_score

    @property
    def is_ready(self):
        return self.__is_ready

    @property
    def operator_out_time(self):
        return self.__operator_out_time

    @operator_out_time.setter
    def operator_out_time(self, delay):
        if not self.is_auto_chupai:
            self.__operator_out_time = delay

    @is_ready.setter
    def is_ready(self, flag):
        self.__is_ready = (flag is True)

    def add_relation_tid(self, tid: int):
        self.__relation_tid_set.add(tid)

    def remove_relation_tid(self, tid: int):
        try:
            self.__relation_tid_set.remove(tid)
        except Exception as data:
            print(data)

    @property
    def offline(self):
        """ 玩家离线标志 """
        return self.__offline

    @offline.setter
    def offline(self, flag):
        self.__offline = flag

    @property
    def tid(self):  # 获得玩家当前所处的桌子ID
        return self.__tid

    @tid.setter
    def tid(self, tid):
        # 设置玩家的桌子ID
        self.__tid = tid

    @property
    def seat_id(self):  # 获得玩家当前的坐位ID
        return self.__seat_id

    @seat_id.setter
    def seat_id(self, seat_id):
        # 设置玩家的坐位ID
        self.__seat_id = seat_id

    @property
    def judge_info(self):
        return self.__judge_info

    @judge_info.setter
    def judge_info(self, data):
        self.__judge_info = data

    @property
    def status(self):
        return self.__status

    @status.setter
    def status(self, status):
        self.__status = status

    @property
    def position(self):
        return self.__x, self.__y

    @property
    def mo_card(self):
        return self.__mo_card

    @mo_card.setter
    def mo_card(self, now_card):
        self.__mo_card = now_card
    @property
    def mo_card1(self):
        return self.__mo_card1

    @mo_card.setter
    def mo_card1(self, now_card):
        self.__mo_card1 = now_card
    def set_position(self, x, y):
        if x is None or y is None:
            return
        self.__x = utils.check_float(x)
        self.__y = utils.check_float(y)

    # 接收牌
    def receive_card(self, card):
        self.__cards.append(card)

    def __clear_cards(self):
        """ 清除所有牌 """
        self.__cards.clear()
        self.__chu_cards.clear()
        self.__zhuo_pai.clear()
        self.__change_card = None
        self.clear_chou_pai()
        self.__qi_shou_ti_cards.clear()

    # 获取玩家的扑克牌
    @property
    def cards(self):
        return self.__cards

    # 获取玩家的扑克牌
    @cards.setter
    def cards(self, cards):
        self.__cards = deepcopy(cards)

    @property
    def zhuo_pai(self):
        return deepcopy(self.__zhuo_pai)

    @property
    def operates(self):
        return deepcopy(self.__operates)

    @operates.setter
    def operates(self, opts):
        self.__operates.clear()
        self.__operates.extend(opts)

    def is_chou_pai(self, card):
        if card in self.__chou_chi_pai:
            return True
        if card in self.__chou_peng_pai:
            return True
        return False

    def add_gang_peng_card(self, card):
        self.__gang_peng_cards.append(card)

    @property
    def gang_peng_cards(self):
        return self.__gang_peng_cards

    @property
    def qi_shou_ti_cards(self):
        return deepcopy(self.__qi_shou_ti_cards)

    @property
    def game_over_data(self):
        return {
            "seatID": self.seat_id,
            "totalScore": self.score,
            "zhuangCount": self.__zhuang_count,  # TODO: remove it
            "winCount": self.__win_count,
            "dianPaoCount": self.__lose_count,  # TODO: remove it
            "ziMoCount": self.__zi_mo_count,  # TODO: remove it
            "chiHuCount": self.__win_count - self.__zi_mo_count,
            "mingGangCount": self.__ming_gang_count,
            "anGangCount": self.__an_gang_count,
            "fangGangCount": self.__gong_gang_count,
            "mingTangCount": self.__ming_tang_count,
            "roundMaxScore": self.__max_round_score,
            "mingTangList": self.__get_ming_tang_stat(),
            "auto_chupai":1 if self.__is_auto_chupai else 0
        }

    def __get_ming_tang_stat(self):
        result = []
        values = self.__ming_tang_dict.values()
        values = sorted(values, reverse=True)
        for i in range(2):
            if i >= len(values):
                break
            for k, v in list(self.__ming_tang_dict.items()):
                if values[i] != v:
                    continue
                result.append([k, v])
        return result[0:2]

    @property
    def zhuo_pai(self):
        return self.__zhuo_pai

    @property
    def in_playing(self):
        return self.__status == IN_PLAYING

    def __get_public_pai(self):
        result = []
        for item in self.__zhuo_pai:
            result.append(deepcopy(item))
        return result

    def match_data(self, club_id, match_type):
        if club_id == -1 or match_type == 0:
            match_score = 0
        else:
            data = club_model.get_player_money_by_club_id(club_id, self.uid)
            if data and 'score' in data:
                match_score = data['score'] + data['lock_score']
            else:
                match_score = 0
        return {
            "seatID": self.seat_id,
            "matchScore": match_score
        }

    def get_all_public_data(self, judge_status):
        result = {
            'uid': self.__uid,
            'score': self.__score,
            'IP': self.ip,
            'seatID': self.__seat_id,
            'isPrepare': self.__is_ready,
            'status': self.__status,
            'offline': self.offline,
            'data': self.static_data,
            'chui': self.__chui,
            'countCard': len(self.__cards),
            'judgeInfo': self.judge_info,
        }

        # 更新static数据中IP
        tmp_data = result['data'].replace(self.session.ip, self.ip)
        result['data'] = tmp_data

        if self.in_playing:
            if judge_status == flow.T_PLAYING:
                result["chengPai"] = self.__get_cheng_pai()
                result["outCards"] = deepcopy(self.__chu_cards)
            else:
                result["chengPai"] = []
                result["outCards"] = []
        return result

    def __get_cheng_pai(self):
        data = self.__get_public_pai()
        result = []
        for zhuo_pai in data:
            if zhuo_pai[0] == ma_jiang.ACTION_TYPE_CHI:
                result.append({
                    "actType": zhuo_pai[0],
                    "cards": zhuo_pai[1:]
                })
            else:
                result.append({
                    "actType": zhuo_pai[0],
                    "card": zhuo_pai[1]
                })

        return result

    def get_all_data(self, judge_status):
        result = self.get_all_public_data(judge_status)
        if self.in_playing:
            result['handCards'] = deepcopy(self.__cards)
            result["chengPai"] = self.__get_cheng_pai()
            result["operates"] = self.operates
            result["louHu"] = int(self.__is_lou_hu)
        return result

    def get_debug_data(self):
        result = {
            'uid': self.__uid,
            'data': self.__static_data,
            'score': self.__score,
            'seatId': self.__seat_id
        }
        if self.in_playing:
            result['handCards'] = deepcopy(self.__cards)
            result["chengPai"] = self.__get_cheng_pai()
        return result

    def set_lou_hu(self, is_chou_hu):
        self.__is_lou_hu = bool(is_chou_hu)

    def is_chou_gang(self, card):
        return card in self.__chou_gang_pai

    def add_chou_gang_pai(self, card):
        self.__chou_gang_pai.add(card)

    def is_chou_hu(self):
        return self.__is_lou_hu

    def add_chou_hu_pai(self, card):
        self.__chou_hu_pai.add(card)

    def is_chou_hu_pai(self, card):
        return card in self.__chou_hu_pai

    def add_chou_peng_pai(self, card):
        self.__chou_peng_pai.add(card)

    def is_chou_peng_pai(self, card):
        return card in self.__chou_peng_pai

    def add_chou_chi_pai(self, card):
        self.__chou_chi_pai.add(card)

    def is_chou_chi_pai(self, card):
        return card in self.__chou_chi_pai

    def clear_chou_pai(self):
        self.__chou_peng_pai.clear()
        self.__chou_chi_pai.clear()
        self.__chou_hu_pai.clear()

    def clear_chou_pai_for_round(self):
        self.__chou_gang_pai.clear()

    def chu_pai(self, card):  # 玩家出牌
        self.add_chou_peng_pai(card)
        self.add_chou_chi_pai(card)
        self.__remove_cards([card])

    def dec_yuan_bao(self, yuan_bao, club_id, record_id):
        players_model.dec_yuan_bao(self.__uid, yuan_bao)
        players_model.write_consume_logs(self.__uid, club_id, yuan_bao, const.PAY_YUAN_BAO,
                                         const.REASON_CREATE_ROOM_SUB, utils.timestamp(), 0, record_id)

    def dec_diamonds(self, num, club_id=-1, union_id=-1, record_id=0):
        """减去玩家钻石"""
        if not num or num <= 0:
            return False
        dec_yuan_bao = 0
        dec_diamond = num
        # if self.__diamond < num:
        #     dec_diamond = self.__diamond
        #     dec_yuan_bao = num - self.__diamond
        #
        # if dec_yuan_bao > 0:
        #     self.dec_yuan_bao(dec_yuan_bao, club_id, record_id)

        if players_model.dec_diamonds(self.__uid, dec_diamond) > 0:
            self.__diamond -= dec_diamond
            players_model.write_consume_logs(self.__uid, club_id,union_id, dec_diamond, const.PAY_DIAMOND,
                                             const.REASON_CREATE_ROOM_SUB, utils.timestamp(), 0, record_id)
            # logs_model.add_diamonds_log(self.uid, num, const.REASON_CREATE_ROOM_SUB, 1, self.__diamond,
            #                             record_id=record_id)
            if club_id != -1:
                logs_model.add_club_diamonds_log(self.__uid, num, club_id, record_id, 0)

            if union_id != -1:
                logs_model.add_union_diamonds_log(self.__uid, num, union_id, record_id)

            return True
        return False

    def dec_la_jiao_dou(self, num, club_id=-1, record_id=0):
        """减去辣椒豆"""
        if not num or num <= 0:
            return False
        if players_model.dec_la_jiao_dou(self.__uid, num) > 0:
            logs_model.add_la_jiao_dou_log(self.uid, num, const.REASON_CREATE_ROOM_LA_JIAO_DOU_SUB, 1, 0,
                                           record_id=record_id)
            if club_id != -1:
                logs_model.add_club_diamonds_log(self.__uid, 0, club_id, record_id, num)
            return True
        return False

    def diamond(self):
        p = players_model.get_diamond_by_uid(self.__uid)
        if not p:
            utils.log("player:" + str(self.__uid) + " is None", 'diamond_exception.log')
            self.__diamond = 0
            return 0
        diamond = int(p['diamond'])
        self.__diamond = diamond
        self.__yuan_bao = int(p['yuan_bao'])
        return diamond

    def update_score(self, score):
        """ 设置玩家积分，只修改内存中的数据，不改数据库 """
        self.__max_round_score = max(score, self.__max_round_score)
        self.__score += score

        return self.__score

    def on_stand_up(self):
        """ 玩家站起响应 """
        self.tid = 0
        self.seat_id = -1
        self.status = IN_IDLE
        self.__score = DEFAULT_SCORE
        onlines_model.set_tid(self.__uid, 0)

    def on_sit_down(self, tid, seat_id):
        """ 玩家坐下响应 """
        self.tid = tid
        if self.status != IN_PLAYING:
            self.__clear_cards()
            self.status = IN_WAITING
        self.offline = False
        self.seat_id = seat_id
        onlines_model.set_tid(self.__uid, tid)

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
        self.__zhuang_count = 0
        self.__ming_gang_count = 0
        self.__an_gang_count = 0
        self.__gong_gang_count = 0
        self.__ming_tang_count = 0
        self.__zi_mo_count = 0
        self.__max_round_score = 0
        self.__ming_tang_dict.clear()
        self.is_ready = False
        self.__is_auto_chupai = False
        self.__iscacel_auto_chupai = False #客户端是否取消自动托管
        self.__user_operation_timeout = const.Auto_Operation_TimeOut

    def __clear_round_data(self):
        self.__clear_cards()
        self.__ren_pai_times = 0
        self.__operates.clear()
        self.__isround_require = False #小局是否已经申请解散

    def on_round_start(self, piao_score=0):
        """ 开局前的清理 """
        self.__clear_round_data()
        self.status = IN_PLAYING
        self.lock = False
        self.__chui = -1
        self.__piao_score = piao_score
        self.__gang_peng_cards = []

    def on_round_over(self, score, is_fang_pao, is_zhuang, is_zi_mo, ming_tang_list):
        """ 一局结束结算 """
        self.update_score(score)
        self.__win_score = score
        self.__is_ready = False  # 一局结束后取消准备
        self.__stat_data(score > 0, is_fang_pao, is_zhuang, is_zi_mo, ming_tang_list)
        self.__operates.clear()
        self.__piao_score = 0

    def __stat_data(self, is_win, is_fang_pao, is_zhuang, is_zi_mo, ming_tang_list):
        if is_win:
            self.__win_count += 1

        if is_fang_pao:
            self.__lose_count += 1

        if is_zhuang:
            self.__zhuang_count += 1

        if is_zi_mo:
            self.__zi_mo_count += 1

        self.__ming_tang_count += len(ming_tang_list)
        for i in range(len(ming_tang_list)):
            ming_tang = ming_tang_list[i]
            self.__ming_tang_dict[ming_tang] = self.__ming_tang_dict.get(ming_tang, 0)

    def __remove_cards(self, cards):
        for card in cards:
            if card in self.__cards:
                self.__cards.remove(card)

    def __add_zhuo_pai(self, card_type, cards):
        cards = deepcopy(cards)
        cards.insert(0, card_type)
        self.__zhuo_pai.append(cards)

    def can_chi(self, card, rule):
        """ 判断能不能吃得起某牌，当吃得起并且比得出的时候返回true"""
        if self.is_chou_chi_pai(card):
            return False

        if self.lock:
            return False

        return rule.can_chi(self.__zhuo_pai, self.cards, card)

    def can_peng(self, card, rule):
        """ 1. 手牌有两张相同 2. 碰牌之后还要有牌可以打出 """
        if self.is_chou_peng_pai(card):
            return False

        if self.lock:
            return False

        return rule.can_peng(self.__zhuo_pai, self.cards, card)

    def can_hu(self, card, rule, is_seven_pairs, check_lou_hu=True):
        if self.is_chou_hu_pai(card):
            return False, []

        if check_lou_hu and self.__is_lou_hu:
            return False, []
        print("zhuopai:", self.__zhuo_pai, " cards: ", self.__cards, " card:", card)
        ret = rule.can_hu(self.__zhuo_pai, self.__cards, card, is_seven_pairs)
        print("zhuopai:", self.__zhuo_pai, " cards: ", self.__cards, " card:", card)
        print("+++++++++ ret = ", ret)
        return ret

    def can_ming_gang(self, _):
        cards = self.__cards

        for card in cards:
            for i in range(len(self.__zhuo_pai)):
                card_type = self.__zhuo_pai[i][0]
                first_card = self.__zhuo_pai[i][1]
                if card_type not in (ma_jiang.ACTION_TYPE_PENG,):
                    continue
                if first_card != card:
                    continue
                if card in self.__chou_gang_pai:
                    continue

                return True, card

        return False, 0

    def can_an_gang(self, rule):
        return rule.can_an_gang(self.__cards)

    def can_gong_gang(self, card, rule):
        return rule.can_gong_gang(self.__cards, card)

    def ming_gang(self, card, _):  # 明杠
        for i in range(len(self.__zhuo_pai)):
            card_type = self.__zhuo_pai[i][0]
            first_card = self.__zhuo_pai[i][1]
            if card_type not in (ma_jiang.ACTION_TYPE_PENG,):
                continue
            if first_card != card:
                continue
            self.__zhuo_pai[i] = [ma_jiang.ACTION_TYPE_MING_GANG, card, card, card, card]
            self.__cards.remove(card)
            self.__ming_gang_count += 1
            return True

        return False

    def gong_gang(self, card, _):
        if 3 != self.__cards.count(card):
            return False

        cards = [card, card, card, card]
        self.__remove_cards([card] * 3)
        self.__add_zhuo_pai(ma_jiang.ACTION_TYPE_GONG_GANG, cards)
        self.__gong_gang_count += 1
        return True

    def an_gang(self, card, _):  # 暗杠
        if self.__cards.count(card) < 4:
            return False

        cards = [card, card, card, card]
        self.__remove_cards([card] * 4)
        self.__add_zhuo_pai(ma_jiang.ACTION_TYPE_AN_GANG, cards)
        self.__an_gang_count += 1
        return True

    def chi(self, card, chi_pai, rule):
        flag = rule.can_chi(self.__zhuo_pai, self.cards, card)

        if not flag:
            return False

        self.__remove_cards(chi_pai)

        chi_pai.insert(0, card)
        card_type = rule.get_card_type_of_three(chi_pai)
        self.__add_zhuo_pai(card_type, chi_pai)
        return True

    def peng(self, card):
        if self.__cards.count(card) < 2:
            return False

        cards = [card, card, card]
        self.__remove_cards([card] * 2)
        self.__add_zhuo_pai(ma_jiang.ACTION_TYPE_PENG, cards)
        return True

    def add_chu_pai(self, card):
        self.__chu_cards.append(card)

    def pop_chu_pai(self):
        return self.__chu_cards.pop()

    def chu_card_len(self):
        return len(self.__chu_cards)

    @property
    def round_over_data(self):
        ret = {
            "seatID": self.__seat_id,
            "handCards": self.cards,
            "tableCards": self.__zhuo_pai,
            "score": self.__win_score,
            "totalScore": self.__score,
            "chui": self.chui,
            "auto_chupai":1 if self.is_auto_chupai  else 0
        }
        return deepcopy(ret)

    def chi_de_qi(self):
        return ma_jiang.ACTION_TYPE_CHI in self.__operates

    def peng_de_qi(self):
        return ma_jiang.ACTION_TYPE_PENG in self.__operates

    def an_gang_de_qi(self):
        return ma_jiang.ACTION_TYPE_AN_GANG in self.__operates

    def ming_gang_de_qi(self):
        return ma_jiang.ACTION_TYPE_MING_GANG in self.__operates

    def bu_de_qi(self):
        return ma_jiang.ACTION_TYPE_BU in self.__operates

    def gong_gang_de_qi(self):
        return ma_jiang.ACTION_TYPE_GONG_GANG in self.__operates

    def hu_de_qi(self):
        return ma_jiang.ACTION_TYPE_HU in self.__operates

    def ren_pai(self):
        """ 忍牌的操作 """
        if 0 >= self.__ren_pai_times:
            return False
        self.__ren_pai_times -= 1
        return True

    @property
    def club_info(self):
        data = {
            "uid": self.__uid,
            "nickName": self.__nick_name,
            "remark": "",
            "avatar": self.__avatar,
            "seatID": self.__seat_id,
        }
        return data

        # def is_chong_pao(self):  # 判断是否重跑
        #     count = 0
        #     for item in self.__zhuo_pai:
        #         if not item:
        #             continue
        #         if item[0] in (ma_jiang.CARD_TYPE_TI, ):
        #             count += 1
        #     return count >= 2

    def return_score(self, club_id):
        floor_model.update_club_user_score_by_lock_score(self.uid, club_id)
