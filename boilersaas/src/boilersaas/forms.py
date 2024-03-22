from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField,BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError
from flask_babel import lazy_gettext as _l
from .models import User

input_text = "input-text"
input_submit= "submit-button"

class RegistrationForm(FlaskForm):
    fname = StringField('First Name', validators=[DataRequired()],render_kw={"class": input_text})
    email = StringField('Email', validators=[DataRequired(), Email()],render_kw={"class": input_text})
    password = PasswordField('Password', validators=[DataRequired()],render_kw={"class": input_text})
    submit = SubmitField('Register',render_kw={"class": input_submit})
    
    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('An account with this email already exists.')


class RegistrationByInviteForm(FlaskForm):
    invite_code = StringField('',render_kw={"class": "hidden"})
    fname = StringField('First Name', validators=[DataRequired()],render_kw={"class": input_text})
    password = PasswordField('Password', validators=[DataRequired()],render_kw={"class": input_text})
    submit = SubmitField('Register',render_kw={"class": input_submit})
    


class LoginForm(FlaskForm):
    email = StringField(_l('Email'), validators=[DataRequired(), Email()],render_kw={"class": input_text})
    password = PasswordField(_l('Password'), validators=[DataRequired()],render_kw={"class": input_text})
    remember = BooleanField('',default=True,render_kw={"class": "hidden"}) # _l('Remember Me')
    submit = SubmitField(_l('Log In'),render_kw={"class": input_submit})
    
class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired()],render_kw={"class": input_text})
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')],render_kw={"class": input_submit})
    submit = SubmitField('Reset Password',render_kw={"class": input_submit})
    
    
class RequestResetForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()],render_kw={"class": input_text})
    submit = SubmitField('Request Password Reset',render_kw={"class": input_submit})


class InviteForm(FlaskForm):
    email = StringField(_l('Email'), validators=[DataRequired(), Email()],render_kw={"class": input_text})
    submit = SubmitField(_l('Create Invite'),render_kw={"class": input_submit})
