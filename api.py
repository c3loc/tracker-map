from server import *

import hashlib
import base64
import struct

from util import *

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

@app.route("/gateway/push_lora")
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

@app.route("/gateway/push_ulogger/<id>/<apikey>/client/index.php", methods=['POST'])
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
