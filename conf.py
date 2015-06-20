class Config(object):
	DEBUG = False
	TESTING = False
	DATABASE = '/var/pyyli/pyyli.db'
	SECRET_KEY = "notsosecret"

class ReleaseConfig(Config):
	# TODO: Setup a default database
	DATABASE = ':memory:'

class DevelopmentConfig(Config):
	DEBUG = True