# -*- coding: utf-8 -*-

# Python is seriously retarded and doesn't look for modules in folders
import sys
sys.path.append("utils")
sys.path.append("src/forms")
sys.path.append("src/models")

from flask import Flask, render_template, request, url_for, g, redirect, flash, make_response
from dotaccessdict import DotAccessDict
from contextlib import closing
from link import Link
import forms
import sqlite3, os, time, markdown, bleach
import gettext

app = Flask(__name__) # THAT is me being retarded.

# TODO: find out how to load that. Really.
Config = DotAccessDict();
Config.name = "Pyyli - Default Name"
Config.theme = "default/"
Config.base_stylesheet = "style.css"
Config.source_page = "http://feula.me/pyyli"
Config.lang = "en-EN"

def setup_i18n():
	'''
	Configures gettext to use the appropriate domain & path, then
	registers `translate` and `i18n` as filters for Jinja
	'''
	gettext.bindtextdomain('amethyst', 'lang/')
	gettext.textdomain('amethyst')
	app.jinja_env.filters['translate'] = gettext.gettext
	app.jinja_env.filters['i18n']      = gettext.gettext

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
	Inserts the (sanitized) data into the database. The description is parsed as Markdown
	and saved in HTML, while allowing a few attributes
	------------------
	NOTE: `request` is global and is implicitly passed as a parameter. It would probably
	be better to pass the data as a param for testing purposes.
	------------------
	NOTE: Maybe save the raw data as Markdown and only render it once needed ? Makes editing 
	posts easier, but puts more load on the server.
	'''
	allowed_tags = ("p", "h1", "h2", "h3", "h4", "h5", "h6", "b", "em", "small", "code", "i", "pre", "strong", "table", 'thead', 'tbody', 'th', 'tr', 'td', 'ul', 'ol', 'li', 'input')
	allowed_attrs = ('type', 'disabled', 'checked')

	title = bleach.clean(request.form['title'])
	desc  = bleach.clean(request.form['desc'], tags=allowed_tags, attributes=allowed_attrs)
	url   = bleach.clean(request.form["url"])
	timestamp  = time.time()
	tags = []

	post = Link(title, url, desc, timestamp)
	post.set_tags(bleach.clean(request.form['tags']))

	post.write()
	return redirect("/")

@app.route('/')
@app.route('/links/<int:start>')
def index(start=None):
	'''
	ROUTE : localhost/
	Displays an unfiltered list of links, ranging from `start` (0 if not set) to `Config.max_links_per_page`.
	--------------------
	Parameters:
		- `start`: Amount of links to skip (i.e. ignore the `start`ieth first posts)
	'''
	start = 0 if start is None else start

	links = Link.get_posts(start, 20)
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

@app.route("/delete_link/<int:id>", methods=["GET","POST"])
def delete_link(id):
	form = forms.DeleteLinkForm()
	link = Link.from_id(id)
	if link is None:
		return redirect('/404')

	if request.method == "GET":
		return render_template(Config.theme + "delete.jinja", app=Config, link=link, form=form)
	else:
		Link.delete_from_id(id)
		return redirect("/")

@app.route("/edit_link/<int:id>", methods=["GET", "POST"])
def edit_link(id):
	form = forms.SubmitLinkForm()
	link = Link.from_id(id, format=False)
	if link is None:
		return redirect('/404')

	if form.validate_on_submit():
		pass

	for field, error in form.errors.iteritems():
		for err in error:
			flash(err)

	taglist = []
	for tag in link.tags:
		taglist.append(tag.text)

	link.tags_as_string = ','.join(taglist)

	return render_template(Config.theme + "edit.jinja", app=Config, link=link, form=form)

@app.route("/404", methods=["GET"])
def error_404():
	response = (render_template(Config.theme + "404.jinja", app=Config), 404, ())
	return make_response(response)

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