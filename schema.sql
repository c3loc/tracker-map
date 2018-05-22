PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;

CREATE TABLE IF NOT EXISTS 'position' (
	id		integer primary key autoincrement,
	time		datetime,
	tracker_id	integer NOT NULL,
	lon		float NOT NULL,
	lat		float NOT NULL,
	bat		integer NOT NULL,
	gateway		varchar(255) NOT NULL,
	snr		float NOT NULL,
	rssi		integer NOT NULL
);

CREATE TABLE IF NOT EXISTS 'tracker' (
	id		integer NOT NULL,
	name		varchar(255),
	`group`		varchar(255) DEFAULT "" NOT NULL,
	info		text DEFAULT "" NOT NULL
);

CREATE TABLE IF NOT EXISTS 'gateway' (
	id		integer primary key autoincrement,
	name		varchar(255),
	info		text DEFAULT "" NOT NULL,
	lon		float NOT NULL,
	lat		float NOT NULL
);

COMMIT
