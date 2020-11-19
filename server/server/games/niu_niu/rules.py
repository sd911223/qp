# coding:utf-8
from games.niu_niu import niu_niu
from utils.singleton import Singleton
import pydash as _

# 花色的定义
SUIT_HEI = 4
SUIT_HONG = 3
SUIT_MEI = 2
SUIT_ZHUAN = 1


class Rules(metaclass=Singleton):
    __pokers = (
        101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113,  # 方块
        201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 211, 212, 213,  # 梅花
        301, 302, 303, 304, 305, 306, 307, 308, 309, 310, 311, 312, 313,  # 红心
        401, 402, 403, 404, 405, 406, 407, 408, 409, 410, 411, 412, 413,  # 黑桃
    )

    __pokers_with_joker = (
        101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113,  # 方块
        201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 211, 212, 213,  # 梅花
        301, 302, 303, 304, 305, 306, 307, 308, 309, 310, 311, 312, 313,  # 红心
        401, 402, 403, 404, 405, 406, 407, 408, 409, 410, 411, 412, 413,  # 黑桃
        518, 520,
    )

    __yi_yang_pokers = (
        101, 102, 103, 104, 105, 106, 107, 108, 109,  # 方块
        201, 202, 203, 204, 205, 206, 207, 208, 209,  # 梅花
        301, 302, 303, 304, 305, 306, 307, 308, 309,  # 红心
        401, 402, 403, 404, 405, 406, 407, 408, 409,  # 黑桃
    )

    def __init__(self):
        pass

    # 返回所有的有效扑克牌
    @staticmethod
    def make_pokers(detail_type, joker=False):
        if joker:
            return list(Rules.__pokers_with_joker)
        if detail_type == 1:
            return list(Rules.__pokers)
        if detail_type == 2:
            return list(Rules.__yi_yang_pokers)

    # 制造一张扑克牌
    @staticmethod
    def make(s, v):
        return s * 100 + v

    # 获得一张牌的花色
    @staticmethod
    def suit(c):
        return c // 100

    # 获得一张牌值的大小
    @staticmethod
    def value(c, trans=True):
        res = c % 100
        if trans:
            return 10 if res >= 10 else res
        else:
            return res

    # 获得一张牌值的大小
    @staticmethod
    def abs_value(c):
        return c % 100

    # 测试是否是扑克牌
    @staticmethod
    def is_poker(c):
        return c in Rules.__pokers

    @staticmethod
    def get_all_cards_val(cards, trans=True):
        val = []
        for card in cards:
            val.append(Rules.value(card, trans))
        return val

    @staticmethod
    def get_all_cards_suit(cards):
        val = []
        for card in cards:
            val.append(Rules.suit(card))
        return val

    @staticmethod
    def is_all_pokers(cards):
        if not cards or type(cards) is not list:
            return False
        for c in cards:
            if not Rules.is_poker(c):
                return False
        return True

    @staticmethod
    def get_winner(player, dealer, detail_type=1, spec_type=list([-1]), joker=False):
        result = [-1, 0]
        data, card_type = Rules.compare(player.cards, dealer.cards, detail_type, spec_type, joker)
        if data == niu_niu.IS_MORE:
            result = [player.seat_id, Rules.get_times(card_type, detail_type, player.cards, joker)]
        elif data == niu_niu.IS_LESS:
            result = [dealer.seat_id, Rules.get_times(card_type, detail_type, dealer.cards, joker)]
        return result

    @staticmethod
    def get_yi_yang_times(card_type):
        if card_type == niu_niu.NO_SCORE:
            return 1
        if niu_niu.NIU_1 <= card_type <= niu_niu.NIU_7:
            return 1
        if card_type == niu_niu.NIU_8:
            return 2
        if card_type == niu_niu.NIU_9:
            return 3
        res = {
            niu_niu.NIU_NIU: 4,
            niu_niu.SHUN_ZI: 5,
            niu_niu.HU_LU: 6,
            niu_niu.DA_NIU: 7,
            niu_niu.WU_XIAO: 7,
            niu_niu.ZHA_DAN: 8,
        }
        return res[card_type]

    @staticmethod
    def get_default_times(card_type):
        if card_type == niu_niu.NO_SCORE:
            return 1
        if niu_niu.NIU_1 <= card_type <= niu_niu.NIU_6:
            return 1
        if niu_niu.NIU_7 <= card_type <= niu_niu.NIU_8:
            return 2
        if card_type == niu_niu.NIU_9:
            return 2
        res = {
            niu_niu.NIU_NIU: 4,
            niu_niu.SI_HUA: 4,
            niu_niu.WU_HUA: 5,
            niu_niu.SHUN_ZI: 5,
            niu_niu.TONG_HUA: 6,
            niu_niu.HU_LU: 7,
            niu_niu.ZHA_DAN: 8,
            niu_niu.WU_XIAO: 10,
            niu_niu.TONG_HUA_SHUN: 10,
        }
        return res[card_type]

    @staticmethod
    def get_times(card_type, detail_type=1, cards=[], joker=False):
        times = 0
        if detail_type == 1:
            times = Rules.get_default_times(card_type)
        if detail_type == 2:
            times = Rules.get_yi_yang_times(card_type)
        if joker and times >= 4:  # 如果开启了大小王 & 且牌型大于等于牛牛
            times += Rules.check_joker_count(cards)
        return times

    @staticmethod
    def check_joker_count(cards):
        count = 0
        for i in cards:
            if i in (518, 520,):
                count += 1
        return count

    @staticmethod
    def check_straight(vals):
        return vals[0] + 1 == vals[1] and vals[1] + 1 == vals[2] and vals[2] + 1 == vals[3] and vals[3] + 1 == vals[4]

    @staticmethod
    def check_all_color(suits):
        return suits[0] == suits[1] and suits[1] == suits[2] and suits[2] == suits[3] and suits[3] == suits[4]

    @staticmethod
    def check_bomb(i):
        if 4 in i and i[4] == 1:
            return True
        return False

    @staticmethod
    def check_hu_lu(i):
        if 3 in i and i[3] == 1 and 2 in i and i[2] == 1:
            return True
        return False

    @staticmethod
    def get_type(cards: list, detail_type=1, spec_type=list([-1]), joker=False):
        if len(cards) != 5:
            return -1, cards
        sum_total = 0
        hua_count = 0
        cards = _.sort(cards)

        vals = Rules.get_all_cards_val(cards, False)
        vals = _.sort(vals)
        suits = Rules.get_all_cards_suit(cards)

        is_straight = Rules.check_straight(vals)
        is_same_color = Rules.check_all_color(suits)

        if is_straight and is_same_color and (
                niu_niu.TONG_HUA_SHUN in spec_type or -1 in spec_type) and detail_type == 1:
            return niu_niu.TONG_HUA_SHUN, cards

        for card in cards:
            val = Rules.value(card)
            if val == 10:
                hua_count += 1
            sum_total += val

        pairs = _.count_by(vals)
        i = {}
        for k, v in pairs.items():
            if v >= 2:
                if v in i:
                    i[v] += 1
                else:
                    i[v] = 1

        if sum_total >= 40 and (niu_niu.DA_NIU in spec_type or -1 in spec_type) and detail_type == 2:
            return niu_niu.DA_NIU, cards
        if sum_total <= 10 and (niu_niu.WU_XIAO in spec_type or -1 in spec_type):
            return niu_niu.WU_XIAO, cards
        if Rules.check_bomb(i) and (niu_niu.ZHA_DAN in spec_type or -1 in spec_type):
            return niu_niu.ZHA_DAN, cards
        if Rules.check_hu_lu(i) and (niu_niu.HU_LU in spec_type or -1 in spec_type):
            return niu_niu.HU_LU, cards
        if is_same_color and (niu_niu.TONG_HUA in spec_type or -1 in spec_type) and detail_type == 1:
            return niu_niu.TONG_HUA, cards
        if sum_total == 50:
            if hua_count == 5 and (niu_niu.WU_HUA in spec_type or -1 in spec_type):
                return niu_niu.WU_HUA, cards
            # if hua_count == 4 and (niu_niu.SI_HUA in spec_type or -1 in spec_type):
            #     return niu_niu.SI_HUA, cards
            return niu_niu.NIU_NIU, cards
        if (is_straight or Rules.check_joker_shun_zi(vals, joker)) and (
                niu_niu.SHUN_ZI in spec_type or -1 in spec_type):
            return niu_niu.SHUN_ZI, cards
        if detail_type == 2:
            yi_yang_niu = Rules.get_yi_yang_niu_type(vals)[0]
            if yi_yang_niu != -1:
                card_type = Rules.get_niu_type(cards)
                return max(yi_yang_niu, card_type), cards

        return Rules.get_niu_type(cards), cards

    @staticmethod
    def check_joker_shun_zi(vals, joker):
        if not joker:
            return False
        return vals in (
            [6, 7, 8, 9, 18], [6, 7, 8, 9, 20], [7, 8, 9, 18, 20], [7, 8, 9, 10, 18], [7, 8, 9, 10, 20],
            [7, 8, 9, 11, 18],
            [7, 8, 9, 11, 20], [8, 9, 10, 18, 20], [8, 9, 11, 18, 20], [8, 9, 12, 18, 20], [8, 9, 10, 11, 18],
            [8, 9, 10, 11, 20], [8, 9, 10, 12, 18], [8, 9, 10, 12, 20], [8, 9, 11, 12, 18], [8, 9, 11, 12, 20],
            [9, 12, 13, 18, 20], [9, 11, 13, 18, 20], [9, 11, 12, 18, 20], [9, 10, 13, 18, 20], [9, 10, 12, 18, 20],
            [9, 10, 11, 18, 20], [9, 11, 12, 13, 18], [9, 11, 12, 13, 20], [9, 10, 12, 13, 18], [9, 10, 12, 13, 20],
            [9, 10, 11, 13, 18], [9, 10, 11, 13, 20], [9, 10, 11, 12, 18], [9, 10, 11, 12, 20]
        )

    @staticmethod
    def get_yi_yang_niu_type(vals):
        vals.sort()
        res = -1
        value = -1
        if vals[0] == vals[1] and vals[1] == vals[2]:
            res = vals[3] + vals[4]
            value = vals[0]
        if vals[1] == vals[2] and vals[2] == vals[3]:
            res = vals[0] + vals[4]
            value = vals[1]
        if vals[2] == vals[3] and vals[3] == vals[4]:
            res = vals[0] + vals[1]
            value = vals[2]

        if res == -1:
            return res, value

        res = res % 10
        if res == 0:
            res = 20
        return res, value

    @staticmethod
    def get_niu_type(cards):
        if not cards or len(cards) == 0:
            return -1
        cards_val_list = Rules.get_all_cards_val(cards)
        cards_maps = [[0, 1, 2, 3, 4], [0, 1, 3, 2, 4], [0, 1, 4, 2, 3], [0, 2, 3, 1, 4], [0, 2, 4, 1, 3],
                      [0, 3, 4, 1, 2], [1, 2, 3, 0, 4], [1, 2, 4, 0, 3], [1, 3, 4, 0, 2], [2, 3, 4, 1, 0]]
        for maps in cards_maps:
            if (cards_val_list[maps[0]] + cards_val_list[maps[1]] + cards_val_list[maps[2]]) % 10 == 0:
                point = (cards_val_list[maps[3]] + cards_val_list[maps[4]]) % 10
                return niu_niu.NIU_NIU if point == 0 else point
        return niu_niu.NO_SCORE

    @staticmethod
    def get_max_card_and_suit(cards):
        biggest_card, biggest_card_suit = 101, 1
        for card in cards:
            if Rules.abs_value(card) > Rules.abs_value(biggest_card):
                biggest_card = Rules.abs_value(card)
                biggest_card_suit = Rules.suit(card)
            elif Rules.abs_value(card) == Rules.abs_value(biggest_card):
                if Rules.suit(card) > Rules.suit(biggest_card_suit):
                    biggest_card = Rules.abs_value(card)
                    biggest_card_suit = Rules.suit(card)
        return biggest_card, biggest_card_suit

    @staticmethod
    def __compare_by_data(type1, data1, type2, data2, detail_type=1):
        if type1 > type2:
            return niu_niu.IS_MORE, type1
        elif type1 < type2:
            return niu_niu.IS_LESS, type2
        max_card_1_val, max_card_1_suit = Rules.get_max_card_and_suit(data1)
        max_card_2_val, max_card_2_suit = Rules.get_max_card_and_suit(data2)
        if detail_type == 2:
            tie_ban_1 = Rules.get_yi_yang_niu_type(Rules.get_all_cards_val(data1, False))[1]
            tie_ban_2 = Rules.get_yi_yang_niu_type(Rules.get_all_cards_val(data2, False))[1]

            if tie_ban_1 != -1 or tie_ban_2 != -1:
                if tie_ban_1 > tie_ban_2:
                    return niu_niu.IS_MORE, type1
                elif tie_ban_2 < tie_ban_2:
                    return niu_niu.IS_LESS, type2

        if max_card_1_val != max_card_2_val:
            if max_card_1_val > max_card_2_val:
                return niu_niu.IS_MORE, type1
            return niu_niu.IS_LESS, type2
        if max_card_1_suit != max_card_2_suit:
            if max_card_1_suit > max_card_2_suit:
                return niu_niu.IS_MORE, type1
            return niu_niu.IS_LESS, type2
        return niu_niu.IS_EQUAL

    @staticmethod
    def compare(cards1, cards2, detail_type=1, spec_type=list([-1]), joker=False):
        type1, data1 = Rules.get_type(cards1, detail_type, spec_type, joker)
        type2, data2 = Rules.get_type(cards2, detail_type, spec_type, joker)
        return Rules.__compare_by_data(type1, data1, type2, data2, detail_type)
