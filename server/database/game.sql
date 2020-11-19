SET FOREIGN_KEY_CHECKS=0;

-- ----------------------------
-- Table structure for admins
-- ----------------------------
DROP TABLE IF EXISTS `admins`;
CREATE TABLE `admins` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL DEFAULT '' COMMENT '用户名',
  `password` varchar(40) NOT NULL DEFAULT '' COMMENT '密码',
  `powers` varchar(255) NOT NULL DEFAULT '' COMMENT '权限列表',
  `is_root` tinyint(4) NOT NULL DEFAULT '0' COMMENT '是否根用户',
  `status` tinyint(4) DEFAULT '1' COMMENT '用户状态 -1 禁止访问 1 正常用户状态 -1 禁止访问 1 正常',
  `wx_username` varchar(128) DEFAULT NULL,
  `refer_uid` int(11) DEFAULT NULL,
  `is_partner` int(11) NOT NULL DEFAULT '0' COMMENT '是否是总代',
  `union_id` varchar(128) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`) USING BTREE,
  KEY `wx_username` (`wx_username`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for agent_config
-- ----------------------------
DROP TABLE IF EXISTS `agent_config`;
CREATE TABLE `agent_config` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `var` varchar(32) DEFAULT NULL,
  `value` text,
  `desc` varchar(30) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for baidutranslate
-- ----------------------------
DROP TABLE IF EXISTS `baidutranslate`;
CREATE TABLE `baidutranslate` (
  `Id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `Userid` bigint(20) DEFAULT NULL,
  `Cashamount` decimal(18,4) DEFAULT NULL,
  `Ordernum` varchar(50) DEFAULT NULL,
  `Createtime` datetime DEFAULT NULL,
  `type` int(11) DEFAULT NULL,
  `bili` decimal(18,2) DEFAULT NULL,
  `bitype` int(11) DEFAULT NULL,
  `uid` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`Id`),
  UNIQUE KEY `Id` (`Id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for balance
-- ----------------------------
DROP TABLE IF EXISTS `balance`;
CREATE TABLE `balance` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `uid` int(11) DEFAULT NULL,
  `refer_uid` int(11) DEFAULT NULL,
  `level` int(11) DEFAULT NULL,
  `total_charge` int(11) NOT NULL DEFAULT '0',
  `current_charge` int(11) NOT NULL DEFAULT '0',
  `withdraw_count` int(11) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `uid` (`uid`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- Table structure for channels
-- ----------------------------
DROP TABLE IF EXISTS `channels`;
CREATE TABLE `channels` (
  `channel_id` int(11) unsigned NOT NULL AUTO_INCREMENT COMMENT '渠道ID',
  `channel_name` varchar(50) NOT NULL DEFAULT '' COMMENT '渠道名称',
  `channel_version` varchar(50) NOT NULL DEFAULT '' COMMENT '渠道版本号',
  `channel_apk` varchar(100) NOT NULL DEFAULT '' COMMENT 'APK文件名',
  `sub_count` int(11) NOT NULL DEFAULT '0' COMMENT '扣量百分比',
  PRIMARY KEY (`channel_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='渠道信息表';

-- ----------------------------
-- Table structure for channel_configs
-- ----------------------------
DROP TABLE IF EXISTS `channel_configs`;
CREATE TABLE `channel_configs` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `channel_id` int(11) unsigned NOT NULL DEFAULT '0' COMMENT '渠道ID',
  `platform` int(11) unsigned NOT NULL DEFAULT '0' COMMENT '平台ID',
  `name` varchar(255) NOT NULL DEFAULT '' COMMENT '配置名字',
  `value` varchar(255) NOT NULL DEFAULT '' COMMENT '配置的值',
  `desc` varchar(11) NOT NULL DEFAULT '''''' COMMENT '配置描述',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=99 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for club
-- ----------------------------
DROP TABLE IF EXISTS `club`;
CREATE TABLE `club` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `uid` int(11) NOT NULL COMMENT '用户 ID',
  `name` varchar(255) DEFAULT '' COMMENT '茶馆名称',
  `notice` varchar(255) DEFAULT NULL COMMENT '公告',
  `level` tinyint(2) NOT NULL DEFAULT '1' COMMENT '等级',
  `count` int(11) NOT NULL DEFAULT '1' COMMENT '玩家数量',
  `status` tinyint(2) NOT NULL DEFAULT '0' COMMENT '0 正常 -1 已解散',
  `create_time` int(11) DEFAULT NULL COMMENT '创建时间',
  `dismiss_time` int(11) DEFAULT '0' COMMENT '解散时间',
  `lock_status` int(11) NOT NULL DEFAULT '0',
  `wet_chat` varchar(32) DEFAULT NULL,
  `query_winner_score` int(11) DEFAULT '0',
  `task_share` int(11) DEFAULT '0',
  `task_today_game_round` varchar(128) DEFAULT '{}',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for club_block
-- ----------------------------
DROP TABLE IF EXISTS `club_block`;
CREATE TABLE `club_block` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `club_id` int(11) DEFAULT NULL,
  `uid` int(11) DEFAULT NULL,
  `ref_uid` int(11) DEFAULT NULL,
  `time` int(11) DEFAULT NULL,
  `status` int(11) NOT NULL DEFAULT '0',
  `block_status` int(11) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`) USING BTREE,
  UNIQUE KEY `club_id,uid,ref_uid` (`club_id`,`uid`,`ref_uid`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for club_config
-- ----------------------------
DROP TABLE IF EXISTS `club_config`;
CREATE TABLE `club_config` (
  `var` varchar(50) NOT NULL DEFAULT '' COMMENT '配置KEY',
  `value` varchar(255) NOT NULL DEFAULT '' COMMENT '配置的值',
  `desc` varchar(255) DEFAULT '' COMMENT '配置说明',
  PRIMARY KEY (`var`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for club_floor
-- ----------------------------
DROP TABLE IF EXISTS `club_floor`;
CREATE TABLE `club_floor` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `club_id` int(11) DEFAULT NULL,
  `game_type` int(11) DEFAULT NULL,
  `match_type` int(11) NOT NULL DEFAULT '0' COMMENT '0 普通楼层 1 比赛楼层',
  PRIMARY KEY (`id`),
  KEY `club_id` (`club_id`) USING BTREE,
  KEY `club_id,match_type` (`club_id`,`match_type`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- Table structure for club_level_config
-- ----------------------------
DROP TABLE IF EXISTS `club_level_config`;
CREATE TABLE `club_level_config` (
  `level` int(11) NOT NULL COMMENT '等级',
  `limit` int(11) NOT NULL COMMENT '人数限制',
  `price` int(11) NOT NULL COMMENT '消耗',
  PRIMARY KEY (`level`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for club_profit_record
-- ----------------------------
DROP TABLE IF EXISTS `club_profit_record`;
CREATE TABLE `club_profit_record` (
  `id` int(11) NOT NULL,
  `union_id` int(11) DEFAULT NULL COMMENT '大联盟id',
  `uid` int(11) DEFAULT NULL COMMENT '用户id',
  `source_uid` int(11) DEFAULT NULL COMMENT '源用户id',
  `game_kind` int(11) DEFAULT NULL COMMENT '游戏类型',
  `timestamp` int(11) DEFAULT NULL COMMENT '时间',
  `tid` int(11) DEFAULT NULL COMMENT '桌子号',
  `settlementtime` int(11) DEFAULT NULL COMMENT '结算时间',
  `amount` int(11) DEFAULT NULL COMMENT '福利数量',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for club_sub_floor
-- ----------------------------
DROP TABLE IF EXISTS `club_sub_floor`;
CREATE TABLE `club_sub_floor` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `club_id` int(11) NOT NULL,
  `floor_id` int(11) DEFAULT NULL,
  `play_config` varchar(1024) DEFAULT NULL,
  `auto_room` int(11) DEFAULT NULL,
  `game_type` int(11) NOT NULL,
  `match_type` int(11) NOT NULL DEFAULT '0' COMMENT '0 普通子楼层 1 比赛子楼层',
  `match_config` varchar(512) DEFAULT NULL,
  `tip` int(11) NOT NULL DEFAULT '0' COMMENT '抽水',
  `tip_limit` int(11) NOT NULL DEFAULT '0' COMMENT '抽水分数过滤',
  `tip_payment_method` int(11) NOT NULL DEFAULT '0' COMMENT '抽水结算方式',
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`) USING BTREE,
  KEY `club_id,floor` (`club_id`,`floor_id`) USING BTREE,
  KEY `club_id,floor,match_type` (`club_id`,`floor_id`,`match_type`) USING BTREE,
  KEY `floor` (`floor_id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for club_user
-- ----------------------------
DROP TABLE IF EXISTS `club_user`;
CREATE TABLE `club_user` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `club_id` int(11) DEFAULT NULL COMMENT '茶馆 ID',
  `club_owner` int(11) DEFAULT NULL COMMENT '馆主 ID',
  `uid` int(11) NOT NULL DEFAULT '-1' COMMENT '用户 ID',
  `score` int(11) NOT NULL DEFAULT '0',
  `remark` varchar(36) DEFAULT NULL COMMENT '用户名备注',
  `permission` int(11) DEFAULT NULL COMMENT '权限',
  `join_time` int(11) DEFAULT NULL COMMENT '加入时间',
  `lock_score` int(11) NOT NULL DEFAULT '0' COMMENT '游戏锁定分数',
  `add_score` int(11) NOT NULL DEFAULT '0' COMMENT '总上分',
  `minus_score` int(11) NOT NULL DEFAULT '0' COMMENT '总下分',
  `add_time` int(11) DEFAULT NULL COMMENT '最近上分时间',
  `minus_time` int(11) DEFAULT NULL COMMENT '最近下分时间',
  `game_score` int(11) NOT NULL DEFAULT '0' COMMENT '游戏输赢分',
  `game_round` int(11) NOT NULL DEFAULT '0' COMMENT '游戏总局数',
  `limit_score` int(11) NOT NULL DEFAULT '0' COMMENT '总抽成',
  `lock_table` int(11) NOT NULL DEFAULT '0',
  `lock_time` int(11) NOT NULL DEFAULT '0',
  `tag_uid` int(11) NOT NULL DEFAULT '0' COMMENT '关联UID',
  `tag_name` varchar(32) DEFAULT NULL COMMENT '关联昵称',
  `share_time` int(11) DEFAULT '0',
  `bonus_share_time` int(11) DEFAULT '0',
  `today_game_round` int(11) DEFAULT '0',
  `bonus_today_game_round` varchar(128) DEFAULT '{}',
  PRIMARY KEY (`id`),
  UNIQUE KEY `club_id_2` (`club_id`,`uid`) USING BTREE,
  KEY `club_id` (`club_id`) USING BTREE,
  KEY `club_owner` (`club_owner`) USING BTREE,
  KEY `club_owner_2` (`club_owner`,`uid`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for club_verify
-- ----------------------------
DROP TABLE IF EXISTS `club_verify`;
CREATE TABLE `club_verify` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `club_id` int(11) NOT NULL COMMENT '茶馆 ID',
  `uid` int(11) NOT NULL COMMENT '用户 ID',
  `time` int(11) NOT NULL DEFAULT '0' COMMENT '申请时间',
  `status` int(11) NOT NULL DEFAULT '0' COMMENT '0 待验证 -1 已拒绝 -2 已屏蔽 1 通过',
  `update_time` int(11) DEFAULT '0' COMMENT '操作时间',
  `operator_user` varchar(32) DEFAULT '',
  `promo` int(11) DEFAULT NULL COMMENT '玩家进入邀请码',
  PRIMARY KEY (`id`),
  UNIQUE KEY `club_id` (`club_id`,`uid`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for configdetailed
-- ----------------------------
DROP TABLE IF EXISTS `configdetailed`;
CREATE TABLE `configdetailed` (
  `Id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `Configid` bigint(20) DEFAULT NULL COMMENT '类型编号：3商城',
  `Centers` varchar(500) DEFAULT NULL,
  `Title` varchar(50) DEFAULT NULL,
  `Creatimes` datetime DEFAULT NULL,
  `Serialnumber` int(11) DEFAULT NULL,
  `Numbers` int(11) DEFAULT NULL COMMENT '充值数量',
  `Imgpath` varchar(500) DEFAULT NULL,
  `Phonetype` int(11) DEFAULT NULL COMMENT '手机类型：1安卓，2ios',
  `Gifts` bigint(20) DEFAULT NULL COMMENT '赠送数量',
  `Prices` decimal(18,2) DEFAULT NULL COMMENT '价格',
  `Currencytype` int(11) DEFAULT NULL COMMENT '充值类型：1金币 2钻石',
  `Isservice` int(11) DEFAULT '0' COMMENT '0实物商品 1服务商品',
  `LimitCount` int(11) DEFAULT '0' COMMENT '用户可以兑换次数限制',
  PRIMARY KEY (`Id`),
  UNIQUE KEY `Id` (`Id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for configs
-- ----------------------------
DROP TABLE IF EXISTS `configs`;
CREATE TABLE `configs` (
  `var` varchar(50) NOT NULL COMMENT '配置KEY',
  `value` varchar(1024) NOT NULL DEFAULT '' COMMENT '配置的值',
  `desc` varchar(255) NOT NULL DEFAULT '''''' COMMENT '配置说明',
  PRIMARY KEY (`var`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='配置表';

-- ----------------------------
-- Table structure for configurations
-- ----------------------------
DROP TABLE IF EXISTS `configurations`;
CREATE TABLE `configurations` (
  `Id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `Title` varchar(50) DEFAULT NULL,
  `Key_s` varchar(500) DEFAULT NULL,
  PRIMARY KEY (`Id`),
  UNIQUE KEY `Id` (`Id`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for denny_words
-- ----------------------------
DROP TABLE IF EXISTS `denny_words`;
CREATE TABLE `denny_words` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `word` varchar(32) NOT NULL DEFAULT '' COMMENT '敏感词',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for exchangeamount
-- ----------------------------
DROP TABLE IF EXISTS `exchangeamount`;
CREATE TABLE `exchangeamount` (
  `Id` bigint(11) NOT NULL AUTO_INCREMENT,
  `UserId` bigint(11) DEFAULT NULL COMMENT '用户id',
  `yuanbao` bigint(11) DEFAULT NULL COMMENT '元宝数量',
  `moneys` decimal(18,2) DEFAULT NULL COMMENT '实际到账金额',
  `staues` int(11) DEFAULT NULL COMMENT '0 未到账 1 到账',
  `creatime` datetime DEFAULT NULL COMMENT '创建时间',
  `updatetime` datetime DEFAULT NULL COMMENT '更新时间',
  `txmoneys` decimal(18,2) DEFAULT NULL COMMENT '提现金额',
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- ----------------------------
-- Table structure for exchangeyb
-- ----------------------------
DROP TABLE IF EXISTS `exchangeyb`;
CREATE TABLE `exchangeyb` (
  `Id` bigint(11) NOT NULL AUTO_INCREMENT,
  `UserId` bigint(11) DEFAULT NULL,
  `Yuanbao` bigint(11) DEFAULT NULL,
  `CreaTime` int(20) DEFAULT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- ----------------------------
-- Table structure for iap
-- ----------------------------
DROP TABLE IF EXISTS `iap`;
CREATE TABLE `iap` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `uid` int(11) DEFAULT NULL COMMENT '用户 ID',
  `oid` varchar(128) DEFAULT NULL COMMENT '第三方订单 ID',
  `raw_data` text COMMENT '原始数据',
  `ret_raw_data` text COMMENT '第三方返回原始数据',
  `item_id` varchar(24) DEFAULT NULL COMMENT '物品 ID',
  `channel_id` int(11) DEFAULT NULL COMMENT '渠道 ID',
  `sandbox` tinyint(1) DEFAULT NULL COMMENT '是否沙盒',
  `status` smallint(2) DEFAULT NULL COMMENT '状态 0:生成待检测 1:已返回支付成功 2:检测不到订单',
  `time` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `oid` (`oid`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for integralorder
-- ----------------------------
DROP TABLE IF EXISTS `integralorder`;
CREATE TABLE `integralorder` (
  `Id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键',
  `integral_num` varchar(50) CHARACTER SET latin1 DEFAULT NULL COMMENT '订单号',
  `product_id` bigint(20) DEFAULT NULL COMMENT '积分商品Id',
  `states` int(11) DEFAULT NULL COMMENT '处理状态：0待处理 1已处理',
  `uid` bigint(20) DEFAULT NULL COMMENT '用户Uid',
  `phone` varchar(20) CHARACTER SET latin1 DEFAULT NULL COMMENT '电话号码',
  `numbers` bigint(20) DEFAULT NULL COMMENT '积分数量',
  `creation_time` datetime DEFAULT NULL COMMENT '创建时间',
  `real_name` varchar(20) DEFAULT NULL COMMENT '????',
  `receiving_address` varchar(200) DEFAULT NULL COMMENT '??????',
  `remark` varchar(200) DEFAULT NULL COMMENT '??',
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for ji_fu
-- ----------------------------
DROP TABLE IF EXISTS `ji_fu`;
CREATE TABLE `ji_fu` (
  `uid` bigint(20) NOT NULL,
  `invitee` bigint(20) NOT NULL COMMENT '被邀请人',
  `first_round` tinyint(4) NOT NULL DEFAULT '0' COMMENT '完成首局',
  `first_invite` tinyint(4) NOT NULL DEFAULT '0' COMMENT '完成邀请',
  `first_round_time` bigint(20) NOT NULL DEFAULT '0' COMMENT '首局完成时间',
  `first_invite_time` bigint(20) NOT NULL DEFAULT '0' COMMENT '首次邀请时间',
  `bind_time` bigint(20) NOT NULL COMMENT '绑定时间',
  `total_fu` int(11) NOT NULL DEFAULT '0' COMMENT '积福数',
  UNIQUE KEY `invitee` (`invitee`) USING BTREE,
  KEY `uid` (`uid`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- Table structure for level_ip
-- ----------------------------
DROP TABLE IF EXISTS `level_ip`;
CREATE TABLE `level_ip` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `round_count` int(11) DEFAULT NULL,
  `level` int(11) DEFAULT NULL,
  `ips` varchar(512) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- Table structure for lottery
-- ----------------------------
DROP TABLE IF EXISTS `lottery`;
CREATE TABLE `lottery` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `round` int(11) DEFAULT NULL,
  `diamond` int(11) DEFAULT NULL,
  `count` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for onlines
-- ----------------------------
DROP TABLE IF EXISTS `onlines`;
CREATE TABLE `onlines` (
  `uid` int(11) NOT NULL COMMENT '玩家ID',
  `token` varchar(40) NOT NULL DEFAULT '' COMMENT '玩家KEY',
  `login_time` int(11) NOT NULL COMMENT '登陆时间',
  `tid` int(11) NOT NULL DEFAULT '0' COMMENT '桌子ID',
  `state` bigint(20) DEFAULT '0' COMMENT '当前在线玩家状态 0:未开始游戏 1:已开始游戏',
  UNIQUE KEY `uid` (`uid`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='在线表';

-- ----------------------------
-- Table structure for operatorlist
-- ----------------------------
DROP TABLE IF EXISTS `operatorlist`;
CREATE TABLE `operatorlist` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `gradename` varchar(100) DEFAULT NULL COMMENT '等级名字（平台写死）',
  `bll` decimal(18,2) DEFAULT NULL COMMENT '当前生效比例',
  `creatime` datetime DEFAULT NULL COMMENT '创建时间',
  `Uid` bigint(20) DEFAULT NULL COMMENT '区域代理id',
  `Bbll` decimal(18,2) DEFAULT NULL COMMENT '下月1号生效比例',
  `midftime` datetime DEFAULT NULL COMMENT '修改时间',
  `Levels` int(11) DEFAULT NULL COMMENT '等级：1、2、3、4、5',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for orders
-- ----------------------------
DROP TABLE IF EXISTS `orders`;
CREATE TABLE `orders` (
  `Id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `Userinfoid` bigint(20) DEFAULT NULL COMMENT 'UID',
  `Ordernum` varchar(50) DEFAULT NULL COMMENT '订单编号',
  `Orderprice` decimal(18,2) DEFAULT NULL COMMENT '价格',
  `Ordertype` int(11) DEFAULT NULL COMMENT '1、金币 2、钻石 3辣椒豆',
  `Paystates` int(11) DEFAULT NULL,
  `Ordertates` int(11) DEFAULT NULL,
  `Ordernumber` bigint(20) DEFAULT NULL,
  `Givenumber` bigint(20) DEFAULT NULL,
  `Productid` bigint(20) DEFAULT NULL,
  `Creationtime` datetime DEFAULT NULL,
  `IsFrozen` int(11) DEFAULT NULL COMMENT '是否冻结 1冻结 0未冻结',
  PRIMARY KEY (`Id`),
  UNIQUE KEY `Id` (`Id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for payment
-- ----------------------------
DROP TABLE IF EXISTS `payment`;
CREATE TABLE `payment` (
  `pid` int(11) NOT NULL AUTO_INCREMENT,
  `uid` bigint(20) NOT NULL,
  `nick_name` varchar(32) DEFAULT NULL COMMENT '昵称',
  `game_id` int(10) unsigned NOT NULL DEFAULT '0' COMMENT '游戏ID',
  `channel_id` int(10) unsigned NOT NULL DEFAULT '0' COMMENT '客户端渠道',
  `pay_method` int(10) unsigned NOT NULL DEFAULT '0' COMMENT '支付方式',
  `amount` int(11) NOT NULL COMMENT '订单金额',
  `coins` int(11) NOT NULL DEFAULT '0' COMMENT '低级币数量',
  `diamonds` int(11) NOT NULL COMMENT '高级币数量',
  `billing_number` varchar(100) NOT NULL DEFAULT '0' COMMENT '平台流水号',
  `status` tinyint(4) NOT NULL DEFAULT '0' COMMENT '订单状态',
  `order_time` int(11) NOT NULL COMMENT '下单时间',
  `finish_time` int(11) NOT NULL DEFAULT '0' COMMENT '完成时间',
  `ip` varchar(32) NOT NULL DEFAULT '' COMMENT '操作IP',
  `admin_id` int(11) NOT NULL DEFAULT '0' COMMENT '管理员ID',
  `admin_name` varchar(50) DEFAULT NULL COMMENT '管理员名称',
  `memo` varchar(255) DEFAULT '' COMMENT '附加信息',
  PRIMARY KEY (`pid`),
  KEY `uid` (`uid`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for players
-- ----------------------------
DROP TABLE IF EXISTS `players`;
CREATE TABLE `players` (
  `uid` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '内部uid',
  `nick_name` varchar(32) CHARACTER SET utf8 NOT NULL DEFAULT '' COMMENT '昵称',
  `avatar` varchar(255) CHARACTER SET utf8 NOT NULL DEFAULT '' COMMENT '头像URL',
  `sex` tinyint(1) unsigned NOT NULL DEFAULT '2' COMMENT '1男，0女, 2未知',
  `imei` varchar(32) CHARACTER SET utf8 DEFAULT '',
  `imsi` varchar(32) CHARACTER SET utf8 NOT NULL DEFAULT '',
  `mac` varchar(32) CHARACTER SET utf8 DEFAULT '' COMMENT '设备类型',
  `model` varchar(50) CHARACTER SET utf8 NOT NULL DEFAULT '' COMMENT '设备型号',
  `reg_time` bigint(20) NOT NULL DEFAULT '0' COMMENT '注册时间',
  `channel_id` int(11) NOT NULL DEFAULT '0' COMMENT '注册渠道',
  `platform` int(11) NOT NULL COMMENT '平台',
  `ver` varchar(20) CHARACTER SET utf8 NOT NULL DEFAULT '' COMMENT '版本',
  `diamond` int(11) NOT NULL DEFAULT '0' COMMENT '钻石',
  `token` varchar(255) CHARACTER SET utf8 DEFAULT NULL COMMENT '玩家token',
  `refresh_token` varchar(255) CHARACTER SET utf8 DEFAULT NULL COMMENT '刷新token',
  `expires_at` int(11) NOT NULL DEFAULT '0' COMMENT '过期时间',
  `auto_token` varchar(42) CHARACTER SET utf8 DEFAULT NULL COMMENT '自动登录token',
  `openid` varchar(100) CHARACTER SET utf8 DEFAULT NULL COMMENT '开放平台ID',
  `unionid` varchar(100) CHARACTER SET utf8 DEFAULT NULL COMMENT 'UNION_ID',
  `agent` tinyint(4) DEFAULT '0' COMMENT '0用户1代理',
  `phone` varchar(20) DEFAULT '' COMMENT '手机号码',
  `pwd` varchar(32) DEFAULT '' COMMENT '密码',
  `verify_code` varchar(6) DEFAULT '' COMMENT '验证码',
  `verify_expire_at` bigint(20) DEFAULT '0' COMMENT '验证码过期时间',
  `login_time` bigint(20) NOT NULL DEFAULT '0' COMMENT '最后登录时间',
  `ip` bigint(20) NOT NULL DEFAULT '0' COMMENT '登录IP',
  `share_time` bigint(20) NOT NULL DEFAULT '0' COMMENT '分享时间 -1 则可以分享 0 则不能分享',
  `get_diamonds` int(11) NOT NULL DEFAULT '0' COMMENT '-1 已领取 0 不能领取',
  `base_refer_uid` int(11) NOT NULL DEFAULT '-1' COMMENT '顶级关联上级 UID',
  `refer_uid` int(11) NOT NULL DEFAULT '-1' COMMENT '关联上级 UID',
  `refer_time` int(11) DEFAULT NULL COMMENT '建立关联时间',
  `withdraw_time` int(11) DEFAULT '-1' COMMENT '提现时间 默认 -1',
  `withdraw_nickname` varchar(128) DEFAULT NULL COMMENT '提现昵称',
  `bind_after_login_time` int(11) DEFAULT '-1' COMMENT '建立关联后首次打开游戏时间 默认 -1',
  `level` int(11) DEFAULT '1' COMMENT '用户等级',
  `wechat_openid` varchar(100) DEFAULT NULL COMMENT '微信公众平台 OPENID',
  `invite_uid_1` int(11) NOT NULL DEFAULT '0' COMMENT '最上级代理 UID',
  `invite_uid_2` int(11) NOT NULL DEFAULT '0' COMMENT '上级代理 UID',
  `bind_time` int(11) NOT NULL DEFAULT '0',
  `pdk_index` int(11) NOT NULL DEFAULT '0',
  `zzmj_index` int(11) NOT NULL DEFAULT '0',
  `custom_type` int(11) NOT NULL DEFAULT '0' COMMENT '0用户 1 代理 3运营',
  `agent_id` int(11) DEFAULT '0' COMMENT '代理商 ID',
  `channel_uid` int(11) DEFAULT '0' COMMENT '渠道商 ID',
  `father_id` int(11) NOT NULL DEFAULT '0',
  `hierarchical` varchar(2000) DEFAULT NULL COMMENT '层级串',
  `la_jiao_dou` int(11) NOT NULL DEFAULT '0',
  `allow_match` int(11) NOT NULL DEFAULT '0' COMMENT '是否允许开启比赛房',
  `score` int(11) NOT NULL DEFAULT '0' COMMENT '积分',
  `sign_time` int(11) NOT NULL DEFAULT '0' COMMENT '最后一次签到时间',
  `sign_count` int(11) NOT NULL DEFAULT '0' COMMENT '签到天数',
  `is_lucker` tinyint(4) NOT NULL DEFAULT '0' COMMENT '是否是幸运玩家',
  `round_count` int(11) NOT NULL DEFAULT '0' COMMENT '游戏局数',
  `rate_score` int(11) NOT NULL DEFAULT '5' COMMENT '评分',
  `channel_lvid` int(11) DEFAULT '0' COMMENT '运营账号等级',
  `gold` int(11) NOT NULL DEFAULT '0' COMMENT '金币',
  `lock_gold` int(11) NOT NULL DEFAULT '0' COMMENT '锁定金币',
  `lock_table` int(11) NOT NULL DEFAULT '0' COMMENT '锁定桌子',
  `lock_time` int(11) NOT NULL DEFAULT '0' COMMENT '锁定时间',
  `allow_niu_niu` int(11) NOT NULL DEFAULT '0' COMMENT '允许开牛牛',
  `yuan_bao` int(11) NOT NULL DEFAULT '0' COMMENT '元宝',
  `manage_yuan_bao` int(11) NOT NULL DEFAULT '0' COMMENT '返还的元宝',
  `Tmanage_yuan_bao` int(11) DEFAULT '0' COMMENT '提现消耗元宝数',
  `IsDelete` int(11) DEFAULT '0' COMMENT '设置标志',
  PRIMARY KEY (`uid`),
  UNIQUE KEY `auto_token` (`auto_token`) USING BTREE,
  UNIQUE KEY `openid` (`openid`) USING BTREE,
  UNIQUE KEY `unionid` (`unionid`) USING BTREE,
  KEY `mac` (`mac`,`imei`) USING BTREE,
  KEY `token` (`token`) USING BTREE,
  KEY `login_time` (`login_time`) USING BTREE,
  KEY `reg_time` (`reg_time`) USING BTREE,
  KEY `uid` (`uid`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=999578 DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- Table structure for players_android
-- ----------------------------
DROP TABLE IF EXISTS `players_android`;
CREATE TABLE `players_android` (
  `uid` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '内部uid',
  `nick_name` varchar(32) CHARACTER SET utf8 NOT NULL DEFAULT '' COMMENT '昵称',
  `avatar` varchar(255) CHARACTER SET utf8 NOT NULL DEFAULT '' COMMENT '头像URL',
  `sex` tinyint(1) unsigned NOT NULL DEFAULT '2' COMMENT '1男，0女, 2未知',
  `imei` varchar(32) CHARACTER SET utf8 DEFAULT '',
  `imsi` varchar(32) CHARACTER SET utf8 NOT NULL DEFAULT '',
  `mac` varchar(32) CHARACTER SET utf8 DEFAULT '' COMMENT '设备类型',
  `model` varchar(50) CHARACTER SET utf8 NOT NULL DEFAULT '' COMMENT '设备型号',
  `reg_time` bigint(20) NOT NULL DEFAULT '0' COMMENT '注册时间',
  `channel_id` int(11) NOT NULL DEFAULT '0' COMMENT '注册渠道',
  `platform` int(11) NOT NULL COMMENT '平台',
  `ver` varchar(20) CHARACTER SET utf8 NOT NULL DEFAULT '' COMMENT '版本',
  `diamond` int(11) NOT NULL DEFAULT '0' COMMENT '钻石',
  `token` varchar(255) CHARACTER SET utf8 DEFAULT NULL COMMENT '玩家token',
  `refresh_token` varchar(255) CHARACTER SET utf8 DEFAULT NULL COMMENT '刷新token',
  `expires_at` int(11) NOT NULL DEFAULT '0' COMMENT '过期时间',
  `auto_token` varchar(42) CHARACTER SET utf8 DEFAULT NULL COMMENT '自动登录token',
  `openid` varchar(100) CHARACTER SET utf8 DEFAULT NULL COMMENT '开放平台ID',
  `unionid` varchar(100) CHARACTER SET utf8 DEFAULT NULL COMMENT 'UNION_ID',
  `agent` tinyint(4) DEFAULT '0' COMMENT '0用户1代理',
  `phone` varchar(20) DEFAULT '' COMMENT '手机号码',
  `pwd` varchar(32) DEFAULT '' COMMENT '密码',
  `verify_code` varchar(6) DEFAULT '' COMMENT '验证码',
  `verify_expire_at` bigint(20) DEFAULT '0' COMMENT '验证码过期时间',
  `login_time` bigint(20) NOT NULL DEFAULT '0' COMMENT '最后登录时间',
  `ip` bigint(20) NOT NULL DEFAULT '0' COMMENT '登录IP',
  `share_time` bigint(20) NOT NULL DEFAULT '0' COMMENT '分享时间 -1 则可以分享 0 则不能分享',
  `get_diamonds` int(11) NOT NULL DEFAULT '0' COMMENT '-1 已领取 0 不能领取',
  `base_refer_uid` int(11) NOT NULL DEFAULT '-1' COMMENT '顶级关联上级 UID',
  `refer_uid` int(11) NOT NULL DEFAULT '-1' COMMENT '关联上级 UID',
  `refer_time` int(11) DEFAULT NULL COMMENT '建立关联时间',
  `withdraw_time` int(11) DEFAULT '-1' COMMENT '提现时间 默认 -1',
  `withdraw_nickname` varchar(128) DEFAULT NULL COMMENT '提现昵称',
  `bind_after_login_time` int(11) DEFAULT '-1' COMMENT '建立关联后首次打开游戏时间 默认 -1',
  `level` int(11) DEFAULT '1' COMMENT '用户等级',
  `wechat_openid` varchar(100) DEFAULT NULL COMMENT '微信公众平台 OPENID',
  `invite_uid_1` int(11) NOT NULL DEFAULT '0' COMMENT '最上级代理 UID',
  `invite_uid_2` int(11) NOT NULL DEFAULT '0' COMMENT '上级代理 UID',
  `bind_time` int(11) NOT NULL DEFAULT '0',
  `pdk_index` int(11) NOT NULL DEFAULT '0',
  `zzmj_index` int(11) NOT NULL DEFAULT '0',
  `custom_type` int(11) NOT NULL DEFAULT '0' COMMENT '0用户 1 代理 3运营',
  `agent_id` int(11) DEFAULT '0' COMMENT '代理商 ID',
  `channel_uid` int(11) DEFAULT '0' COMMENT '渠道商 ID',
  `father_id` int(11) NOT NULL DEFAULT '0',
  `hierarchical` varchar(2000) DEFAULT NULL COMMENT '层级串',
  `la_jiao_dou` int(11) NOT NULL DEFAULT '0',
  `allow_match` int(11) NOT NULL DEFAULT '0' COMMENT '是否允许开启比赛房',
  `score` int(11) NOT NULL DEFAULT '0' COMMENT '积分',
  `sign_time` int(11) NOT NULL DEFAULT '0' COMMENT '最后一次签到时间',
  `sign_count` int(11) NOT NULL DEFAULT '0' COMMENT '签到天数',
  `is_lucker` tinyint(4) NOT NULL DEFAULT '0' COMMENT '是否是幸运玩家',
  `round_count` int(11) NOT NULL DEFAULT '0' COMMENT '游戏局数',
  `rate_score` int(11) NOT NULL DEFAULT '5' COMMENT '评分',
  `channel_lvid` int(11) DEFAULT '0' COMMENT '运营账号等级',
  `gold` int(11) NOT NULL DEFAULT '0' COMMENT '金币',
  `lock_gold` int(11) NOT NULL DEFAULT '0' COMMENT '锁定金币',
  `lock_table` int(11) NOT NULL DEFAULT '0' COMMENT '锁定桌子',
  `lock_time` int(11) NOT NULL DEFAULT '0' COMMENT '锁定时间',
  `allow_niu_niu` int(11) NOT NULL DEFAULT '0' COMMENT '允许开牛牛',
  `yuan_bao` int(11) NOT NULL DEFAULT '0' COMMENT '元宝',
  `manage_yuan_bao` int(11) NOT NULL DEFAULT '0' COMMENT '返还的元宝',
  `Tmanage_yuan_bao` int(11) DEFAULT '0' COMMENT '提现消耗元宝数',
  `IsDelete` int(11) DEFAULT '0' COMMENT '设置标志',
  PRIMARY KEY (`uid`),
  UNIQUE KEY `auto_token` (`auto_token`) USING BTREE,
  UNIQUE KEY `openid` (`openid`) USING BTREE,
  UNIQUE KEY `unionid` (`unionid`) USING BTREE,
  KEY `mac` (`mac`,`imei`) USING BTREE,
  KEY `token` (`token`) USING BTREE,
  KEY `login_time` (`login_time`) USING BTREE,
  KEY `reg_time` (`reg_time`) USING BTREE,
  KEY `uid` (`uid`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=999842 DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- Table structure for player_address
-- ----------------------------
DROP TABLE IF EXISTS `player_address`;
CREATE TABLE `player_address` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `address` varchar(500) DEFAULT NULL,
  `real_name` varchar(12) DEFAULT NULL,
  `uid` int(11) DEFAULT NULL,
  `phone` varchar(24) NOT NULL DEFAULT '',
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`) USING BTREE,
  UNIQUE KEY `uid` (`uid`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for present
-- ----------------------------
DROP TABLE IF EXISTS `present`;
CREATE TABLE `present` (
  `Id` bigint(20) NOT NULL AUTO_INCREMENT,
  `Userid` bigint(20) DEFAULT NULL,
  `price` decimal(10,0) DEFAULT NULL,
  `Uid` bigint(20) DEFAULT NULL,
  `Creatime` datetime DEFAULT NULL,
  `Staues` int(11) DEFAULT NULL,
  `transNo` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- ----------------------------
-- Table structure for presentrecord
-- ----------------------------
DROP TABLE IF EXISTS `presentrecord`;
CREATE TABLE `presentrecord` (
  `Id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `Userid` bigint(20) DEFAULT NULL,
  `Moneys` decimal(18,2) DEFAULT NULL,
  `States` int(11) DEFAULT NULL,
  `Creationtime` datetime DEFAULT NULL,
  PRIMARY KEY (`Id`),
  UNIQUE KEY `Id` (`Id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for price_config
-- ----------------------------
DROP TABLE IF EXISTS `price_config`;
CREATE TABLE `price_config` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `count` int(11) DEFAULT NULL,
  `price` float DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- Table structure for proportions
-- ----------------------------
DROP TABLE IF EXISTS `proportions`;
CREATE TABLE `proportions` (
  `Id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `Regionid` bigint(20) DEFAULT NULL,
  `General` decimal(18,2) DEFAULT NULL,
  `Projects` decimal(18,2) DEFAULT NULL,
  `Operates` decimal(18,2) DEFAULT NULL,
  `Agents` decimal(18,2) DEFAULT NULL,
  `Oneagents` decimal(18,2) DEFAULT NULL,
  `Twoagents` decimal(18,2) DEFAULT NULL,
  `Threeagents` decimal(18,2) DEFAULT NULL,
  `Creationtime` datetime DEFAULT NULL,
  `Utime` datetime DEFAULT NULL,
  PRIMARY KEY (`Id`),
  UNIQUE KEY `Id` (`Id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for recharge
-- ----------------------------
DROP TABLE IF EXISTS `recharge`;
CREATE TABLE `recharge` (
  `Id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `Type` int(11) DEFAULT NULL COMMENT '1比赛卡 2钻石',
  `Creauserid` bigint(20) DEFAULT NULL COMMENT '代充Id',
  `Userid` bigint(20) DEFAULT NULL COMMENT '用户id',
  `Numbers` bigint(20) DEFAULT NULL COMMENT '数量',
  `Creationtime` datetime DEFAULT NULL COMMENT '创建时间',
  `CZtype` int(11) DEFAULT NULL COMMENT '1直冲',
  `UserType` int(11) DEFAULT NULL COMMENT '1后台账户 2 游戏账户',
  PRIMARY KEY (`Id`),
  UNIQUE KEY `Id` (`Id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for recommend
-- ----------------------------
DROP TABLE IF EXISTS `recommend`;
CREATE TABLE `recommend` (
  `uid` bigint(20) NOT NULL,
  `invitee` bigint(20) NOT NULL COMMENT '被邀请人',
  `bind_time` bigint(20) NOT NULL COMMENT '绑定时间',
  `count` int(11) NOT NULL DEFAULT '0' COMMENT '再邀请数',
  UNIQUE KEY `invitee` (`invitee`) USING BTREE,
  KEY `uid` (`uid`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- Table structure for recommend_ip
-- ----------------------------
DROP TABLE IF EXISTS `recommend_ip`;
CREATE TABLE `recommend_ip` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `uid` bigint(20) DEFAULT NULL COMMENT '推荐者的用户 ID',
  `ip` bigint(20) unsigned NOT NULL COMMENT '被推荐者的 IP 地址',
  `time` bigint(20) unsigned NOT NULL COMMENT '创建时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for rewards
-- ----------------------------
DROP TABLE IF EXISTS `rewards`;
CREATE TABLE `rewards` (
  `Id` bigint(11) unsigned NOT NULL AUTO_INCREMENT,
  `RoomId` bigint(11) DEFAULT NULL,
  `reward_count` bigint(11) DEFAULT NULL COMMENT '打赏金额',
  `Staues` int(11) DEFAULT NULL COMMENT '状态:0 未到账 1到账',
  `UserId` bigint(11) DEFAULT NULL COMMENT '代理Id',
  `Uid` bigint(11) DEFAULT NULL COMMENT 'Uid',
  `CreationTime` int(11) DEFAULT NULL COMMENT '时间',
  `record_id` varchar(128) DEFAULT NULL COMMENT '牌桌ID',
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- ----------------------------
-- Table structure for robot
-- ----------------------------
DROP TABLE IF EXISTS `robot`;
CREATE TABLE `robot` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `wx_id` varchar(128) NOT NULL DEFAULT '' COMMENT '微信用户 ID',
  `status` int(11) NOT NULL DEFAULT '0' COMMENT '状态 0 下线 1 上线',
  `remark` varchar(128) DEFAULT NULL COMMENT '备注名称',
  `time` int(11) DEFAULT NULL COMMENT '最后变更时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `wx_id` (`wx_id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for robot_group
-- ----------------------------
DROP TABLE IF EXISTS `robot_group`;
CREATE TABLE `robot_group` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `group_id` varchar(128) DEFAULT '' COMMENT '群组 ID',
  `remark` varchar(128) DEFAULT '' COMMENT '备注',
  `wx_id` varchar(128) DEFAULT NULL COMMENT '首次发消息的人 ID',
  `diamond_uid` int(11) DEFAULT NULL COMMENT '扣钻用户 ID',
  `rule` varchar(256) DEFAULT NULL COMMENT '开房规则',
  `robot_id` varchar(128) DEFAULT NULL COMMENT '机器人 ID',
  `time` int(11) DEFAULT NULL COMMENT '时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `group_id` (`group_id`,`robot_id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for room_config
-- ----------------------------
DROP TABLE IF EXISTS `room_config`;
CREATE TABLE `room_config` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `data` varchar(512) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=67 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for room_user
-- ----------------------------
DROP TABLE IF EXISTS `room_user`;
CREATE TABLE `room_user` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `record_id` varchar(32) DEFAULT NULL,
  `uid` int(11) NOT NULL COMMENT '玩家ID',
  `score` int(11) NOT NULL COMMENT '分数',
  `game_type` int(11) NOT NULL COMMENT '游戏编号',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- Table structure for servers
-- ----------------------------
DROP TABLE IF EXISTS `servers`;
CREATE TABLE `servers` (
  `sid` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `IP` varchar(50) NOT NULL DEFAULT '',
  `port` int(11) NOT NULL,
  `status` int(11) NOT NULL COMMENT '0未启动1运行中2已停服',
  `key` varchar(40) NOT NULL DEFAULT '' COMMENT '服务器的KEY',
  PRIMARY KEY (`sid`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for server_rooms
-- ----------------------------
DROP TABLE IF EXISTS `server_rooms`;
CREATE TABLE `server_rooms` (
  `sid` int(11) unsigned NOT NULL,
  `game_type` tinyint(4) NOT NULL DEFAULT '0' COMMENT '游戏类型',
  `status` int(11) NOT NULL COMMENT '0未启动1运行中2已停服',
  `key` varchar(40) NOT NULL DEFAULT '' COMMENT '服务器的KEY',
  `weight` tinyint(4) NOT NULL COMMENT '权重',
  `count` int(11) NOT NULL DEFAULT '0' COMMENT '当前桌数',
  `pid` int(11) NOT NULL DEFAULT '0' COMMENT '进程ID',
  `ack_time` int(11) NOT NULL DEFAULT '0' COMMENT 'ACK_TIME',
  `file_path` varchar(256) NOT NULL COMMENT '文件绝对路径',
  `version` varchar(64) NOT NULL,
  UNIQUE KEY `sid` (`sid`,`game_type`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for services
-- ----------------------------
DROP TABLE IF EXISTS `services`;
CREATE TABLE `services` (
  `stype` int(11) unsigned NOT NULL AUTO_INCREMENT COMMENT '服务类型',
  `sname` varchar(40) NOT NULL DEFAULT '' COMMENT '服务名称',
  PRIMARY KEY (`stype`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for share_activity_config
-- ----------------------------
DROP TABLE IF EXISTS `share_activity_config`;
CREATE TABLE `share_activity_config` (
  `var` varchar(64) NOT NULL,
  `value` varchar(64) DEFAULT NULL,
  `desc` varchar(64) DEFAULT NULL,
  PRIMARY KEY (`var`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for sign_activity_item
-- ----------------------------
DROP TABLE IF EXISTS `sign_activity_item`;
CREATE TABLE `sign_activity_item` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `item_type` int(3) DEFAULT NULL COMMENT '1、钻石 2、金币 3、辣椒豆',
  `item_count` int(11) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=latin1;

-- ----------------------------
-- Table structure for spring_activity
-- ----------------------------
DROP TABLE IF EXISTS `spring_activity`;
CREATE TABLE `spring_activity` (
  `uid` int(11) NOT NULL DEFAULT '0',
  `last_game_time` int(11) NOT NULL DEFAULT '0',
  `login_bonus_time` int(11) NOT NULL DEFAULT '0',
  `game_bonus_time` int(11) NOT NULL DEFAULT '0',
  `curr_score` int(11) NOT NULL DEFAULT '0',
  `use_score` int(11) NOT NULL DEFAULT '0',
  `item_1_status` int(11) NOT NULL DEFAULT '0',
  `item_2_status` int(11) NOT NULL DEFAULT '0',
  `item_3_status` int(11) NOT NULL DEFAULT '0',
  `item_4_status` int(11) NOT NULL DEFAULT '0',
  `item_5_status` int(11) NOT NULL DEFAULT '0',
  PRIMARY KEY (`uid`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- ----------------------------
-- Table structure for tables
-- ----------------------------
DROP TABLE IF EXISTS `tables`;
CREATE TABLE `tables` (
  `tid` int(10) unsigned NOT NULL COMMENT '桌子id',
  `owner` bigint(20) NOT NULL DEFAULT '0' COMMENT '创建者',
  `is_agent` tinyint(4) NOT NULL DEFAULT '0' COMMENT '0非代开1代开',
  `state` varchar(32) NOT NULL DEFAULT '0' COMMENT '桌子状态',
  `time` bigint(20) NOT NULL DEFAULT '0' COMMENT '创建时间',
  `round_count` int(11) DEFAULT '0' COMMENT '总局数',
  `diamonds` int(11) NOT NULL COMMENT '消耗钻石',
  `sid` int(11) NOT NULL COMMENT '服务器ID',
  `game_type` tinyint(4) NOT NULL COMMENT '游戏类型',
  `rule_type` tinyint(4) NOT NULL DEFAULT '1' COMMENT '规则类型',
  `rules` varchar(1000) NOT NULL DEFAULT '{}' COMMENT '游戏规则[json]',
  `group_id` varchar(128) NOT NULL DEFAULT '-1' COMMENT '群Id',
  `robot_id` varchar(128) NOT NULL DEFAULT '-1' COMMENT '机器人Id',
  `club_id` int(11) NOT NULL DEFAULT '-1' COMMENT '俱乐部Id',
  `floor` int(11) DEFAULT '-1',
  `consume_type` int(11) NOT NULL DEFAULT '0' COMMENT '0 房主扣钻 1 AA 扣钻 2 大赢家',
  `match_type` int(11) NOT NULL DEFAULT '0' COMMENT '0 亲友圈 1 比赛房',
  `sub_floor` int(11) DEFAULT '-1',
  `match_config` varchar(256) NOT NULL DEFAULT '{}' COMMENT '比赛房规则',
  `private` int(11) NOT NULL DEFAULT '0' COMMENT '私密',
  `password` varchar(12) DEFAULT NULL COMMENT '私密房密码',
  `union_id` int(11) DEFAULT '-1' COMMENT '联盟ID',
  PRIMARY KEY (`tid`),
  KEY `club_id,floor` (`club_id`,`floor`) USING BTREE,
  KEY `sub_floor,state` (`sub_floor`,`state`) USING BTREE,
  KEY `floor,state` (`floor`,`state`) USING BTREE,
  KEY `club_id,match_type` (`club_id`,`match_type`) USING BTREE,
  KEY `union_id` (`union_id`) USING BTREE,
  KEY `union_id,floor` (`union_id`,`floor`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='桌子表';

-- ----------------------------
-- Table structure for tranorder
-- ----------------------------
DROP TABLE IF EXISTS `tranorder`;
CREATE TABLE `tranorder` (
  `Id` bigint(11) NOT NULL COMMENT '迁移订单记录表',
  `orderid` bigint(11) DEFAULT NULL COMMENT '订单ID',
  `agent_id` bigint(20) DEFAULT NULL COMMENT '区域ID',
  `hierarchical` varchar(2000) DEFAULT NULL COMMENT '原关系链',
  `uid` bigint(11) DEFAULT NULL COMMENT '用户Uid',
  `OrderPrice` decimal(18,2) DEFAULT NULL COMMENT '订单金额',
  `CreaTime` datetime DEFAULT NULL COMMENT '创建时间',
  `OrderTime` datetime DEFAULT NULL COMMENT '订单创时间',
  `Isagent_id` int(11) DEFAULT NULL COMMENT '是否同区域：1不同区域 0：同区域',
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- ----------------------------
-- Table structure for union
-- ----------------------------
DROP TABLE IF EXISTS `union`;
CREATE TABLE `union` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `uid` int(11) NOT NULL COMMENT '创建者ID',
  `name` varchar(32) DEFAULT '' COMMENT '联盟名称',
  `notice` varchar(255) DEFAULT NULL COMMENT '公告',
  `union_type` tinyint(2) DEFAULT '0' COMMENT '联盟类型 0=小联盟 1=大联盟',
  `count` int(11) NOT NULL DEFAULT '1' COMMENT '玩家数量',
  `status` tinyint(2) NOT NULL DEFAULT '0' COMMENT '0 正常 -1 已解散',
  `create_time` int(11) DEFAULT NULL COMMENT '创建时间',
  `dismiss_time` int(11) DEFAULT '0' COMMENT '解散时间',
  `lock_status` tinyint(2) NOT NULL DEFAULT '0',
  `wechat` varchar(32) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=100003 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for unionandroid
-- ----------------------------
DROP TABLE IF EXISTS `unionandroid`;
CREATE TABLE `unionandroid` (
  `aid` int(11) NOT NULL AUTO_INCREMENT,
  `union_id` int(11) NOT NULL,
  `minnum` int(11) NOT NULL COMMENT '最少机器人数',
  `maxnum` int(11) NOT NULL COMMENT '最大机器人数量',
  `start` time NOT NULL COMMENT '开始时间',
  `end` time NOT NULL COMMENT '机器人关闭时间',
  `state` int(11) DEFAULT NULL COMMENT '状态 0 开启 1 关闭',
  PRIMARY KEY (`aid`,`union_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=latin1;

-- ----------------------------
-- Table structure for union_banpalyer
-- ----------------------------
DROP TABLE IF EXISTS `union_banpalyer`;
CREATE TABLE `union_banpalyer` (
  `union_banpalyerid` int(11) NOT NULL AUTO_INCREMENT,
  `unionid` int(11) DEFAULT NULL,
  `union_banpalyer_userid` int(11) DEFAULT NULL,
  `union_banpalyer_state` int(11) DEFAULT NULL,
  `union_banpalyer_optionid` int(11) DEFAULT NULL,
  `union_banpalyer_optiontime` int(11) DEFAULT NULL,
  PRIMARY KEY (`union_banpalyerid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for union_block
-- ----------------------------
DROP TABLE IF EXISTS `union_block`;
CREATE TABLE `union_block` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `union_id` int(11) DEFAULT NULL,
  `uid` int(11) DEFAULT NULL,
  `ref_uid` int(11) DEFAULT NULL,
  `time` int(11) DEFAULT NULL,
  `status` int(11) NOT NULL DEFAULT '0',
  `block_status` int(11) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `union_id,uid,ref_uid` (`union_id`,`uid`,`ref_uid`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for union_cs
-- ----------------------------
DROP TABLE IF EXISTS `union_cs`;
CREATE TABLE `union_cs` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `uid` int(11) NOT NULL COMMENT '抽给了谁',
  `cs_score` int(11) NOT NULL COMMENT '抽了多少水',
  `cs_rate` int(11) NOT NULL COMMENT '抽水比例',
  `cs_date` datetime NOT NULL COMMENT '抽水时间',
  `union_id` int(11) NOT NULL,
  `tid` int(11) NOT NULL COMMENT '桌子编号',
  `score` decimal(17,2) NOT NULL COMMENT '返给抽水分水',
  `pid` varchar(55) NOT NULL COMMENT '批次号码',
  `state` int(11) NOT NULL DEFAULT '0' COMMENT '状态 1 已经返给抽水 0 未抽水',
  `queryid` varchar(55) DEFAULT NULL COMMENT '查询批次号，每次查询更新一次批次号，每次修改根据批次号码修改',
  `subfloorid` int(11) DEFAULT '0' COMMENT '玩法编号',
  `from_userid` int(11) DEFAULT '0',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=184209 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for union_cs_log
-- ----------------------------
DROP TABLE IF EXISTS `union_cs_log`;
CREATE TABLE `union_cs_log` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `union_id` int(11) NOT NULL,
  `uid` int(11) NOT NULL,
  `score` decimal(17,2) DEFAULT NULL COMMENT '税钱',
  `addtime` datetime DEFAULT NULL,
  `queryid` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2279 DEFAULT CHARSET=latin1;

-- ----------------------------
-- Table structure for union_divide
-- ----------------------------
DROP TABLE IF EXISTS `union_divide`;
CREATE TABLE `union_divide` (
  `union_divide_id` int(11) NOT NULL AUTO_INCREMENT,
  `unionid` int(11) DEFAULT NULL,
  `union_small_divide` int(11) DEFAULT NULL,
  `union_partnerdivide` int(11) DEFAULT NULL,
  PRIMARY KEY (`union_divide_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for union_energy_config
-- ----------------------------
DROP TABLE IF EXISTS `union_energy_config`;
CREATE TABLE `union_energy_config` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `union_id` int(11) NOT NULL COMMENT '联盟 ID',
  `game_type` int(11) NOT NULL DEFAULT '0' COMMENT '游戏类别',
  `uid` int(11) NOT NULL COMMENT '对应人UID',
  `energy_percent` int(11) NOT NULL COMMENT '下级能量百分比',
  `time` int(11) NOT NULL DEFAULT '0' COMMENT '设置时间',
  `operator_user` int(11) NOT NULL DEFAULT '0' COMMENT '设置人ID',
  `sub_floor` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `union_id,uid,sub_floor` (`union_id`,`uid`,`sub_floor`) USING BTREE,
  KEY `union_id` (`union_id`) USING BTREE,
  KEY `union_id,uid` (`union_id`,`uid`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for union_floor
-- ----------------------------
DROP TABLE IF EXISTS `union_floor`;
CREATE TABLE `union_floor` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `union_id` int(11) DEFAULT NULL,
  `game_type` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `union_id` (`union_id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for union_partner
-- ----------------------------
DROP TABLE IF EXISTS `union_partner`;
CREATE TABLE `union_partner` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '合伙人ID',
  `name` varchar(200) DEFAULT NULL COMMENT '名称',
  `uid` int(11) DEFAULT NULL COMMENT '用户ID',
  `union_id` int(11) DEFAULT NULL COMMENT '大联盟ID',
  `union_small_id` int(11) DEFAULT NULL COMMENT '小联盟ID',
  `parent_id` int(11) DEFAULT NULL COMMENT '上级合伙人ID',
  `promo` int(11) DEFAULT NULL COMMENT '推广码',
  `divide` int(11) DEFAULT NULL COMMENT '分成比例',
  `remark` varchar(200) DEFAULT NULL COMMENT '备注',
  `create_time` int(11) DEFAULT NULL COMMENT '创建时间',
  `notice` varchar(255) DEFAULT NULL COMMENT '公告',
  `status` int(11) DEFAULT NULL COMMENT '状态',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for union_playerconfirm
-- ----------------------------
DROP TABLE IF EXISTS `union_playerconfirm`;
CREATE TABLE `union_playerconfirm` (
  `union_playerconfirm` int(11) NOT NULL AUTO_INCREMENT,
  `union_playerid` int(11) DEFAULT NULL,
  `union_id` int(11) DEFAULT NULL,
  `union_Invitationtype` int(11) DEFAULT NULL,
  `union_Invitationuserid` int(11) DEFAULT NULL,
  `union_Invitationrmtime` int(11) DEFAULT NULL,
  `union_playerconfirmstate` int(11) DEFAULT NULL,
  `union_playerconfirmtime` int(11) DEFAULT NULL,
  PRIMARY KEY (`union_playerconfirm`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for union_profit_record
-- ----------------------------
DROP TABLE IF EXISTS `union_profit_record`;
CREATE TABLE `union_profit_record` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `union_id` int(11) DEFAULT NULL COMMENT '大联盟id',
  `uid` int(11) DEFAULT NULL COMMENT '用户id',
  `source_uid` int(11) DEFAULT NULL COMMENT '源用户id',
  `game_kind` int(11) DEFAULT NULL COMMENT '游戏类型',
  `timestamp` int(11) DEFAULT NULL COMMENT '时间',
  `tid` int(11) DEFAULT NULL COMMENT '桌子号',
  `settlementtime` int(11) DEFAULT NULL COMMENT '结算时间',
  `amount` int(11) DEFAULT NULL COMMENT '福利数量',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for union_small
-- ----------------------------
DROP TABLE IF EXISTS `union_small`;
CREATE TABLE `union_small` (
  `id` int(11) NOT NULL COMMENT '小联盟ID',
  `name` varchar(200) DEFAULT NULL COMMENT '小联盟名称',
  `union_id` int(11) DEFAULT NULL COMMENT '所属大联盟ID',
  `promo` int(11) DEFAULT NULL COMMENT '推广码',
  `uid` int(11) DEFAULT NULL COMMENT '小盟主ID',
  `divide` decimal(17,2) DEFAULT NULL COMMENT '分成比例',
  `remark` varchar(200) DEFAULT NULL COMMENT '备注',
  `notice` varchar(100) DEFAULT NULL COMMENT '公告',
  `create_time` int(11) DEFAULT NULL COMMENT '创建时间',
  `count` int(11) DEFAULT NULL COMMENT '玩家数量',
  `status` int(2) DEFAULT NULL COMMENT '联盟状态',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for union_small_wf
-- ----------------------------
DROP TABLE IF EXISTS `union_small_wf`;
CREATE TABLE `union_small_wf` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `subfloorid` int(255) NOT NULL COMMENT '玩法对应的编号',
  `limitscore` decimal(17,2) NOT NULL COMMENT '可操作分成',
  `union_id` int(11) NOT NULL COMMENT '联盟编号',
  `uid` int(11) NOT NULL COMMENT '用户编号',
  `score` decimal(17,2) NOT NULL COMMENT '分成比例',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5165 DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- Table structure for union_sub_floor
-- ----------------------------
DROP TABLE IF EXISTS `union_sub_floor`;
CREATE TABLE `union_sub_floor` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `union_id` int(11) NOT NULL,
  `floor_id` int(11) DEFAULT NULL,
  `play_config` varchar(1024) DEFAULT NULL,
  `auto_room` int(11) DEFAULT NULL,
  `game_type` int(11) NOT NULL,
  `match_type` int(11) NOT NULL DEFAULT '0' COMMENT '0 普通子楼层 1 比赛子楼层',
  `match_config` varchar(512) DEFAULT NULL,
  `tip` int(11) NOT NULL DEFAULT '0' COMMENT '抽水',
  `tip_limit` int(11) NOT NULL DEFAULT '0' COMMENT '抽水分数过滤',
  `tip_payment_method` int(11) NOT NULL DEFAULT '0' COMMENT '抽水结算方式',
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`) USING BTREE,
  KEY `union_id,floor` (`union_id`,`floor_id`) USING BTREE,
  KEY `floor` (`floor_id`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=811 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for union_user
-- ----------------------------
DROP TABLE IF EXISTS `union_user`;
CREATE TABLE `union_user` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `union_id` int(11) DEFAULT NULL COMMENT '联盟 ID',
  `uid` int(11) NOT NULL DEFAULT '-1' COMMENT '用户 ID',
  `remark` varchar(36) DEFAULT NULL COMMENT '用户名备注',
  `permission` int(11) DEFAULT NULL COMMENT '权限',
  `join_time` int(11) DEFAULT NULL COMMENT '加入时间',
  `limit_energy` int(11) NOT NULL DEFAULT '0' COMMENT '总能量限制',
  `energy` int(11) NOT NULL DEFAULT '0' COMMENT '当前能量',
  `lock_energy` int(11) NOT NULL DEFAULT '0' COMMENT '锁定能量',
  `lock_table` int(11) NOT NULL DEFAULT '0',
  `lock_time` int(11) NOT NULL DEFAULT '0',
  `tag_uid` int(11) NOT NULL DEFAULT '0' COMMENT '关联UID',
  `tag_name` varchar(32) DEFAULT NULL COMMENT '关联昵称',
  `union_user_id` int(11) DEFAULT '-1' COMMENT '小盟主UID',
  `game_round` int(11) NOT NULL DEFAULT '0' COMMENT '游戏局数',
  `union_small_id` int(11) DEFAULT NULL COMMENT '小联盟ID',
  `partner_id` int(11) DEFAULT NULL COMMENT '合伙人ID 非合伙人的用户ID',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uid` (`uid`) USING BTREE,
  KEY `union_id` (`union_id`) USING BTREE,
  KEY `union_id,tag_uid` (`union_id`,`tag_uid`) USING BTREE,
  KEY `union_user_id` (`union_user_id`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=11011 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for union_verify
-- ----------------------------
DROP TABLE IF EXISTS `union_verify`;
CREATE TABLE `union_verify` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `union_id` int(11) NOT NULL COMMENT '联盟 ID',
  `uid` int(11) NOT NULL COMMENT '用户 ID',
  `ref_union_id` int(11) DEFAULT '-1' COMMENT '关联联盟 ID',
  `time` int(11) NOT NULL DEFAULT '0' COMMENT '申请时间',
  `status` int(11) NOT NULL DEFAULT '0' COMMENT '0 待验证 -1 已拒绝 -2 已屏蔽 1 通过',
  `type` tinyint(2) NOT NULL DEFAULT '0' COMMENT '0 玩家申请加入 1 小联盟申请加入 2 主动添加小联盟',
  `update_time` int(11) NOT NULL DEFAULT '0' COMMENT '操作时间',
  `operator_user` varchar(32) DEFAULT '',
  `operator_uid` int(11) DEFAULT NULL,
  `promo` int(11) DEFAULT NULL COMMENT '玩家进入邀请码',
  PRIMARY KEY (`id`),
  UNIQUE KEY `union_id,uid` (`union_id`,`uid`) USING BTREE,
  KEY `union_id` (`union_id`) USING BTREE,
  KEY `ref_union_id` (`ref_union_id`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=26 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for usercashaccount
-- ----------------------------
DROP TABLE IF EXISTS `usercashaccount`;
CREATE TABLE `usercashaccount` (
  `Id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `Userid` bigint(20) DEFAULT NULL,
  `Totalamount` decimal(18,4) DEFAULT NULL,
  `Payamount` decimal(18,4) DEFAULT NULL,
  `Lockingamount` decimal(18,4) DEFAULT NULL,
  `Islocked` int(11) DEFAULT NULL,
  `Modifytime` datetime DEFAULT NULL,
  PRIMARY KEY (`Id`),
  UNIQUE KEY `Id` (`Id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for usercashaccountdetail
-- ----------------------------
DROP TABLE IF EXISTS `usercashaccountdetail`;
CREATE TABLE `usercashaccountdetail` (
  `Id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `Userid` bigint(20) DEFAULT NULL,
  `Cashamount` decimal(18,4) DEFAULT NULL,
  `type` int(11) DEFAULT NULL,
  `Createtime` datetime DEFAULT NULL,
  `Reason` varchar(50) DEFAULT NULL,
  `Remark` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`Id`),
  UNIQUE KEY `id` (`Id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for userinfo
-- ----------------------------
DROP TABLE IF EXISTS `userinfo`;
CREATE TABLE `userinfo` (
  `Id` bigint(20) NOT NULL AUTO_INCREMENT,
  `UseNumber` bigint(50) DEFAULT NULL,
  `UserName` varchar(50) DEFAULT NULL,
  `Password` varchar(50) DEFAULT NULL,
  `Nickname` varchar(500) DEFAULT NULL,
  `CustomerType` int(11) DEFAULT NULL,
  `FatherId` bigint(20) DEFAULT NULL,
  `RegionId` bigint(20) DEFAULT NULL COMMENT '代理ID',
  `OperateId` bigint(20) DEFAULT NULL COMMENT '运营商 ID',
  `States` int(11) DEFAULT NULL,
  `Phone` varchar(50) DEFAULT NULL,
  `WechatNum` varchar(50) DEFAULT NULL,
  `SplitColumn` decimal(18,2) DEFAULT NULL COMMENT '区域返佣比列',
  `Autograph` varchar(200) DEFAULT NULL,
  `HeadImg` varchar(1000) DEFAULT NULL,
  `WeixinOpenId` varchar(200) DEFAULT NULL,
  `CreationTime` datetime DEFAULT NULL,
  `unionid` varchar(200) DEFAULT NULL,
  `qcodes` varchar(1000) DEFAULT NULL,
  `ATotalColumn` decimal(18,2) DEFAULT NULL COMMENT '总后台返佣数据',
  `BTotalColumn` decimal(18,2) DEFAULT NULL COMMENT '下月生效总后台返佣',
  `BSplitColumn` decimal(18,2) DEFAULT NULL COMMENT '区域下月生效返佣比列',
  `AoneColumn` decimal(18,2) DEFAULT NULL COMMENT '一级返佣比列',
  `BoneColumn` decimal(18,2) DEFAULT NULL COMMENT '下月1号生效返佣比列',
  `ATwoColumn` decimal(18,2) DEFAULT NULL COMMENT '二级返佣比列',
  `BTwoColumn` decimal(18,2) DEFAULT NULL COMMENT '下月1号生效返佣比列',
  `AThreeColumn` decimal(18,2) DEFAULT NULL COMMENT '三级返佣比列',
  `BThreeColumn` decimal(18,2) DEFAULT NULL COMMENT '下月1号生效返佣比列',
  `MdifTime` datetime DEFAULT NULL COMMENT '修改时间',
  `channel_lvid` int(11) DEFAULT '0' COMMENT '运营等级',
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for user_feedback
-- ----------------------------
DROP TABLE IF EXISTS `user_feedback`;
CREATE TABLE `user_feedback` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `uid` int(11) DEFAULT NULL,
  `phone` varchar(20) CHARACTER SET utf8 DEFAULT NULL,
  `content` varchar(512) CHARACTER SET utf8 DEFAULT NULL,
  `time` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- ----------------------------
-- Table structure for verify_withdraw
-- ----------------------------
DROP TABLE IF EXISTS `verify_withdraw`;
CREATE TABLE `verify_withdraw` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `uid` bigint(20) NOT NULL,
  `nick_name` varchar(255) NOT NULL,
  `money` float NOT NULL,
  `time` int(11) NOT NULL,
  `status` int(11) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- Table structure for versions
-- ----------------------------
DROP TABLE IF EXISTS `versions`;
CREATE TABLE `versions` (
  `channel_id` int(11) NOT NULL COMMENT '渠道ID',
  `platform` int(11) NOT NULL COMMENT '平台ID',
  `version` varchar(20) NOT NULL DEFAULT '' COMMENT '版本号',
  `update_url` varchar(255) NOT NULL DEFAULT '' COMMENT '更新链接',
  `desc` varchar(255) NOT NULL DEFAULT '' COMMENT '更新说明',
  `is_force` tinyint(4) NOT NULL DEFAULT '0' COMMENT '强制更新',
  KEY `platform` (`platform`) USING BTREE,
  KEY `channel_id` (`channel_id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for virtualaccount
-- ----------------------------
DROP TABLE IF EXISTS `virtualaccount`;
CREATE TABLE `virtualaccount` (
  `Id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `UserInfoId` bigint(20) DEFAULT NULL,
  `TotalGold` decimal(18,2) DEFAULT NULL COMMENT '总金币',
  `ConsumerGoId` decimal(18,2) DEFAULT NULL COMMENT '总消耗金币',
  `TotalDiamonds` decimal(18,2) DEFAULT NULL COMMENT '总钻石',
  `ConsumerDiamonds` decimal(18,2) DEFAULT NULL COMMENT '总消耗钻石',
  `uid` bigint(20) DEFAULT NULL COMMENT 'uid',
  PRIMARY KEY (`Id`),
  UNIQUE KEY `Id` (`Id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for withdraw
-- ----------------------------
DROP TABLE IF EXISTS `withdraw`;
CREATE TABLE `withdraw` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `uid` int(11) DEFAULT NULL COMMENT '发起提款用户 ID',
  `money` float DEFAULT NULL COMMENT '提款金额',
  `time` int(11) DEFAULT NULL COMMENT '提款时间',
  `status` int(11) NOT NULL DEFAULT '0' COMMENT '状态 0 待处理 1 已处理',
  `admin_id` int(11) DEFAULT NULL COMMENT '后台处理用户 ID',
  `refer_uid` int(11) NOT NULL COMMENT '提款关联用户 ID',
  `accept_time` int(11) DEFAULT NULL COMMENT '处理时间',
  PRIMARY KEY (`id`),
  KEY `status` (`status`) USING BTREE,
  KEY `uid` (`uid`) USING BTREE,
  KEY `refer_uid` (`refer_uid`) USING BTREE,
  KEY `uid_refer_uid` (`uid`,`refer_uid`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for withdraw_code
-- ----------------------------
DROP TABLE IF EXISTS `withdraw_code`;
CREATE TABLE `withdraw_code` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `uid` int(11) DEFAULT NULL COMMENT '用户 ID',
  `code` varchar(128) DEFAULT NULL COMMENT '提现 CODE',
  `money` float DEFAULT '0' COMMENT '提现金额',
  `refer_uids` varchar(512) DEFAULT NULL COMMENT '关联用户 ID',
  `time` int(11) DEFAULT '-1' COMMENT '兑换码生成时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for wx_payment
-- ----------------------------
DROP TABLE IF EXISTS `wx_payment`;
CREATE TABLE `wx_payment` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `uid` bigint(20) NOT NULL,
  `openid` varchar(100) NOT NULL,
  `trade_id` varchar(100) NOT NULL,
  `money` float NOT NULL,
  `diamond` int(11) NOT NULL,
  `detail` longtext NOT NULL,
  `status` int(11) NOT NULL,
  `time` int(11) NOT NULL,
  `is_agent` int(11) DEFAULT '0',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- Table structure for yao_qing
-- ----------------------------
DROP TABLE IF EXISTS `yao_qing`;
CREATE TABLE `yao_qing` (
  `uid` bigint(20) NOT NULL,
  `invitee` bigint(20) NOT NULL COMMENT '被邀请人',
  `first_round` tinyint(4) NOT NULL DEFAULT '0' COMMENT '完成首局',
  `first_round_bonus` tinyint(4) NOT NULL DEFAULT '0' COMMENT '首局奖励领取',
  `re_invite_count` tinyint(4) NOT NULL DEFAULT '0' COMMENT '再邀请次数',
  `bind_time` bigint(20) NOT NULL COMMENT '绑定时间',
  UNIQUE KEY `invitee` (`invitee`) USING BTREE,
  KEY `uid` (`uid`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- Procedure structure for p_safebox_fetch
-- ----------------------------
DROP PROCEDURE IF EXISTS `p_safebox_fetch`;
DELIMITER ;;
CREATE DEFINER=`root`@`%` PROCEDURE `p_safebox_fetch`(
	in unionid  int,	
	in uid int,	
	in queryid varchar(60) 
)
begin
declare energy int;
set energy = 0;
update union_cs set state = 1
where union_cs.union_id=union_id and union_cs.uid = uid and 
union_cs.queryid = queryid;
if row_count() > 0 
then 
	update union_user as a inner join (
	select a1.union_id,a1.uid,sum(if(a1.score is null,0,a1.score)) as score
	from union_cs  as a1 where a1.queryid=queryid and a1.union_id=unionid and 
	a1.uid = uid
	group by a1.union_id,a1.uid
	) as f
	on a.uid=f.uid and a.union_id = f.union_id 
	set a.energy = a.energy + if(f.score is null,0,f.score);
	select a.energy into energy from union_user as a 
	where a.union_id = unionid and a.uid = uid limit 1;
	select 1 as effects,energy as energy;
else 
	select 0 as effects;
end if;

end
;;
DELIMITER ;

-- ----------------------------
-- Procedure structure for p_safebox_query
-- ----------------------------
DROP PROCEDURE IF EXISTS `p_safebox_query`;
DELIMITER ;;
CREATE DEFINER=`root`@`%` PROCEDURE `p_safebox_query`(in unionid  int,	
	in uid int)
begin
declare queryid	varchar(55);
declare sumsf	decimal(17,2);
set queryid = uuid();
set sumsf = 0;
update union_cs set queryid=queryid where union_cs.uid=uid  and union_cs.union_id=union_id and state = 0; 
select nullif(sum(score),0) into sumsf  from `union_cs` as a where a.queryid=queryid limit 1; 
set sumsf = ifnull(sumsf,0);
select cast(sumsf as char(10)) as tj,queryid as queryid ;

end
;;
DELIMITER ;

-- ----------------------------
-- Procedure structure for p_tiqu_unionuid
-- ----------------------------
DROP PROCEDURE IF EXISTS `p_tiqu_unionuid`;
DELIMITER ;;
CREATE DEFINER=`root`@`%` PROCEDURE `p_tiqu_unionuid`( in areaId  int,
	in union_id int
)
begin
DECLARE sTemp VARCHAR(4000);
DECLARE sTempChd VARCHAR(4000);
DECLARE sTempChd1 VARCHAR(4000);
SET sTemp='$';
SET sTempChd = CAST(areaId AS CHAR);
SET sTempChd1 = CAST(areaId AS CHAR);
create temporary table if not exists tmpuid
(
			uid 	int(11) primary key
);
truncate table tmpuid;
WHILE sTempChd IS NOT NULL DO
SET sTemp= CONCAT(sTemp,',',sTempChd);
SELECT GROUP_CONCAT(uid) INTO sTempChd FROM union_user 
WHERE union_id=union_id and FIND_IN_SET(union_user_id,sTempChd)>0;
insert into tmpuid(uid)
SELECT uid FROM union_user 
WHERE union_id=union_id and FIND_IN_SET(union_user_id,sTempChd1)>0;
set sTempChd1 = sTempChd;
END WHILE;
insert into tmpuid(uid)
select areaId;
select cast(sum(energy) as char(10)) as energy
from union_user as g 
where exists(
select 1 from tmpuid as a where g.uid = a.uid
);
end
;;
DELIMITER ;

-- ----------------------------
-- Procedure structure for p_tiqu_unionuid1
-- ----------------------------
DROP PROCEDURE IF EXISTS `p_tiqu_unionuid1`;
DELIMITER ;;
CREATE DEFINER=`root`@`%` PROCEDURE `p_tiqu_unionuid1`( in areaId  int,
	in union_id int,
  in uid1 int
)
begin
DECLARE sTemp VARCHAR(4000);
DECLARE sTempChd VARCHAR(4000);
DECLARE sTempChd1 VARCHAR(4000);
SET sTemp='$';
SET sTempChd = CAST(areaId AS CHAR);
SET sTempChd1 = CAST(areaId AS CHAR);
create temporary table if not exists tmpuid
(
			uid 	int(11) primary key
);
truncate table tmpuid;
WHILE sTempChd IS NOT NULL DO
SET sTemp= CONCAT(sTemp,',',sTempChd);
SELECT GROUP_CONCAT(uid) INTO sTempChd FROM union_user 
WHERE union_id=union_id and FIND_IN_SET(union_user_id,sTempChd)>0;
insert into tmpuid(uid)
SELECT uid FROM union_user 
WHERE union_id=union_id and FIND_IN_SET(union_user_id,sTempChd1)>0;
set sTempChd1 = sTempChd;
END WHILE;
select a.energy,a.permission,d.nick_name,d.uid 
from union_user as a 
inner join
players as d
on a.uid=d.uid
where a.uid = uid1 and a.union_id=union_id and 
exists(
select * from tmpuid as f where f.uid=uid1
);
end
;;
DELIMITER ;

-- ----------------------------
-- Procedure structure for p_union
-- ----------------------------
DROP PROCEDURE IF EXISTS `p_union`;
DELIMITER ;;
CREATE DEFINER=`root`@`%` PROCEDURE `p_union`(in param  varchar(4000),	
	in param2 varchar(1000),	
	in tid 		int,
	in subfloorid int)
begin
declare uid int(11) default 0;
declare count int(11) default 0;
declare i	int(11) default 1;
declare cs_score decimal(17,2) default 0;
declare cs_rate  int(11) default 0;
declare cs_up_userid int(11) default 0; 
declare left_score int(11) default 0;
declare pid				varchar(55) default '';
declare puid			int(11) default 0;
declare permission int(11) default 0;
call tt(param,@a1,@a2,@a3);

select count(*) into count from tmpTable1 as a;
set pid = uuid();
while i<=count do
	select a.uid into uid from tmpTable1 as a where a.id=i;
	select a.score into cs_score from tmpTable1 as a where a.id=i;
	select a.union_user_id into puid  from union_user as a where a.uid = uid and a.union_id=param2;
	select a.permission into permission  from union_user as a where a.uid = uid and a.union_id=param2;

	if permission in (0,10,11)
	then
		if cs_score > 0
		then
		call p_union_p4 (uid,param2,0,tid,pid,1,subfloorid,cs_score,uid);
		end if;
	else
		if cs_score > 0
		then
		call p_union_p4 (puid,param2,0,tid,pid,1,subfloorid,cs_score,uid);
		end if;
	end if;
	set i = i + 1;
end while ;
end
;;
DELIMITER ;

-- ----------------------------
-- Procedure structure for p_union_p
-- ----------------------------
DROP PROCEDURE IF EXISTS `p_union_p`;
DELIMITER ;;
CREATE DEFINER=`root`@`%` PROCEDURE `p_union_p`(in uid  		int(11),	
	in union_id int(11),	
	in cs_score int(11),	
	in cs_tid 	int(11) , pid varchar(55))
begin
declare permission1 int(11) default 0;
declare union_user_id1 int(11) default 0;
declare cs_rate				 int(11) default 0;
SET @@SESSION.max_sp_recursion_depth=25;

select  a.permission into permission1  from union_user as a where a.uid = uid and a.union_id = union_id;
select  a.union_user_id into union_user_id1  from union_user as a where a.uid = uid and a.union_id = union_id;

if permission1 = 10
then
	select 'a';
	select a.divide into cs_rate from union_small as a 
	where a.union_id=union_id and a.uid=uid limit 1;
	insert into union_cs(union_id,uid,cs_score,cs_rate,cs_date,tid,score,pid)
	select union_id,uid,cs_score,cs_rate,now(),cs_tid,cs_score * cs_rate / 100.00,pid;
elseif permission1 = 0
then
	select '';
elseif permission1 = 11
then
	select 'a';
	select a.divide into cs_rate from union_small as a 
	where a.union_id=union_id and a.uid=uid limit 1;
	insert into union_cs(union_id,uid,cs_score,cs_rate,cs_date,tid,score,pid)
	select union_id,uid,cs_score,cs_rate,now(),cs_tid,cs_score * cs_rate / 100.00,pid;
else
	select 'contiune' , union_user_id1 , permission1 ;
	call p_union_p(union_user_id1,union_id,cs_score,cs_tid,pid);
end if;

end
;;
DELIMITER ;

-- ----------------------------
-- Procedure structure for p_union_p1
-- ----------------------------
DROP PROCEDURE IF EXISTS `p_union_p1`;
DELIMITER ;;
CREATE DEFINER=`root`@`%` PROCEDURE `p_union_p1`(in uid  		int(11),	
	in union_id int(11),	
	in cs_score int(11),	
	in cs_tid 	int(11) , pid varchar(55))
begin
declare permission1 int(11) default 0;
declare union_user_id1 int(11) default 0;
declare cs_rate				 int(11) default 0;
set @@SESSION.max_sp_recursion_depth=25;

select  a.permission into permission1  from union_user as a where a.uid = uid and a.union_id = union_id;
select  a.union_user_id into union_user_id1  from union_user as a where a.uid = uid and a.union_id = union_id;

if permission1 = 10 or permission1 = 11
then
	select a.divide into cs_rate from union_small as a 
	where a.union_id=union_id and a.uid=uid limit 1;
	insert into union_cs(union_id,uid,cs_score,cs_rate,cs_date,tid,score,pid)
	select union_id,uid,cs_score,cs_rate,now(),cs_tid,cs_score * cs_rate / 100.00,pid;
elseif permission1 = 0
then
	select '';
else
	select 'contiune' , union_user_id1 , permission1 ;
	#call p_union_p(union_user_id1,union_id,cs_score,cs_tid,pid);
end if;

end
;;
DELIMITER ;

-- ----------------------------
-- Procedure structure for p_union_p2
-- ----------------------------
DROP PROCEDURE IF EXISTS `p_union_p2`;
DELIMITER ;;
CREATE DEFINER=`root`@`%` PROCEDURE `p_union_p2`(in uid  		int(11),	
	in union_id int(11),	
	in cs_score decimal(17,2) ,	
	in cs_tid 	int(11) , 
 pid varchar(55),index_num int(11))
begin
declare permission1 int(11) default 0;
declare union_user_id1 int(11) default 0;
declare cs_rate				 decimal(17,2) default 0;
declare cs_score_one	 decimal(17,2) default 0.00;
set @@SESSION.max_sp_recursion_depth=25;

select  a.permission into permission1  from union_user as a 
where a.uid = uid and a.union_id = union_id;
select  a.union_user_id into union_user_id1  from union_user as a 
where a.uid = uid and a.union_id = union_id;
if permission1 = 10 or permission1 = 11 
then
	select a.divide into cs_rate from union_small as a 
	where a.union_id=union_id and a.uid=uid limit 1;
	if index_num = 1
	then
		set cs_score_one = cs_score / 2.00;
		insert into union_cs(union_id,uid,cs_score,cs_rate,cs_date,tid,score,pid)
		select union_id,uid,cs_score,cs_rate,now(),cs_tid,cs_score_one - cs_rate ,pid;
		set index_num = index_num + 1;
		call p_union_p2(union_user_id1,union_id,cs_rate,cs_tid,pid,index_num);
	else
		insert into union_cs(union_id,uid,cs_score,cs_rate,cs_date,tid,score,pid)
		select union_id,uid,cs_score,cs_rate,now(),cs_tid,cs_score - cs_rate ,pid;
		set index_num = index_num + 1;
		call p_union_p2(union_user_id1,union_id,cs_rate,cs_tid,pid,index_num);
	end if;
elseif permission1 = 0
then
		insert into union_cs(union_id,uid,cs_score,cs_rate,cs_date,tid,score,pid)
		select union_id,uid,cs_score,cs_rate,now(),cs_tid,cs_score ,pid;
else
	select 0;
end if;

end
;;
DELIMITER ;

-- ----------------------------
-- Procedure structure for p_union_p3
-- ----------------------------
DROP PROCEDURE IF EXISTS `p_union_p3`;
DELIMITER ;;
CREATE DEFINER=`root`@`%` PROCEDURE `p_union_p3`(in uid  		int(11),	
	in union_id int(11),	
	in cs_score decimal(17,2) ,	
	in cs_tid 	int(11), 
 pid varchar(55),index_num int(11),subfloorid int(11),ks_score decimal(17,2),from_userid int(11))
begin
declare permission1 int(11) default 0;
declare union_user_id1 int(11) default 0;
declare cs_rate				 decimal(17,2) default 0;
declare cs_score_one	 decimal(17,2) default 0.00;
set @@SESSION.max_sp_recursion_depth=25;

#获取当前用户的权限
select  a.permission into permission1  from union_user as a where a.uid = uid and a.union_id = union_id;
#用户当前用户的上级用户
select  a.union_user_id into union_user_id1  from union_user as a where a.uid = uid and a.union_id = union_id;
if permission1 = 10 or permission1 = 11 
then
	set cs_rate = 0;
	select a.score into cs_rate from union_small_wf as a 
	where a.union_id=union_id and a.uid=uid and a.subfloorid=subfloorid  ;
	if cs_rate = 0
	then
		set index_num = index_num + 1;
		set cs_score_one = cs_score / 2.00;
		select cs_score_one '剩余1' , index_num 第几层;
		call p_union_p3(union_user_id1,union_id,cs_score_one,cs_tid,pid,index_num,subfloorid,ks_score,uid);
	else
		if index_num = 1
		then
			set cs_score_one = cs_score / 2.00;
			set cs_score_one = cs_score_one - (cs_rate/2);
			insert into union_cs(union_id,uid,cs_score,cs_rate,cs_date,tid,score,pid,subfloorid,from_userid)
			select union_id,uid,cs_score,cs_rate,now(),cs_tid,cs_rate/2 ,pid,subfloorid,from_userid;
			set index_num = index_num + 1;
			select cs_score_one '剩余2' , index_num 第几层,cs_rate;
			#call p_union_p3(union_user_id1,union_id,cs_rate/2,cs_tid,pid,index_num,subfloorid,ks_score,uid);
			call p_union_p3(union_user_id1,union_id,cs_score_one,cs_tid,pid,index_num,subfloorid,ks_score,uid);
		else
			insert into union_cs(union_id,uid,cs_score,cs_rate,cs_date,tid,score,pid,subfloorid,from_userid)
			select union_id,uid,cs_score,cs_rate,now(),cs_tid,(cs_rate/2.00) - cs_score ,pid,subfloorid,from_userid;
			set index_num = index_num + 1;
			set cs_score_one = cs_score - (cs_rate/2);
			select cs_score_one '剩余3' , index_num 第几层,cs_rate;
			#call p_union_p3(union_user_id1,union_id,cs_rate/2.00,cs_tid,pid,index_num,subfloorid,ks_score,uid);
			call p_union_p3(union_user_id1,union_id,cs_score_one,cs_tid,pid,index_num,subfloorid,ks_score,uid);
		end if;
	end if;
elseif permission1 = 0
then
		
		if (ks_score/2)-cs_score > 0
		then
		insert into union_cs(union_id,uid,cs_score,cs_rate,cs_date,tid,score,pid,subfloorid,from_userid)
		select union_id,uid,cs_score,cs_rate,now(),cs_tid,(ks_score/2)-cs_score ,pid,subfloorid,from_userid;
	  else
			insert into union_cs(union_id,uid,cs_score,cs_rate,cs_date,tid,score,pid,subfloorid,from_userid)
			select union_id,uid,cs_score,cs_rate,now(),cs_tid,(ks_score/2) ,pid,subfloorid,from_userid;
		end if;
else
	select 0;
end if;

end
;;
DELIMITER ;

-- ----------------------------
-- Procedure structure for p_union_p4
-- ----------------------------
DROP PROCEDURE IF EXISTS `p_union_p4`;
DELIMITER ;;
CREATE DEFINER=`root`@`%` PROCEDURE `p_union_p4`(in uid  		int(11),	
	in union_id int(11),	
	in cs_score decimal(17,2) ,	
	in cs_tid 	int(11), 
 pid varchar(55),index_num int(11),subfloorid int(11),ks_score decimal(17,2),from_userid int(11))
begin
declare permission1 int(11) default 0;
declare union_user_id1 int(11) default 0;
declare cs_rate				 decimal(17,2) default 0;
declare cs_score_one	 decimal(17,2) default 0.00;
set @@SESSION.max_sp_recursion_depth=25;

#获取当前用户的权限
select  a.permission into permission1  from union_user as a where a.uid = uid and a.union_id = union_id;
#用户当前用户的上级用户
select  a.union_user_id into union_user_id1  from union_user as a where a.uid = uid and a.union_id = union_id;
if permission1 = 10 or permission1 = 11 
then
	set cs_rate = 0;
	select a.score into cs_rate from union_small_wf as a 
	where a.union_id=union_id and a.uid=uid and a.subfloorid=subfloorid  ;
	if cs_rate = 0
	then
		set index_num = index_num + 1;
		select cs_rate , cs_score;
		call p_union_p4(union_user_id1,union_id,cs_rate,cs_tid,pid,index_num,subfloorid,ks_score,uid);
	else
		if index_num = 1
		then
			set cs_score_one = (cs_rate - cs_score)/2;
			select cs_rate , cs_score;
			insert into union_cs(union_id,uid,cs_score,cs_rate,cs_date,tid,score,pid,subfloorid,from_userid)
			select union_id,uid,cs_score,cs_rate,now(),cs_tid,cs_score_one ,pid,subfloorid,from_userid;
			set index_num = index_num + 1;
			call p_union_p4(union_user_id1,union_id,cs_rate,cs_tid,pid,index_num,subfloorid,ks_score,uid);
		else
			set cs_score_one = (cs_rate - cs_score)/2;
			select cs_rate , cs_score;
			insert into union_cs(union_id,uid,cs_score,cs_rate,cs_date,tid,score,pid,subfloorid,from_userid)
			select union_id,uid,cs_score,cs_rate,now(),cs_tid,cs_score_one ,pid,subfloorid,from_userid;
			set index_num = index_num + 1;
			call p_union_p4(union_user_id1,union_id,cs_rate,cs_tid,pid,index_num,subfloorid,ks_score,uid);
		end if;
	end if;
elseif permission1 = 0
then
		if ks_score - cs_score > 0
		then
		insert into union_cs(union_id,uid,cs_score,cs_rate,cs_date,tid,score,pid,subfloorid,from_userid)
		select union_id,uid,cs_score,cs_rate,now(),cs_tid, (ks_score - cs_score)/2 ,pid,subfloorid,from_userid;
	  else
			insert into union_cs(union_id,uid,cs_score,cs_rate,cs_date,tid,score,pid,subfloorid,from_userid)
			select union_id,uid,cs_score,cs_rate,now(),cs_tid,0 ,pid,subfloorid,from_userid;
		end if;
else
	select 0;
end if;

end
;;
DELIMITER ;

-- ----------------------------
-- Procedure structure for tt
-- ----------------------------
DROP PROCEDURE IF EXISTS `tt`;
DELIMITER ;;
CREATE DEFINER=`root`@`%` PROCEDURE `tt`(para text,
OUT uid int(11),
OUT score int(11),out iswin int(11))
BEGIN
    declare Count int;
    declare i int;
    declare v_id int;
    declare v_insurance_amount decimal(18, 6);
    declare v_rate decimal(18, 6);
    set i = 1;
    set Count = ExtractValue(para, 'count(/list/pl)');
		create temporary table if not exists tmpTable1
		(
					id    int(11) AUTO_INCREMENT primary key,
					uid 	int(11),
					score decimal(17,2),
					iswin tinyint(4)
					
		);
		truncate table tmpTable1;
    while i <= Count DO
        SET uid = ExtractValue(para,'/list/pl[$i]/uid');
				SET score = ExtractValue(para,'/list/pl[$i]/score');
				SET iswin = ExtractValue(para,'/list/pl[$i]/iswin');
				insert into tmpTable1(uid,score,iswin) select uid,score,iswin;
        set i = i + 1;
    end while;
		#select * from tmpTable1 as a;
		select 'tt procedure';
END
;;
DELIMITER ;

-- ----------------------------
-- Function structure for qcp
-- ----------------------------
DROP FUNCTION IF EXISTS `qcp`;
DELIMITER ;;
CREATE DEFINER=`root`@`%` FUNCTION `qcp`(areaId INT,union_id INT) RETURNS varchar(4000) CHARSET utf8
BEGIN
DECLARE sTemp VARCHAR(4000);
DECLARE sTempChd VARCHAR(4000);
declare sIndex int;

set sIndex = 0;
SET sTemp='$';
SET sTempChd = CAST(areaId AS CHAR);
SET sTemp = CONCAT(sTemp,',',sTempChd);

SELECT union_user_id INTO sTempChd   FROM union_user WHERE uid = sTempChd and union_id=union_id;
WHILE sTempChd <> 0 and sIndex < 5  DO
SET sTemp = CONCAT(sTemp,',',sTempChd);
SELECT union_user_id INTO sTempChd   FROM union_user WHERE uid = sTempChd and union_id=union_id;
set sIndex = sIndex + 1;
END WHILE;
RETURN sTemp;
END
;;
DELIMITER ;

-- ----------------------------
-- Function structure for queryuser
-- ----------------------------
DROP FUNCTION IF EXISTS `queryuser`;
DELIMITER ;;
CREATE DEFINER=`root`@`%` FUNCTION `queryuser`(areaId int,union_id int) RETURNS varchar(4000) CHARSET latin1
BEGIN
DECLARE sTemp VARCHAR(4000);
DECLARE sTempChd VARCHAR(4000);

SET sTemp='$';
SET sTempChd = CAST(areaId AS CHAR);

WHILE sTempChd IS NOT NULL DO
SET sTemp= CONCAT(sTemp,',',sTempChd);
SELECT GROUP_CONCAT(uid) INTO sTempChd FROM union_user WHERE union_id=union_id and FIND_IN_SET(union_user_id,sTempChd)>0;
END WHILE;
RETURN sTemp;
END
;;
DELIMITER ;
