import math
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom.minidom import parseString
from flask import Blueprint, redirect, render_template, request, send_from_directory, url_for,Response
from flask_login import current_user
from markdown import markdown
from web.controller import get_playable_sets, get_playable_sets_number
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
    l = {
        'page_title':  Lang.APP_NAME + ' - '+ 'Turn DJ sets into playlists'
    }
    return render_template('index.html', l=l)
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


@basic_bp.route('/android-chrome-192x192.png')
@basic_bp.route('/android-chrome-512x512.png')
@basic_bp.route('/apple-touch-icon.png')
@basic_bp.route('/favicon-32x32.png')
@basic_bp.route('/favicon-16x16.png')
@basic_bp.route('/favicon.ico')
@basic_bp.route('/site.webmanifest')
@basic_bp.route('/robots.txt')
def serve_static_files():
    return send_from_directory('static/root', request.path[1:])


@basic_bp.route('/help')
def help():
    return 'yo help'
    return render_template('help.html')


@basic_bp.route('/pricing')
def pricing():
    # TODO: Add useer integration
    l = {
        'page_title': 'Pricing - ' + Lang.APP_NAME,
    }
    return render_template('pricing.html', l=l)


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


MAX_ITEMS_PER_MAP = 1000

@basic_bp.route('/sitemap.xml')
def sitemap():
    """Generate the main sitemap index file."""
    urlset = Element('sitemapindex', {'xmlns': 'http://www.sitemaps.org/schemas/sitemap/0.9'})

    base_url = request.host_url.rstrip('/')

    # Add main sitemap entry points
    sitemap_main = SubElement(urlset, 'sitemap')
    loc = SubElement(sitemap_main, 'loc')
    loc.text = f"{base_url}/sitemap_main_entry_points.xml"

    # Dynamically generated sitemaps for sets
    nb_sets = get_playable_sets_number()
    total_sitemaps = math.ceil(nb_sets / MAX_ITEMS_PER_MAP)

    for i in range(1, total_sitemaps + 1):
        sitemap = SubElement(urlset, 'sitemap')
        loc = SubElement(sitemap, 'loc')
        loc.text = f"{base_url}/sitemap_sets{i}.xml"

    # Generate XML string
    xml_str = tostring(urlset, encoding='utf-8', method='xml')
    pretty_xml = parseString(xml_str).toprettyxml(indent="  ")
    return Response(pretty_xml, mimetype='application/xml')



@basic_bp.route('/sitemap_sets<int:page>.xml')
def sitemap_set(page):
    sets, _ = get_playable_sets(page=page, per_page=MAX_ITEMS_PER_MAP)

    # Build sitemap
    urlset = Element('urlset', {'xmlns': 'http://www.sitemaps.org/schemas/sitemap/0.9'})
    base_url = request.host_url.rstrip('/')

    for playable_set in sets:
        url = SubElement(urlset, 'url')
        loc = SubElement(url, 'loc')
        loc.text = f"{base_url}/set/{playable_set.id}"  # Adjust to your set URL structure
        lastmod = SubElement(url, 'lastmod')
        lastmod.text = playable_set.updated_at.isoformat()

    xml_str = tostring(urlset, encoding='utf-8', method='xml')
    pretty_xml = parseString(xml_str).toprettyxml(indent="  ")
    return Response(pretty_xml, mimetype='application/xml')


@basic_bp.route('/sitemap_main_entry_points.xml')
def sitemap_main_entry_points():
    """Generate a separate sitemap file for static URLs."""
    urlset = Element('urlset', {'xmlns': 'http://www.sitemaps.org/schemas/sitemap/0.9'})

    base_url = request.host_url.rstrip('/')
    
    # Static URLs
    static_urls = [
        '/',
        '/explore',
        '/explore/channels',
        '/explore/tracks',
        '/login',
        '/register',
    ]

    for static_url in static_urls:
        url = SubElement(urlset, 'url')
        loc = SubElement(url, 'loc')
        loc.text = f"{base_url}{static_url}"

    # Generate XML string
    xml_str = tostring(urlset, encoding='utf-8', method='xml')
    pretty_xml = parseString(xml_str).toprettyxml(indent="  ")
    return Response(pretty_xml, mimetype='application/xml')
