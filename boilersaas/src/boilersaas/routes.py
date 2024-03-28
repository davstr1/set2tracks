
import string
from flask import render_template, flash, redirect, url_for,request, current_app as app
from flask_login import current_user, login_user, logout_user
from .utils.db import db
from .types import UserType, UserConnectMethod
from .utils.mail import send_email
from . import bp
from .models import User, Invite
from .forms import InviteForm, RegistrationByInviteForm, RegistrationForm,LoginForm,RequestResetForm,ResetPasswordForm
from werkzeug.security import generate_password_hash,check_password_hash
from flask_babel import _
import secrets

@app.context_processor
def inject_translations():
    return dict(_=_,page_title='TODO : page_title',app_name='TODO : app_name')

@bp.route('/user')
def user():
    return _('hello world!')

@bp.route('/register', methods=['GET', 'POST'])
def register():

    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard')) 
    
    if not app.config.get('SIGNUP_OPTIONS')['allow_site']:
        flash(_('Registration is not currently allowed.'), 'error')
        return redirect(url_for('main.index'))

    form = RegistrationForm()
    if form.validate_on_submit():
         # Check if email already exists
        # user_exists = User.query.filter_by(email=form.email.data).first()
        # if user_exists:
        #     flash(_('An account with this email already exists.'), 'error')
        #     return redirect(url_for('users.register'))  # Adjust to your actual registration page route

        hashed_pwd = generate_password_hash(form.password.data, method=app.config.get('PWD_HASH_METHOD'), salt_length=app.config.get('PWD_SALT_LENGTH'))
        user = User(fname=form.fname.data, email=form.email.data, password=hashed_pwd,connect_method=UserConnectMethod.Site, type=UserType.User, lang='en')
        db.session.add(user)
        db.session.commit()
        login_user(user, remember=True)
        flash(_('Congratulations, you are now a registered user!'),'success')
        send_email(user.email, 'Welcome!', 'email/welcome', username=user.fname)

        return redirect(url_for('main.dashboard'))  # Adjust according to your app's structure
    return render_template('register.html', title=_('Register'), form=form,SIGNUP_OPTIONS=app.config.get('SIGNUP_OPTIONS'))


@bp.route('/invite/<invite_code>', methods=['GET', 'POST'])
def register_invite(invite_code):
    
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard')) 
    
    if not app.config.get('SIGNUP_OPTIONS')['allow_invite']:
        flash(_('Invites are not currently allowed.'), 'error')
        return redirect(url_for('main.index'))

    form = RegistrationByInviteForm()
      
    #invite_code = request.args.get('invite_code') or request.form.get('invite_code')
    if invite_code:
        form.invite_code.data = invite_code
       
        invite = Invite.query.filter_by(invite_code=invite_code).first()
        if not invite:
            flash(_('Invalid or expired invite code.'), 'error')
            return redirect(url_for('main.index'))
    else:
        flash(_('No invite code provided.'), 'error')
        return redirect(url_for('main.index'))
    
    if form.validate_on_submit():
        
        hashed_pwd = generate_password_hash(form.password.data, method=app.config.get('PWD_HASH_METHOD'), salt_length=app.config.get('PWD_SALT_LENGTH'))
        user = User(fname=form.fname.data, email=invite.email, password=hashed_pwd,connect_method=UserConnectMethod.Site, type=UserType.User, lang='en')
        db.session.add(user)
        db.session.commit()
        login_user(user, remember=True)
        flash(_('Congratulations, you are now a registered user!'),'success')
        send_email(user.email, 'Welcome!', 'email/welcome', username=user.fname)

        return redirect(url_for('main.dashboard'))  # Adjust according to your app's structure
    return render_template('register_invite.html', title=_('Register'), form=form,email=invite.email,invite_code=invite_code)



@bp.route('/login', methods=['GET', 'POST'])
def login():
   
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard')) 
    
    form = LoginForm()  # Assuming you have a LoginForm similar to RegistrationForm
    if form.validate_on_submit():
        # Assuming User model has an email field and a method to query by email
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)  # Log in the user
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))  # Adjust according to your app's structure
        else:
            flash(_('Invalid email or password'),'error')
    return render_template('login.html', title=_('Log In'), form=form,SIGNUP_OPTIONS=app.config.get('SIGNUP_OPTIONS'))

@bp.route('/logout')
def logout():
    if not current_user.is_authenticated:
        return redirect(url_for('main.index'))  # Adjust according to your app's structure
    
    logout_user()  # Log out the current user
    return redirect(url_for('main.index'))  # Redirect to homepage or login page


@bp.route('/reset_password', methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        # Instead of flashing an error, flash a generic message whether or not the email is found
        flash(_('If an account with that email exists, you will receive an email with instructions to reset your password.'), 'info')
        
        # Proceed with sending the email only if the user is found
        if user:
            token = user.get_reset_token()
            send_email(user.email, 'Password Reset Request',
                       'email/reset_password', user=user, token=token)
        
        return redirect(url_for('users.reset_request'))
    return render_template('reset_request.html', title=_('Reset Password'), form=form)


@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    user = User.verify_reset_token(token)
    if user is None:
        flash(_('That is an invalid or expired token'), 'warning')
        return redirect(url_for('users.reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_pwd = generate_password_hash(form.password.data, method=app.config.get('PWD_HASH_METHOD'), salt_length=app.config.get('PWD_SALT_LENGTH'))
        user.password = hashed_pwd
        db.session.commit()
        flash(_('Your password has been updated! You are now able to log in'), 'success')
        return redirect(url_for('users.login'))
    return render_template('reset_request_with_token.html', title=_('Reset Password'), form=form)


@bp.route('/user/<int:user_id>')
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return {
        'user_id': user.user_id,
        'fname': user.fname,
        'user_email': user.user_email,
        # Do not return sensitive information like passwords
        'user_type': user.user_type.name,
        'user_reg_date': user.user_reg_date.isoformat(),
        'user_last_login': user.user_last_login.isoformat() if user.user_last_login else None,
        'user_lang': user.user_lang,
        'user_connect_method': user.user_connect_method.name,
        'user_extra_fields': user.user_extra_fields
    }




@bp.route('/admin/invites', methods=['GET', 'POST'])
def manage_invites():
   

    
    invites = Invite.query.all()
    for invite in invites:
        invite.url = invite_url = url_for('users.register_invite', invite_code=invite.invite_code)
    return render_template('invites.html', invites=invites)
  
  
@bp.route('/admin/invite_create', methods=['GET', 'POST'])
def invite_create():
    form = InviteForm()
    print(f"Method: {request.method}, Form Valid: {form.validate_on_submit()}")

    if form.validate_on_submit():
        email = form.email.data
        # Generate a unique invite code
        invite_code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
        invite = Invite(email=email, invite_code=invite_code)
        db.session.add(invite)
        db.session.commit()
        flash(_('Invite created successfully!'), 'success')
        return redirect(url_for('users.manage_invites'))
  
    
    
    return render_template('invite_create.html',form=form)