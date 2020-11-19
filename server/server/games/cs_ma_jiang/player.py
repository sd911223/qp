# coding:utf-8
from copy import deepcopy

from base.base_player import BasePlayer
from games.cs_ma_jiang import ma_jiang, flow
from models import onlines_model
from base import const

# 玩家状态标志
IN_IDLE = 0  # 空闲中
IN_WAITING = 1  # 等待中(新玩家加入后等待中)
IN_PLAYING = 2  # 游戏中

DEFAULT_SCORE = 0


class Player(BasePlayer):
    def __init__(self, uid):
        BasePlayer.__init__(self, uid)
        self.tid = 0
        self.seat_id = -1
        self.status = IN_IDLE
        self.offline = False
        self.lock = False
        self.is_ready = False

        self.__cards = []  # 手牌
        self.__chu_cards = []  # 出牌记录
        self.__score = DEFAULT_SCORE
        self.__mo_card = 0
        self.__mo_card1 = 0 # 发牌前的摸牌
        self.__win_score = 0
        self.__piao_score = -1
        self.__judge_info = {}

        self.__is_lock = False
        self.__chui = -1

        self.__zhuang_count = 0
        self.__win_count = 0
        self.__lose_count = 0

        self.__big_Hu_ZiMo_count = 0
        self.__small_Hu_ZiMo_count = 0
        self.__big_Hu_FangPao_count = 0
        self.__small_Hu_FangPao_count = 0
        self.__big_Hu_JiePao_count = 0
        self.__small_Hu_JiePao_count = 0

        self.__zhuo_pai = []  # 玩家桌牌
        self.__chou_peng_pai = set()  # 臭碰牌
        self.__chou_chi_pai = set()  # 臭吃牌
        self.__chou_hu_pai = set()
        self.__chou_gang_pai = set()  # 臭杠牌
        self.__is_lou_hu = False
        self.__operates = dict()  # 能做的操作
        self.__zi_mo_count = 0
        self.__ming_gang_count = 0
        self.__an_gang_count = 0
        self.__gong_gang_count = 0
        self.__ming_bu_count = 0
        self.__an_bu_count = 0
        self.__gong_bu_count = 0
        self.__ming_tang_count = 0
        self.__big_hu_count = 0
        self.__small_hu_count = 0
        self.__has_qi_shou_ti = False  # 有没有起手提

        self.__max_round_score = 0  # 单局最高得分
        self.__ming_tang_dict = dict()

        self.__middle_hu_record = []
        self.__is_show_cards = False
        self.__lock_score = 0
        self.__operator_out_time = None  # 用户操作超时定时器对象
        self.__delay_ready = None  # 用户自动托管延迟准备
        self.__change_card = None  # 标记牌
        self.__is_auto_chupai = False #是否自动出牌
        self.__user_operation_timeout =  const.Auto_Operation_TimeOut #自动出牌等待时间
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

    def get_cheng_pai_count_by_action(self):
        cheng_pai_count = {}
        for cheng_pai in self.__get_cheng_pai():
            if cheng_pai['actType'] not in cheng_pai_count:
                cheng_pai_count[cheng_pai['actType']] = 0

            cheng_pai_count[cheng_pai['actType']] += 1

        return cheng_pai_count

    @property
    def is_show_cards(self):
        return self.__is_show_cards

    @is_show_cards.setter
    def is_show_cards(self, is_show_cards):
        self.__is_show_cards = is_show_cards

    @property
    def lock_score(self):
        return self.__lock_score

    @property
    def zhuo_pai_origin(self):
        origin = []
        for z in self.__zhuo_pai:
            cards = deepcopy(z['cards'])
            cards.insert(0, z['card_type'])
            origin.append(cards)
        return origin

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

    @piao_score.setter
    def piao_score(self, score):
        self.__piao_score = score

    @property
    def win_score(self):
        return self.__win_score

    @property
    def judge_info(self):
        return self.__judge_info

    @property
    def operator_out_time(self):
        return self.__operator_out_time

    @operator_out_time.setter
    def operator_out_time(self, delay):
        if not self.is_auto_chupai:
            self.__operator_out_time = delay
    @property
    def delay_ready(self):
        return self.__delay_ready

    @delay_ready.setter
    def delay_ready(self, delay):
        if not self.is_auto_chupai:
            self.__delay_ready = delay
    @judge_info.setter
    def judge_info(self, data):
        self.__judge_info = data

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
    # 接收牌
    def receive_card(self, card):
        self.__cards.append(card)

    def __clear_cards(self):
        """ 清除所有牌 """
        self.__cards.clear()
        self.__change_card = None
        self.__chu_cards.clear()
        self.__zhuo_pai.clear()
        self.clear_chou_pai()

    # 获取玩家的扑克牌
    @property
    def cards(self):
        return self.__cards

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
        self.__operates.update(opts)

    def is_chou_pai(self, card):
        if card in self.__chou_chi_pai:
            return True
        if card in self.__chou_peng_pai:
            return True
        return False

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
            "gangCount": self.__an_gang_count + self.__gong_gang_count + self.__ming_gang_count,
            "bigHuCount": self.__big_hu_count,
            "smallHuCount": self.__small_hu_count,
            "roundMaxScore": self.__max_round_score,
            "mingTangList": self.__get_ming_tang_stat(),

            "daHuZiMo": self.__big_Hu_ZiMo_count,
            "xiaoHuZiMo": self.__small_Hu_ZiMo_count,
            "daHuJiePao": self.__big_Hu_JiePao_count,
            "xiaoHuJiePao": self.__small_Hu_JiePao_count,
            "daHuFangPao": self.__big_Hu_FangPao_count,
            "xiaoHuFangPao": self.__small_Hu_FangPao_count,
            "auto_chupai":1 if self.__is_auto_chupai else 0
        }

    def chu_card_len(self):
        return len(self.__chu_cards)

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
    def in_playing(self):
        return self.status == IN_PLAYING

    def __get_public_pai(self):
        result = []
        for item in self.__zhuo_pai:
            result.append(deepcopy(item))
        return result

    def get_all_public_data(self, judge_status):

        result = {
            'uid': self.uid,
            'score': self.__score,
            'IP': self.ip,
            'seatID': self.seat_id,
            'isPrepare': self.is_ready,
            'status': self.status,
            'offline': self.offline,
            'data': self.static_data,
            'chui': self.__chui,
            'countCard': len(self.__cards),
            'judgeInfo': self.judge_info,
            'lock': self.lock,
        }

        # 更新static数据中IP
        tmp_data = result['data'].replace(self.session.ip, self.ip)
        result['data'] = tmp_data

        if self.in_playing:
            if judge_status == flow.T_PLAYING:
                result["chengPai"] = self.__get_cheng_pai()
                result["outCards"] = deepcopy(self.__chu_cards)
                if self.is_show_cards and len(self.__middle_hu_record) > 0:
                    huNameList = []
                    format_cards = []
                    for record in self.__middle_hu_record:
                        huNameList.append(record[0])
                        hu_cards = record[1]
                        tmp_format_cards = list(format_cards)

                        for card in hu_cards:
                            if card in tmp_format_cards:
                                tmp_format_cards.remove(card)
                            else:
                                format_cards.append(card)
                        if record[0] in ("danSeYiZhiHua", "jiangYiZhiHua", "yiZhiNiao", "queYiSe", "banBanHu"):
                            result["showCards"] = self.cards

                    #移除开杠 和 中途起手胡 重复显示牌
                    tmp_format_cards = deepcopy(format_cards)
                    for card in tmp_format_cards:
                        for item in self.__zhuo_pai:
                            if item['cards'][0] == card:
                                format_cards.remove(item['cards'][0])

                    result["cards"] = format_cards
                    result["huNameList"] = huNameList
            else:
                result["chengPai"] = []
                result["outCards"] = []
        return result

    def __get_cheng_pai(self):
        data = self.__get_public_pai()
        result = []
        for zhuo_pai in data:
            result.append({
                "actType": zhuo_pai['card_type'],
                "cards": zhuo_pai['cards']
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

    def set_lou_hu(self, is_chou_hu):
        self.__is_lou_hu = bool(is_chou_hu)

    def is_chou_gang(self, card):
        return card in self.__chou_gang_pai

    def add_chou_gang_pai(self, card):
        self.__chou_gang_pai.add(card)

    def is_chou_hu(self):
        return self.__is_lou_hu

    def add_chou_hu_pai(self, cards):
        self.__chou_hu_pai.update(set(cards))

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
        self.__remove_cards([card])

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
        self.is_ready = False
        onlines_model.set_tid(self.uid, 0)

    def on_sit_down(self, tid, seat_id):
        """ 玩家坐下响应 """
        self.tid = tid
        if self.status != IN_PLAYING:
            self.__clear_cards()
            self.status = IN_WAITING
        self.offline = False
        self.seat_id = seat_id
        onlines_model.set_tid(self.uid, tid)

    def add_middle_hu_list(self, hu_info_list):
        self.__is_show_cards = True
        self.__middle_hu_record.extend(hu_info_list)

    def add_middle_hu(self, hu_info):
        self.__middle_hu_record.append(hu_info)

    @property
    def middle_hu_record(self):
        return self.__middle_hu_record

    def on_game_start(self, match_score, round_index):
        """ 房间开始前的清理 """
        self.__lock_score = match_score
        if round_index == 1:
            self.__clear_game_data()

    def on_game_over(self):
        self.__clear_round_data()
        self.__clear_game_data()
        self.__lock_score = 0
        self.on_stand_up()
        self.__piao_score = -1

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

        self.__big_Hu_ZiMo_count = 0
        self.__small_Hu_ZiMo_count = 0
        self.__big_Hu_FangPao_count = 0
        self.__small_Hu_FangPao_count = 0
        self.__big_Hu_JiePao_count = 0
        self.__small_Hu_JiePao_count = 0
        self.__is_auto_chupai = False
        self.__user_operation_timeout = const.Auto_Operation_TimeOut
        self.__iscacel_auto_chupai = False
        if self.__delay_ready:
            self.__delay_ready.cacel()
            self.__delay_ready = None


    def __clear_round_data(self):
        self.__clear_cards()
        self.__operates.clear()
        self.__isround_require = False #小局是否已经申请解散

    def on_round_start(self, piao_score=0):
        """ 开局前的清理 """
        self.__clear_round_data()
        self.status = IN_PLAYING
        self.lock = False
        # self.__piao_score = 0
        self.__chui = -1
        # self.__piao_score = piao_score
        self.__middle_hu_record = []

    def on_round_over(self, score, is_fang_pao, is_zhuang, is_zi_mo, ming_tang_list):
        """ 一局结束结算 """
        self.update_score(score)
        self.__win_score = score
        self.is_ready = False  # 一局结束后取消准备
        self.__stat_data(score > 0, is_fang_pao, is_zhuang, is_zi_mo, ming_tang_list,score)
        self.__operates.clear()

    def __stat_data(self, is_win, is_fang_pao, is_zhuang, is_zi_mo, ming_tang_list,score = 0):

        if score == 0 and not is_fang_pao and not is_zhuang and not is_zi_mo and ming_tang_list == []:
            return

        if is_win:
            self.__win_count += 1

        if is_fang_pao:
            self.__lose_count += 1

        if is_zhuang:
            self.__zhuang_count += 1

        if is_zi_mo:
            self.__zi_mo_count += 1

        if ming_tang_list:
            self.__big_hu_count += 1
        elif is_win:
            self.__small_hu_count += 1

        if is_zi_mo:
            if ming_tang_list:
                self.__big_Hu_ZiMo_count += 1
            else:
                self.__small_Hu_ZiMo_count += 1

        if is_fang_pao:
            if ming_tang_list:
                self.__big_Hu_FangPao_count += 1
            else:
                self.__small_Hu_FangPao_count += 1

        if is_win and not is_fang_pao and not is_zi_mo:
            if ming_tang_list:
                self.__big_Hu_JiePao_count += 1
            else:
                self.__small_Hu_JiePao_count += 1


        # self.__ming_tang_count += len(ming_tang_list)
        # for i in range(len(ming_tang_list)):
        #     ming_tang = ming_tang_list[i]
        #     self.__ming_tang_dict[ming_tang] = self.__ming_tang_dict.get(ming_tang, 0)

    def __remove_cards(self, cards):
        for card in cards:
            if card in self.__cards:
                self.__cards.remove(card)

    def __add_zhuo_pai(self, card_type, cards, from_seat: None):
        if from_seat is None:
            from_seat = self.seat_id

        self.__zhuo_pai.append({
            "card_type": card_type,
            "cards": deepcopy(cards),
            "from_seat": from_seat
        })

    def get_begin_hu(self, rule, options):
        return rule.get_middle_hu(options, self.__cards)

    def get_middle_hu(self, rule, options):
        """
        获取中途胡牌信息
        :param rule:
        :param options:
        :return:
        """
        return rule.get_middle_hu(options, self.__cards, ma_jiang.NULL_CARD, self.__middle_hu_record)

    def can_chi(self, card, rule):
        """ 判断能不能吃得起某牌，当吃得起并且比得出的时候返回true"""
        if self.lock:
            return []

        return rule.can_chi(self.__zhuo_pai, self.cards, card)

    def can_peng(self, card, rule):
        """ 1. 手牌有两张相同 2. 碰牌之后还要有牌可以打出 """
        if self.is_chou_peng_pai(card):
            return []

        if self.lock:
            return []

        return rule.can_peng(self.__zhuo_pai, self.cards, card)

    def can_hu(self, card, rule, is_seven_pairs, check_lou_hu=True):
        if self.is_chou_hu_pai(card):
            return False, []

        if check_lou_hu and self.__is_lou_hu:
            return False, []
        w = []
        for z in self.__zhuo_pai:
            cards = deepcopy(z['cards'])
            cards.insert(0, z['card_type'])
            w.append(cards)
        return rule.can_hu(w, self.__cards, card, is_seven_pairs)

    def can_ming_gang(self, card=ma_jiang.NULL_CARD, rule=None):
        w = []
        for z in self.__zhuo_pai:
            cards = deepcopy(z['cards'])
            cards.insert(0, z['card_type'])
            w.append(cards)
        return rule.can_ming_gang(w, self.__cards, card)

    def can_an_gang(self, card=ma_jiang.NULL_CARD, rule=None):
        return rule.can_an_gang(self.__zhuo_pai, self.__cards, card)

    def can_gong_gang(self, card, rule):
        return rule.can_gong_gang(self.__zhuo_pai, self.__cards, card)

    def base_ming_gang(self, card, _):  # 明杠
        for i in range(len(self.__zhuo_pai)):
            card_type = self.__zhuo_pai[i]['card_type']
            first_card = self.__zhuo_pai[i]['cards'][0]
            if card_type not in (ma_jiang.ACTION_TYPE_PENG,):
                continue
            if first_card != card:
                continue
            self.__zhuo_pai[i] = {
                "card_type": ma_jiang.ACTION_TYPE_MING_GANG,
                "cards": [card, card, card, card],
                "from_seat": self.seat_id
            }

            if card in self.__cards:
                self.__cards.remove(card)
            return True

        return False

    def ming_gang(self, card=ma_jiang.NULL_CARD, rule=None):  # 明杠
        is_ok = self.base_ming_gang(card, rule)
        if is_ok:
            self.__ming_gang_count += 1
        return is_ok

    def ming_bu(self, card=ma_jiang.NULL_CARD, rule=None):  # 明杠
        is_ok = self.base_ming_gang(card, rule)
        if is_ok:
            self.__ming_bu_count += 1
        return is_ok

    def base_gong_gang(self, card, _, from_seat_id):
        if 3 != self.__cards.count(card):
            return False

        self.__remove_cards([card] * 3)
        self.__add_zhuo_pai(ma_jiang.ACTION_TYPE_GONG_GANG, [card] * 4, from_seat_id)
        return True

    def gong_gang(self, card, _, from_seat_id):
        is_ok = self.base_gong_gang(card, _, from_seat_id)
        if is_ok:
            self.__gong_gang_count += 1
        return is_ok

    def gong_bu(self, card, _, from_seat_id):
        is_ok = self.base_gong_gang(card, _, from_seat_id)
        if is_ok:
            self.__gong_bu_count += 1
        return is_ok

    def base_an_gang(self, card, _):  # 暗杠
        if self.__cards.count(card) < 3:
            return False

        self.__remove_cards([card] * 4)
        self.__add_zhuo_pai(ma_jiang.ACTION_TYPE_AN_GANG, [card] * 4, self.seat_id)
        return True

    def an_gang(self, card, _):  # 暗杠
        is_ok = self.base_an_gang(card, _)
        if is_ok:
            self.__an_gang_count += 1
        return is_ok

    def an_bu(self, card, _):  # 暗杠
        is_ok = self.base_an_gang(card, _)
        if is_ok:
            self.__an_bu_count += 1
        return is_ok

    def chi(self, card, chi_pai, rule, from_seat_id):
        chi_pai = deepcopy(chi_pai)
        flag = rule.can_chi(self.__zhuo_pai, self.cards, card)

        if not flag:
            return False

        self.__remove_cards(chi_pai)

        chi_pai.insert(0, card)
        card_type = rule.get_card_type_of_three(chi_pai)
        self.__add_zhuo_pai(card_type, chi_pai, from_seat_id)
        return True

    def peng(self, card, from_seat_id):
        if self.__cards.count(card) < 2:
            return False

        self.__remove_cards([card] * 2)
        self.__add_zhuo_pai(ma_jiang.ACTION_TYPE_PENG, [card] * 3, from_seat_id)
        return True

    def add_chu_pai(self, card):
        self.__chu_cards.append(card)

    def pop_chu_pai(self, card=None):
        chu_length = len(self.__chu_cards)
        if not card:
            card = self.__chu_cards[chu_length - 1]

        try:
            revese_chu_cards = deepcopy(self.__chu_cards)
            revese_chu_cards.reverse()
            index = chu_length - revese_chu_cards.index(card) - 1
            return self.__chu_cards.pop(index)
        except Exception as error:
            print(error)
            return card

    @property
    def round_over_data(self):
        ret = {
            "seatID": self.seat_id,
            "handCards": self.cards,
            "tableCards": self.zhuo_pai_origin,
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

    def an_bu_de_qi(self):
        return ma_jiang.ACTION_TYPE_AN_BU in self.__operates

    def gong_bu_de_qi(self):
        return ma_jiang.ACTION_TYPE_GONG_BU in self.__operates

    def ming_bu_de_qi(self):
        return ma_jiang.ACTION_TYPE_MING_BU in self.__operates

    def gong_gang_de_qi(self):
        return ma_jiang.ACTION_TYPE_GONG_GANG in self.__operates

    def hu_de_qi(self):
        return ma_jiang.ACTION_TYPE_HU in self.__operates
