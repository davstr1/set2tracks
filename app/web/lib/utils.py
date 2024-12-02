
from collections import Counter
import contextlib
import io
from typing import Union
from web.logger import logger
import numpy as np





from sqlalchemy.inspection import inspect

# Define a function to suppress stdout
def silent_function(func, *args, **kwargs):
    with contextlib.redirect_stdout(io.StringIO()):
        return func(*args, **kwargs)

def as_dict(model_instance):
    """Convert SQLAlchemy model instance to dictionary."""
    return {c.key: getattr(model_instance, c.key) for c in inspect(model_instance).mapper.column_attrs}



        
def safe_get(data, path, default=None):
    """
    Safely get a value from a nested dictionary or list.

    :param data: The dictionary or list to navigate.
    :param path: A list of keys and/or indices to navigate through `data`.
    :param default: The value to return if any key/index is not found.
    :return: The value at the end of the path, or `default` if any key/index is missing.
    """
    try:
        for key in path:
            if isinstance(data, dict):
                data = data[key]
            elif isinstance(data, list) and isinstance(key, int):
                data = data[key]
            else:
                return default
        return data
    except (KeyError, IndexError, TypeError):
        return default



def extract_full_date(date_input: Union[str, None]) -> str:
    # Check if the input is None or empty
    if not date_input or date_input.lower() == 'null':
        return ''
    
    # Split the input by hyphens
    parts = date_input.split('-')
    
    # Check if the input has three parts (YYYY-MM-DD)
    if len(parts) == 3 and all(part.isdigit() for part in parts):
        return date_input
    else:
        return ''

def extract_year(date_input: Union[str, None]) -> str:
    # Check if the input is None or empty
    if not date_input or date_input.lower() == 'null':
        return ''
    
    # Split the input by hyphens
    parts = date_input.split('-')
    
    # Check if the first part is a valid year
    if parts[0].isdigit() and len(parts[0]) == 4:
        return parts[0]
    else:
        return ''
    

def calculate_avg_properties(tracks):
    # Initialize sums and counts for each property
    sums = {
        'acousticness': 0,
        'danceability': 0,
      
        'energy': 0,
        'instrumentalness': 0,
        'liveness': 0,
        'loudness': 0,
        'speechiness': 0,
       
        'valence': 0,
        'artist_popularity_spotify': 0,
    }
    counts = {
        'acousticness': 0,
        'danceability': 0,
     
        'energy': 0,
        'instrumentalness': 0,
        'liveness': 0,
        'loudness': 0,
        'speechiness': 0,
       
        'valence': 0,
        'artist_popularity_spotify': 0,
    }
   
    # Iterate over each track and accumulate sums and counts
    for track in tracks:
       
        for key in sums.keys():
            value = value = track.get(key)
            
            if isinstance(value, (int, float)):  # Ensure value is a number
                sums[key] += value
                counts[key] += 1
        
     
    # Calculate the average for each property
    averages = {}
    for key in sums.keys():
        if counts[key] > 0:
            averages[key] = int(sums[key] / counts[key])
        else:
            averages[key] = None
            
   

    return averages


def calculate_decade_distribution(tracks):
    decades = []

    # Extract and process the year to find the decade
    for track in tracks:
        year = track.get('release_year')
        if year not in (None, '', 'null'):
            try:
                year = int(year)
                decade = (year // 10) * 10
                decades.append(decade)
            except ValueError:
                pass  # Ignore non-numeric values

    # Determine the most common decade and the percentage of tracks in each decade
    decade_counter = Counter(decades)
    total_tracks = len(decades)
    decade_percentages = {str(decade): int((count / total_tracks) * 100) for decade, count in decade_counter.items()}
    
    sorted_decade_percentages = dict(sorted(decade_percentages.items(), key=lambda item: item[1],reverse=True))


    
    
    return sorted_decade_percentages


def remove_outliers(tempos):
    if not tempos:
        return tempos

    Q1 = np.percentile(tempos, 25)
    Q3 = np.percentile(tempos, 75)
    IQR = Q3 - Q1

    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR

    filtered_tempos = [tempo for tempo in tempos if lower_bound <= tempo <= upper_bound]
    return filtered_tempos

def calculate_and_sort_tempo_distribution(tracks):

    tempos = []

    # Extract and process the tempo to find the ranges
    for track in tracks:
        tempo = track.get('tempo')
        if tempo not in (None, '', 'null'):
            try:
                tempo = float(tempo)
                tempos.append(tempo)
            except ValueError:
                pass  # Ignore non-numeric values

    # Remove outliers
    filtered_tempos = remove_outliers(tempos)

    # Classify tempos into specified ranges
    classified_tempos = []
    for tempo in filtered_tempos:
        if 56 <= tempo <= 65:
            classified_tempos.append(60)
        elif 66 <= tempo <= 75:
            classified_tempos.append(70)
        elif 76 <= tempo <= 85:
            classified_tempos.append(80)
        elif 86 <= tempo <= 95:
            classified_tempos.append(90)
        elif 96 <= tempo <= 105:
            classified_tempos.append(100)
        elif 106 <= tempo <= 115:
            classified_tempos.append(110)
        elif 116 <= tempo <= 125:
            classified_tempos.append(120)
        elif 126 <= tempo <= 135:
            classified_tempos.append(130)
        elif 136 <= tempo <= 145:
            classified_tempos.append(140)
        elif 146 <= tempo <= 155:
            classified_tempos.append(150)
        elif 156 <= tempo <= 165:
            classified_tempos.append(160)
        elif 166 <= tempo <= 175:
            classified_tempos.append(170)
        elif 176 <= tempo <= 185:
            classified_tempos.append(180)
        elif 186 <= tempo <= 195:
            classified_tempos.append(190)
        elif 196 <= tempo <= 205:
            classified_tempos.append(200)
        # Add more ranges if necessary

    # Determine the percentage of tracks in each tempo range
    tempo_counter = Counter(classified_tempos)
    total_tracks = len(classified_tempos)
    tempo_percentages = {f"{tempo_range}": (count / total_tracks) * 100 for tempo_range, count in tempo_counter.items()}
    
    # Sort the dictionary by values (percentages)
    sorted_tempo_percentages = dict(sorted(tempo_percentages.items(), key=lambda item: item[1], reverse=True))

    return sorted_tempo_percentages



def discarded_reason_to_ux(reason):
       
       if '0 unique track' in reason:
           return 'No track found'
       if '1 unique track' in reason:
           return 'Only 1 track found'
       if 'unique track' in reason:
           return reason.replace('unique','')
       if '15m' in reason:
           return 'Shorter than 15 minutes'
       if 'private' in reason:
           return 'private'
       if 'embeddable' in reason:
           return 'Not embeddable'
       if 'live event' in reason or 'offline' in reason:
           return 'Live event. Please retry when it is over'
       if 'Unable to process >4GB files' in reason:
           return "> 4GB. We can't process extra-long videos (typically > 3h)."
       if 'removed by the uploader' in reason:
           return 'Removed by the uploader'
       if 'copyright' in reason:
           return 'Copyright strike'
       if 'unavailable' in reason:
           return 'Content Unavailable'
       if 'age' in reason:  
            return 'Age restricted'
       
       # Retry errors
       if 'bot' in reason:
           return 'Busted as a bot. Queued to rety...'
       if 'download' in reason:
           return 'Error downloading the video. Queued to retry...'
       if 'premiere' in reason:
              return f'{reason}. Will be queued to retry...'
       else:
            msg = f'Unknown discarded reason: {reason}'
            logger.error(msg)
            return msg


def get_camelot_notation(key, mode):
    """
    Convert a musical key and mode to Camelot notation.
    key: 0-11 (C to B)
    mode: 0 (minor) or 1 (major)
    """
    camelot_number = (key + 3) % 12 + 1  # Shift to match Camelot numbering
    camelot_letter = "A" if mode == 0 else "B"
    return f"{camelot_letter}{camelot_number}"

def get_compatible_keys(key, mode):
    """
    Calculate compatible keys based on Camelot wheel rules.
    Returns a comma-separated string of compatible keys in Camelot notation.
    """
    camelot_notation = get_camelot_notation(key, mode)
    number = int(camelot_notation[1:])  # Extract number
    letter = camelot_notation[0]       # Extract letter

    # Determine compatible keys
    compatible = []

    # Add same letter, 2 around current number
    for offset in [-1, 0, 1]:
        compatible_number = (number + offset - 1) % 12 + 1
        compatible.append(f"{letter}{compatible_number}")

    # Add opposite letter with the same number
    opposite_letter = "B" if letter == "A" else "A"
    compatible.append(f"{opposite_letter}{number}")

    return ",".join(compatible)

