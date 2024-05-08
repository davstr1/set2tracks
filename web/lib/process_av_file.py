
from concurrent.futures import ThreadPoolExecutor
import os
os.environ["IMAGEIO_FFMPEG_EXE"] = "/opt/homebrew/opt/ffmpeg/bin/ffmpeg"
from moviepy.editor import *
import math

def video_to_audio_file(mp4, output_file,use_vbr=True, target_bitrate="16k", complexity=10):
    
    vbr_arg = "on" if use_vbr else "off"
    ffmpeg_params=["-c:a", "libopus", "-b:a", target_bitrate, "-vbr", vbr_arg, "-compression_level", str(complexity)]
   
    file_handle = AudioFileClip(mp4)
    file_handle.write_audiofile(output_file, fps=16000, nbytes=2, bitrate="32k", ffmpeg_params=ffmpeg_params)
    file_handle.close()






def process_segment(segment_num, start_time, end_time, num_digits, output_folder, fps, nbytes, bitrate, ffmpeg_params, audio_file):
    audio_clip = AudioFileClip(audio_file)  # Open the audio clip in each thread
    segment = audio_clip.subclip(start_time, end_time)
    segment_file_name = f"{output_folder}/segment_{str(segment_num).zfill(num_digits)}.ogg"
    segment.write_audiofile(segment_file_name, fps=fps, nbytes=nbytes, bitrate=bitrate, ffmpeg_params=ffmpeg_params)
    print(f"Segment {segment_num} saved: {segment_file_name}")
    audio_clip.close()

def cut_audio_file_into_segments(audio_file, output_folder, segment_length_sec, use_vbr=True, target_bitrate="16k", complexity=10, num_workers=100):
    audio_clip = AudioFileClip(audio_file)
    duration = audio_clip.duration
    audio_clip.close()  # Close here since we'll open it in each thread again
    
    num_segments = math.ceil(duration / segment_length_sec)
    num_digits = len(str(num_segments))
    
    vbr_arg = "on" if use_vbr else "off"
    ffmpeg_params = ["-c:a", "libopus", "-b:a", target_bitrate, "-vbr", vbr_arg, "-compression_level", str(complexity)]

    tasks = []
    for i in range(num_segments):
        start_time = i * segment_length_sec
        end_time = min((i + 1) * segment_length_sec, duration)
        task = (i + 1, start_time, end_time, num_digits, output_folder, 16000, 2, "32k", ffmpeg_params, audio_file)
        tasks.append(task)

    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        for task in tasks:
            executor.submit(process_segment, *task)

    

name = "/Users/imac1/Documents/code2024/set2tracks/mix.mp4"

cut_audio_file_into_segments("/Users/imac1/Documents/code2024/set2tracks/mix.mp4", "segments", 60)


