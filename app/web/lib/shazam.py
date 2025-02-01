from aiohttp_retry import ExponentialRetry
from shazamio import HTTPClient, Shazam
from shazamio.exceptions import FailedDecodeJson, BadParseData,BadMethod
import asyncio
import os
import json
import dotenv

from web.lib.utils import safe_get
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
dotenv.load_dotenv(dotenv_path)

from web.lib.process_shazam_json import transform_track_data
import logging
logger = logging.getLogger('root')

PROXY_URL = os.getenv('SHAZAM_PROXY_URL')

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

async def shazam_track_add_label(track, semaphore, MAX_RETRIES=3, RETRY_DELAY=0):
    async with semaphore:
        shazam = Shazam()
        logger.info(f"Getting label for track {track['title']}")
        
        retries = 0
        while retries < MAX_RETRIES:
            try:
                about_track = await asyncio.wait_for(
                    shazam.track_about(track_id=track['key_track_shazam'], proxy=PROXY_URL), 
                    timeout=3  # Set a 10-second timeout
                )
                track['label'] = safe_get(about_track, ['sections', 0, 'metadata', 1, 'text'])
                return track  # Exit if successful

            except asyncio.TimeoutError:
                logger.error(f"Timeout getting label for track {track['title']}")
            except Exception as e:
                logger.error(f"Error getting label for track {track['title']}: {e}")
                
            retries += 1
            if retries < MAX_RETRIES:
                backoff_delay = RETRY_DELAY * (2 ** (retries - 1))  # Exponential backoff
                logger.info(f"Retrying... attempt {retries + 1} in {backoff_delay} seconds.")
                await asyncio.sleep(backoff_delay)  # Wait before retrying

        # If all retries fail, handle the case for a missing label
        track['label'] = None
        return track

async def shazam_add_tracks_label(tracks, MAX_CONCURRENT_REQUESTS=30):
    logger.info(f"shazam_add_tracks_label for {len(tracks)} tracks")
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    tasks = [shazam_track_add_label(track, semaphore) for track in tracks]
    return await asyncio.gather(*tasks)

async def shazam_related_tracks(track_id, limit=20):
    """
    Retrieves related tracks from Shazam for a given track ID.

    Args:
        track_id (str): The ID of the track for which related tracks are to be retrieved.
        limit (int, optional): The maximum number of related tracks to retrieve. Defaults to 20.

    Returns:
        list: A list of transformed related tracks data.
        Or an empty list if there is an error. (but errors are logged)
        In general, an error means shazam API just returned a blank page. which means no related tracks fro him
        @TODO : watch for shazam errors that are not FailedDecodeJson error.
    Logs:
        FailedDecodeJson: If there is an error decoding the JSON response from Shazam.
        BadMethod: If there is an HTTP error while making the request to Shazam.
        BadParseData: If there is an error parsing the data from Shazam.
        Exception: If there is an unknown error.

    """
    logger.info(f'Starting shazam_related_tracks for {track_id} with limit {limit}')
    try:
        shazam = Shazam()
        logger.info('Initialized Shazam client')
        
        related = await shazam.related_tracks(track_id=track_id, limit=limit, proxy=PROXY_URL)
        logger.info(f'Received related tracks from Shazam {related}')
        transformed = transform_shazam_data(related)
        logger.info('Transformed related tracks data')
        
        logger.debug(f"Get label info for tracks")
       # tracks = await shazam_add_tracks_label(transformed)
        return transformed
        #return transformed
    
    except FailedDecodeJson as json_error:
        logger.error(f"FailedDecodeJson error in shazam_related_tracks for track id {track_id} : {json_error}")
        return []
    except BadMethod as http_error:
        logger.error(f"BadMethod error in shazam_related_tracks for track id {track_id} : {http_error}")
        return []
    except BadParseData as shazam_error:
        logger.error(f"BadParseData error in shazam_related_tracks for track id {track_id} : {shazam_error}")
        return []
    except Exception as e:
        logger.error(f"Unknown error in shazam_related_tracks for track id {track_id} : {e}")
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
            logger.debug(f"Shazaming song from ... {file_name}... at proxy {proxy}")
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

import asyncio
import logging
from shazamio import Shazam

logger = logging.getLogger(__name__)

async def shazam_search_track(track_name, semaphore, MAX_RETRIES=3, RETRY_DELAY=0):
    async with semaphore:
        shazam = Shazam()
        logger.info(f"Searching for track: {track_name}")

        retries = 0
        while retries < MAX_RETRIES:
            try:
                search_result = await asyncio.wait_for(
                    shazam.search_track(track_name,1), timeout=3
                )
                if search_result :#and "tracks" in search_result and search_result["tracks"]["hits"]:
                    return search_result
                    # first_track = search_result["tracks"]["hits"][0]["track"]
                    # return {
                    #     "title": first_track.get("title"),
                    #     "artist": first_track.get("subtitle"),
                    #     "key_track_shazam": first_track.get("key")
                    # }

            except asyncio.TimeoutError:
                logger.error(f"Timeout searching for track: {track_name}")
            except Exception as e:
                logger.error(f"Error searching for track {track_name}: {e}")

            retries += 1
            if retries < MAX_RETRIES:
                backoff_delay = RETRY_DELAY * (2 ** (retries - 1))  # Exponential backoff
                logger.info(f"Retrying... attempt {retries + 1} in {backoff_delay} seconds.")
                await asyncio.sleep(backoff_delay)

        logger.warning(f"Failed to find track: {track_name} after {MAX_RETRIES} attempts.")
        return None
