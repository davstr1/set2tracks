from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField,BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError
from flask_babel import _
from .models import User

input_text = "input-text"
input_submit= "submit-button"

class RegistrationForm(FlaskForm):
    fname = StringField(_('First Name'), validators=[DataRequired()],render_kw={"class": input_text})
    email = StringField(_('Email'), validators=[DataRequired(), Email()],render_kw={"class": input_text})
    password = PasswordField(_('Password'), validators=[DataRequired()],render_kw={"class": input_text})
    submit = SubmitField(_('Register'),render_kw={"class": input_submit})
    
    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError(_('An account with this email already exists.'))


class RegistrationByInviteForm(FlaskForm):
    invite_code = StringField('',render_kw={"class": "hidden"})
    fname = StringField(_('First Name'), validators=[DataRequired()],render_kw={"class": input_text})
    password = PasswordField(_('Password'), validators=[DataRequired()],render_kw={"class": input_text})
    submit = SubmitField(_('Register'),render_kw={"class": input_submit})
    


class LoginForm(FlaskForm):
    email = StringField(_('Email'), validators=[DataRequired(), Email()],render_kw={"class": input_text})
    password = PasswordField(_('Password'), validators=[DataRequired()],render_kw={"class": input_text})
    remember = BooleanField('',default=True,render_kw={"class": "hidden"}) # _('Remember Me')
    submit = SubmitField(_('Log In'),render_kw={"class": input_submit})
    
class ResetPasswordForm(FlaskForm):
    password = PasswordField(_('New Password'), validators=[DataRequired()],render_kw={"class": input_text})
    confirm_password = PasswordField(_('Confirm Password'),
                                     validators=[DataRequired(), EqualTo('password')],render_kw={"class": input_submit})
    submit = SubmitField(_('Reset Password'),render_kw={"class": input_submit})
    
    
class RequestResetForm(FlaskForm):
    email = StringField(_('Email'), validators=[DataRequired(), Email()],render_kw={"class": input_text})
    submit = SubmitField(_('Request Password Reset'),render_kw={"class": input_submit})


class InviteForm(FlaskForm):
    email = StringField(_('Email'), validators=[DataRequired(), Email()],render_kw={"class": input_text})
    submit = SubmitField(_('Create Invite'),render_kw={"class": input_submit})
