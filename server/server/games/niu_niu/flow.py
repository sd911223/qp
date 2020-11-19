# coding:utf-8

# 此文件是流程的相关的常量定义处

# 桌子的状态
# 注意顺序不可修改，否则影响游戏进程
T_IDLE = 0  # 空闲中
T_READY = 1  # 准备中
T_PLAYING = 2  # 游戏中
T_CHECK_OUT = 3  # 结算中

T_IN_IDLE = 0  # 无状态
T_IN_CALL_SCORE = 1  # 待叫分
T_IN_KAI_PAI = 2  # 待开牌
T_IN_DEALER = 3  # 待选择庄
# T_IN_FAN_CARD = 4 # 翻牌

PASS_SECONDS = 1  # 过场时间
CALL_SECONDS = 20  # 等待玩家响应的秒数
FIRST_CALL_SECONDS = 20  # 第一位玩家的等待时间
CHECKOUT_SECONDS = 10

HEART_BEAT_SECONDS = 10  # 玩家端的心跳超时时间


class GameFlow(object):
    pass
