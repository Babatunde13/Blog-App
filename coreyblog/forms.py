from flask_wtf import FlaskForm
from flask_login import current_user
from wtforms import (
    StringField, PasswordField, SelectField,
    SubmitField, BooleanField, TextAreaField)
from wtforms.validators import (
    DataRequired, Length, 
    Email, EqualTo, ValidationError)
from flask_wtf.file import FileField, FileAllowed
from flask_pagedown.fields import PageDownField
from coreyblog.models import User, Post


class RegistrationForm(FlaskForm):
    username = StringField('Username', 
                            validators=[DataRequired(), 
                                        Length(min=2, max=20)])
    email = StringField('Email', 
                        validators=[DataRequired(),
                                 Email()])
    password = PasswordField('Password', 
                            validators=[DataRequired(),
                                        Length(min=6, max=14)])
    confirm_password = PasswordField('confirm password',
                                    validators=[DataRequired(),
                                                EqualTo('password')])
    submit = SubmitField('Sign up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username taken. Please choose another.')
                                
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email taken. Please choose another.')

class LoginForm(FlaskForm):
    email = StringField('Email', 
                        validators=[DataRequired(),
                                 Email()])
    password = PasswordField('Password', 
                            validators=[DataRequired()])
    remember = BooleanField('Remember me')
    submit = SubmitField('Log in')

class UpdateAccountForm(FlaskForm):
    username = StringField('Username', 
                            validators=[DataRequired(), 
                                        Length(min=2, max=20)])
    email = StringField('Email', 
                        validators=[DataRequired(),
                                 Email()])
                
    picture = FileField('Update Profile Picture', 
                        validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Update')

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('Username taken. Please choose another.')
    
    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('Email taken. Please choose another.')

class PostForm(FlaskForm):

    title = StringField('Blog Title', 
                            validators=[DataRequired(), 
                                        Length(min=2, max=30)])
    content = PageDownField('Body', 
                        validators=[DataRequired()])
                
    submit = SubmitField('Create')

class UpdatePostForm(FlaskForm):

    title = StringField('Blog Title', 
                            validators=[DataRequired(), 
                                        Length(min=2, max=30)])
    content = PageDownField('Body', 
                        validators=[DataRequired()])
                
    submit = SubmitField('Update')

class RequestResetForm(FlaskForm):
    email = StringField('Email', 
                        validators=[DataRequired(),
                                 Email()])    
    submit = SubmitField('Reset Password')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError('There is no account for that email')
       
class ResetPasswordForm(FlaskForm):

    password = PasswordField('Password', 
                            validators=[DataRequired(),
                                        Length(min=6, max=14)])
    confirm_password = PasswordField('confirm password',
                                    validators=[DataRequired(),
                                                EqualTo('password')])
    submit = SubmitField('Reset Passowrd')

class CommentForm(FlaskForm):
    body = PageDownField('', validators=[DataRequired()])
    submit = SubmitField('Submit')
