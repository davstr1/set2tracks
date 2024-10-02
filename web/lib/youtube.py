import logging, dotenv, os
from math import e
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse
from venv import logger
import requests
import re
from yt_dlp import YoutubeDL
import xml.etree.ElementTree as ET

from web.lib.utils import silent_function
# for list of options see https://github.com/ytdl-org/youtube-dl/blob/3e4cedf9e8cd3157df2457df7274d0c842421945/youtube_dl/YoutubeDL.py#L137-L312

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
dotenv.load_dotenv(dotenv_path)
PROXY_URL = os.getenv('SHAZAM_PROXY_URL')

logger = logging.getLogger('root')

# Regular expressions for YouTube URL and video ID validation
YOUTUBE_URL_PATTERN = re.compile(
    r'^(?:http(s)?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})$'
)
VIDEO_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{11}$')


ydl_logger = logging.getLogger('youtube')
previous_level = ydl_logger.level
ydl_logger.setLevel(logging.CRITICAL)


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

# def youbube_video_info(video_id:str)->dict:
#     properties_to_keep = ['upload_date','thumbnail', 'title','description','channel','','channel_id','channel_url','duration','playable_in_embed','chapters','channel_follower_count','like_count','view_count','is_live','availability','error']
#     options = {'quiet':True,'no_warnings':True,'proxy':PROXY_URL }
#     with YoutubeDL(params=options) as ydl:
#         yt = f"https://www.youtube.com/watch?v={video_id}"
#         try :
#             video_info = ydl.extract_info(yt,download=False)
#         except Exception as e:
#             #logger.error(f'Error getting video info for {video_id} : {e}')
#             video_info = { 'video_id':video_id,'error' : str(e)}
            
        
#         ret = {key: video_info[key] for key in properties_to_keep if key in video_info}
        
#         if 'error' in ret:
#             ret['error'] = ret['error'].replace('\x1b[0;31mERROR:\x1b[0m [youtube]','').strip()
#             e = ret['error']
#             logger.error(f'Error getting video info for {video_id} : {e}')
        
#         ret['video_id'] = video_id
#         return ret
    
def youbube_video_info(video_id: str, retry_count: int = 5) -> dict:
    properties_to_keep = [
        'upload_date', 'thumbnail', 'title', 'description', 'channel', 
        'channel_id', 'channel_url', 'duration', 'playable_in_embed', 
        'chapters', 'channel_follower_count', 'like_count', 'view_count', 
        'is_live', 'availability', 'error'
    ]
    options = {'quiet': True, 'no_warnings': True, 'proxy': PROXY_URL}

    attempt = 0
    while attempt < retry_count:
        with YoutubeDL(params=options) as ydl:
            yt = f"https://www.youtube.com/watch?v={video_id}"
            try:
                video_info = ydl.extract_info(yt, download=False)
                break  # Exit loop if successful
            except Exception as e:
                video_info = {'video_id': video_id, 'error': str(e)}
                if "not a bot" not in str(e).lower():
                    break  # Exit loop if it's not a bot error
                attempt += 1
                logger.warning(f'Retrying ({attempt}/{retry_count}) due to bot error: {e}')
        
    ret = {key: video_info[key] for key in properties_to_keep if key in video_info}

    if 'error' in ret:
        ret['error'] = e = ret['error'].replace('\x1b[0;31mERROR:\x1b[0m [youtube]', '').strip()
        if "not a bot" in e.lower():
            ret['error'] = e =  f"bot verification required after {retry_count} attempts"
        logger.error(f'Error getting video info for {video_id} : {e}')

    ret['video_id'] = video_id
    return ret

 


def download_youtube_video(id: str, vid_dir: str, retry_count: int = 5) -> str:
    
    def my_hook(d):
        if d['status'] == 'downloading':
            logger.debug(f"{d['downloaded_bytes'] / d['total_bytes'] * 100:.2f}% downloaded")
    
    options = {
        'proxy': PROXY_URL,
        'progress_hooks': [my_hook],
        'write-thumbnail': True,
        'format': 'bestaudio/best',
        'outtmpl': f'{vid_dir}/full.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'opus',
            'preferredquality': '192',
        }],
    }
    
    yt = f"https://www.youtube.com/watch?v={id}"
    
    for attempt in range(retry_count):
        try:
            with YoutubeDL(params=options) as ydl:
                ydl.download([yt])
                return f"{id}.opus"
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt + 1 == retry_count:
                raise e
            logger.info("Retrying...")

    


def youtube_get_channel_feed_video_ids(channel_id: str)->list[str]:
    feed_url = f'https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}'
    response = requests.get(feed_url)
    root = ET.fromstring(response.content)
    video_ids = []

    for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
        video_id = entry.find('{http://www.youtube.com/xml/schemas/2015}videoId').text
        video_ids.append(video_id)

    return video_ids
    



