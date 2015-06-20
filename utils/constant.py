# -*- coding: utf-8 -*-

def constant(f):
	def fset(self, value):
		raise SyntaxError # We dont want to be able to modify constants. 
	def fget(self):
		return f()

	return property(fget, fset)