from flask_mail import Message,Mail
from flask import render_template, current_app



def send_email(to, subject, template, **kwargs):
    app = current_app._get_current_object()  # Get the actual application instance
    msg = Message(subject, recipients=[to], sender=app.config['MAIL_DEFAULT_SENDER'])
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    mail = Mail(current_app)
    # with app.app_context():
    mail.send(msg)
