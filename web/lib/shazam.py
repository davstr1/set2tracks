from aiohttp_retry import ExponentialRetry
from shazamio import HTTPClient, Shazam
from shazamio.user_agent import USER_AGENTS
import asyncio
import os
import json

from web.lib.process_shazam_json import transform_track_data
import logging
logger = logging.getLogger('root')

# TODO add logging capacities
# TODO remove proxy + semaphore concurrency hardcoding

PROXY_URL='http://sxbrfiav-rotate:z1rnitsp7b1x@p.webshare.io:80/'

def transform_shazam_data(data):
    """
    Transforms Shazam data into an array of dictionaries with specific fields,
    ensuring preview_uri is from Apple Music (.m4a link).
    
    Parameters:
    data (dict): The input data from Shazam.
    
    Returns:
    list: A list of transformed dictionaries.
    """
    result = []
    for track in data.get('tracks', []):
        transformed_track = transform_track_data(track)
        result.append(transformed_track)
    return result


async def shazam_related_tracks(track_id,limit=20):
   
    try:
        shazam = Shazam()
        related = await shazam.related_tracks(track_id=track_id, limit=limit,proxy=PROXY_URL)
        transformed = transform_shazam_data(related)
        return transformed
    except Exception as e:
        logger.error(f"Error in shazam_related_tracks: {e}")
        return []
        




async def recognize_song(file_path, proxy, retries=1):
    shazam = Shazam(
        http_client=HTTPClient(
            retry_options=ExponentialRetry(
                attempts=5, max_timeout=204.8, statuses={500, 502, 503, 504, 429}
            ),
        ),
    )
    attempt = 0
    while attempt < retries:
        try:
            file_name = os.path.basename(file_path)
            logger.debug(f"Shazaming song from ... {file_name}...")
            result = await shazam.recognize(file_path, proxy=proxy)
            return result
        except Exception as e:
            logger.error(f"Attempt {attempt+1} failed to recognize song: {e}")
            attempt += 1
            if attempt == retries:
                return {"error": str(e)}
            

async def process_segment(file, folder_path,results_folder_path,semaphore):
    async with semaphore:
        file_path = os.path.join(folder_path, file)
        out = await recognize_song(file_path,PROXY_URL)
        #print(out)

        # Define the path for the output JSON file
        output_file_path = os.path.join(results_folder_path, f"{os.path.splitext(file)[0]}.json")

        # Write the output to a JSON file
        with open(output_file_path, 'w') as json_file:
            json.dump(out, json_file, indent=4)

        file_name = os.path.basename(file)
        output_file_name = os.path.basename(output_file_path)
        logger.debug(f"Results for {file_name} saved to ...{output_file_name}")


async def process_segments(folder_path,results_path):
    logger.debug(f'process_segments from folder_path {folder_path} to results_path {results_path}')
    files = [f for f in os.listdir(folder_path) if f.endswith('.opus')]
    sorted_files = sorted(files)
    
    semaphore = asyncio.Semaphore(30) # Limit the number of concurrent tasks to 10
    # Create a list of tasks for each file
    tasks = [process_segment(file, folder_path,results_path,semaphore) for file in sorted_files]

    # Run tasks concurrently
    await asyncio.gather(*tasks)

def sync_process_segments(folder_path,results_path):
    logger.info('sync_process_segments')
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(process_segments(folder_path,results_path))
    loop.close()
    return result

