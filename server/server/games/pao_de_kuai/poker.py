# coding:utf-8
import random

from games.pao_de_kuai.rules import Rules

'''
序牌：方梅红黑王 分别对应花色：1,2,3,4,5
牌净值：3、4、5、6、7、8、9、10、11、12、13、14、16、18、20
关联牌：3、4、5、6、7、8、9、T、 J、 Q、 K、 A、 2、 SK，BK
牌值的组成：花色*100 + 牌净值
'''


class Poker:
    def __init__(self, card_count):
        self.__cards = Rules.make_pokers(card_count)  # 扑克所含的所有牌
        self.__card_count = card_count
        self.__cursor = 0  # 当前所发到的牌的位置

    def shuffle(self):
        self.__cursor = 0
        random.shuffle(self.__cards)
        random.shuffle(self.__cards)

    def pop(self):
        if self.__cursor >= len(self.__cards):
            return 0
        c = self.__cards[self.__cursor]
        self.__cursor += 1
        return c

    def modify(self, cards):
        for i in cards:
            self.__cards.remove(i)
        self.__cursor = 0

    def reinit(self):
        self.__cards = Rules.make_pokers(self.__card_count)  # 扑克所含的所有牌
        self.__cursor = 0  # 当前所发到的牌的位置

    # 剩余张数
    @property
    def left_count(self):
        return max(len(self.__cards) - self.__cursor, 0)
