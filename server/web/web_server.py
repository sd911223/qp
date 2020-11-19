#!/usr/bin/env python3
# coding:utf-8

import logging
import os.path
import signal

import tornado.auth
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
from tornado.options import define, options

from configs import config
from configs.const import *
from controllers.aac_handler import UploadAACHandler, GetAACHandler
from controllers.activity_handler import SignInActivity, SignInItemInfo, SpringActivity, SpringActivityLogs, \
    SpringActivityRecv
from controllers.agent_handler import GetAgentRoomList
from controllers.agents import DiamondRecordsHandler, GiveDiamondsHandler, EditProfileHandler, ResetPwdHandler
from controllers.agents import RequestVerifyCodeHandler
from controllers.bind_handler import BindHandler
from controllers.channel_config import ChannelConfigHandler
from controllers.charge_handler import ChargePushHandler
from controllers.club_handler import CreateClubHandler, GetClubHandler, DismissClubHandler, CopyClubHandler, \
    GetClubScoreListHandler, UpdateClubNameHandler, UpdateClubNoticeHandler, ApplyClubHandler, AgreeClubHandler, \
    GetClubInfoHandler, GetVerifyListClubHandler, VerifyClubUserHandler, SetClubAutoRoomHandler, SetClubModeHandler, \
    GetClubUserHandler, GetClubRoomHandler, KickUserHandler, SetUserPermission, SetUserRemark, UpgradeClubHandler, \
    GetClubConfig, GetClubQuickRoom, GetClubWinnerList, SetClubWinnerList, GetClubScoreByUid, \
    QuitClubHandler, GetClubUserRank, GetClubWinnerRank, TransferClub, GetClubOwnerInfo, GetClubRoomByMatchTypeHandler, \
    GetClubUserRoomInfo, GetClubGamePlay, TransferClubUser, GetClubBaseInfo, TagClubUser, GetClubTagUserRoomInfo, \
    GetClubGameLogs, SetClubQueryWinnerScore, GetClubScoreListByGameTypeAndTime, GetClubDiamondInfo
from controllers.club_match_handler import GetFloorHandler, GetSubFloorHandler, AddFloorHandler, AddSubFloorHandler, \
    DelFloorHandler, DelSubFloorHandler, EditFloorHandler, EditSubFloorHandler, ClubDouLogs, ClubUserDouLogs, \
    ClubUserDetailDouLogs, QueryDouOperLogs, GetGameCountLogs, SetGameCountLogs, GetSubFloorByMatchTypeHandler, \
    SetClubBlockHandler, QueryClubBlockHandler
from controllers.club_share import ClubShareHandler
from controllers.club_task import GetClubTask, ModifyClubTask, TaskClubShare, BonusClubTaskShare, BonusClubTaskRound
from controllers.clubs_data_handler import ClubsDataHandler
from controllers.debug_handler import DumpRecordHandler
from controllers.geo_handler import UploadGeoHandler
from controllers.hall import DiamondsHandler, RefreshHandler, DiamondPriceHandler, FeedBackHandler
from controllers.iap_handler import IAPHandler
from controllers.invite_handler import InviteActivityConfigHandler, InviteFriendListHandler, WithdrawHandler, \
    WithdrawRecordsHandler, ExchangeHandler, ShareInviteHandler, QRCodeHandler
from controllers.ji_fu import QueryUidHandler
from controllers.login_diamond_handler import LoginDiamondHandler
from controllers.login_handlers import GuestLoginHandler
from controllers.login_handlers import WeChatLoginHandler
from controllers.money_handler import IncreaseDou, ReduceDou, QueryDou, QueryDouLogs, RechargeConfig
from controllers.records import RePlayDetailsHandler, GetByReviewCodeHandler, RoundRankHandler
from controllers.records import RoundListHandler, PlayRoomListHandler, MakeReviewCodeHandler, GetDetailsResultHandler
from controllers.records import SetPhoneHandler, PlayRoomListWithClubAndTimeHandler
from controllers.robot_handler import RobotRoomsHandler
from controllers.room_handler import CreateRoomHandler, QueryRoomHandler, OpenRoomInfoHandler, CheckRoomHandler
from controllers.share_diamond_handler import ShareDiamondHandler, ShareDiamondEveryDayHandler
from controllers.shop import ModifyAddressHandler, GetAddressHandler, BuyScoreItemHandler, ChangeYuanBaoToDiamond, \
    BuyYuanBaoHandler
from controllers.union_handler import QueryAllSmallUnionManager, QuerySmallUnionUsers, QueryUnionPartner, \
    QueryUnionPartnerUsers, SetSmallUnionProfit, SetUnionPartnerProfit, QueryUnionManagerInfo, GetUnionFloor, \
    DelUnionFloor, EditUnionFloor, AddUnionFloor, GetUnionSubFloor, DelUnionSubFloor, EditUnionSubFloor, \
    AddUnionSubFloor, CreateUnion, EditUnionNotice, EditUnionName, GetUnionDiamondInfo, QueryUnionUsers, \
    SetUnionPlayerPermission, TagUnionUser, AddEnergy, ReduceEnergy, TransferEnergy, QueryTransferEnergyLogs, \
    SetUnionBlock, QueryUnionBlock, JoinUnion, GetUnionInfo, GetMyUnionInfo, QuitUnion, GetUnionGamePlay, \
    QueryUnionRoomsByFloor, QueryUnionRoomsBySubFloor ,QueryUnionAllRooms, RemarkUnionUser, KickUnionUser, AddPlayerToUnion, RequestMergeUnion, \
    QueryUnionRequestJoinList, VerifyUnionRequestJoin, QueryUnionScoreList, QueryUnionGameLogs, QueryEnergyLogs, \
    QueryUnionAllUsers, GetUnionGameCountLogs, SetUnionGameCountLogs, GetUnionAllSubFloor, \
    SetUnionPlayerAsSubManager, SetUnionPlayerAsPartner, SetSmallUnionDivide, SetUnionPartnerDivide, \
    QuerySubManagerOrPartnerUsers, GetUnionUserDivide, UnionManagerAddEnergy,SpeedJoinUnionRoom,\
    QueryUnionSafeBoxBalance,FetchUnionSafeBoxBalance,QueryUnionCSList,QueryUserExtraList,GetUnionUserDive, \
    SetUnionUserPlayerDivide,GetSafeBoxFaxList,GetOnlineUnionCount,SaveUnionCSLog,QueryUnionCSLog, \
    QueryUnionDirectUsers,TestOK,NoticeUnionMessage
from controllers.version_handler import CheckUpdateHandler
from controllers.wechat_pay import WechatPayHandler

# define("port", default=8899, help="run on the given port", type=int)
define("port", default=8194, help="run on the given port", type=int)


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            ("/iap", IAPHandler),#创建苹果订单
            ("/guestLogin", GuestLoginHandler),#游客登陆
            ("/getChannelConfig", ChannelConfigHandler),#获得渠道配置信息
            ("/refreshToken", RefreshHandler),#刷新接口
            ("/createRoom", CreateRoomHandler),
            ("/getOpenRoomInfo", OpenRoomInfoHandler),
            ("/getDiamondsChange", DiamondsHandler),
            ("/queryServerInfo", QueryRoomHandler),
            ("/getRoomList", PlayRoomListHandler),
            ("/getRoundList", RoundListHandler),
            ("/uploadAAC", UploadAACHandler),
            ("/fetchAAC/(\w+)", GetAACHandler),
            ("/checkUpdate", CheckUpdateHandler),
            ("/wechatLogin", WeChatLoginHandler),
            ("/getAgentRoomList", GetAgentRoomList),
            ("/QueryUnionCSLog",QueryUnionCSLog),

            ("/queryUid", QueryUidHandler),#查询uid是否存在

            ("/getDiamondRecords", DiamondRecordsHandler),
            ("/giveDiamonds", GiveDiamondsHandler),
            ("/editProfiles", EditProfileHandler),
            ("/resetPwd", ResetPwdHandler),
            ("/requestVerifyCode", RequestVerifyCodeHandler),

            ("/makeReviewCode", MakeReviewCodeHandler),
            ("/getRoundInfo", GetByReviewCodeHandler),
            ("/getRoundPlayDetail", RePlayDetailsHandler),

            ("/getRoundRank", RoundRankHandler),
            ("/saveMobilePhone", SetPhoneHandler),
            ("/uploadGeo", UploadGeoHandler),
            ("/shareDiamond", ShareDiamondHandler),
            ("/loginDiamond", LoginDiamondHandler),
            ("/shareDiamondEveryDay", ShareDiamondEveryDayHandler),

            ("/createClub", CreateClubHandler),
            ("/getClubs", GetClubHandler),
            ("/copyClub", CopyClubHandler),
            ("/editClubNotice", UpdateClubNoticeHandler),
            ("/editClubName", UpdateClubNameHandler),
            ("/joinClub", ApplyClubHandler),
            ("/addPlayerToClub", AgreeClubHandler),
            ("/getRequestJoinList", GetVerifyListClubHandler),
            ("/verifyClubUser", VerifyClubUserHandler),
            ("/clubUserList", GetClubUserHandler),
            ("/kickClubUser", KickUserHandler),
            ("/setPlayerPermission", SetUserPermission),
            ("/remarkClubUser", SetUserRemark),
            ("/dismissClub", DismissClubHandler),
            ("/upgradeClub", UpgradeClubHandler),
            ("/getClubConfig", GetClubConfig),

            ("/getDetailsResult", GetDetailsResultHandler),
            ("/getClubScoreList", GetClubScoreListHandler),
            ("/getClubScoreListByGameTypeAndTime", GetClubScoreListByGameTypeAndTime),
            ("/getClubInfo", GetClubInfoHandler),
            ("/getClubOwnerInfo", GetClubOwnerInfo),
            ("/getClubDiamondInfo", GetClubDiamondInfo),
            ("/setClubAutoRoom", SetClubAutoRoomHandler),
            ("/setClubMode", SetClubModeHandler),
            ("/getClubRooms", GetClubRoomHandler),
            ("/getClubRoomsByMatchType", GetClubRoomByMatchTypeHandler),
            ("/getRobotRooms", RobotRoomsHandler),
            ("/clubsRoomRank", ClubsDataHandler),
            # ("/getClubOwnerRoomInfo", GetClubOwnerRoomInfo),
            ("/clubQuickRoom", GetClubQuickRoom),
            ("/getClubScoreByUid", GetClubScoreByUid),
            ("/getClubWinnerList", GetClubWinnerList),
            ("/setClubWinnerList", SetClubWinnerList),
            ("/getClubWinnerRank", GetClubWinnerRank),
            ("/transferClub", TransferClub),

            ("/inviteFriendList", InviteFriendListHandler),
            ("/withdrawRecords", WithdrawRecordsHandler),
            ("/getInviteActivityConfig", InviteActivityConfigHandler),
            ("/exchange", ExchangeHandler),
            ("/withdraw", WithdrawHandler),
            ("/shareInvite", ShareInviteHandler),
            ("/clubShare", ClubShareHandler),
            ("/clubShare.json", ClubShareHandler),

            ("/shop", DiamondPriceHandler),
            ("/feedBack", FeedBackHandler),

            ("/quitClub", QuitClubHandler),
            ("/bindInvite", BindHandler),
            ("/wxpay", WechatPayHandler),
            ("/clubUserRank", GetClubUserRank),
            ("/dumpRecord", DumpRecordHandler),

            ("/increaseDou", IncreaseDou),
            ("/reduceDou", ReduceDou),
            ("/queryDou", QueryDou),
            ("/queryDouLogs", QueryDouLogs),
            ("/queryDouOperLogs", QueryDouOperLogs),

            ("/getFloor", GetFloorHandler),
            ("/addFloor", AddFloorHandler),
            ("/editFloor", EditFloorHandler),
            ("/delFloor", DelFloorHandler),

            ("/getSubFloor", GetSubFloorHandler),
            ("/getSubFloorByMatchType", GetSubFloorByMatchTypeHandler),
            ("/addSubFloor", AddSubFloorHandler),
            ("/editSubFloor", EditSubFloorHandler),
            ("/delSubFloor", DelSubFloorHandler),

            ("/clubDouLogs", ClubDouLogs),
            ("/clubUserDouLogs", ClubUserDouLogs),
            ("/clubUserDetailDouLogs", ClubUserDetailDouLogs),
            ("/qrcode", QRCodeHandler),

            ("/recharge", RechargeConfig),
            ("/modifyAddress", ModifyAddressHandler),
            ("/getAddress", GetAddressHandler),
            ("/buyScoreItem", BuyScoreItemHandler),
            ("/GetOnlineUnionCount",GetOnlineUnionCount),
            ("/signInActivity", SignInActivity),
            ("/signInItemInfo", SignInItemInfo),
            ("/checkRoom", CheckRoomHandler),

            ("/getGameCountLogs", GetGameCountLogs),
            ("/setGameCountLogs", SetGameCountLogs),

            ("/setClubBlock", SetClubBlockHandler),
            ("/getClubGamePlay", GetClubGamePlay),
            ("/queryClubBlock", QueryClubBlockHandler),
            ("/getClubUserRoomInfo", GetClubUserRoomInfo),

            ("/transferClubUser", TransferClubUser),
            ("/getClubBaseInfo", GetClubBaseInfo),
            ("/tagClubUser", TagClubUser),
            ("/getClubTagUserRoomInfo", GetClubTagUserRoomInfo),
            ("/getClubGameLogs", GetClubGameLogs),
            ("/getClubRoomList", PlayRoomListWithClubAndTimeHandler),

            ("/setClubQueryWinnerScore", SetClubQueryWinnerScore),

            ("/getClubTask", GetClubTask),
            ("/modifyClubTask", ModifyClubTask),
            ("/taskClubShare", TaskClubShare),
            ("/bonusClubTaskShare", BonusClubTaskShare),
            ("/bonusClubTaskRound", BonusClubTaskRound),

            ("/changeYuanBaoToDiamond", ChangeYuanBaoToDiamond),
            ("/buyYuanBaoHandler", BuyYuanBaoHandler),

            ("/springActivity", SpringActivity),
            ("/springActivityRecv", SpringActivityRecv),
            ("/springActivityLogs", SpringActivityLogs),

            ("/chargePush", ChargePushHandler),

            # 联盟相关接口
            ("/queryAllSmallUnionManager", QueryAllSmallUnionManager),
            ("/querySmallUnionUsers", QuerySmallUnionUsers),
            ("/queryUnionPartner", QueryUnionPartner),
            ("/queryUnionPartnerUsers", QueryUnionPartnerUsers),
            ("/setSmallUnionProfit", SetSmallUnionProfit),
            ("/setUnionPartnerProfit", SetUnionPartnerProfit),
            ("/queryUnionManagerInfo", QueryUnionManagerInfo),
            ("/getUnionFloor", GetUnionFloor),
            ("/delUnionFloor", DelUnionFloor),
            ("/editUnionFloor", EditUnionFloor),
            ("/addUnionFloor", AddUnionFloor),
            ("/getUnionAllSubFloor", GetUnionAllSubFloor),
            ("/getUnionSubFloor", GetUnionSubFloor),
            ("/delUnionSubFloor", DelUnionSubFloor),
            ("/editUnionSubFloor", EditUnionSubFloor),
            ("/addUnionSubFloor", AddUnionSubFloor),
            ("/createUnion", CreateUnion),
            ("/editUnionNotice", EditUnionNotice),
            ("/editUnionName", EditUnionName),
            ("/getUnionDiamondInfo", GetUnionDiamondInfo),
            ("/queryUnionUsers", QueryUnionUsers),
            ("/setUnionPlayerPermission", SetUnionPlayerPermission),
            ("/tagUnionUser", TagUnionUser),
            ("/addEnergy", AddEnergy),
            ("/reduceEnergy", ReduceEnergy),
            ("/queryEnergyLogs", QueryEnergyLogs),
            ("/transferEnergy", TransferEnergy),
            ("/queryTransferEnergyLogs", QueryTransferEnergyLogs),
            ("/setUnionBlock", SetUnionBlock),
            ("/queryUnionBlock", QueryUnionBlock),
            ("/QueryUnionDirectUsers",QueryUnionDirectUsers),
            ("/joinUnion", JoinUnion),
            ("/getUnionInfo", GetUnionInfo),
            ("/getMyUnionInfo", GetMyUnionInfo),
            ("/quitUnion", QuitUnion),
            ("/getUnionGamePlay", GetUnionGamePlay),
            ("/queryUnionRoomsByFloor", QueryUnionRoomsByFloor),
            ("/queryUnionRoomsBySubFloor", QueryUnionRoomsBySubFloor),
            ("/queryUnionAllRooms", QueryUnionAllRooms),
            ("/GetSafeBoxFaxList",GetSafeBoxFaxList),
            ("/SaveUnionCSLog",SaveUnionCSLog),
            ("/remarkUnionUser", RemarkUnionUser),
            ("/kickUnionUser", KickUnionUser),
            ("/addPlayerToUnion", AddPlayerToUnion),
            ("/requestMergeUnion", RequestMergeUnion),
            ("/queryUnionRequestJoinList", QueryUnionRequestJoinList),
            ("/verifyUnionRequestJoin", VerifyUnionRequestJoin),
            ("/queryUnionScoreList", QueryUnionScoreList),
            ("/queryUnionGameLogs", QueryUnionGameLogs),
            ('/queryUnionAllUsers', QueryUnionAllUsers),
            ("/NoticeUnionMessage",NoticeUnionMessage),
            ("/getUnionGameCountLogs", GetUnionGameCountLogs),
            ("/setUnionGameCountLogs", SetUnionGameCountLogs),

            ("/SetUnionPlayerAsSubManager", SetUnionPlayerAsSubManager),
            ("/SetUnionPlayerAsPartner", SetUnionPlayerAsPartner),
            ("/SetSmallUnionDivide", SetSmallUnionDivide),
            ("/SetUnionPartnerDivide", SetUnionPartnerDivide),
            ("/SetUnionUserPlayerDivide",SetUnionUserPlayerDivide),
            ("/QuerySubManagerOrPartnerUsers", QuerySubManagerOrPartnerUsers),
            ("/QueryUserExtraList",QueryUserExtraList),
            ("/GetUnionUserDive",GetUnionUserDive),
            ("/GetUnionUserDivide", GetUnionUserDivide),
            ("/UnionManagerAddEnergy", UnionManagerAddEnergy),
            ("/SpeedJoinUnionRoom", SpeedJoinUnionRoom),
            ("/QueryUnionSafeBoxBalance",QueryUnionSafeBoxBalance),
            ("/FetchUnionSafeBoxBalance",FetchUnionSafeBoxBalance),
            ("/QueryUnionCSList",QueryUnionCSList),
            ("/TestOK",TestOK)

        ]
        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "views"),
            static_path=config.static_path,
            xsrf_cookies=False,
            debug=config.IS_DEBUG,
            xheaders=True,
        )
        tornado.web.Application.__init__(self, handlers, **settings)


# Web Server 实例
server = None


def sig_handler(sig, frame):
    logging.warning('Caught signal: %s', sig)
    tornado.ioloop.IOLoop.instance().add_callback(shutdown)


def shutdown():
    logging.info('Stopping http server')
    server.stop()

    logging.info(
        'Will shutdown in %s seconds ...',
        config.SHUTDOWN_WAIT_SECONDS)
    io_loop = tornado.ioloop.IOLoop.instance()
    io_loop.stop()
    logging.info('Shutdown')


def main():
    global server
    logging.basicConfig(filename=LOG_PATH + 'run.txt', level=logging.DEBUG,
                        format='%(asctime)-15s %(levelname)s %(message)s')
    tornado.options.parse_command_line()
    server = tornado.httpserver.HTTPServer(Application(), xheaders=True)
    server.listen(options.port)

    signal.signal(signal.SIGTERM, sig_handler)
    signal.signal(signal.SIGINT, sig_handler)

    tornado.ioloop.IOLoop.instance().start()
    logging.info('Exit')


if __name__ == "__main__":
    main()
