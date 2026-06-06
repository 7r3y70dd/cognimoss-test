from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email, Length

class UserForm(FlaskForm):
    """Example user form - Hello World style"""
    username = StringField(
        'Username',
        validators=[
            DataRequired(),
            Length(min=3, max=80, message='Username must be between 3 and 80 characters')
        ]
    )
    email = StringField(
        'Email',
        validators=[
            DataRequired(),
            Email(message='Invalid email address')
        ]
    )
    submit = SubmitField('Create User')

class PostForm(FlaskForm):
    """Example post form - Hello World style"""
    title = StringField(
        'Title',
        validators=[
            DataRequired(),
            Length(min=1, max=200, message='Title must be between 1 and 200 characters')
        ]
    )
    content = TextAreaField(
        'Content',
        validators=[
            DataRequired(),
            Length(min=1, message='Content cannot be empty')
        ]
    )
    submit = SubmitField('Create Post')
