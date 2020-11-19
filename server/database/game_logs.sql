SET FOREIGN_KEY_CHECKS=0;

-- ----------------------------
-- Table structure for active_user_geo_logs
-- ----------------------------
DROP TABLE IF EXISTS `active_user_geo_logs`;
CREATE TABLE `active_user_geo_logs` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `x` decimal(11,8) DEFAULT NULL COMMENT '坐标 X',
  `y` decimal(11,8) DEFAULT NULL COMMENT '坐标 Y',
  `uid` bigint(20) DEFAULT NULL COMMENT '用户 ID',
  `time` bigint(20) DEFAULT NULL COMMENT '记录时间',
  `type` int(4) DEFAULT '1' COMMENT '类型',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for active_user_login_ip_logs
-- ----------------------------
DROP TABLE IF EXISTS `active_user_login_ip_logs`;
CREATE TABLE `active_user_login_ip_logs` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `uid` bigint(20) DEFAULT NULL COMMENT '用户 ID',
  `ip` bigint(20) DEFAULT NULL COMMENT 'IP 地址',
  `time` bigint(20) DEFAULT NULL COMMENT '记录时间',
  `type` tinyint(4) DEFAULT '1' COMMENT '登录 1 注册 2',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=26003 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for admin_logs
-- ----------------------------
DROP TABLE IF EXISTS `admin_logs`;
CREATE TABLE `admin_logs` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `admin_id` bigint(20) NOT NULL COMMENT '后台管理员 ID',
  `refer_id` varchar(32) DEFAULT NULL COMMENT '操作对象 ID',
  `type` int(11) NOT NULL COMMENT '操作类型',
  `action` text COMMENT '操作细节',
  `time` bigint(20) NOT NULL COMMENT '时间',
  `admin_username` varchar(32) DEFAULT '' COMMENT '后台管理员用户名',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for agent_logs
-- ----------------------------
DROP TABLE IF EXISTS `agent_logs`;
CREATE TABLE `agent_logs` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `uid` bigint(20) NOT NULL,
  `ref_user_id` bigint(20) NOT NULL,
  `ref_order_id` bigint(20) NOT NULL,
  `type` int(11) NOT NULL,
  `money` float NOT NULL,
  `current_money` float NOT NULL,
  `time` int(11) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- Table structure for agent_operation_logs
-- ----------------------------
DROP TABLE IF EXISTS `agent_operation_logs`;
CREATE TABLE `agent_operation_logs` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `uid` bigint(20) NOT NULL,
  `ref_uid` bigint(20) NOT NULL,
  `type` int(11) NOT NULL,
  `money` float NOT NULL,
  `card_count` int(11) NOT NULL,
  `status` int(11) NOT NULL,
  `current_money` float NOT NULL,
  `time` int(11) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- Table structure for bonus_logs
-- ----------------------------
DROP TABLE IF EXISTS `bonus_logs`;
CREATE TABLE `bonus_logs` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `uid` int(11) DEFAULT NULL,
  `money` int(11) DEFAULT NULL,
  `admin` varchar(32) DEFAULT NULL,
  `time` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `uid` (`uid`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- Table structure for club_diamond_logs
-- ----------------------------
DROP TABLE IF EXISTS `club_diamond_logs`;
CREATE TABLE `club_diamond_logs` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `uid` int(11) DEFAULT NULL,
  `club_id` int(11) DEFAULT NULL,
  `time` int(11) DEFAULT NULL,
  `diamonds` int(11) DEFAULT NULL,
  `record_id` varchar(32) NOT NULL,
  `la_jiao_dou` int(11) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`) USING BTREE,
  KEY `index` (`uid`,`club_id`,`time`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for club_game_count_logs
-- ----------------------------
DROP TABLE IF EXISTS `club_game_count_logs`;
CREATE TABLE `club_game_count_logs` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `uid1` int(11) DEFAULT NULL,
  `uid2` int(11) DEFAULT NULL,
  `status` int(11) NOT NULL DEFAULT '0',
  `time` int(11) DEFAULT NULL,
  `count` int(11) DEFAULT NULL,
  `club_id` int(11) DEFAULT NULL,
  `name1` varchar(32) DEFAULT NULL,
  `name2` varchar(32) DEFAULT NULL,
  `avatar1` varchar(512) DEFAULT NULL,
  `avatar2` varchar(512) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`) USING BTREE,
  KEY `club_id` (`club_id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for club_logs
-- ----------------------------
DROP TABLE IF EXISTS `club_logs`;
CREATE TABLE `club_logs` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `uid` int(11) DEFAULT NULL COMMENT '用户 ID',
  `club_id` int(11) DEFAULT NULL COMMENT '茶馆 ID',
  `ref_uid` int(11) DEFAULT NULL COMMENT '对象 ID',
  `game_id` int(11) DEFAULT NULL COMMENT '游戏 ID',
  `type` int(11) DEFAULT NULL COMMENT '类型 // 赠送 审核',
  `detail` varchar(512) DEFAULT NULL COMMENT '细节 JSON ',
  `time` int(11) DEFAULT NULL COMMENT '时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for club_player_room_logs
-- ----------------------------
DROP TABLE IF EXISTS `club_player_room_logs`;
CREATE TABLE `club_player_room_logs` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT COMMENT '主键自增',
  `uid` int(11) NOT NULL COMMENT '用户ID',
  `winner_count` int(11) NOT NULL DEFAULT '0' COMMENT '大赢家场次',
  `round_count` int(11) NOT NULL DEFAULT '0' COMMENT '局数',
  `lose_count` int(11) NOT NULL DEFAULT '0' COMMENT '大输家场次',
  `winner_score` int(11) NOT NULL DEFAULT '0' COMMENT '大赢家总得分',
  `total_score` int(11) NOT NULL DEFAULT '0' COMMENT '总得分',
  `lose_score` int(11) NOT NULL DEFAULT '0' COMMENT '大输家失分',
  `club_id` int(11) NOT NULL COMMENT '俱乐部ID',
  `start_time` bigint(20) NOT NULL COMMENT '开始时间',
  `game_type` int(11) NOT NULL COMMENT '游戏类型',
  `end_time` bigint(20) NOT NULL COMMENT '结束时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- ----------------------------
-- Table structure for club_send_log
-- ----------------------------
DROP TABLE IF EXISTS `club_send_log`;
CREATE TABLE `club_send_log` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `club_id` int(11) DEFAULT NULL,
  `uid` int(11) DEFAULT NULL,
  `before_count` int(11) DEFAULT NULL,
  `count` int(11) DEFAULT NULL,
  `time` int(11) DEFAULT NULL,
  `reason` int(11) DEFAULT NULL,
  `record_id` varchar(128) DEFAULT NULL,
  `operation_uid` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `club_id,uid` (`club_id`,`uid`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- Table structure for club_statistics
-- ----------------------------
DROP TABLE IF EXISTS `club_statistics`;
CREATE TABLE `club_statistics` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `time` int(11) DEFAULT NULL COMMENT '记录时间',
  `room_club_count` int(11) DEFAULT NULL COMMENT '至少一局俱乐部数量',
  `club_open_room_count` int(11) DEFAULT NULL COMMENT '俱乐部开房数量',
  `club_round_count` int(11) DEFAULT NULL COMMENT '俱乐部局数数量',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for club_tag_player_room_logs
-- ----------------------------
DROP TABLE IF EXISTS `club_tag_player_room_logs`;
CREATE TABLE `club_tag_player_room_logs` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT COMMENT '主键自增',
  `club_id` int(11) NOT NULL COMMENT '俱乐部ID',
  `tag_uid` int(11) NOT NULL COMMENT '用户ID',
  `winner_count` int(11) NOT NULL DEFAULT '0' COMMENT '大赢家场次',
  `round_count` int(11) NOT NULL DEFAULT '0' COMMENT '局数',
  `score_less_10_count` int(11) NOT NULL DEFAULT '0' COMMENT '小于10分场次',
  `start_time` bigint(20) NOT NULL COMMENT '开始时间',
  `end_time` bigint(20) NOT NULL COMMENT '结束时间',
  PRIMARY KEY (`id`),
  KEY `club_id` (`club_id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for club_upgrade_log
-- ----------------------------
DROP TABLE IF EXISTS `club_upgrade_log`;
CREATE TABLE `club_upgrade_log` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `club_id` int(11) DEFAULT NULL,
  `club_owner` int(11) DEFAULT NULL,
  `uid` int(11) DEFAULT NULL,
  `avatar` varchar(255) DEFAULT NULL,
  `nick_name` varchar(32) DEFAULT NULL,
  `before_score` int(11) DEFAULT NULL,
  `score` int(11) DEFAULT NULL,
  `is_read` int(11) NOT NULL DEFAULT '0',
  `time` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `club_owner` (`club_owner`) USING BTREE,
  KEY `is_read` (`is_read`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- Table structure for club_user_game_count
-- ----------------------------
DROP TABLE IF EXISTS `club_user_game_count`;
CREATE TABLE `club_user_game_count` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `club_id` int(11) DEFAULT NULL,
  `uid` int(11) DEFAULT NULL,
  `ref_uid` int(11) DEFAULT NULL,
  `count` int(11) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`) USING BTREE,
  UNIQUE KEY `club_id,uid,ref_uid` (`club_id`,`uid`,`ref_uid`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- ----------------------------
-- Table structure for club_user_money_log
-- ----------------------------
DROP TABLE IF EXISTS `club_user_money_log`;
CREATE TABLE `club_user_money_log` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `club_id` int(11) DEFAULT NULL,
  `uid` int(11) DEFAULT NULL,
  `before_score` int(11) DEFAULT NULL,
  `score` int(11) DEFAULT NULL,
  `record_id` varchar(32) DEFAULT NULL,
  `time` int(11) DEFAULT NULL,
  `type` int(11) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- Table structure for club_user_rank_logs
-- ----------------------------
DROP TABLE IF EXISTS `club_user_rank_logs`;
CREATE TABLE `club_user_rank_logs` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `start_time` int(11) DEFAULT NULL,
  `end_time` int(11) DEFAULT NULL,
  `uid` int(11) DEFAULT NULL,
  `club_id` int(11) DEFAULT NULL,
  `game_count` int(11) DEFAULT NULL,
  `total_score` int(11) DEFAULT NULL,
  `game_type` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- Table structure for club_user_stat
-- ----------------------------
DROP TABLE IF EXISTS `club_user_stat`;
CREATE TABLE `club_user_stat` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `club_id` int(11) DEFAULT NULL,
  `user_count` int(11) DEFAULT NULL,
  `time` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `club_id` (`club_id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for club_winner
-- ----------------------------
DROP TABLE IF EXISTS `club_winner`;
CREATE TABLE `club_winner` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `record_id` varchar(32) NOT NULL,
  `club_id` int(11) DEFAULT NULL,
  `players` int(11) DEFAULT NULL,
  `score` int(11) NOT NULL,
  `time` int(11) NOT NULL,
  `is_read` tinyint(1) NOT NULL DEFAULT '0',
  `game_type` int(11) NOT NULL,
  `rule_details` varchar(1024) NOT NULL DEFAULT '',
  `room_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `club_id` (`club_id`,`is_read`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for day_logs
-- ----------------------------
DROP TABLE IF EXISTS `day_logs`;
CREATE TABLE `day_logs` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `new_user` int(11) DEFAULT NULL COMMENT '新用户数',
  `new_play_user` int(11) DEFAULT NULL COMMENT '新玩游戏用户',
  `active_user` int(11) DEFAULT NULL COMMENT '活跃用户',
  `new_agent` int(11) DEFAULT NULL COMMENT '新代理',
  `active_agent` int(11) DEFAULT NULL COMMENT '活跃代理',
  `diamond_consume` int(11) DEFAULT NULL COMMENT '钻石消耗',
  `room_count` int(11) DEFAULT NULL COMMENT '开房数',
  `round_count` int(11) DEFAULT NULL COMMENT '开局数',
  `pay_user` int(11) DEFAULT NULL COMMENT '购买用户数',
  `pay_user_total_money` float DEFAULT NULL COMMENT '购买用户总金额',
  `pay_agent` int(11) DEFAULT NULL COMMENT '购买代理',
  `pay_agent_total_money` float DEFAULT NULL COMMENT '购买代理总金额',
  `system_diamond` bigint(22) DEFAULT NULL COMMENT '系统剩余钻石',
  `time` int(11) DEFAULT NULL COMMENT '时间',
  `active_player_diamond` int(11) DEFAULT '0' COMMENT '活跃玩家钻石总数',
  `active_agent_diamond` int(11) DEFAULT '0' COMMENT '活跃代理钻石总数',
  PRIMARY KEY (`id`),
  UNIQUE KEY `time` (`time`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for debug_log
-- ----------------------------
DROP TABLE IF EXISTS `debug_log`;
CREATE TABLE `debug_log` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `record_id` varchar(32) DEFAULT NULL,
  `table_id` int(11) DEFAULT NULL,
  `seq` int(11) DEFAULT NULL,
  `nickname` varchar(24) DEFAULT NULL,
  `time` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- Table structure for diamond_logs
-- ----------------------------
DROP TABLE IF EXISTS `diamond_logs`;
CREATE TABLE `diamond_logs` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `uid` bigint(20) NOT NULL,
  `refer_uid` bigint(20) NOT NULL COMMENT '关联UID',
  `refer_nick_name` varchar(32) NOT NULL DEFAULT '' COMMENT '关联玩家昵称',
  `diamonds` int(11) NOT NULL COMMENT '变化钻石数',
  `reason_id` tinyint(4) NOT NULL COMMENT '变化的原因ID',
  `left_diamonds` int(11) NOT NULL COMMENT '当时剩余钻石数',
  `time` bigint(20) NOT NULL COMMENT '发生时间',
  `memo` varchar(100) DEFAULT '' COMMENT '备忘',
  `step` tinyint(4) DEFAULT '0' COMMENT '执行到的步骤',
  `record_id` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `uid` (`uid`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=144 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for diamond_logs_statistics
-- ----------------------------
DROP TABLE IF EXISTS `diamond_logs_statistics`;
CREATE TABLE `diamond_logs_statistics` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `time` bigint(20) DEFAULT NULL COMMENT '记录时间',
  `total` bigint(20) DEFAULT NULL COMMENT '钻石总量',
  `diamond_type` int(11) DEFAULT NULL COMMENT '类型',
  `count` bigint(20) DEFAULT NULL COMMENT '数量',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for emotion_logs
-- ----------------------------
DROP TABLE IF EXISTS `emotion_logs`;
CREATE TABLE `emotion_logs` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `uid` bigint(20) NOT NULL COMMENT '玩家 ID',
  `refer_id` bigint(20) DEFAULT NULL COMMENT '对象 ID',
  `display_diamond` int(11) unsigned DEFAULT NULL COMMENT '显示钻石',
  `actual_diamond` int(11) unsigned DEFAULT NULL COMMENT '实际钻石',
  `emotion_id` int(11) unsigned DEFAULT NULL COMMENT '表情 ID',
  `time` bigint(20) DEFAULT NULL COMMENT '记录时间',
  `type` tinyint(4) DEFAULT '1' COMMENT '表情类型（是否给自己发送)',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for emotion_logs_statistics
-- ----------------------------
DROP TABLE IF EXISTS `emotion_logs_statistics`;
CREATE TABLE `emotion_logs_statistics` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `emotion_id` int(11) unsigned DEFAULT NULL COMMENT '表情 ID',
  `emotion_count` int(11) unsigned DEFAULT NULL COMMENT '表情使用数量',
  `start_time` bigint(20) unsigned NOT NULL COMMENT '开始时间',
  `end_time` bigint(20) unsigned NOT NULL COMMENT '结束时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for exchange_gold_logs
-- ----------------------------
DROP TABLE IF EXISTS `exchange_gold_logs`;
CREATE TABLE `exchange_gold_logs` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `uid` int(11) DEFAULT NULL COMMENT '用户ID',
  `diamond` int(11) DEFAULT NULL COMMENT '兑换钻石',
  `extra_diamond` int(11) DEFAULT NULL COMMENT '赠送钻石',
  `gold` int(11) DEFAULT NULL COMMENT '兑换金币',
  `status` int(11) DEFAULT NULL COMMENT '状态 0 未处理 1已处理',
  `time` int(11) DEFAULT NULL COMMENT '兑换时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- ----------------------------
-- Table structure for gold_logs
-- ----------------------------
DROP TABLE IF EXISTS `gold_logs`;
CREATE TABLE `gold_logs` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `uid` bigint(20) NOT NULL,
  `refer_uid` bigint(20) NOT NULL COMMENT '关联UID',
  `refer_nick_name` varchar(32) NOT NULL DEFAULT '' COMMENT '关联玩家昵称',
  `gold` int(11) NOT NULL COMMENT '变化金币',
  `reason_id` tinyint(4) NOT NULL COMMENT '变化的原因ID',
  `left_gold` int(11) NOT NULL COMMENT '当时剩余金币数',
  `time` bigint(20) NOT NULL COMMENT '发生时间',
  `memo` varchar(100) DEFAULT '' COMMENT '备忘',
  `step` tinyint(4) DEFAULT '0' COMMENT '执行到的步骤',
  `game_type` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `uid` (`uid`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for ip_geo
-- ----------------------------
DROP TABLE IF EXISTS `ip_geo`;
CREATE TABLE `ip_geo` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `ip` bigint(20) DEFAULT NULL COMMENT 'IP 地址',
  `province` varchar(24) DEFAULT NULL COMMENT '省份',
  `city` varchar(24) DEFAULT NULL COMMENT '市',
  `county_area` varchar(24) DEFAULT NULL COMMENT '县 / 区',
  `x` decimal(11,8) NOT NULL COMMENT '坐标 X',
  `y` decimal(11,8) NOT NULL COMMENT '坐标 Y',
  PRIMARY KEY (`id`),
  UNIQUE KEY `ip_2` (`ip`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for la_jiao_dou_logs
-- ----------------------------
DROP TABLE IF EXISTS `la_jiao_dou_logs`;
CREATE TABLE `la_jiao_dou_logs` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `uid` bigint(20) NOT NULL,
  `refer_uid` bigint(20) NOT NULL COMMENT '关联UID',
  `refer_nick_name` varchar(32) NOT NULL DEFAULT '' COMMENT '关联玩家昵称',
  `la_jiao_dou` int(11) NOT NULL COMMENT '变化钻石数',
  `reason_id` tinyint(4) NOT NULL COMMENT '变化的原因ID',
  `left_la_jiao_dou` int(11) NOT NULL COMMENT '当时剩余钻石数',
  `time` bigint(20) NOT NULL COMMENT '发生时间',
  `memo` varchar(100) DEFAULT '' COMMENT '备忘',
  `step` tinyint(4) DEFAULT '0' COMMENT '执行到的步骤',
  `record_id` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `uid` (`uid`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for message_logs
-- ----------------------------
DROP TABLE IF EXISTS `message_logs`;
CREATE TABLE `message_logs` (
  `Id` bigint(20) NOT NULL AUTO_INCREMENT,
  `Roomid` bigint(20) DEFAULT NULL,
  `uid` bigint(20) DEFAULT NULL,
  `Name` varchar(50) DEFAULT NULL,
  `avatar` varchar(500) DEFAULT NULL,
  `mesImg` varchar(500) DEFAULT NULL,
  `Messages` varchar(500) DEFAULT NULL,
  `Creatime` datetime DEFAULT NULL,
  `imgtyps` int(10) DEFAULT NULL COMMENT '0 聊天图片 1收款图片',
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for month_logs
-- ----------------------------
DROP TABLE IF EXISTS `month_logs`;
CREATE TABLE `month_logs` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `new_user` int(11) DEFAULT NULL COMMENT '新用户数',
  `new_play_user` int(11) DEFAULT NULL COMMENT '新玩游戏用户',
  `active_user` int(11) DEFAULT NULL COMMENT '活跃用户',
  `new_agent` int(11) DEFAULT NULL COMMENT '新代理',
  `active_agent` int(11) DEFAULT NULL COMMENT '活跃代理',
  `diamond_consume` int(11) DEFAULT NULL COMMENT '钻石消耗',
  `room_count` int(11) DEFAULT NULL COMMENT '开房数',
  `round_count` int(11) DEFAULT NULL COMMENT '开局数',
  `pay_user` int(11) DEFAULT NULL COMMENT '购买用户数',
  `pay_user_total_money` float DEFAULT NULL COMMENT '购买用户总金额',
  `pay_agent` int(11) DEFAULT NULL COMMENT '购买代理',
  `pay_agent_total_money` float DEFAULT NULL COMMENT '购买代理总金额',
  `system_diamond` int(11) DEFAULT NULL COMMENT '系统剩余钻石',
  `time` int(11) DEFAULT NULL COMMENT '时间',
  `active_player_diamond` int(11) DEFAULT '0' COMMENT '活跃玩家钻石总数',
  `active_agent_diamond` int(11) DEFAULT '0' COMMENT '活跃代理钻石总数',
  PRIMARY KEY (`id`),
  UNIQUE KEY `time` (`time`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for online_player_statistics
-- ----------------------------
DROP TABLE IF EXISTS `online_player_statistics`;
CREATE TABLE `online_player_statistics` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `count` bigint(20) DEFAULT NULL COMMENT '在线玩家数量',
  `time` bigint(20) unsigned NOT NULL COMMENT '时间(每分钟)',
  `playing_count` bigint(20) DEFAULT '0' COMMENT '在玩玩家数量',
  `in_table_count` bigint(20) DEFAULT '0' COMMENT '在桌子中玩家数量',
  `hall_count` bigint(20) DEFAULT '0' COMMENT '大厅玩家数量',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for players_round_count_logs
-- ----------------------------
DROP TABLE IF EXISTS `players_round_count_logs`;
CREATE TABLE `players_round_count_logs` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `uid` int(11) DEFAULT NULL,
  `round_count` int(11) DEFAULT NULL,
  `time` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for players_round_logs
-- ----------------------------
DROP TABLE IF EXISTS `players_round_logs`;
CREATE TABLE `players_round_logs` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `uid` int(11) DEFAULT NULL,
  `round` int(11) DEFAULT NULL,
  `finish_time` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `uid` (`uid`) USING BTREE,
  KEY `finish_time` (`finish_time`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for players_statistics
-- ----------------------------
DROP TABLE IF EXISTS `players_statistics`;
CREATE TABLE `players_statistics` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `start_time` bigint(20) unsigned NOT NULL COMMENT '开始时间',
  `end_time` bigint(20) unsigned NOT NULL COMMENT '结束时间',
  `login_count` int(11) NOT NULL DEFAULT '0' COMMENT '登录数量',
  `reg_count` int(11) NOT NULL DEFAULT '0' COMMENT '注册数量',
  PRIMARY KEY (`id`),
  UNIQUE KEY `start_time` (`start_time`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=4472 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for player_consume_logs
-- ----------------------------
DROP TABLE IF EXISTS `player_consume_logs`;
CREATE TABLE `player_consume_logs` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `club_id` int(11) DEFAULT NULL COMMENT '俱乐部ID',
  `uid` int(11) DEFAULT NULL COMMENT '用户ID',
  `count` int(11) DEFAULT NULL COMMENT '数量',
  `pay_type` int(11) DEFAULT NULL COMMENT '支付类型 1=钻石 2=元宝',
  `reason` int(11) DEFAULT NULL COMMENT '扣除原因 开房消耗 | 抽水',
  `time` int(11) DEFAULT NULL COMMENT '时间',
  `status` int(11) DEFAULT NULL COMMENT '状态 0 = 未处理',
  `record_id` varchar(128) DEFAULT NULL,
  `union_id` int(11) DEFAULT NULL COMMENT '联盟ID',
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`) USING BTREE,
  KEY `status` (`status`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=23774 DEFAULT CHARSET=latin1;

-- ----------------------------
-- Table structure for player_score_logs
-- ----------------------------
DROP TABLE IF EXISTS `player_score_logs`;
CREATE TABLE `player_score_logs` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `uid` int(11) DEFAULT NULL,
  `score` int(11) DEFAULT NULL,
  `reason` int(11) DEFAULT NULL,
  `time` int(11) DEFAULT NULL,
  `refer_id` varchar(64) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`) USING BTREE,
  KEY `uid` (`uid`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=48038 DEFAULT CHARSET=latin1;

-- ----------------------------
-- Table structure for player_stat_logs
-- ----------------------------
DROP TABLE IF EXISTS `player_stat_logs`;
CREATE TABLE `player_stat_logs` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `uid` int(11) DEFAULT NULL,
  `score` int(11) DEFAULT NULL,
  `time` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- ----------------------------
-- Table structure for playing_table_statistics
-- ----------------------------
DROP TABLE IF EXISTS `playing_table_statistics`;
CREATE TABLE `playing_table_statistics` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `count` bigint(20) DEFAULT NULL COMMENT '在玩桌子数量',
  `time` bigint(20) unsigned NOT NULL COMMENT '时间(每分钟)',
  `ready_count` bigint(20) DEFAULT '0' COMMENT '准备桌子数量',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for robot_logs
-- ----------------------------
DROP TABLE IF EXISTS `robot_logs`;
CREATE TABLE `robot_logs` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `wx_id` varchar(128) DEFAULT NULL,
  `group_id` varchar(128) DEFAULT NULL,
  `red_packet_count` int(11) DEFAULT NULL,
  `message_count` int(11) DEFAULT NULL,
  `open_room_count` int(11) DEFAULT NULL,
  `time` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for room_logs
-- ----------------------------
DROP TABLE IF EXISTS `room_logs`;
CREATE TABLE `room_logs` (
  `record_id` varchar(32) CHARACTER SET utf8 NOT NULL DEFAULT '' COMMENT '记录ID',
  `room_id` int(11) NOT NULL COMMENT '房间ID',
  `uid1` int(11) NOT NULL COMMENT '玩家ID1',
  `name1` varchar(32) CHARACTER SET utf8 NOT NULL DEFAULT '' COMMENT '玩家昵称1',
  `score1` int(11) NOT NULL COMMENT '积分1',
  `avatar1` varchar(255) DEFAULT NULL COMMENT '玩家1头像',
  `uid2` int(11) NOT NULL COMMENT '玩家ID2',
  `name2` varchar(32) CHARACTER SET utf8 NOT NULL DEFAULT '' COMMENT '玩家昵称2',
  `score2` int(11) NOT NULL COMMENT '积分2',
  `avatar2` varchar(255) DEFAULT NULL COMMENT '玩家2头像',
  `uid3` int(11) NOT NULL COMMENT '玩家ID3',
  `name3` varchar(32) CHARACTER SET utf8 NOT NULL DEFAULT '' COMMENT '玩家昵称3',
  `score3` int(11) NOT NULL COMMENT '积分3',
  `avatar3` varchar(255) DEFAULT NULL COMMENT '玩家3头像',
  `uid4` int(11) DEFAULT NULL COMMENT '玩家ID4',
  `name4` varchar(32) DEFAULT NULL COMMENT '玩家昵称4',
  `score4` int(11) DEFAULT NULL COMMENT '积分4',
  `avatar4` varchar(255) DEFAULT NULL COMMENT '玩家4头像',
  `uid5` int(11) DEFAULT NULL,
  `name5` varchar(32) DEFAULT NULL,
  `score5` int(11) DEFAULT NULL,
  `avatar5` varchar(255) DEFAULT NULL,
  `finish_time` bigint(20) NOT NULL COMMENT '完成时间',
  `owner` bigint(20) NOT NULL DEFAULT '0' COMMENT '房主',
  `round_count` int(11) NOT NULL DEFAULT '0' COMMENT '局数',
  `agent_name` varchar(32) NOT NULL DEFAULT '' COMMENT '代开玩家昵称',
  `is_agent` int(4) NOT NULL DEFAULT '0' COMMENT '是否为代开房间',
  `rule_type` int(4) NOT NULL DEFAULT '0' COMMENT '游戏模式',
  `game_finish_data` varchar(8192) DEFAULT NULL COMMENT '游戏结束数据',
  `club_id` int(11) NOT NULL DEFAULT '-1' COMMENT '茶馆 ID',
  `diamond` int(11) DEFAULT '0' COMMENT '游戏消耗钻石数',
  `rule_details` varchar(1000) DEFAULT NULL COMMENT '房间规则详情',
  `game_type` int(11) DEFAULT NULL COMMENT '游戏类型',
  `group_id` varchar(255) NOT NULL DEFAULT '-1' COMMENT '微信群组 ID',
  `is_dou` tinyint(2) NOT NULL DEFAULT '1',
  `uid6` int(11) DEFAULT NULL,
  `uid7` int(11) DEFAULT NULL,
  `uid8` int(11) DEFAULT NULL,
  `uid9` int(11) DEFAULT NULL,
  `uid10` int(11) DEFAULT NULL,
  `name6` varchar(32) DEFAULT NULL,
  `name7` varchar(32) DEFAULT NULL,
  `name8` varchar(32) DEFAULT NULL,
  `name9` varchar(32) DEFAULT NULL,
  `score7` int(11) DEFAULT NULL,
  `score8` int(11) DEFAULT NULL,
  `avatar6` varchar(255) DEFAULT NULL,
  `avatar7` varchar(255) DEFAULT NULL,
  `avatar8` varchar(255) DEFAULT NULL,
  `avatar9` varchar(255) DEFAULT NULL,
  `avatar10` varchar(255) DEFAULT NULL,
  `score9` int(11) DEFAULT NULL,
  `score10` int(11) DEFAULT NULL,
  `name10` varchar(32) DEFAULT NULL,
  `score6` int(11) DEFAULT NULL,
  `match_type` int(11) DEFAULT NULL COMMENT '0 亲友圈 或 普通房 1 比赛房',
  `floor` int(11) NOT NULL DEFAULT '-1',
  `sub_floor` int(11) NOT NULL DEFAULT '-1',
  `match_config` varchar(1024) DEFAULT NULL,
  `reward_count` int(11) DEFAULT '0' COMMENT '打赏金币',
  `is_reward_finish` int(11) DEFAULT '0' COMMENT '是否返佣 0 待返佣 1 已返佣',
  `pay_type` int(11) NOT NULL DEFAULT '0' COMMENT '0 钻石 1 金币',
  `union_id` int(11) DEFAULT '-1' COMMENT '联盟ID',
  PRIMARY KEY (`record_id`),
  KEY `room_id` (`room_id`) USING BTREE,
  KEY `uid1` (`uid1`) USING BTREE,
  KEY `uid2` (`uid2`) USING BTREE,
  KEY `uid3` (`uid3`) USING BTREE,
  KEY `finish_time` (`finish_time`) USING BTREE,
  KEY `uid4` (`uid4`) USING BTREE,
  KEY `owner` (`owner`) USING BTREE,
  KEY `club_id` (`club_id`) USING BTREE,
  KEY `club_id,finish_time` (`club_id`,`finish_time`) USING BTREE,
  KEY `union_id` (`union_id`) USING BTREE,
  KEY `union_id,finish_time` (`union_id`,`finish_time`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- Table structure for room_logs_in_activity
-- ----------------------------
DROP TABLE IF EXISTS `room_logs_in_activity`;
CREATE TABLE `room_logs_in_activity` (
  `record_id` varchar(32) NOT NULL DEFAULT '' COMMENT '记录ID',
  `uid1` int(11) NOT NULL COMMENT '玩家ID1',
  `name1` varchar(32) NOT NULL DEFAULT '' COMMENT '玩家昵称1',
  `uid2` int(11) NOT NULL COMMENT '玩家ID2',
  `name2` varchar(32) NOT NULL DEFAULT '' COMMENT '玩家昵称2',
  `uid3` int(11) NOT NULL COMMENT '玩家ID3',
  `name3` varchar(32) NOT NULL DEFAULT '' COMMENT '玩家昵称3',
  `finish_time` bigint(20) NOT NULL COMMENT '完成时间',
  `round_count` tinyint(4) NOT NULL DEFAULT '0' COMMENT '局数',
  PRIMARY KEY (`record_id`),
  KEY `uid1` (`uid1`) USING BTREE,
  KEY `uid2` (`uid2`) USING BTREE,
  KEY `uid3` (`uid3`) USING BTREE,
  KEY `finish_time` (`finish_time`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for room_logs_statistics
-- ----------------------------
DROP TABLE IF EXISTS `room_logs_statistics`;
CREATE TABLE `room_logs_statistics` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `start_time` bigint(20) unsigned NOT NULL COMMENT '开始时间',
  `end_time` bigint(20) unsigned NOT NULL COMMENT '结束时间',
  `room_count` int(11) NOT NULL DEFAULT '0' COMMENT '开房数量',
  `round_count` int(11) NOT NULL DEFAULT '0' COMMENT '局数',
  `zzmj_room_count` int(11) NOT NULL DEFAULT '0',
  `zzmj_round_count` int(11) NOT NULL DEFAULT '0',
  `pdk_room_count` int(11) NOT NULL DEFAULT '0',
  `pdk_round_count` int(11) NOT NULL DEFAULT '0',
  `nn_room_count` int(11) NOT NULL DEFAULT '0',
  `nn_round_count` int(11) NOT NULL DEFAULT '0',
  `hzmj_room_count` int(11) NOT NULL DEFAULT '0',
  `hzmj_round_count` int(11) NOT NULL DEFAULT '0',
  `csmj_room_count` int(11) NOT NULL DEFAULT '0',
  `csmj_round_count` int(11) NOT NULL DEFAULT '0',
  `dtz_room_count` int(11) NOT NULL DEFAULT '0',
  `dtz_round_count` int(11) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

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
) ENGINE=InnoDB AUTO_INCREMENT=1308 DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- Table structure for round_logs
-- ----------------------------
DROP TABLE IF EXISTS `round_logs`;
CREATE TABLE `round_logs` (
  `round_id` bigint(11) unsigned NOT NULL AUTO_INCREMENT COMMENT '对局ID',
  `record_id` varchar(32) NOT NULL DEFAULT '' COMMENT '记录ID',
  `seq` tinyint(4) NOT NULL COMMENT '序号',
  `score1` int(11) NOT NULL COMMENT '积分1',
  `score2` int(11) NOT NULL COMMENT '积分2',
  `score3` int(11) NOT NULL COMMENT '积分3',
  `finish_time` bigint(20) NOT NULL COMMENT '结束时间',
  `share_code` int(11) DEFAULT NULL COMMENT '分享码',
  `share_time` bigint(20) DEFAULT NULL COMMENT '分享时间',
  `resource_path` varchar(100) DEFAULT NULL COMMENT '云资源路径',
  `score4` int(11) DEFAULT NULL COMMENT '积分4',
  `game_type` int(11) DEFAULT NULL COMMENT '游戏类型',
  `diamond` int(11) DEFAULT NULL,
  `score5` int(11) DEFAULT NULL,
  `score6` int(11) DEFAULT NULL,
  `score7` int(11) DEFAULT NULL,
  `score8` int(11) DEFAULT NULL,
  `score9` int(11) DEFAULT NULL,
  `score10` int(11) DEFAULT NULL,
  `round_detail` varchar(2048) DEFAULT NULL,
  PRIMARY KEY (`round_id`),
  UNIQUE KEY `share_code` (`share_code`) USING BTREE,
  KEY `record_id` (`record_id`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=170335 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for round_rank_logs
-- ----------------------------
DROP TABLE IF EXISTS `round_rank_logs`;
CREATE TABLE `round_rank_logs` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `uid` bigint(20) NOT NULL,
  `nickname` varchar(100) NOT NULL DEFAULT '',
  `count` int(11) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uid` (`uid`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- Table structure for share_logs
-- ----------------------------
DROP TABLE IF EXISTS `share_logs`;
CREATE TABLE `share_logs` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `union_id` varchar(256) DEFAULT NULL COMMENT '微信 UNIONID',
  `type` int(4) DEFAULT NULL COMMENT '1 提现成功(回调时记录) 2 分享成功 3 点击分享',
  `time` int(11) DEFAULT NULL COMMENT '时间',
  `amount` int(11) DEFAULT '0' COMMENT '提现 or 兑换数量',
  `item_type` int(11) DEFAULT '0' COMMENT '1 钻石 2 红包',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for spring_activity_logs
-- ----------------------------
DROP TABLE IF EXISTS `spring_activity_logs`;
CREATE TABLE `spring_activity_logs` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `uid` int(11) DEFAULT NULL,
  `item_id` int(11) DEFAULT NULL,
  `item_type` int(11) DEFAULT NULL,
  `time` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- ----------------------------
-- Table structure for union_diamond_logs
-- ----------------------------
DROP TABLE IF EXISTS `union_diamond_logs`;
CREATE TABLE `union_diamond_logs` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `uid` int(11) DEFAULT NULL,
  `union_id` int(11) DEFAULT NULL,
  `time` int(11) DEFAULT NULL,
  `diamonds` int(11) DEFAULT NULL,
  `record_id` varchar(32) NOT NULL,
  `la_jiao_dou` int(11) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`) USING BTREE,
  KEY `index` (`union_id`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=23386 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for union_energy_logs
-- ----------------------------
DROP TABLE IF EXISTS `union_energy_logs`;
CREATE TABLE `union_energy_logs` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `union_id` int(11) DEFAULT NULL,
  `uid` int(11) DEFAULT NULL,
  `refer_uid` int(11) DEFAULT NULL,
  `count` int(11) DEFAULT NULL,
  `before_count` int(11) DEFAULT NULL,
  `type` int(11) DEFAULT NULL COMMENT '0 = 减少 1 = 增加 2 = 转移',
  `time` int(11) DEFAULT NULL,
  `after_count` int(11) DEFAULT NULL COMMENT '这个是能量操作之后的',
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`) USING BTREE,
  KEY `union_id` (`union_id`) USING BTREE,
  KEY `union_id,uid` (`union_id`,`uid`) USING BTREE,
  KEY `union_id,refer_uid` (`union_id`,`refer_uid`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=69296 DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- Table structure for union_game_count_logs
-- ----------------------------
DROP TABLE IF EXISTS `union_game_count_logs`;
CREATE TABLE `union_game_count_logs` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `uid1` int(11) DEFAULT NULL,
  `uid2` int(11) DEFAULT NULL,
  `status` int(11) NOT NULL DEFAULT '0',
  `time` int(11) DEFAULT NULL,
  `count` int(11) DEFAULT NULL,
  `union_id` int(11) DEFAULT NULL,
  `name1` varchar(32) DEFAULT NULL,
  `name2` varchar(32) DEFAULT NULL,
  `avatar1` varchar(512) DEFAULT NULL,
  `avatar2` varchar(512) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`) USING BTREE,
  KEY `union_id` (`union_id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for verify_withdraw_logs
-- ----------------------------
DROP TABLE IF EXISTS `verify_withdraw_logs`;
CREATE TABLE `verify_withdraw_logs` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `ref_id` bigint(20) NOT NULL,
  `uid` bigint(20) NOT NULL,
  `nick_name` varchar(255) NOT NULL,
  `money` float NOT NULL,
  `time` int(11) NOT NULL,
  `status` int(11) NOT NULL,
  `admin_uid` bigint(20) NOT NULL,
  `admin_name` varchar(255) NOT NULL,
  `reply` varchar(120) NOT NULL,
  `detail` longtext NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
