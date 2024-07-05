import json,os
from pprint import pprint
from typing import Optional, Dict, Any
from web.lib.utils import safe_get
import logging
logger = logging.getLogger('root')


def transform_track_data(track: Dict[str, Any]):
    preview_uri = None
    for action in track.get("hub", {}).get("actions", []):
        if action.get("type") == "uri" and action.get("uri", "").endswith(".m4a"):
            preview_uri = action.get("uri")
            break
        
    return {
    "key_track_shazam": track.get("key"),
    "key_track_apple": next((action.get("id") for action in track.get("hub", {}).get("actions", []) if action.get("type") == "applemusicplay"), None),
    "title": track.get("title"),
    "artist_name": track.get("subtitle"),
    "cover_art_apple": safe_get(track, ['images', 'coverart']),
    "preview_uri_apple": preview_uri,
    "genre": safe_get(track, ['genres', 'primary']),
    "subgenre": safe_get(track, ['genres', 'subgenres']),  # Adjust based on actual data structure
    "album": safe_get(track, ['sections', 0, 'metadata', 0, 'text']),
    "label": safe_get(track, ['sections', 0, 'metadata', 1, 'text']),
    "release_year": safe_get(track, ['sections', 0, 'metadata', 2, 'text']),
    "release_date": safe_get(track, ["releasedate"])  # Adjust based on actual data if different
    }

def extract_track_data(file_path: str) -> Dict[str, Any]:
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)

        track = data.get('track', {})
        return transform_track_data(track)
        
        


    except FileNotFoundError:
        logger.error("The file does not exist.")
        return {}
    except json.JSONDecodeError:
        logger.error("Error decoding JSON ")
        return {}
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return {}

      
def get_segments(directory_path: str):
    # List all files in the directory
    files = os.listdir(directory_path)
    # Filter and sort files based on the numeric value after 'segment_'
    segment_files = sorted(
        (file for file in files if file.startswith("segment_") and file.endswith(".json")),
        key=lambda x: int(x.split('_')[1].split('.')[0])
    )

    segments = []
    for file_name in segment_files:
            segments.append(file_name)

    return segments


def write_segments_from_chapter(directory_path: str, output_file_path: str, chapters):
    segment_files = get_segments(directory_path)
    logger.info(f"writing segments from chapters at {directory_path} with {len(segment_files)} segments.")

    with open(output_file_path, 'w') as file:
        file.write('[')
        first = True
        
        for i,file_name in enumerate(segment_files):
            logger.info(f"Segments from chapters, processing {file_name}")
            file_path = os.path.join(directory_path, file_name)
            segment_data = extract_track_data(file_path)
            
            current_track_data = {
                    "start_time": int(chapters[i]['start_time']),
                    "end_time": int(chapters[i]['end_time'])
                }
               
            if not first:
                file.write(',')
            else:
                first = False
            
            current_track_data.update(segment_data)
            json.dump(current_track_data, file, indent=4)

        file.write(']')



def write_deduplicated_segments(directory_path: str, output_file_path: str, segment_duration: int = 120,chapters={}):
    segment_files = get_segments(directory_path)
    current_start_time = 0  # Initialize start time for the first track
    current_track_data = None  

    with open(output_file_path, 'w') as file:
        file.write('[')
        first = True
        logger.info(f"Deduplicating segments at {directory_path}")
        for file_name in segment_files:
            logger.info(f"Deduplication, processing {file_name}")
            file_path = os.path.join(directory_path, file_name)
            segment_data = extract_track_data(file_path)
            title = segment_data.get("title")
            artist_name = segment_data.get("subtitle")
            

            # First track 
            if current_track_data is None:
               
                current_track_data = {
                    "start_time": current_start_time,
                    "end_time": current_start_time + segment_duration
                }
            
            # Track is the same as prev or track not found    
            elif (last_title is not None and title == last_title and artist_name == last_artist) or (title is None and last_title is None):
                # If the title and subtitle haven't changed, extend the current track's duration
                current_track_data["end_time"] += segment_duration
            
            # New track    
            else:
                
                if not first:
                    file.write(',')
                else:
                    first = False
                json.dump(current_track_data, file, indent=4)

                # Start new track
                current_track_data = {
                    "start_time": current_start_time,
                    "end_time": current_start_time + segment_duration
                }
            
            current_track_data.update(segment_data)

            # Prepare for next segment
            last_title = title
            last_artist = artist_name

            current_start_time += segment_duration

        # After loop, write the last track if any
        if current_track_data is not None:
            if not first:
                file.write(',')
            json.dump(current_track_data, file, indent=4)

        file.write(']')


