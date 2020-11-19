# coding:utf-8
import os

IS_DEBUG = True  # 是否测试环境

GAME_ID = 10  # 游戏ID

MAIN_VERSION = 1  # 主版本号
SUB_VERSION = 2  # 子版本号

SERVICE_GATE = 9999  # 网关服务
SERVICE_PUB_SUB = 9998  # 发布订阅服务
SERVICE_AGENT = 9997  # 机器人
SERVICE_WEB = 9996  # Web
SERVICE_SYSTEM = 1  # 系统服务
SERVICE_AUTH = 2  # 登录认证服务
SERVICE_MALL = 3  # 商城服务
SERVICE_CDPH = 8  # 常德跑胡
SERVICE_ZZMJ = 9  # 转转麻将
SERVICE_HZMJ = 10  # 红中麻将
SERVICE_SYMJ = 11  # 邵阳麻将
SERVICE_CSMJ = 12  # 长沙麻将
SERVICE_TIAN_ZHA = 13  # 天炸
SERVICE_KOU_BO = 14  # 抠僰
SERVICE_YXHZP = 15  # 攸县胡子牌
SERVICE_GHZ = 16  # 鬼胡子
SERVICE_BPH = 17  # 剥皮胡
SERVICE_SXH = 18  # 上下混
SERVICE_NIU_GUI = 19  # 牛鬼
SERVICE_GDMJ = 20  # 桂东麻将
SERVICE_PDK = 21  # 跑得快
SERVICE_DTZ = 22  # 打筒子
SERVICE_BCNN = 23  # 冰城牛牛
SERVICE_ZHU_PO_JIU = 24  # 猪婆九
SERVICE_XTMJ = 25  # 湘潭麻将
SERVICE_YXPH = 26  # 攸县碰胡
SERVICE_510K = 27  # 510K
SERVICE_XTPH = 28  # 湘潭跑胡
SERVICE_SDH = 29  # 三打哈
SERVICE_NIU_NIU = 30  # 牛牛
SERVICE_SHUANG_KOU = 32  # 双扣
SERVICE_SHI_SAN_DAO = 33  # 十三道
SERVICE_YZCHZ = 34  # 永州扯胡子
SERVICE_CZPHZ = 35  # 郴州跑胡子
SERVICE_FENG_HUANG_HUA_SHUI = 36  # 凤凰划水
SERVICE_HENG_YANG_MO_MO = 37  # 衡阳摸摸
SERVICE_FENG_HUANG_HONG_ZHONG = 38  # 凤凰红中
SERVICE_ZLMZ = 39  # 捉老麻子
SERVICE_HUAI_HUA_QUAN_MING_TANG = 40  # 怀化全名堂
SERVICE_TUI_DAO_HU = 41  # 推倒胡
SERVICE_FANG_PAO_FA = 42  # 放炮罚
SERVICE_HAN_SHOU_PAO_HU = 43  # 汉寿跑胡子

SERVICE_ZJH = 47 # 诈金花

SERVICE_AHPF = 66 #安化跑胡子

QUIT_NORMAL = 0
QUIT_DISMISS = 1
QUIT_KICK = 2
QUIT_GAME_OVER = 3

# 桌子的状态
# 注意顺序不可修改，否则影响游戏进程
T_IDLE = 0  # 空闲中
T_READY = 1  # 准备中
T_PLAYING = 2  # 游戏中
T_CHECK_OUT = 3  # 结算中

DISMISS_SECONDS = 60  # 解散房间的等待时间
HEART_BEAT_SECONDS = 8  # 玩家的心跳时间

REASON_SEND = 1  # 玩家转账
REASON_RECEIVE = 2  # 接收到转账
REASON_SYSTEM_ADD = 3  # 系统添加
REASON_SYSTEM_SUB = 4  # 系统减少
REASON_BIND_SUCCESS = 5  # 绑定成功
REASON_INVITE_SUCCESS = 6  # 邀请成功
REASON_RE_INVITE_SUCCESS = 7  # 二次邀请成功
REASON_CREATE_ROOM_SUCCESS = 8  # 第一次创建房间成功
REASON_CREATE_ROOM_SUB = 10  # 开房扣除
REASON_CREATE_ROOM_LA_JIAO_DOU_SUB = 11  # 开房扣除辣椒豆
REASON_LOTTERY = 15  # 抽奖赠送

REASON_CLUB_ADD = 25  # 俱乐部馆主增加
REASON_CLUB_SUB = 26  # 俱乐部馆主扣除
REASON_GAME_ADD = 27  # 游戏增加
REASON_GAME_SUB = 28  # 游戏扣除
REASON_GAME_LIMIT_SUB = 29  # 游戏抽成

REASON_SCORE_GAME_ADD = 30  # 游戏积分增加
REASON_GAME_WINNER_SUB = 31  # 大赢家扣除

MODIFY_FLOOR = 1
MODIFY_SUB_FLOOR = 2
DEL_FLOOR = 3
DEL_SUB_FLOOR = 4

PAY_TYPE_CREATOR = 0
PAY_TYPE_AA = 1
PAY_TYPE_WINNER = 2

TIP_PAY_TYPE_BIG_WINNER = 0
TIP_PAY_TYPE_AA = 1
TIP_PAY_TYPE_WINNERS = 2

DIAMOND_ROOM = 0
MATCH_ROOM = 1

PAY_DIAMOND = 1
PAY_YUAN_BAO = 2

PLAYER_TABLE_REMOVE = 71
PLAYER_UNREADY = 81
ACK = 99

BROAD_CAST_LOTTERY = 1  # 红包广播
AGENT_UPDATE = 8  # 红包广播

PUSH_MESSAGE_CLUB_ROOM_CHANGE = 1  # 推送俱乐部房间状态更改

CALC_DIAMOND_WITH_PLAYER_NUM = [SERVICE_FENG_HUANG_HUA_SHUI, SERVICE_FENG_HUANG_HONG_ZHONG]

# System Running Path.
BASE_PATH = os.path.dirname(os.path.realpath(__file__)) + '/../'

# 输出目录路径
OUTPUT_PATH = BASE_PATH + 'output/'

# 日志文件写入路径
LOG_PATH = OUTPUT_PATH + 'logs/'

# 日志文件名
GAME_LOG_FILE = "game.log"

# 多久自动进入托管
Auto_Operation_TimeOut = 10
# 托管自动出牌时间间隔
Auto_Play_TimeStamp = 1

if __name__ == "__main__":
    print(BASE_PATH, LOG_PATH)
