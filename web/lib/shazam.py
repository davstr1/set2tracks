from shazamio import Shazam
from shazamio.user_agent import USER_AGENTS
import asyncio
import os
import json

async def recognize_song(file_path):
    shazam = Shazam()
    return await shazam.recognize(file_path)


async def process_file(file, folder_path):
    file_path = os.path.join(folder_path, file)
    out = await recognize_song(file_path)
    
    # Create the /results/ directory if it doesn't already exist
    results_folder_path = os.path.join(folder_path, "results")
    os.makedirs(results_folder_path, exist_ok=True)
    
    # Define the path for the output JSON file
    output_file_path = os.path.join(results_folder_path, f"{os.path.splitext(file)[0]}.json")
    
    # Write the output to a JSON file
    with open(output_file_path, 'w') as json_file:
        json.dump(out, json_file, indent=4)

    print(f"Results for {file} saved to {output_file_path}")


async def main():
    folder_path = 'segments'
    files = [f for f in os.listdir(folder_path) if f.endswith('.ogg')]
    sorted_files = sorted(files)

    # Create a list of tasks for each file
    tasks = [process_file(file, folder_path) for file in sorted_files]

    # Run tasks concurrently
    await asyncio.gather(*tasks)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())

# TODO : plug to a proxy server rotator to avoid being blocked by shazam
# try with this first : https://www.webshare.io/proxy-server