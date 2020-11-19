""" 游戏命令列表 """
ENTER_ROOM = 1  # 进入房间
EXIT_ROOM = 2  # 退出房间
ROOM_CONFIG = 3  # 下发房间配置数据

PLAYER_ENTER_ROOM = 4  # 玩家进入
OWNER_DISMISS = 5  # 解散房间

GAME_START = 6  # 游戏开始
GAME_OVER = 7  # 游戏结束

ROUND_START = 8  # 一局开始
ROUND_OVER = 9  # 一局结束
REQUEST_DISMISS = 10  # 申请解散房间

READY = 11  # 准备消息

SCORE = 12  # 允许下多少分
CALL_SCORE = 17  # 叫分
DEAL_CARDS = 18  # 发牌
SHOW_CARDS = 19  # 开牌
CALL_DEALER = 20  # 叫庄
DING_ZHUANG = 22  # 定庄
ROUND_FLOW = 23  # 游戏流程通知

PLAYER_ONLINE = 24  # 玩家在线状态变化

CLIENT_BROAD_CAST = 25  # 客户端广播数据
FAN_CARD = 26  # 翻牌

NOTIFY_LOTTERY = 30  # 通知用户抽奖
SUBMIT_LOTTERY = 31  # 请求抽奖
PLAYER_SCORE_CHANGE = 33  # 玩家分数变动

NOTIFY_POSITION = 77  # 开局通知定位
REQUEST_POSITION = 78  # 请求定位信息
PLAYER_COUNT = 80  # 玩家数量信息

FORCE_DISMISS = 83  # 强制解散房间
ROOM_LIST = 86  # 房间列表
UPDATE_ROOM_LIST = 87  # 更新房间列表
ADD_ROOM = 88  # 创建房间
PLAY_CONFIG_CHANGE = 90  # 玩法更改
PLAYER_FAN_CARD = 91  # 玩家翻牌

CLUB_FORCE_DISMISS = 92  # 俱乐部强制解散房间

UNION_FORCE_DISMISS = 85  # 联盟强制解散房间
