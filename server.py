from flask import Flask, render_template, render_template_string, g, session, Response, redirect, request, url_for, flash, escape, jsonify
from functools import wraps
from socket import gethostname
import sqlite3
import locale
import random
import string
import os
import datetime
import json
from db import query, modify, init_db

locale.setlocale(locale.LC_ALL, 'de_DE.utf8')

app = Flask(__name__)

app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True
app.add_template_global(random.randint, name='randint')
app.add_template_global(datetime, name='datetime')
app.add_template_global(gethostname, name='gethostname')
app.add_template_global(min, name='min')
app.add_template_global(max, name='max')

config = app.config

def load_config_file():
	config.from_pyfile('config.py.example', silent=True)
	config.from_pyfile('config.py', silent=True)
	if config['DEBUG']:
		app.jinja_env.auto_reload = True
	if not config['SECRET_KEY'] or not len(config['SECRET_KEY']) > 32:
		config['SECRET_KEY'] = os.urandom(128)
load_config_file()
init_db(app)

def date_json_handler(obj):
	return obj.isoformat() if hasattr(obj, 'isoformat') else obj

@app.template_global()
def isadmin(*args):
	return session.get('loggedin', False)

admin_endpoints = []
def admin_required(func):
	admin_endpoints.append(func.__name__)
	@wraps(func)
	def decorator(*args, **kwargs):
		if not isadmin():
			flash('You need to be logged in to do that!')
			return redirect(url_for('login', ref=request.url))

		else:
			return func(*args, **kwargs)
	return decorator

csrf_endpoints = []
def csrf_protect(func):
	csrf_endpoints.append(func.__name__)
	@wraps(func)
	def decorator(*args, **kwargs):
		if '_csrf_token' in request.values:
			token = request.values['_csrf_token']
		elif request.get_json() and ('_csrf_token' in request.get_json()):
			token = request.get_json()['_csrf_token']
		else:
			token = None
		if app.testing:
			return func(*args, **kwargs)
		if not ('_csrf_token' in session) or (session['_csrf_token'] != token ) or not token:
			return 'csrf test failed', 403
		else:
			return func(*args, **kwargs)
	return decorator

@app.url_defaults
def csrf_inject(endpoint, values):
	if not '_csrf_token' in session:
		session['_csrf_token'] = ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(64))
	if endpoint not in csrf_endpoints or not session.get('_csrf_token'):
		return
	values['_csrf_token'] = session['_csrf_token']

app.jinja_env.globals['navbar'] = []
# iconlib can be 'bootstrap'
# ( see: http://getbootstrap.com/components/#glyphicons )
# or 'fa'
# ( see: http://fontawesome.io/icons/ )
def register_navbar(name, iconlib='bootstrap', icon=None, visible=False):
	def wrapper(func):
		endpoint = func.__name__
		app.jinja_env.globals['navbar'].append((endpoint, name, iconlib, icon, visible))
		return func
	return wrapper

@app.template_filter("tracker")
def trackerJoinPos(id):
	return query(
		"""SELECT * FROM
			(SELECT tracker.*, position.bat, position.lon, position.lat, position.time FROM tracker JOIN position ON tracker.id = position.tracker_id WHERE (tracker.id = ?) OR (? = -1)  ORDER BY position.time DESC) t
		GROUP BY t.id"""
		, int(id), int(id), flatten=True)

admin_endpoints = []
def admin_required(func):
	admin_endpoints.append(func.__name__)
	@wraps(func)
	def decorator(*args, **kwargs):
		if not isadmin():
			flash('You need to be logged in to do that!')
			return redirect(url_for('login', ref=request.url))

		else:
			return func(*args, **kwargs)
	return decorator

csrf_endpoints = []
def csrf_protect(func):
	csrf_endpoints.append(func.__name__)
	@wraps(func)
	def decorator(*args, **kwargs):
		if '_csrf_token' in request.values:
			token = request.values['_csrf_token']
		elif request.get_json() and ('_csrf_token' in request.get_json()):
			token = request.get_json()['_csrf_token']
		else:
			token = None
		if app.testing:
			return func(*args, **kwargs)
		if not ('_csrf_token' in session) or (session['_csrf_token'] != token ) or not token:
			return 'csrf test failed', 403
		else:
			return func(*args, **kwargs)
	return decorator

@app.url_defaults
def csrf_inject(endpoint, values):
	if not '_csrf_token' in session:
		session['_csrf_token'] = ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(64))
	if endpoint not in csrf_endpoints or not session.get('_csrf_token'):
		return
	values['_csrf_token'] = session['_csrf_token']

@app.route("/tracker/history")
def tracker_history():
	id = request.values.get('id')
	start = int(request.values.get('start', 0))
	until = int(request.values.get('until', datetime.datetime.now().timestamp()))
	output = []
	for i in query("SELECT id, lon, lat, CAST(time as INT) AS time, rssi, snr FROM `position` WHERE tracker_id = ? ORDER BY time", id):
		if i['time'] >= start and i['time'] <= until:
			output.append(i)
	return jsonify(output)

@app.route("/login", methods=['GET', 'POST'])
def login():
	if request.method == 'GET':
		return render_template('login.html')
	user, pw = request.form.get('user'), request.form.get('password')
	if not valid_credentials(user, pw):
		flash('Login failed!')
		return render_template('login.html')
	session['user'] = user
	session['loggedin'] = True
	session['logindate'] = datetime.datetime.now()
	return redirect(request.values.get('ref', url_for('index')))

def valid_credentials(user, pw):
	return True
	from ldap3 import Server, Connection

	if not user or not pw:
		return False

	bindstring = config['LDAP_BINDSTRING_USER'].format(user)
	conn = Connection(Server(config['LDAP_SERVER'], use_ssl=True), bindstring, pw)
	if not conn.bind():
		return False
	conn.search(config['LDAP_GROUPS'], config['LDAP_GROUP_FILTER'].format('admin'), attributes=[config['LDAP_GROUP_MEMBERS_ATTRIBUTE']])
	members = conn.response[0]['attributes'][config['LDAP_GROUP_MEMBERS_ATTRIBUTE']]
	conn.unbind()
	return user in members

@app.route("/logout")
def logout():
	session.pop('user', None)
	session.pop('logindate', None)
	session.pop('loggedin', None)
	return redirect(request.values.get('ref', url_for('index')))

@register_navbar('Overview', icon='globe', iconlib='fa', visible=True)
@app.route("/")
def index():
	groupfilter = request.values.get('groupfilter', '')
	return render_template('overview.html',
			pos = query('SELECT * FROM `position` GROUP BY tracker_id ORDER BY time'),
			tracker = query('SELECT * FROM `tracker` WHERE `group` = ? OR ? == ""', groupfilter, groupfilter),
			groupfilter = groupfilter
		)

@register_navbar('Tracker', icon='list', iconlib='fa', visible=True)
@app.route("/tracker")
@app.route("/tracker/<int:id>")
def tracker(id=None):
	if id:
		timeslider=query('SELECT min(time) as start, max(time) as until FROM `position` WHERE tracker_id = ?', id)
		if len(timeslider) == 0:
			timeslider = {'start': datetime.datetime.now(), 'until': datetime.datetime.now()}
		else:
			timeslider = timeslider[0]
		if not timeslider['until']:
			timeslider['until'] = 0
		if not timeslider['start']:
			timeslider['start'] = 0
		return render_template('trackerdetails.html',
				tracker=trackerJoinPos(id),
				positions=query('SELECT * FROM `position` WHERE tracker_id=? ORDER BY time', id),
				groups=query('SELECT distinct(`group`) FROM `tracker`'),
				timeslider=timeslider)
	else:
		return render_template('trackerlist.html', tracker=trackerJoinPos(-1))

@app.route("/tracker/<int:id>/edit", methods=['POST'])
def tracker_edit(id):
	name = request.values.get('name')
	info = request.values.get('info')
	group = request.values.get('group')
	if not id or (not name and not info and not group):
		return 'Bad Request', 400
	if name:
		query('UPDATE `tracker` SET name = ? WHERE id = ?', name, id)
	if info:
		query('UPDATE `tracker` SET info = ? WHERE id = ?', info, id)
	if group:
		query('UPDATE `tracker` SET `group` = ? WHERE id = ?', group, id)
	flash("saved")
	return tracker(id)


@register_navbar('Probes', icon='map-marker', iconlib='fa', visible=True)
@app.route("/probes")
def probes():
	try:
		return render_template('probes.html', lasttrackerid=query("SELECT id FROM `position` ORDER BY id DESC LIMIT 1")['id'])
	except:
		return render_template('probes.html', lasttrackerid=-1)

import api
