from flask import g
from constant import constant

class Link(object):
	@constant
	def TABLE_NAME():
		return "posts"
	

	def __init__(self, title, url, description, posted_on):
		self.title = title
		self.url = url
		self.description = description
		self.posted_on = posted_on
		self.tags = []
		self.tags_id = []

	@staticmethod
	def from_id(id):
		cur = g.db.cursor()
		cur.execute("""SELECT posts.id, title, url, description, posted_on, GROUP_CONCAT(tag_id) AS tags_id, GROUP_CONCAT(tag) AS tags
			           FROM posts 
			           LEFT JOIN tags_for_post ON post_id = posts.id 
			                                  AND posts.id = ?
			           LEFT JOIN tags ON tags.id = tag_id""", (id,))
		return cur.fetchone()

	@staticmethod
	def delete_from_id(id):
		cur = g.db.cursor()
		cur.execute("DELETE FROM posts WHERE id = ?", (id,))
		g.db.commit()

	@staticmethod
	def get_posts(start, count):
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
			link = Link(row['title'], row['url'], row['description'], row['posted_on'])
			splitted_ids = row['tag_id'].split(',')
			splitted_tag = row['tag'].split(',')
			for i in range(0, len(splitted_ids)):
				link.add_tag(splitted_ids[i], splitted_tag[i])

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
			cur.execute("INSERT OR IGNORE INTO tags (tag) VALUES (?)", (val,))
			tup = (post_id, val)
			cur.execute("INSERT INTO tags_for_post(post_id, tag_id) VALUES(?, (SELECT id FROM tags WHERE tag = ?))", tup)

		g.db.commit()

	def add_tag(self, tag_id, tag):
		self.tags_id.append(tag_id)
		self.tags.append(tag)