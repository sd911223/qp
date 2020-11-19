# coding:utf-8

# 服务端错误码列表
OK = 0  # 请求正常
DATA_BROKEN = -1  # 客户端请求数据错误，不符合即定格式
TOKEN_ERROR = -2
SYSTEM_ERROR = -3  # 系统错误
DUPLICATE_LOGIN = -4  # 客户端收到通知，账号已在别处登录
SEAT_FULL = -5  # 坐位已满
TABLE_NOT_EXIST = -6  # 桌子不存在
USER_NOT_EXIST = -7  # 玩家数据不存在
RULE_ERROR = -8  # 出牌不符合规则
NOT_YOUR_TURN = -9  # 当前循问的玩家不是你
CARD_NOT_EXIST = -10  # 所出牌不存在
IN_OTHER_ROOM = -11  # 玩家当前已在其它房间中
TABLE_FULL = -12  # 桌子已满
NOT_YOUR_ROOM = -13  # 不是你的桌子无法解散
COMMAND_DENNY = -14  # 命令不允许被执行
OPERATES_ILLEGAL = -15  # 当前玩家无此操作
OPERATES_DUPLICATE = -16  # 此玩家已操作
FLOW_ERROR = -17  # 当前流程不允许此操作
NOT_CLUB_MEMBER = -18  # 非俱乐部成员
DOU_ERROR = -19  # 豆子数量错误
AA_DIAMOND_ERROR = -22  # AA 钻石不足
GAME_ALREADY_START = -23  # 游戏已经开始
RULE_BOMB_ERROR = -30  # 双扣出牌不符合规则
OTHER_BOMB_ERROR = -31  # 双扣出牌不符合规则
YUAN_BAO_NOT_ENOUGH = -32  # 元宝不足
DISTANCE_TOO_SHORT = -34 #距离太近不予进入
POSTION_UNKNOWN = -35 #位置不明不予进入
ENERGE_NOT_ENOUGH = -36 # 能量不足不予进入
TABLE_PLAYER_BLOCK = -37  # 禁止同桌
PROHIBIT_ENTER_IN_MIDDLE = -38 # 禁止中途加入游戏

