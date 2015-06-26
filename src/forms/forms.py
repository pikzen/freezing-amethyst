from flask_wtf import Form
from wtforms import StringField, TextAreaField
from wtforms.validators import Required, Optional, URL

class SubmitLinkForm(Form):
	title = StringField('Title', validators=[Required()])
	url   = StringField('URL',   validators=[Optional()])
	desc  = TextAreaField('Description',  validators=[Optional()])
	tags  = StringField('Tags',  validators=[Optional()])
	target = "post"

class DeleteLinkForm(Form):
	pass