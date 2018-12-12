from flask import g, request
import sqlite3
import server


def init_db(app):
	config = server.config
	db = sqlite3.connect(config['SQLITE_DB'])
	cur = db.cursor()
	with app.open_resource('schema.sql', mode='r') as schema_file:
		cur.executescript(schema_file.read())
	db.commit()
	db.close()
	app.teardown_request(commit_db)
	app.teardown_appcontext(close_db)

def get_dbcursor():
	if 'db' not in g:
		g.db = sqlite3.connect(server.config['SQLITE_DB'], detect_types=sqlite3.PARSE_DECLTYPES)
		g.db.isolation_level = None
	if not hasattr(request, 'db'):
		request.db = g.db.cursor()
	return request.db

def commit_db(*args):
	if hasattr(request, 'db'):
		request.db.close()
		g.db.commit()

def close_db(*args):
	if 'db' in g:
		g.db.close()
		del g.db

def query(operation, *params, delim="sep", flatten=False):
	cur = get_dbcursor()
	cur.execute(operation, params)
	rows = []
	rows = cur.fetchall()
	res = []
	for row in rows:
		res.append({})
		ptr = res[-1]
		for col, desc in zip(row, cur.description):
			name = desc[0].split('.')[-1].split(':')[0]
			if name == delim:
				ptr = res[-1][col] = {}
				continue
			if type(col) == str:
				col = col.replace('\\n', '\n').replace('\\r', '\r')
			ptr[name] = col
	if flatten and len(res) == 1:
		return res[0]
	return res

def modify(operation, *params):
	cur = get_dbcursor()
	cur.execute(operation, params)
	return cur.lastrowid
