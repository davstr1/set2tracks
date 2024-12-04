

import math
import os
from pydub import AudioSegment
import socket

from web.lib.utils import is_dev_env

# Determine if running on localhost
is_localhost = is_dev_env()


if not is_localhost:
    # Set the ffmpeg converter path dynamically for non-localhost environments
    ffmpeg_path = f"{os.getcwd()}/ffmpeg/ffmpeg"

    if os.path.isfile(ffmpeg_path):
        AudioSegment.converter = ffmpeg_path
        print("Using ffmpeg at:", AudioSegment.converter)
    else:
        raise FileNotFoundError(f"ffmpeg not found at {ffmpeg_path}")
else:
    print("Running on localhost; ffmpeg configuration skipped.")

from concurrent.futures import ThreadPoolExecutor
import logging
logger = logging.getLogger('root')

def cut_audio(file_path, chapters=[],segment_length_s=120, frame_rate=None, segments_dir='segments'):
    logger.info('cutting audio')
    # Load the audio file
    logger.info('extracting audio segment (this may take a while)')
    audio = AudioSegment.from_file(file_path)

    if frame_rate:
        audio = audio.set_frame_rate(frame_rate)
        
    logger.info('Audio segment extracted')

    # Calculate the number of segments
    duration_ms = len(audio)
    segment_length_ms = segment_length_s * 1000
    logger.info(f'duration_ms: {duration_ms}')
    if len(chapters):
        num_segments = len(chapters)
        logger.info(f'num_segments (from chapters): {num_segments}')
    else:
        num_segments = math.ceil(duration_ms / segment_length_ms)
        logger.info(f'num_segments (from duration): {num_segments}')

    # Create segments directory if it does not exist
    os.makedirs(segments_dir, exist_ok=True)

    def process_segment(i):
        logger.info(f"Cutting segment {i+1}/{num_segments}")
        if not len(chapters):
            start_ms = i * segment_length_ms
            end_ms = min(start_ms + segment_length_ms, duration_ms)
        else:
            start_ms = int(chapters[i]['start_time'] * 1000)
            end_ms = int(chapters[i]['end_time'] * 1000)
            
        segment = audio[start_ms:end_ms]
        segment.export(f"{segments_dir}/segment_{i}.opus", format="opus")
        return segment

    # Cut the audio into segments and save them using multithreading
    with ThreadPoolExecutor(max_workers=30) as executor:
        segments = list(executor.map(process_segment, range(num_segments)))

    return segments





