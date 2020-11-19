# coding:utf-8
from games.hong_zhong_ma_jiang import ma_jiang
from utils.singleton import Singleton
from utils.utils import remove_by_value


class RuleBase(metaclass=Singleton):

    def __init__(self):
        pass

    @staticmethod
    def make_majiang_card(
            dong_count=0,
            xi_count=0,
            nan_count=0,
            bei_count=0,
            zhong_count=0,
            fa_count=0,
            bai_count=0):
        cards = list()
        for card in ma_jiang.ALL_PAPER_CARDS:
            cards.extend([card] * ma_jiang.CARD_COUNT)

        parms = [
            (ma_jiang.DONG_FENG, dong_count),
            (ma_jiang.NAN_FENG, xi_count),
            (ma_jiang.XI_FENG, nan_count),
            (ma_jiang.BEI_FENG, bei_count),
            (ma_jiang.HONG_ZHONG, zhong_count),
            (ma_jiang.FA, fa_count),
            (ma_jiang.BAI, bai_count)
        ]

        for value, count in parms:
            remove_count = ma_jiang.CARD_COUNT - count
            if remove_count != 0:
                remove_by_value(cards, value, remove_count)

        return cards

    @staticmethod
    def make(s, v):
        """制造一张麻将"""
        return s * 10 + v

    @staticmethod
    def get_value(card):
        return (card or 0) % 10

    @staticmethod
    def get_suit(card):
        return (card or 0) // 10

    @staticmethod
    def is_card(card):
        if not card or not isinstance(card, int):
            return False

        if not 10 <= card <= 60:
            return False

        return card in ma_jiang.ALL_PAPER_CARDS

    @staticmethod
    def is_bird(card):
        return RuleBase.get_value(card) in ma_jiang.BIRD_VALUE

    @staticmethod
    def sort(cards):
        def compare(value):
            if value == ma_jiang.NAI_ZI:
                return 0

            return value

        cards.sort(key=compare)

    @staticmethod
    def make_card(suit, value):
        return suit * 10 + value

    @staticmethod
    def group_by_suit(cards):
        """ 麻将分组,只有无花色 """
        group = dict()

        for card in cards:
            suit = RuleBase.get_suit(card)
            value = RuleBase.get_value(card)
            if not group.get(suit):
                group[suit] = list()
            group[suit].append(value)

        return group

    @staticmethod
    def is_value_shun_zi(cards):
        """
        -- 判断牌值是否全部由顺子构成，注意这里不能直接传牌过来，只能传牌值，不能带花色
        -- 所有会改变原参数的值的方法，都应该在开始的时候直接复制list
        """
        cards = list(cards)
        path = []
        for i in range(0, len(cards) - 1, 3):
            v = cards[0]
            if v in cards and v + 1 in cards and v + 2 in cards:
                cards.remove(v)
                cards.remove(v + 1)
                cards.remove(v + 2)
                path.append([v, v + 1, v + 2])
            else:
                return False, []

        return True, path

    @staticmethod
    def is_value_ke_zi(cards):
        """ 判断牌值是否刻子，注意这里不能直接传牌过来，只能传牌值，不能带花色 """
        return len(cards) == 3 and cards[0] == cards[1] == cards[2]

    @staticmethod
    def is_value_gang(cards):
        """ 判断能不能是不是杠 """
        return len(cards) == 4 and cards[0] == cards[1] == cards[2] == cards[3]

    @staticmethod
    def calc_value_count(cards, value):
        """计算给定值在列表中出现的次数"""
        return cards.count(value)

    @staticmethod
    def calc_suits(cards):
        """查找指定的牌中所出现的花色列表"""
        suits = dict()
        for v in cards:
            suits[RuleBase.get_suit(v)] = 1

        return suits.keys()

    @staticmethod
    def make_wst_cards_by_suits(suits):
        """返回给定花色（万索筒内）的所有牌"""
        result = list()
        suit = (ma_jiang.SUIT_SUO, ma_jiang.SUIT_TONG, ma_jiang.SUIT_WAN)
        for v in suits:
            if v in suit:
                for i in range(1, 10):
                    result.append(RuleBase.make_card(v, i))

        return result
