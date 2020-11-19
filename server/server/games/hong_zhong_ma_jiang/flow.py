# coding:utf-8

# 此文件是流程的相关的常量定义处

TOTAL_SEAT = 4  # 一个桌子的坐位数


# 桌子的状态
# 注意顺序不可修改，否则影响游戏进程
T_IDLE = 0  # 空闲中
T_READY = 1  # 准备中
T_PLAYING = 2  # 游戏中
T_CHECK_OUT = 3  # 结算中

T_IN_IDLE = 0  # 无状态
T_IN_CHU_PAI = 1  # 在出牌中
T_IN_PUBLIC_OPRATE = 2  # 公共操作过程中
T_IN_MO_PAI = 3  # 在摸牌中暗(未公示)
T_IN_MO_PAI_CALL = 4  # 在摸牌后的呼叫中
T_IN_MING_GANG_PAI_CALL = 5  # 抢杠胡判断流程
T_IN_GONG_GANG_PAI_CALL = 6  # 抢杠胡判断流程
T_IN_AN_GANG_PAI_CALL = 7  # 抢杠胡判断流程
T_IN_GANG_PAI_CALL = 8  # 杠牌操作流程
T_IN_OTHER_GANG_PAI_CALL = 9  # 杠牌后自己不可操作别人的操作流程
T_IN_WILL_BEGIN_OPTION = 10  # 开局前的玩家操作选项

PASS_SECONDS = 1  # 过场时间
TIAN_HU_SECONDS = 10  # 天胡时间
CALL_SECONDS = 10  # 等待玩家响应的秒数
ATTACK_SECONDS = 10  # 出牌等待时间
FIRST_CALL_SECONDS = 10  # 第一位玩家的等待时间
CHECKOUT_SECONDS = 10

HEART_BEAT_SECONDS = 10  # 玩家端的心跳超时时间
