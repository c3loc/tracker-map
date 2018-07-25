from server import *

def addposition(lon, lat, bat, trackerid, gateway, time=None, rssi=0, snr=0):
	if not time:
		time = datetime.datetime.now().timestamp()
	if not len(query('SELECT id FROM `tracker` WHERE id = ?', trackerid)) > 0:
		query('INSERT INTO `tracker` (id, name, info) VALUES (?, ?, ?)', trackerid, trackerid, '')
	if not len(query('SELECT id FROM `gateway` WHERE name = ?', gateway)) > 0:
		query('INSERT INTO `gateway` (name, info, lon, lat) VALUES (?, ?, ?, ?)', gateway, '', 0, 0)
	query('INSERT INTO `position` (time, tracker_id, lat, lon, bat, gateway, rssi, snr) VALUES (CAST(? as INT), ?, ?, ?, ?, ?, ?, ?)', time, trackerid, lat, lon, bat, gateway, rssi, snr)
	pass
