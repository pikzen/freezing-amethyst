# -*- coding: utf-8 -*-

from flask import g
from constant import constant
from collections import namedtuple
import markdown

class Link(object):
	####################################################
	####################################################
	#
	# Properties & Attributes
	#
	####################################################
	####################################################
	# INDEV: Declare everything as properties ? This is long, but ensures consistency
	@property
	def id(self):
		"""This link's ID in the database"""
		return self._id
	
	@id.setter
	def id(self, value):
		"""Sets this link's ID

		Parameters
		value -- New value of the ID
		"""
		self._id = value

	def __init__(self, title="", url="", description="", posted_on=0):
		"""Create a link.

		Parameters:
		title -- Title of the Link (default "")
		url   -- URL to which this Link points (default "", does not check validity)
		description -- Description of the Link (default "")
		posted_on -- Timestamp at which this link was posted (default 0 (Jan 1st 1970))
		"""
		self.title = title
		self.url = url
		self.description = description
		self.posted_on = posted_on
		self.tags = []
		self.id = None

	def _set_tags(self, taglist="", tag_ids=""):
		"""Reads a series of tags and IDs and writes them to the `tags` and `tags_id` attributes

		Parameters
		taglist -- A string representing a list of tags, separated by ','
		tag_ids -- A string representing a list of tag IDs. They should map accurately to `taglist`

		Throws
		IndexError -- If once trimmed and splitted on ',' there is not the same amount of tags and tag IDs
		"""
		splitted_tag = taglist.strip().split(',')
		splitted_id  = tag_ids.strip().split(',')
		if len(splitted_tag) != len(splitted_id):
			raise IndexError('The amount of tags (%d) differs from the amount of IDs (%d)' % len(splitted_tag), len(splitted_id))

		Tag = namedtuple('Tag', ['text', 'id'])
		for x in xrange(0,len(splitted_tag)):
			self.tags.append(Tag(text=splitted_tag[x], id=splitted_id[x]))

	def set_tags(self, taglist=""):
		"""Reads a series of tags and writes them to the `tags` attribute. This method does NOT set the IDs.
		Only use if if you're constructing a link manually

		Parameters
		taglist -- List of tags, separated by ','
		"""
		splitted_tag = taglist.strip().split(',')

		Tag = namedtuple('Tag', ['text', 'id'])
		for x in xrange(0, len(splitted_tag)):
			self.tags.append(Tag(text=splitted_tag[x], id=-1))

	@staticmethod
	def from_id(id):
		"""Retrieve a single link from its ID

		Parameters
		id -- ID of the link in the database
		"""
		cur = g.db.cursor()
		cur.execute("""SELECT posts.id, title, url, description, posted_on, GROUP_CONCAT(tag_id) AS tags_id, GROUP_CONCAT(tag) AS tags
			             FROM posts 
			             LEFT JOIN tags_for_post ON post_id = posts.id 
			                                    AND posts.id = ?
			             LEFT JOIN tags ON tags.id = tag_id""", (id,))
		row = cur.fetchone()
		
		link = Link(row['title'], row['url'], row['description'], row['posted_on'])
		link._set_tags(row['tags'], row['tags_id'])
		link.id = row['id']
		return link

	@staticmethod
	def delete_from_id(id):
		cur = g.db.cursor()
		cur.execute("DELETE FROM posts WHERE id = ?", (id,))
		g.db.commit()

	@staticmethod
	def get_posts(start, count):
		"""Retrieve `count` links starting at the `start`ieth last post

		Parameters
		start -- Amount of links to skip before retrieving
		count -- Amount of links to retrieve
		"""
		# TODO: Handle the parsing of unexpected inputs (plugins ?)
		
		markdown_ext  = ('markdown.extensions.tables', 'markdown.extensions.fenced_code', 'markdown.extensions.nl2br', 'markdown_checklist.extension')

		cur = g.db.cursor()
		cur.execute("""SELECT posts.id, title, url, description, posted_on, GROUP_CONCAT(tag_id) AS tag_id, GROUP_CONCAT(tag) AS tag
		           FROM posts 
		           LEFT JOIN tags_for_post ON post_id = posts.id 
		           LEFT JOIN tags ON tags.id = tag_id
		           GROUP BY posts.id 
		           ORDER BY posts.id DESC
		           LIMIT ?, ?;""", (start, count))
		
		all = cur.fetchall()
		for row in all:
			marked_desc = markdown.markdown(row['description'], markdown_ext)
			link = Link(row['title'], row['url'], marked_desc, row['posted_on'])
			if (row['tag'] is not None and row['tag_id'] is not None):
				link._set_tags(row['tag'], row['tag_id'])
			link.id = row['id']
			yield link

	def write(self):
		'''
		Insert this Link into the database
		'''
		post = (self.title, self.url, self.description, self.posted_on)
		cur = g.db.cursor()
		cur.execute("INSERT INTO posts (title, url, description, posted_on) VALUES (?, ?, ?, ?);", post)
		post_id = cur.lastrowid
		
		# Map tags to the post
		for val in self.tags:
			cur.execute("INSERT OR IGNORE INTO tags (tag) VALUES (?)", (val.text,))
			tup = (post_id, val.id)
			cur.execute("INSERT INTO tags_for_post(post_id, tag_id) VALUES(?, (SELECT id FROM tags WHERE tag = ?))", tup)

		g.db.commit()

	def add_tag(self, tag_id, tag):
		self.tags_id.append(tag_id)
		self.tags.append(tag)