from flask import render_template,redirect,url_for,request,flash
from flask_login import current_user, login_required
from web import bp
from flask_babel import lazy_gettext as _l

from web.lib.youtube import download_youtube_video, youbube_video_title, youtube_video_exists, youtube_video_id_from_url, youtube_video_input_is_valid, youtube_video_to_chapters_list


@bp.route('/')
def index():
    return render_template('index.html')
       
@bp.route('/dashboard')
def dashboard():
    if current_user.is_authenticated:
        return render_template('dashboard.html')
    
    return redirect(url_for('main.index'))



@bp.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        youtube_url = request.form.get('youtube_url')
        if not youtube_url:
            flash('No YouTube URL provided. Please enter a URL.', 'error')
            return redirect(url_for('main.add'))
        if not youtube_video_input_is_valid(youtube_url):
            flash('Invalid YouTube URL. Please enter a valid URL.', 'error')
            return redirect(url_for('main.add'))
       
        
        # Process the YouTube URL as needed
        # Example of successful processing redirect or message
        #flash('URL received successfully.', 'success')
        video_id = youtube_video_id_from_url(youtube_url)
        return redirect(url_for('main.check_online_chapters',video_id=video_id))
    return render_template('add.html',no_flash_top=True)


@bp.route('/checkonlinechapters/<video_id>', methods=['GET'])
def check_online_chapters(video_id):
    
    if video_id is None:
        flash("No video ID provided.", "error")
        return redirect(url_for('main.add'))
    
    if not youtube_video_exists(video_id):
           flash('Youtube Video doesn\t exist.', 'error')
           return redirect(url_for('main.add'))
    #download_youtube_video(video_id)   
    #youbube_video_title(video_id)   
    chapters = youtube_video_to_chapters_list(video_id)
    
    if not (len(chapters) > 0):
        return "No chapters found for this video."
    
    print(chapters)
    return 'chapters found'
    
    #return f'Video {video_id} exists'




