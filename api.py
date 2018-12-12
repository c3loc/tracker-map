from server import *

import hashlib
import base64
import struct

def api_token_required(func):
	@wraps(func)
	def decorator(*args, **kwargs):
		if 'apikey' in request.values:
			token = request.values['apikey']
		elif request.get_json() and ('apikey' in request.get_json()):
			token = request.get_json()['apikey']
		elif 'apikey' in kwargs:
			token = kwargs['apikey']
			del(kwargs['apikey'])
		else:
			token = None
		
		if not token == config.get('API_KEY', [None]):
			return 'Permission denied', 403
		else:
			return func(*args, **kwargs)
	return decorator

@app.route("/api/gateway/push_lora")
@api_token_required
def gateway_push_lora():
	data = request.json.get('data')
	gateway = request.json.get('gateway')
	if not data or not gateway:
		return 'Bad Request', 400
	data = base64.b64decode(data)
	lat, lon, bat, mac = struct.unpack("<ffBL", data)
	addposition(lon, lat, bat, mac, gateway, snr=request.json.get('snr'), rssi=request.json.get('rssi'))
	return 'OK'

@app.route("/api/gateway/push_ulogger/<id>/<apikey>/client/index.php", methods=['POST'])
@api_token_required
def gateway_push_ulogger(id):
	action = request.values.get('action')
	if action == 'auth':
		user = request.values.get('user')
		password = request.values.get('pass')
		return jsonify({'error': False})
	elif action == 'addtrack':
		track = request.values.get('track')
		return jsonify({'error': False, 'trackid': 1})
	elif action == 'addpos':
		lon = request.values.get('lon')
		lat = request.values.get('lat')
		time = int(request.values.get('time'))
		accuracy = float(request.values.get('accuracy'))
		altitude = float(request.values.get('altitude', -1))
		provider = request.values.get('provider')
		addposition(lon, lat, 0, id, 'Android', time=time)
		return jsonify({'error': False})
	return 'ok'

@app.route("/api/tracker/<int:trackerid>/probes")
@app.route("/api//tracker/<int:trackerid>/probes/<int:after>")
@app.route("/api/tracker/probes")
@app.route("/api/tracker/probes/<int:after>")
def api_tracker_probes(trackerid=-1, after=-1):
	output = []
	for i in query("SELECT id, lon, lat, CAST(time as INT) AS time, rssi, snr, tracker_id, bat FROM `position` WHERE (tracker_id = ? OR ? = -1) AND (id > ?) ORDER BY id LIMIT 5000", trackerid, trackerid, after):
		output.append(i)
	return jsonify(output)

@app.route("/api/tracker/<int:id>")
@app.route("/api/tracker")
def api_tracker(id=-1):
	return jsonify(query(
		"""SELECT * FROM
			(SELECT tracker.*, position.bat, position.lon, position.lat, position.time FROM tracker JOIN position ON tracker.id = position.tracker_id WHERE (tracker.id = ?) OR (? = -1)  ORDER BY position.time ASC) t
		GROUP BY t.id"""
		, id, id))

def addposition(lon, lat, bat, trackerid, gateway, time=None, rssi=0, snr=0):
	if not time:
		time = datetime.datetime.now().timestamp()
	if not len(query('SELECT id FROM `tracker` WHERE id = ?', trackerid)) > 0:
		query('INSERT INTO `tracker` (id, name, info) VALUES (?, ?, ?)', trackerid, trackerid, '')
	if not len(query('SELECT id FROM `gateway` WHERE name = ?', gateway)) > 0:
		query('INSERT INTO `gateway` (name, info, lon, lat) VALUES (?, ?, ?, ?)', gateway, '', 0, 0)
	query('INSERT INTO `position` (time, tracker_id, lat, lon, bat, gateway, rssi, snr) VALUES (CAST(? as INT), ?, ?, ?, ?, ?, ?, ?)', time, trackerid, lat, lon, bat, gateway, rssi, snr)
	pass
