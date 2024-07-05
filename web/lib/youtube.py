import logging
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse
from venv import logger
import requests
import re
from yt_dlp import YoutubeDL
# for list of options see https://github.com/ytdl-org/youtube-dl/blob/3e4cedf9e8cd3157df2457df7274d0c842421945/youtube_dl/YoutubeDL.py#L137-L312

logger = logging.getLogger('root')

# Regular expressions for YouTube URL and video ID validation
YOUTUBE_URL_PATTERN = re.compile(
    r'^(?:http(s)?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})$'
)
VIDEO_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{11}$')


def retain_v_parameter(url):
    # Parse the URL into components
    parsed_url = urlparse(url)
    
    # Parse the query parameters
    query_params = parse_qs(parsed_url.query)
    
    # Retain only the 'v' parameter
    filtered_params = { 'v': query_params['v'] } if 'v' in query_params else {}
    
    # Reconstruct the URL with only the 'v' parameter
    new_query = urlencode(filtered_params, doseq=True)
    new_url = urlunparse(parsed_url._replace(query=new_query))
    
    return new_url



def youtube_video_id_from_url(input_str: str) -> str:
    """ Returns the YouTube video ID from a URL or video ID. Or None if the input is invalid."""
    
    
    if re.match(VIDEO_ID_PATTERN, input_str):
        return input_str

    input_str = retain_v_parameter(input_str)
    match = re.search(YOUTUBE_URL_PATTERN, input_str)
    if match:
        return match.group(4)
    
    return None

def youtube_video_input_is_valid(input_str: str) -> bool:
    """
    Check if the input is a valid YouTube URL or video ID.
    
    Args:
        input_str (str): The input string to validate.
    
    Returns:
        bool: True if the input is a valid YouTube URL or video ID, False otherwise.
    """
    
    input_str = retain_v_parameter(input_str)
    return bool(re.match(YOUTUBE_URL_PATTERN, input_str) or re.match(VIDEO_ID_PATTERN, input_str))

def youtube_video_exists(input_str: str) -> bool:
    """
    Verify if a YouTube video exists by making a HEAD request to its URL.
    
    Args:
        input_str (str): A YouTube video ID or URL.
    
    Returns:
        bool: True if the video exists, False otherwise.
    """
    # Extract video ID from input or use the input directly if it's already a video ID
    match = re.match(YOUTUBE_URL_PATTERN, input_str)
    video_id = match.group(4) if match else input_str

    video_url = f"https://www.youtube.com/watch?v={video_id}"
    try:
        response = requests.head(video_url, timeout=10)
        return response.status_code in [200, 301, 302, 303, 307, 308]
    except requests.RequestException:
        return False

def youbube_video_info(video_id:str)->dict:
    properties_to_keep = ['upload_date','thumbnail', 'title','description','channel','','channel_id','channel_url','duration','playable_in_embed','chapters','channel','channel_follower_count']
    options = {}
    with YoutubeDL(params=options) as ydl:
        yt = f"https://www.youtube.com/watch?v={video_id}"
        video_info = ydl.extract_info(yt,download=False)
        
        ret = {key: video_info[key] for key in properties_to_keep if key in video_info}
        ret['video_id'] = video_id
        return ret
   
 


def download_youtube_video(id:str,vid_dir)->str:
    
    def my_hook(d):
        #print(d)
        if d['status'] == 'downloading':
            logger.debug(f"{d['downloaded_bytes'] / d['total_bytes'] * 100:.2f}% downloaded")

    options = {
        'progress_hooks':[my_hook],
        'write-thumbnail': True,
        'format': 'bestaudio/best',
        'outtmpl': f'{vid_dir}/full.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
           'preferredcodec': 'opus',
            'preferredquality': '192',
        }],
    }
    with YoutubeDL(params=options) as ydl:
        yt = f"https://www.youtube.com/watch?v={id}"
        ydl.download([yt])
        return f"{id}.opus"
    



