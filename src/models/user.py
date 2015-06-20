from werkzeug.security import generate_password_hash, check_password_hash
from constant import constant

class User(object):
	'''
	Represents a single user
	'''
	@constant
	def PERMISSION_ALL():
		return 16384;

	def __init__(self, name, password, permissions):
		self.username = name
		self.set_password(password)
		self.decode_permissions(permissions)

	def set_password(self, password):
		self.password_hash = generate_password_hash(password)

	def check_password(self, password):
		return check_password_hash(self.pw_hash, password)

	def decode_permissions(self, permissions):
		# TODO: granular permissions ? only grant add rights, or delete rights, etc.
		self.permissions = permissions