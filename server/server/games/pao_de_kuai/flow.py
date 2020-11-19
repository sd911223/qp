# coding:utf-8

# 此文件是流程的相关的常量定义处

TOTAL_SEAT = 3  # 一个桌子的坐位数

# 桌子的状态
# 注意顺序不可修改，否则影响游戏进程
T_IDLE = 0  # 空闲中
T_READY = 1  # 准备中
T_PLAYING = 2  # 游戏中
T_CHECK_OUT = 3  # 结算中

T_IN_IDLE = 0  # 无状态
T_IN_PLAYING = 1  # 在行牌中
T_IN_SELECT_CARD = 2  # 选择牌中

PASS_SECONDS = 1  # 过场时间
CALL_SECONDS = 20  # 等待玩家响应的秒数
ATTACK_SECONDS = 15  # 出牌等待时间
FIRST_CALL_SECONDS = 20  # 第一位玩家的等待时间
CHECKOUT_SECONDS = 10

HEART_BEAT_SECONDS = 10  # 玩家端的心跳超时时间


class GameFlow(object):
    pass
