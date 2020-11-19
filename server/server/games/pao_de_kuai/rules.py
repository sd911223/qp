# coding:utf-8
from copy import deepcopy

from games.pao_de_kuai import pao_de_kuai
from utils.singleton import Singleton

# 花色的定义
SUIT_HEI = 4
SUIT_HONG = 3
SUIT_MEI = 2
SUIT_ZHUAN = 1


class Rules(metaclass=Singleton):
    __pokers_16 = (
        103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113,  # 方块
        203, 204, 205, 206, 207, 208, 209, 210, 211, 212, 213, 214,  # 梅花
        303, 304, 305, 306, 307, 308, 309, 310, 311, 312, 313, 314,  # 红心
        403, 404, 405, 406, 407, 408, 409, 410, 411, 412, 413, 414, 416,  # 黑桃
    )

    __pokers_15 = (
        103, 104, 105, 106, 107, 108, 109, 110, 111, 112,  # 方块
        203, 204, 205, 206, 207, 208, 209, 210, 211, 212, 213,  # 梅花
        303, 304, 305, 306, 307, 308, 309, 310, 311, 312, 313,  # 红心
        403, 404, 405, 406, 407, 408, 409, 410, 411, 412, 413, 414, 416,  # 黑桃
    )

    def __init__(self):
        pass

        # 返回所有的有效扑克牌

    @staticmethod
    def make_pokers(card_count):
        if card_count == 16:
            return list(Rules.__pokers_16)
        elif card_count == 15:
            return list(Rules.__pokers_15)

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
    def value(c):
        return c % 100

    # 测试是否是扑克牌
    @staticmethod
    def is_poker(c):
        return c in Rules.__pokers_16

    # 提取牌值
    @staticmethod
    def abstract_values(cards: list) -> list:
        result = []
        for card in cards:
            result.append(Rules.value(card))
        return result

    # 提取花色
    @staticmethod
    def abstract_suits(cards: list) -> list:
        result = []
        for card in cards:
            result.append(Rules.suit(card))
        return result

    @staticmethod
    def is_dan_zhang(cards):
        cards_type, _ = Rules.get_type(cards)
        return cards_type == pao_de_kuai.DAN_ZHANG

    @staticmethod
    def is_biggest_dan_zhang(cards, card):
        card_val = card[0] % 100
        for i in cards:
            if i % 100 > card_val:
                return False
        return True

    @staticmethod
    def __stat_values(cards):
        result = {}
        for c in cards:
            if not result.get(c):
                result[c] = 1
            else:
                result[c] += 1
        return result
    @staticmethod
    def stat_values(cards):
        result = {}
        for c in cards:
            if not result.get(c):
                result[c] = 1
            else:
                result[c] += 1
        return result
    # 判断所给牌是不是顺子
    @staticmethod
    def is_shun_zi(cards):
        if not cards or len(cards) < 5:
            return False
        cards_type, data = Rules.get_type(cards)
        return cards_type == pao_de_kuai.SHUN_ZI

    @staticmethod
    def is_all_pokers(cards):
        if not cards or type(cards) is not list:
            return False
        for c in cards:
            if not Rules.is_poker(c):
                return False
        return True

    @staticmethod
    def get_type(cards: list, three_a_bomb=False, four_three=True, four_two=True, card_count=16):
        """
        获得牌型以及大小比较的元数据
        算法说明：
        特殊牌型
        四炸 4 (牌型 最大牌值)

        普通牌型
        单张 1 (牌型 牌值)
        顺子 5 6 7 8 9 10 11 12 (牌型 长度 最大牌值)
        对子 2 (牌型 牌值)
        连对 4 6 (牌型 最大牌值 长度)
        三带 3 4 5 (牌型 牌值)
        飞机 6 7 8 9 10 11 12 13 14 15 16 17 (牌型 长度 最大牌值)
        四带三 5 6 7
        连四带三[大飞机]

        :param cards: 所要获得牌型的牌组
        :param three_a_bomb: 三 A 算炸弹
        :param four_three: 四带三
        :param four_two: 四带二
        :param card_count: 牌张数
        :return: tuple(牌型, tuple(牌型元数据))
        """
        result = [0, []]
        if not Rules.is_all_pokers(cards):
            return tuple(result)

        length = len(cards)
        if 1 == length:
            Rules.__match_dan_zhang(cards, result)
        elif 2 == length:
            Rules.__match_dui_zi(cards, result)
        elif 3 == length:
            if (three_a_bomb and cards[0] % 100 == 14 and card_count == 16) \
                    or (three_a_bomb and cards[0] % 100 == 13 and card_count == 15):
                Rules.__match_zha_dan(cards, result)
                if result[0] is not 0:
                    return tuple(result)
            Rules.__match_san_dai(cards, result)
        elif 4 == length:
            Rules.__match_lian_dui(cards, result)
            Rules.__match_san_dai(cards, result)
            Rules.__match_zha_dan(cards, result)
        elif 5 == length:
            Rules.__match_san_dai(cards, result)
            Rules.__match_shun_zi(cards, result)
        elif 6 == length:
            if four_two:
                Rules.__match_4_dai_2(cards, result)
            Rules.__match_lian_dui(cards, result)
            Rules.__match_shun_zi(cards, result)
            Rules.__match_fei_ji(cards, result)
        elif length in (7, 9, 11):
            if length == 7 and four_three:
                Rules.__match_4_dai_3(cards, result)
            Rules.__match_shun_zi(cards, result)
            Rules.__match_fei_ji(cards, result)
        elif length in (8, 10, 12):
            Rules.__match_shun_zi(cards, result)
            Rules.__match_lian_dui(cards, result)
            Rules.__match_fei_ji(cards, result)
        elif length in (13, 15, 17):
            Rules.__match_fei_ji(cards, result)
        elif length in (14, 16):
            Rules.__match_fei_ji(cards, result)
            Rules.__match_lian_dui(cards, result)
        if length >= 8:
            Rules.__match_da_fei_ji(cards, result)

        return tuple(result)

    @staticmethod
    def __match_4_dai_3(cards, result):
        """4带3牌型"""
        values = Rules.abstract_values(cards)
        for v in values:
            if values.count(v) == 4:
                result[0] = pao_de_kuai.SI_DAI_SAN
                result[1] = [v, len(cards)]
                return

    @staticmethod
    def __match_4_dai_2(cards, result):
        """4带2牌型"""
        values = Rules.abstract_values(cards)
        for v in values:
            if values.count(v) == 4:
                result[0] = pao_de_kuai.SI_DAI_ER
                result[1] = [v, len(cards)]
                return

    @staticmethod
    def __match_zha_dan(cards, result):
        values = Rules.abstract_values(cards)
        if max(values) != min(values):
            return
        result[0] = pao_de_kuai.ZHA_DAN
        result[1] = [values[0]]

    @staticmethod
    def __fetch_more_than_values(cards: list, more_count: int) -> list:
        """取出牌列表中牌值数量大于某值的牌值"""
        values = Rules.abstract_values(cards)
        results = []
        for v in set(values):
            if values.count(v) >= more_count:
                results.append(v)
        return results

    @staticmethod
    def __search_straight_values(cards: list, more_count: int):
        more_than_cards = Rules.__fetch_more_than_values(cards, more_count)
        if not more_than_cards:
            return []
        more_than_cards.sort()

        tmp_list = []
        tmp = []
        for i in range(len(more_than_cards)):
            v = more_than_cards[i]
            tmp.append(v)
            if not more_than_cards.count(v + 1):
                tmp_list.append(tmp)
                tmp = []

        if not tmp_list:
            return []

        straight_values = tmp_list[0]
        for item in tmp_list:
            if len(item) >= len(straight_values):
                straight_values = item

        return straight_values

    @staticmethod
    def __match_da_fei_ji(cards, result):
        straight_four_values = Rules.__search_straight_values(cards, 4)
        if not straight_four_values:
            return

        max_dai_pai = len(straight_four_values) * 3
        if len(cards) - len(straight_four_values) * 4 != max_dai_pai:
            return
        result[0] = pao_de_kuai.FEI_JI_DAI_CHI_BANG
        result[1] = [len(straight_four_values), min(straight_four_values), len(cards)]

    @staticmethod
    def __match_dan_zhang(cards, result):
        result[0] = pao_de_kuai.DAN_ZHANG
        result[1] = [Rules.value(cards[0])]

    @staticmethod
    def __match_dui_zi(cards, result):
        values = Rules.abstract_values(cards)
        if values[0] != values[1]:
            return
        result[0] = pao_de_kuai.YI_DUI
        result[1] = [values[0]]

    @staticmethod
    def __match_lian_xu_dui_zi(cards):
        values = Rules.abstract_values(cards)
        values.sort()
        r = range(len(values))
        in_tuple = list(r[0:len(values):2])
        for i in in_tuple:
            if values[i] != values[i + 1]:
                return False, 0, 0
            if i != in_tuple[len(in_tuple) - 1]:
                if values[i + 1] + 1 != values[i + 2]:
                    return False, 0, 0
        return True, int(len(values) / 2), min(values)

    @staticmethod
    def __match_lian_dui(cards, result):
        flag, length, value = Rules.__match_lian_xu_dui_zi(cards)
        if not flag:
            return
        result[0] = pao_de_kuai.LIAN_DUI
        result[1] = [value, length]

    @staticmethod
    def __is_three_equals(values):
        return values[0] == values[1] and values[1] == values[2]

    @staticmethod
    def __is_four_equals(values):
        return values[0] == values[1] and values[1] == values[2] and values[2] == values[3]

    @staticmethod
    def __match_san_dai(cards, result):
        values = Rules.abstract_values(cards)
        values.sort()
        card_type = pao_de_kuai.SAN_ZHANG
        if 3 == len(values):
            if not Rules.__is_three_equals(values):
                return
        elif 4 == len(values):
            if not Rules.__is_three_equals(values[0:3]) \
                    and not Rules.__is_three_equals(values[1:]):
                return
            card_type = pao_de_kuai.SAN_DAI_YI
        elif 5 == len(values):
            if Rules.__is_four_equals(values[0:4]) or Rules.__is_four_equals(values[1:5]):
                return
            if not Rules.__is_three_equals(values[0:3]) \
                    and not Rules.__is_three_equals(values[1:4]) \
                    and not Rules.__is_three_equals(values[2:]):
                return
            card_type = pao_de_kuai.SAN_DAI_ER
        result[0] = card_type
        result[1] = [values[2], len(values)]

    @staticmethod
    def __match_shun_zi(cards, result):
        values = Rules.abstract_values(cards)
        values.sort()
        for i in range(len(values) - 1):
            if values[i] + 1 != values[i + 1]:
                return
        result[0] = pao_de_kuai.SHUN_ZI
        result[1] = [min(values), len(values)]

    @staticmethod
    def __match_fei_ji(cards, result):
        straight_three_values = Rules.__search_straight_values(cards, 3)
        if not straight_three_values:
            return

        max_dai_pai = len(straight_three_values) * 2
        if len(cards) - len(straight_three_values) * 3 > max_dai_pai:
            return
        result[0] = pao_de_kuai.FEI_JI_DAI_CHI_BANG
        result[1] = [len(straight_three_values), min(straight_three_values), len(cards)]

    @staticmethod
    def is_fei_ji_normal(straight_three_length, cards_len, san_dai_yi):
        if san_dai_yi:
            return (cards_len - straight_three_length * 3) == straight_three_length
        else:
            return (cards_len - straight_three_length * 3) == straight_three_length * 2

    @staticmethod
    def __compare_normal_cards_not_equal_type(type1, type2, data1, data2):
        if type1 in (
                pao_de_kuai.SI_DAI_ER,
                pao_de_kuai.SI_DAI_SAN, pao_de_kuai.SAN_ZHANG, pao_de_kuai.SAN_DAI_ER,
                pao_de_kuai.SAN_DAI_YI) and type2 in (
                pao_de_kuai.SI_DAI_ER,
                pao_de_kuai.SI_DAI_SAN, pao_de_kuai.SAN_ZHANG, pao_de_kuai.SAN_DAI_ER, pao_de_kuai.SAN_DAI_YI):
            v1, len1 = data1
            v2, len2 = data2
            if v1 > v2 and len1 <= 5 and len2 <= 5:
                return pao_de_kuai.IS_MORE
        if type1 in (pao_de_kuai.FEI_JI_DAI_CHI_BANG, pao_de_kuai.FEI_JI_DAI_CHI_BANG) and type2 in (
                pao_de_kuai.FEI_JI_DAI_CHI_BANG, pao_de_kuai.FEI_JI_DAI_CHI_BANG):
            s_len1, v1, len1 = data1
            s_len2, v2, len2 = data2
            if s_len1 == s_len2 and v1 > v2 and len1 <= s_len1 * 5 and len2 <= s_len2 * 5:
                return pao_de_kuai.IS_MORE
        return pao_de_kuai.IS_ILLEGAL

    @staticmethod
    def __compare_te_shu(type1, type2, data1, data2):
        """ 比较两组都是特殊牌的大小 """
        if type1 > type2:
            return pao_de_kuai.IS_MORE
        elif type1 < type2:
            return pao_de_kuai.IS_LESS
        else:
            if data1[0] > data2[0]:
                return pao_de_kuai.IS_MORE
            elif data1[0] < data2[0]:
                return pao_de_kuai.IS_LESS
            return pao_de_kuai.IS_EQUAL

    @staticmethod
    def __compare_by_data(type1, data1, type2, data2):
        """实际的比较算法"""
        is_te_shu1 = type1 in pao_de_kuai.TE_SHU_PAI_XING
        is_te_shu2 = type2 in pao_de_kuai.TE_SHU_PAI_XING
        if is_te_shu1 and not is_te_shu2:  # 组1为特殊牌型，组2不是
            return pao_de_kuai.IS_MORE
        if not is_te_shu1 and is_te_shu2:  # 组1为普通牌型，组2是特殊牌型
            return pao_de_kuai.IS_LESS
        if is_te_shu1 and is_te_shu2:  # 两组都是特殊牌型
            return Rules.__compare_te_shu(type1, type2, data1, data2)

        if type1 != type2:  # 普通牌型比较时必须是一致的，否则不能比较大小
            return Rules.__compare_normal_cards_not_equal_type(type1, type2, data1, data2)

        if type1 == pao_de_kuai.SHUN_ZI:
            if data1[1] != data2[1]:
                return pao_de_kuai.IS_ILLEGAL
        if type1 == pao_de_kuai.LIAN_DUI:
            if data1[1] != data2[1]:
                return pao_de_kuai.IS_ILLEGAL

        if type1 == pao_de_kuai.FEI_JI_DAI_CHI_BANG:
            if data1[0] != data2[0]:
                return pao_de_kuai.IS_ILLEGAL

        for i in range(len(data1)):
            if data1[i] > data2[i]:
                return pao_de_kuai.IS_MORE
            elif data1[i] < data2[i]:
                return pao_de_kuai.IS_LESS

        return pao_de_kuai.IS_EQUAL

    # 比牌，所属牌型和每张牌的大小来判断两手牌的大小
    @staticmethod
    def compare(cards1, cards2, three_a_bomb=False, card_count=16):
        """
        牌型大小比较
        :param cards1: 第一组比较的牌
        :param cards2: 第二组比较的牌
        :param three_a_bomb: 三A算炸
        :return: pao_de_kuai.IS_MORE or pao_de_kuai.IS_LESS or pao_de_kuai.IS_EQUAL or pao_de_kuai.IS_ILLEGAL
        """
        type1, data1 = Rules.get_type(cards1, three_a_bomb, card_count=card_count)
        type2, data2 = Rules.get_type(cards2, three_a_bomb, card_count=card_count)
        ret = Rules.__compare_by_data(type1, data1, type2, data2)
        return ret

    @staticmethod
    def is_bigger(cards1, cards2, three_a_bomb=False, card_count=16):
        """当且仅当第一手牌大于第二手牌的时候返回True"""
        return True if Rules.compare(cards1, cards2, three_a_bomb, card_count) == pao_de_kuai.IS_MORE else False

    @staticmethod
    def contain(container_cards, cards):
        if not container_cards or not (type(container_cards) is list):
            return False
        if not cards or not (type(cards) is list):
            return False
        stat = Rules.__stat_values(cards)
        for card, count in list(stat.items()):
            if container_cards.count(card) < count:
                return False
        return True

    @staticmethod
    def __fetch_four_cards(cards: list, bombs: list):
        """ 取出所有的四炸 """
        fours = Rules.__fetch_more_than_values(cards, 4)
        if not fours:
            return
        for four in fours:
            bomb = []
            for c in cards:
                if Rules.value(c) == four:
                    bomb.append(c)
            if not bomb:
                continue
            bombs.append(set(bomb))

    @staticmethod
    def __combination_cards(cards: list, count: int) -> list:
        """从列表中组合所需要张数的牌"""
        result = []
        if len(cards) < count:
            return result
        if len(cards) == count:
            result.append(cards[:])
            return result
        for i in range(0, len(cards) - 1):
            result.append(cards[i:i + count])
        return result

    @staticmethod
    def __search_biggest_si_zha(stat):
        """搜索最大的四炸"""
        l4 = []
        for v, count in list(stat.items()):
            if count >= 4:
                l4.append(v)
        if l4:
            max_4 = max(l4)
            return pao_de_kuai.ZHA_DAN, [max_4]
        return None, []

    @staticmethod
    def __search_three_a_bomb(cards, card_count):
        three_a_count = 0
        for i in cards:
            if (i % 100 == 14 and card_count == 16) or (i % 100 == 13 and card_count == 15):
                three_a_count += 1
            if three_a_count == 3 and card_count == 16:
                return pao_de_kuai.ZHA_DAN, [14]
            elif three_a_count == 3 and card_count == 15:
                return pao_de_kuai.ZHA_DAN, [13]
        return None, []

    @staticmethod
    def search_biggest_bomb(cards: list, three_a_bomb: bool, card_count=16):
        values = Rules.abstract_values(cards)
        stat = Rules.__stat_values(values)

        if three_a_bomb:
            m_type, m_data = Rules.__search_three_a_bomb(cards, card_count)
            if m_type:
                return m_type, m_data
        m_type, m_data = Rules.__search_biggest_si_zha(stat)
        if m_type:
            return m_type, m_data

        return None, []

    @staticmethod
    def yao_de_qi(hand_cards: list, curr_cards: list, tail_3_with_1: bool, deny_split_bomb: bool,
                  three_a_bomb: bool, card_count=16, same_card_count=False) -> bool:
        if not hand_cards:
            return False
        if not curr_cards:
            return True

        hand_cards = deepcopy(hand_cards)
        curr_cards = deepcopy(curr_cards)
        curr_type, curr_data = Rules.get_type(curr_cards)
        cards_value = []
        for card in curr_cards:
            cards_value.append(card % 100)
        if (three_a_bomb and cards_value == [14, 14, 14] and card_count == 16) \
                or (three_a_bomb and cards_value == [13, 13, 13] and card_count == 15):
            return False
        if Rules.__yao_de_qi_special(hand_cards, curr_type, curr_data, three_a_bomb, card_count):
            return True
        if len(hand_cards) in (3, 4) and not same_card_count:
            hand_card_type, hand_card_data = Rules.get_type(hand_cards, three_a_bomb, card_count=card_count)
            if curr_type == pao_de_kuai.SAN_DAI_ER and hand_card_type == pao_de_kuai.SAN_ZHANG:
                return False
            if curr_type == pao_de_kuai.SAN_DAI_YI and hand_card_type == pao_de_kuai.SAN_ZHANG:
                return False
            if (curr_type in (pao_de_kuai.SAN_DAI_ER,
                              pao_de_kuai.SAN_DAI_YI,)) and hand_card_type == pao_de_kuai.SAN_DAI_YI and not tail_3_with_1:
                return False
        return Rules.__yao_de_qi_normal(hand_cards, curr_type, curr_data, tail_3_with_1)

    @staticmethod
    def __split_list_by_straight(l: list) -> list:
        """
        将列表按值是否连续来断开，比如 [5, 7, 9, 10, 12] -> [[5], [7], [9, 10], [12]]
        :param l:
        :return:
        """
        result = []
        l.sort()
        cursor = 0
        for i in range(len(l)):
            if i == len(l) - 1:
                result.append(l[cursor:])
                continue
            if l[i] + 1 != l[i + 1]:
                result.append(l[cursor:i + 1])
                cursor = i + 1
                continue
        return result

    @staticmethod
    def __yao_de_qi_dan_zhang(hand_cards, curr_data):
        for c in hand_cards:
            if Rules.value(c) > curr_data[0]:
                return True
        return False

    @staticmethod
    def __yao_de_qi_dui_zi(hand_cards, stat, curr_data):
        if len(hand_cards) < 2:
            return False
        for v, count in list(stat.items()):
            if count >= 2 and v > curr_data[0]:
                return True
        return False

    @staticmethod
    def __yao_de_qi_lian_dui(hand_cards, stat, curr_data):
        if len(hand_cards) < 2 * curr_data[1]:
            return False
        l = []
        for v, count in list(stat.items()):
            if count >= 2 and v > curr_data[0]:
                l.append(v)
        if len(l) < curr_data[1]:
            return False
        l.sort()
        l2 = Rules.__split_list_by_straight(l)
        for v in l2:
            if len(v) >= curr_data[1]:
                return True
        return False

    @staticmethod
    def __yao_de_qi_san_zhang(stat, curr_data):
        for v, count in list(stat.items()):
            if count >= 3 and v > curr_data[0]:
                return True
        return False

    @staticmethod
    def __yao_de_qi_fei_ji(hand_cards, stat, curr_data, tail_3_with_1):
        l = []
        for v, count in list(stat.items()):
            if count >= 3 and v > curr_data[1]:
                l.append(v)
        l2 = Rules.__split_list_by_straight(l)
        for v in l2:
            if v and len(v) >= curr_data[0]:
                if len(hand_cards) < curr_data[2]:
                    if not tail_3_with_1:
                        return False
                return True
        return False

    @staticmethod
    def __yao_de_qi_shun_zi(stat, curr_data):
        l = []
        for v, count in list(stat.items()):
            if count >= 1 and v > curr_data[0]:
                l.append(v)
        l2 = Rules.__split_list_by_straight(l)
        for v in l2:
            if v and len(v) >= curr_data[1]:
                return True
        return False

    @staticmethod
    def __yao_de_qi_si_dai(stat, curr_data):
        if curr_data[1] != 5:
            return False
        for v, count in list(stat.items()):  # 被3带N大起了
            if count >= 3 and v > curr_data[0]:
                return True
        return False

    @staticmethod
    def __yao_de_qi_da_fei_ji(stat, curr_data):
        if curr_data[2] % 5 != 0:
            return False
        l = []
        for v, count in list(stat.items()):
            if count >= 3 and v > curr_data[1]:
                l.append(v)
        l2 = Rules.__split_list_by_straight(l)
        for v in l2:
            if v and len(v) >= curr_data[0]:
                return True
        return False

    @staticmethod
    def __yao_de_qi_normal(hand_cards, curr_type, curr_data, tail_3_with_1) -> bool:
        """
        普通牌型比较
        单张：比它大的单张
        对子：比它大的对子
        连对：比它大的连对
        三张：比它大的三张
        飞机：比它大的飞机
        顺子：比它大的顺子
        四带：此处只判断4带1的情况，如果是四带1的话可用大三张来尝试，其它的情况都算是炸弹了，不在这里判断
        大飞机：此处只判断N个4带1的情况，其它的情况都是有炸弹，不需在这里判断
        :param hand_cards:
        :param curr_type:
        :param curr_data:
        :return:
        """
        if curr_type == pao_de_kuai.DAN_ZHANG:
            return Rules.__yao_de_qi_dan_zhang(hand_cards, curr_data)

        values = Rules.abstract_values(hand_cards)
        stat = Rules.__stat_values(values)

        if curr_type == pao_de_kuai.YI_DUI:
            return Rules.__yao_de_qi_dui_zi(hand_cards, stat, curr_data)

        if curr_type == pao_de_kuai.LIAN_DUI:
            return Rules.__yao_de_qi_lian_dui(hand_cards, stat, curr_data)

        if curr_type == pao_de_kuai.SAN_ZHANG or curr_type == pao_de_kuai.SAN_DAI_ER:
            return Rules.__yao_de_qi_san_zhang(stat, curr_data)

        if curr_type == pao_de_kuai.FEI_JI_DAI_CHI_BANG:
            return Rules.__yao_de_qi_fei_ji(hand_cards, stat, curr_data, tail_3_with_1)

        if curr_type == pao_de_kuai.SHUN_ZI:
            return Rules.__yao_de_qi_shun_zi(stat, curr_data)

        if curr_type == pao_de_kuai.SI_DAI_SAN:
            return Rules.__yao_de_qi_si_dai(stat, curr_data)

        if curr_type == pao_de_kuai.SI_DAI_ER:
            return Rules.__yao_de_qi_si_dai(stat, curr_data)

        if curr_type == pao_de_kuai.FEI_JI_DAI_CHI_BANG:
            return Rules.__yao_de_qi_da_fei_ji(stat, curr_data)

        if curr_type == pao_de_kuai.SAN_DAI_YI:
            return Rules.__yao_de_qi_san_zhang(stat, curr_data)

        return False

    @staticmethod
    def __yao_de_qi_special(hand_cards, curr_type, curr_data, three_a_bomb, card_count=16) -> bool:
        """
        特殊牌型比较
        :param hand_cards:
        :param curr_type:
        :param curr_data:
        :return:
        """
        m_type, m_data = Rules.search_biggest_bomb(hand_cards, three_a_bomb, card_count)
        return Rules.__compare_by_data(m_type, m_data, curr_type, curr_data) == pao_de_kuai.IS_MORE

    @staticmethod
    def valid_deny_split_bomb(out_cards, cards, deny_split_bomb, three_a_bomb, card_count):
        out_cards_value = []
        cards_value = []
        for card in out_cards:
            out_cards_value.append(card % 100)
        for card in cards:
            cards_value.append(card % 100)
        for i in cards_value:
            if cards_value.count(i) == 4 and out_cards_value.count(i) >= 1 and len(out_cards) != 4:
                return not deny_split_bomb
            if three_a_bomb:
                if card_count == 16 and i == 14 and cards_value.count(i) == 3 and \
                        out_cards_value.count(i) >= 1 and len(out_cards) != 3:
                    return not deny_split_bomb
                elif card_count == 15 and i == 13 and cards_value.count(i) == 3 and \
                        out_cards_value.count(i) >= 1 and len(out_cards) != 3:
                    return not deny_split_bomb
        return True

    @staticmethod
    def valid(card_type, out_cards, cards, tail_3_with_1, deny_split_bomb, three_a_bomb, same_card_count,
              card_count) -> bool:
        if card_type == pao_de_kuai.ZHA_DAN and len(out_cards) == 3:
            return three_a_bomb
        if tail_3_with_1 and card_type == pao_de_kuai.SAN_DAI_ER:
            return False
        if not tail_3_with_1:
            if card_type == pao_de_kuai.SAN_DAI_YI and len(cards) != 4:
                return False
        if card_type == pao_de_kuai.SAN_ZHANG and len(cards) != 3:
            return False
        if not deny_split_bomb:
            return True
        return Rules.valid_deny_split_bomb(out_cards, cards, deny_split_bomb, three_a_bomb, card_count)

    @staticmethod
    def is_biggest(cards, three_a_bomb, card_count=16):
        if len(cards) != 3 or len(cards) != 4:
            return False
        cards_value = []
        for card in cards:
            cards_value.append(card % 100)
        if (three_a_bomb and cards_value == [14, 14, 14] and card_count == 16) \
                or (three_a_bomb and cards_value == [13, 13, 13] and card_count == 15):
            return True
        return cards_value == [13, 13, 13, 13]

    @staticmethod
    def search_smallest_dan_zhang(data, values, stat):
        for i in values:
            if i > data[0]:
                return [i]
        return []

    @staticmethod
    def search_smallest_yi_dui(data, values, stat):
        for v, count in list(stat.items()):
            if count == 2 and v > data[0]:
                return [v, v]
        return []
    @staticmethod
    def search_smallest_yi_dui_1(data, values, stat):
        for v, count in list(stat.items()):
            if count >= 2 and v > data[0]:
                return [v, v]
        return []

    @staticmethod
    def search_smallest_san_dai_er(data, values, stat):
        if len(values) < 5:
            return []
        for v, count in list(stat.items()):
            if count == 3 and v > data[0]:
                return [v, v, v]
        return []

    @staticmethod
    def search_smallest_san_dai_yi(data, values, stat):
        if len(values) < 4:
            return []
        for v, count in list(stat.items()):
            if count == 3 and v > data[0]:
                return [v, v, v]
        return []

    @staticmethod
    def search_smallest_zha_dan(data, values, stat):
        for v, count in list(stat.items()):
            if count == 4 and v > data[0]:
                return [v, v, v, v]
        return []
    @staticmethod
    def search_smallest_zha_dan1(data, values, stat):
        for v, count in list(stat.items()):
            if count == 4 and v >= data[0]:
                return [v, v, v, v]
        return []

    @staticmethod
    def search_smallest_shun_zi(data, values, stat):
        l = []
        for v, count in list(stat.items()):
            if count >= 1 and v > data[0]:
                l.append(v)
        l2 = Rules.__split_list_by_straight(l)
        for v in l2:
            if v and len(v) >= data[1]:
                ret_data = []
                for i in range(data[1]):
                    ret_data.append(v[0] + i)
                return ret_data
        return []

    @staticmethod
    def search_smallest_lian_dui(data, values, stat):
        l = []
        for v, count in list(stat.items()):
            if count >= 2 and v > data[0]:
                l.append(v)
        if len(l) < data[1]:
            return []
        l.sort()
        l2 = Rules.__split_list_by_straight(l)
        for v in l2:
            if len(v) >= data[1]:
                ret_data = []
                for i in range(data[1]):
                    ret_data.append((v[0] + i))
                    ret_data.append((v[0] + i))
                return ret_data
        return []

    @staticmethod
    def get_smallest_card(last_cards, cards, three_a_bomb, card_count=16):
        # 获取该玩家要的起的最小一种牌
        type1, data1 = Rules.get_type(last_cards, three_a_bomb, card_count=card_count)
        data = []
        values = Rules.abstract_values(cards)
        values.sort()
        stat = Rules.__stat_values(values)
        if type1 == pao_de_kuai.DAN_ZHANG:
            data = Rules.search_smallest_dan_zhang(data1, values, stat)
        elif type1 == pao_de_kuai.YI_DUI:
            data = Rules.search_smallest_yi_dui(data1, values, stat)
            if len(data) == 0:
                data = Rules.search_smallest_yi_dui_1(data1, values, stat)
        elif type1 == pao_de_kuai.SAN_DAI_YI:
            data = Rules.search_smallest_san_dai_yi(data1, values, stat)
        elif type1 == pao_de_kuai.SAN_DAI_ER:
            data = Rules.search_smallest_san_dai_er(data1, values, stat)
        elif type1 == pao_de_kuai.ZHA_DAN:
            data = Rules.search_smallest_zha_dan(data1, values, stat)
        elif type1 == pao_de_kuai.SHUN_ZI:
            data = Rules.search_smallest_shun_zi(data1, values, stat)
        elif type1 == pao_de_kuai.LIAN_DUI:
            data = Rules.search_smallest_lian_dui(data1, values, stat)
        data.sort()
        return data
