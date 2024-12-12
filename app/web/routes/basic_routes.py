from flask import Blueprint, redirect, render_template, request, send_from_directory, url_for
from flask_login import current_user
from markdown import markdown
from lang import Lang

def load_markdown_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


basic_bp = Blueprint('basic', __name__)

@basic_bp.route('/health', methods=['GET'])
def health():
    return "OK", 200



@basic_bp.route('/')
def index():
    return render_template('index.html')
    # return 'index', 200
    # return redirect(url_for('set.sets'))


@basic_bp.route('/dashboard')
def dashboard():
    if current_user.is_authenticated:
        next_page_cookie = request.cookies.get('next_page_after_login')
        if next_page_cookie:
            response = redirect(next_page_cookie)
            response.delete_cookie('next_page_after_login')
            return response
            
            
        return redirect(url_for('set.sets'))
    
    return redirect(url_for('basic.index'))


@basic_bp.route('/apple-touch-icon.png')
@basic_bp.route('/favicon-32x32.png')
@basic_bp.route('/favicon-16x16.png')
@basic_bp.route('/favicon.ico')
@basic_bp.route('/site.webmanifest')
def serve_static_files():
    return send_from_directory('static/root', request.path[1:])


@basic_bp.route('/help')
def help():
    return 'yo help'
    return render_template('help.html')


@basic_bp.route('/plans')
def plans():
    # TODO: Add useer integration
    l = {
        'page_title': 'Plans - ' + Lang.APP_NAME,
    }
    return render_template('plans.html', l=l)


@basic_bp.route('/terms-of-service')
def terms_of_service():
    markdown_content = load_markdown_file("web/templates/markdown/terms-of-service.md")
    html_content = markdown(markdown_content)
    l = {
        'page_title': 'Terms of Service - ' + Lang.APP_NAME,
    }
    return render_template('generic_text_page.html', l=l,content=html_content)

@basic_bp.route('/privacy-policy')
def privacy_policy():
    markdown_content = load_markdown_file("web/templates/markdown/privacy-policy.md")
    html_content = markdown(markdown_content)
    l = {
        'page_title': 'Privacy Policy - ' + Lang.APP_NAME,
    }
    return render_template('generic_text_page.html', l=l,content=html_content)