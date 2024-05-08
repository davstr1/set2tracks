from http import client
import subprocess
import json
import shlex
import logging
from typing import List, Dict
import requests
import re
import os
from pytube import YouTube 
# from pytube import exceptions
# from pytube.innertube import InnerTube

# class YouTube(OfficialYouTube):
#     def bypass_age_gate(self):
#         """Attempt to update the vid_info by bypassing the age gate."""
#         innertube = InnerTube(
#             # see https://github.com/pytube/pytube/issues/1712
#             client='ANDROID_EMBED', # fix for fake age restricted videos bug 
#             use_oauth=self.use_oauth,
#             allow_cache=self.allow_oauth_cache
#         )
#         print('vid id:',self.video_id)
#         innertube_response = innertube.player(self.video_id)
        

#         playability_status = innertube_response['playabilityStatus'].get('status', None)

#         # If we still can't access the video, raise an exception
#         # (tier 3 age restriction)
#         if playability_status == 'UNPLAYABLE':
#             raise exceptions.AgeRestrictedError(self.video_id)

#         self._vid_info = innertube_response



logger = logging.getLogger(__name__)

def format_seconds(seconds:int)->str:
    """Convert seconds to HH:MM:SS format."""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"



# Regular expressions for YouTube URL and video ID validation
YOUTUBE_URL_PATTERN = re.compile(
    r'^(?:http(s)?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})$'
)
VIDEO_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{11}$')


def youtube_video_id_from_url(input_str: str) -> str:
    """ Returns the YouTube video ID from a URL or video ID. Or None if the input is invalid."""
    
    if re.match(VIDEO_ID_PATTERN, input_str):
        return input_str

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



def youtube_video_to_chapters_list(video_id_or_url: str) -> List[Dict[str, str]]:
    """
    Extracts chapter information from a YouTube video using yt-dlp.
    
    Args:
        video_id_or_url (str): The YouTube video ID or URL.
    
    Returns:
        List[Dict[str, str]]: A list of dictionaries with 'title' and 'start_time' keys.
    """
    yt_dlp_command = f'yt-dlp --dump-json {shlex.quote(video_id_or_url)}'
    try:
        process = subprocess.Popen(yt_dlp_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        output, error = process.communicate()

        if process.returncode == 0:
            data = json.loads(output)
            chapters = [{'title': chapter['title'], 'start_time': format_seconds(chapter['start_time'])} for chapter in data.get('chapters', [])]
            return chapters
        else:
            logger.error("yt-dlp command failed: %s", error)
            return []
    except subprocess.TimeoutExpired:
        logger.error("yt-dlp command timed out")
        return []
    except json.JSONDecodeError as e:
        logger.error("Error parsing JSON: %s", e)
        return []
    except Exception as e:
        logger.error("Unexpected error: %s", e)
        return []
    
def youbube_video_title(video_id:str)->str:
    #return
    yt = YouTube(f"https://www.youtube.com/watch?v={video_id}")  
    properties = {attr: getattr(yt, attr) for attr in dir(yt) if not callable(getattr(yt, attr)) and not attr.startswith("__")}
    print(properties)
    #print(yt)  
 
    

def download_youtube_video(url_or_id: str, output_name: str = None, output_folder: str = '.') -> str:
    """
    Downloads a YouTube video as audio using pytube.
    
    Parameters:
        url_or_id (str): The YouTube video ID or URL.
        output_name (str): Optional; Custom name for the downloaded file.
        output_folder (str): Optional; Folder to save the downloaded file.
        
    Returns:
        str: The path to the downloaded file.
    """
    
    video_id = youtube_video_id_from_url(url_or_id)
    if not video_id:
        raise ValueError("Invalid YouTube video ID or URL.")
        
    yt = YouTube(f"https://www.youtube.com/watch?v={video_id}")
    stream = yt.streams.filter(only_audio=True).first()
    
    if not stream:
        raise ValueError("No audio stream found for this video.")
    
    output_name = output_name if output_name else yt.title
    
    # Ensure the output folder exists
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    file_path = stream.download(output_path=output_folder, filename=output_name)
    
    return file_path  
    

if __name__ == "__main__":
    video_id_or_url = "https://www.youtube.com/watch?v=sfUvkHH7oMA"
    chapters = youtube_video_to_chapters_list(video_id_or_url)
    for chapter in chapters:
        print(f"Title: {chapter['title']}, Start Time: {chapter['start_time']}")

