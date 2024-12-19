import json

def generate_video_object_with_tracklist(set_data, request_url):
    """
    Generate JSON-LD schema for a YouTube video with enhanced tracklist details.

    :param set_data: Dictionary containing set data
    :param request_url: URL of the current request
    :return: JSON object
    """
   
    
    json_object = {
        "@context": "https://schema.org",
        "@type": "VideoObject",
        "name": set_data["title"] + " with Tracklist",
        "description": (
            f"Watch '{set_data['title']}', navigate the video by tracks, preview songs, "
            "and export them to Spotify or Apple Music."
        ),
        "thumbnailUrl": set_data["thumbnail"], # TODO : custom thumbnail by adding "with tracklist" text
        "uploadDate": set_data['upload_date'],
        "contentUrl": request_url,
        "embedUrl": f"https://www.youtube.com/embed/{set_data['video_id']}",
        "duration": f"PT{set_data.get('duration', 3600)}S",
        "hasPart": []
    }

    # Add tracks as parts of the video
    for track in set_data["tracks"]:
        track_data = {
            "@type": "Clip",
            "name": track["title"],
            "startOffset": track["start_time"],
            "endOffset": track["end_time"],
            "url": f"{request_url}?t={track['start_time']}"  # Link directly to timestamp
        }
        json_object["hasPart"].append(track_data)

    return json.dumps(json_object, indent=4)

