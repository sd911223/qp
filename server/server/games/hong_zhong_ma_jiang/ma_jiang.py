NAI_ZI = 51  # 赖子

NULL_CARD = 0

DONG_FENG = 41
XI_FENG = 43
NAN_FENG = 45
BEI_FENG = 47
HONG_ZHONG = 51
FA = 53
BAI = 55

ALL_PAPER_CARDS = (
    11, 12, 13, 14, 15, 16, 17, 18, 19,  # 万字: 1~9
    21, 22, 23, 24, 25, 26, 27, 28, 29,  # 线条: 1~9
    31, 32, 33, 34, 35, 36, 37, 38, 39,  # 筒子：1~9
    HONG_ZHONG,
)

# 每张牌的总数
CARD_COUNT = 4

BIRD_VALUE = (1, 5, 9)

SUIT_WAN = 1
SUIT_SUO = 2
SUIT_TONG = 3
SUIT_FENG = 4
SUIT_ZA = 5

ACTION_TYPE_CHU = 1
ACTION_TYPE_CHI = 2
ACTION_TYPE_PENG = 3
ACTION_TYPE_GONG_GANG = 4
ACTION_TYPE_AN_GANG = 5
ACTION_TYPE_MING_GANG = 6
ACTION_TYPE_BU = 7
ACTION_TYPE_GUO = 8
ACTION_TYPE_HU = 9
ACTION_TYPE_ZI_MO = 10
ACTION_TYPE_ZHUA_NIAO = 11
ACTION_TYPE_QIANG_GANG_HU = 12
ACTION_TYPE_GONG_BU = 13
ACTION_TYPE_AN_BU = 14
ACTION_TYPE_MING_BU = 15

ACTION_PRIORITY = {
    ACTION_TYPE_HU: 99,
    ACTION_TYPE_QIANG_GANG_HU: 98,
    ACTION_TYPE_MING_GANG: 89,
    ACTION_TYPE_AN_GANG: 88,
    ACTION_TYPE_GONG_GANG: 88,
    ACTION_TYPE_AN_BU: 87,
    ACTION_TYPE_GONG_BU: 86,
    ACTION_TYPE_MING_BU: 85,
    ACTION_TYPE_PENG: 70,
    ACTION_TYPE_CHI: 60,
    ACTION_TYPE_GUO: 1,
}

# 对子：两张一样的牌
TYPE_DUI_ZI = 1
# 顺子：三张花色相同且牌值连续的牌
TYPE_SHUN_ZI = 2
# 刻子：三张一样的牌
TYPE_KE_ZI = 3

# 转转麻将
ZZ_MA_JIANG = 1
# 长沙麻将
CS_MA_JIANG = 2
# 邵阳麻将
SY_MA_JIANG = 3
# 桂东麻将
GD_MA_JIANG = 4

