CREATE DATABASE IF NOT EXISTS toilet;
USE toilet;

DROP TABLE toilet_group_map;
DROP TABLE toilet_status;
DROP TABLE toilet_group;
DROP TABLE toilet;
DROP TABLE app_state;

CREATE TABLE IF NOT EXISTS app_state (
	id	INTEGER NOT NULL AUTO_INCREMENT,
	name	TEXT,
	state	INTEGER NOT NULL,
	comment	TEXT,
	modified_time	TIMESTAMP NOT NULL,
	PRIMARY KEY(id)
);

CREATE TABLE IF NOT EXISTS toilet (
	id	INTEGER NOT NULL AUTO_INCREMENT,
	name	TEXT NOT NULL,
	valid	BOOLEAN NOT NULL,
	is_closed	BOOLEAN NOT NULL,
	modified_time	TIMESTAMP NOT NULL,
	PRIMARY KEY(id)
);

CREATE TABLE IF NOT EXISTS toilet_group (
	id	INTEGER NOT NULL AUTO_INCREMENT,
	name	TEXT NOT NULL,
	valid	BOOLEAN NOT NULL,
	modified_time	TIMESTAMP NOT NULL,
	PRIMARY KEY(id)
);

CREATE TABLE IF NOT EXISTS toilet_status (
	id	INTEGER NOT NULL AUTO_INCREMENT,
	toilet_id	INTEGER NOT NULL,
	is_closed	BOOLEAN NOT NULL,
	created_time	TIMESTAMP NOT NULL,
	PRIMARY KEY(id),
	FOREIGN KEY(toilet_id) REFERENCES toilet(id)
);

CREATE TABLE IF NOT EXISTS toilet_group_map (
	id	INTEGER NOT NULL AUTO_INCREMENT,
	toilet_id	INTEGER NOT NULL,
	toilet_group_id	INTEGER NOT NULL,
	PRIMARY KEY(id),
	FOREIGN KEY(toilet_id) REFERENCES toilet(id),
	FOREIGN KEY(toilet_group_id) REFERENCES toilet_group(id)
);

INSERT INTO app_state VALUES (1,'システムモード',1,'0=使用できない状態, 1=使用可能な状態','2020-03-02 00:58:54.749426');

INSERT INTO toilet VALUES (11,'4F 男性用トイレ (洋式)',1,0,'2020-03-02 00:58:54.749426');
INSERT INTO toilet VALUES (21,'6F 男性用トイレ (洋式)',1,0,'2020-03-02 00:58:54.749426');
INSERT INTO toilet VALUES (31,'4F 女性用トイレ (和式)',0,0,'2020-03-02 00:58:54.749426');
INSERT INTO toilet VALUES (32,'4F 女性用トイレ (洋式)',0,0,'2020-03-02 00:58:54.749426');
INSERT INTO toilet VALUES (41,'6F 女性用トイレ (和式)',0,0,'2020-03-02 00:58:54.749426');
INSERT INTO toilet VALUES (42,'6F 女性用トイレ (洋式)',0,0,'2020-03-02 00:58:54.749426');

INSERT INTO toilet_group VALUES (10,'4F 男性用トイレ',1,'2020-03-02 00:58:54.749426');
INSERT INTO toilet_group VALUES (20,'6F 男性用トイレ',1,'2020-03-02 00:58:54.749426');
INSERT INTO toilet_group VALUES (30,'4F 女性用トイレ',0,'2020-03-02 00:58:54.749426');
INSERT INTO toilet_group VALUES (40,'6F 女性用トイレ',0,'2020-03-02 00:58:54.749426');

INSERT INTO toilet_group_map VALUES (11,11,10);
INSERT INTO toilet_group_map VALUES (21,21,20);
INSERT INTO toilet_group_map VALUES (31,31,30);
INSERT INTO toilet_group_map VALUES (32,32,30);
INSERT INTO toilet_group_map VALUES (41,41,40);
INSERT INTO toilet_group_map VALUES (42,42,40);
