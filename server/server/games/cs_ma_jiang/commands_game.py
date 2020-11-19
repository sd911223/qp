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
AUTO_ATTACK_ONE = 99 # 自动进入托管

READY = 11  # 准备消息
TURN_TO = 12  # 轮到某人出牌
PLAYER_CHU_PAI = 13  # 出牌
PLAYER_PASS = 14  # 过牌
DEAL_CARDS = 18  # 发牌
PIAO_FEN = 45  # 飘分

PLAYER_ONLINE = 24  # 玩家在线状态变化
CLIENT_BROAD_CAST = 25  # 客户端广播数据

PLAYER_MO_PAI = 20  # 玩家摸牌

PLAYER_AN_GANG = 17  # 玩家暗杠
PLAYER_MING_GANG = 28  # 玩家明杠
PLAYER_GONG_GANG = 30  # 玩家公杠

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

PLAYER_AN_BU = 21  # 玩家暗补牌
PLAYER_MING_BU = 33  # 玩家明补牌
PLAYER_GONG_BU = 35  # 玩家公补牌

AFTER_GANG_CARD = 19  # 杠后牌

PLAYER_SHOW_CARD = 34  # 玩家摊牌

PLAYER_HAI_DI = 39  # 玩家要海底牌

PLAYER_OPERATES = 40  # 玩家操作
GET_MIDDLE_HU = 41  # 获取玩家板板胡

ENTER_ROOM_INFO = 44  # 发送玩家牌信息
FORCE_DISMISS = 83  # 强制解散房间
ROOM_LIST = 86  # 房间列表
UPDATE_ROOM_LIST = 87  # 更新房间列表
ADD_ROOM = 88  # 创建房间
PLAY_CONFIG_CHANGE = 90  # 玩法更改
PLAYER_PIAO_FEN = 98  # 玩家飘分

CLUB_FORCE_DISMISS = 92  # 俱乐部强制解散房间
UNION_GAME_PLAY_CONFIG_CHANGE = 91  # 联盟玩法修改

LUCKER_GET_LEFT_CARDS = 50 #幸运用户获取剩余牌值
LUCKER_CHANGE_CARD = 51 #幸运用户改变牌值

UNION_FORCE_DISMISS = 85  # 联盟强制解散房间