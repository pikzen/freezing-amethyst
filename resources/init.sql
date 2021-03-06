CREATE TABLE IF NOT EXISTS posts (
	id          INTEGER PRIMARY KEY AUTOINCREMENT,
	title       TEXT NOT NULL,
	url         TEXT NOT NULL,
	description TEXT,
	posted_on   TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS tags (
	id  INTEGER PRIMARY KEY AUTOINCREMENT,
	tag TEXT(40) UNIQUE
);

CREATE TABLE IF NOT EXISTS tags_for_post (
	id  INTEGER PRIMARY KEY AUTOINCREMENT,
	post_id INTEGER,
	tag_id  INTEGER,
	FOREIGN KEY (post_id) REFERENCES posts(id),
	FOREIGN KEY (tag_id)  REFERENCES tags(id)
);