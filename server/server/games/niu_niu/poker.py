# coding:utf-8
import random

from games.niu_niu.rules import Rules


class Poker:

    def __init__(self, detail_type=1, joker=False):
        self.__cards = Rules.make_pokers(detail_type, joker)  # 扑克所含的所有牌
        self.__cursor = 0  # 当前所发到的牌的位置

    def shuffle(self):
        self.__cursor = 0
        random.shuffle(self.__cards)

    def pop(self):
        if self.__cursor >= len(self.__cards):
            return 0
        c = self.__cards[self.__cursor]
        self.__cursor += 1
        return c

    # 剩余张数
    @property
    def left_count(self):
        return max(len(self.__cards) - self.__cursor, 0)
