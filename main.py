# -*- coding: utf-8 -*-

# Python is seriously retarded and doesn't look for modules in folders
import sys
sys.path.append("utils")
sys.path.append("src/forms")
sys.path.append("src/models")

from flask import Flask, render_template, request, url_for, g, redirect, flash
from dotaccessdict import DotAccessDict
from contextlib import closing
from link import Link
import forms
import sqlite3, os, time, markdown, bleach

app = Flask(__name__) # THAT is me being retarded.

# TODO: find out how to load that. Really.
Config = DotAccessDict();
Config.name = "Pyyli - Default Name"
Config.theme = "default/"
Config.base_stylesheet = "style.css"
Config.source_page = "http://feula.me/pyyli";

def connect_db():
	'''
	Connect to the SQLite database using the loaded config.
	Sets up SQLite to use `sqlite3.Row` when returning the data so we can access them through their column name.
	'''
	con = sqlite3.connect(app.config['DATABASE'])
	con.row_factory = sqlite3.Row
	return con

def init_db():
	'''
	Runs init.sql to create the database tables.
	'''
	with connect_db() as db:
		with app.open_resource("resources/init.sql", mode="r") as schema:
			db.cursor().executescript(schema.read())
	db.commit()
	db.close()

@app.before_request
def before_request():
	g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
	db = getattr(g, 'db', None)
	if db is not None:
		db.close()

def post_link():
	'''
	Performed when a link is POSTed.
	Inserts the (sanitized) data into the database. The description is parsed as Markdown.
	'''
	# TODO: Handle the parsing of unexpected inputs (plugins ?)
	allowed_tags = ("p", "h1", "h2", "h3", "h4", "h5", "h6", "b", "em", "small", "code", "i", "pre", "strong", "table", 'thead', 'tbody', 'th', 'tr', 'td', 'ul', 'ol', 'li', 'input')
	allowed_attrs = ('type', 'disabled', 'checked')

	title = bleach.clean(request.form['title'])
	desc  = bleach.clean(markdown.markdown(request.form['desc'], ['markdown.extensions.tables', 'markdown.extensions.fenced_code', 'markdown.extensions.nl2br', 'markdown_checklist.extension']), tags=allowed_tags, attributes=allowed_attrs)
	url   = bleach.clean(request.form["url"])
	timestamp  = time.time()
	tags = []

	post = Link(title, url, desc, timestamp)
	for val in request.form["tags"].split(" "):
		post.add_tag(0, bleach.clean(val))

	post.write()
	return redirect("/")

@app.route('/')
def index():
	links = Link.get_posts(0, 20)
	return render_template(Config.theme + "links.jinja", app=Config, links=links)

@app.route('/install', methods=['GET', 'POST'])
def install():
	if request.method == 'GET':
		if os.path.isfile("installed.lock"):
			redirect("/")
		return render_template(Config.theme + "install.jinja", app=Config)
	else:
		init_db();
		return render_template(Config.theme + "install.jinja", app=Config, success=True)

@app.route("/post", methods=["GET", "POST"])	
def post():
	form = forms.SubmitLinkForm()
	if form.validate_on_submit():
		return post_link()
	
	for field, error in form.errors.iteritems():
		for err in error:
			flash(err)
	return render_template(Config.theme + "post.jinja", app=Config, form=form)

@app.route("/delete_link/<id>", methods=["GET","POST"])
def delete_link(id):
	if request.method == "GET":
		return render_template(Config.theme + "delete.jinja", app=Config, link=Link.from_id(id))
	else:
		Link.delete_from_id(id)
		return redirect("/")

#       ## ##
###     ## ##
####    ## ##
###     ## ##
#       ## ##
# Entry point
if __name__=='__main__':
	app.config.from_object('conf.DevelopmentConfig')
	app.run(debug=True)
	
	if not os.path.isfile("installed.lock"):
		redirect("/install")