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
TURN_TO = 12  # 轮到某人出牌
PLAYER_CHU_PAI = 13  # 出牌
PLAYER_PASS = 14  # 过牌
DEAL_CARDS = 18  # 发牌
AUTO_ATTACK_ONE = 99 # 自动进入托管

PLAYER_ONLINE = 24  # 玩家在线状态变化
CLIENT_BROAD_CAST = 25  # 客户端广播数据

PLAYER_GANG = 17  # 玩家杠
PLAYER_MO_PAI = 20  # 玩家摸牌
PLAYER_PENG = 22  # 玩家碰
PLAYER_CHI = 23  # 玩家吃
PLAYER_HU_PAI = 26  # 玩家胡
NOTIFY_HU_PAI = 27  # 通知玩家是否胡牌

DEBUG_SET_CARDS = 29  # DEBUG模式下的设置牌

NOTIFY_POSITION = 31  # 开局通知定位
REQUEST_POSITION = 32  # 请求定位信息

PUBLIC_OPERATES = 36  # 玩家公共操作
PLAYER_SCORE_UPDATE = 37  # 玩家积分变动
BIRD_LIST = 38

PLAYER_BU = 21  # 玩家补牌
AFTER_GANG_CARD = 19  # 杠后牌

PLAYER_CHUI_BEGIN = 30  # 玩家锤开始
PLAYER_CHUI = 33  # 玩家锤
PLAYER_SHOW_CARD = 34  # 玩家摊牌
ENTER_ROOM_INFO = 44  # 发送玩家牌信息
FORCE_DISMISS = 83  # 强制解散房间
ROOM_LIST = 86  # 房间列表
UPDATE_ROOM_LIST = 87  # 更新房间列表
ADD_ROOM = 88  # 创建房间
PLAY_CONFIG_CHANGE = 90  # 玩法更改
UNION_GAME_PLAY_CONFIG_CHANGE = 91  # 联盟玩法更新

CLUB_FORCE_DISMISS = 92  # 俱乐部强制解散房间
CHANGE_SIT = 95 #调换座位
DEBUG_PLAYERS_INFO = 96
DEBUG_CARDS_INFO = 97

UNION_FORCE_DISMISS = 85  # 联盟强制解散房间
