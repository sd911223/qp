""" 游戏命令列表 """
ENTER_ROOM = 1  # 进入房间
EXIT_ROOM = 2  # 退出房间
ROOM_CONFIG = 3  # 下发房间配置数据
EXPRESS_ENTER_UNION_ROOM = 253 # 快速进入联盟房间

PLAYER_ENTER_ROOM = 4  # 玩家进入
OWNER_DISMISS = 5  # 解散房间

GAME_START = 6  # 游戏开始
GAME_OVER = 7  # 游戏结束

ROUND_START = 8  # 一局开始
ROUND_OVER = 9  # 一局结束
REQUEST_DISMISS = 10  # 申请解散房间

READY = 11  # 准备消息
TURN_TO = 12  # 轮到某人
PLAYER_ATTACK = 13  # 出牌
PLAYER_PASS = 14  # 过
AUTO_ATTACK_ONE = 99 # 自动进入托管

TURN_START = 15  # 一轮开始
TURN_END = 16  # 一轮结束

SELECT_CARD = 17  # 选择一张牌 开局选择一张牌比牌
DEAL_CARDS = 18  # 发牌
BOMB_SCORE = 22  # 炸弹分数协议
ROUND_FLOW = 23  # 游戏流程通知

PLAYER_ONLINE = 24  # 玩家在线状态变化

CLIENT_BROAD_CAST = 25  # 客户端广播数据

NOTIFY_LOTTERY = 30  # 通知用户抽奖
SUBMIT_LOTTERY = 31  # 请求抽奖

NOTIFY_POSITION = 77  # 开局通知定位
REQUEST_POSITION = 78  # 请求定位信息

FORCE_DISMISS = 83  # 强制解散房间
ROOM_LIST = 86  # 房间列表
UPDATE_ROOM_LIST = 87  # 更新房间列表
ADD_ROOM = 88  # 创建房间
PLAY_CONFIG_CHANGE = 90  # 玩法更改
UNION_GAME_PLAY_CONFIG_CHANGE = 91  # 联盟玩法更新

CLUB_FORCE_DISMISS = 92  # 俱乐部强制解散房间

GET_ALL_CARDS = 50 #获取所有牌值
LUCKER_SELECT_CARDS = 51 #选取牌值

UNION_FORCE_DISMISS = 85  # 联盟强制解散房间
