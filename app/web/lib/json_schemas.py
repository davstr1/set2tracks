import json

from web.lib.format import spotify_track_url


def generate_set_json_schema(set_data, request_url):
    """
    Generate JSON object similar to the provided Jinja2 template.

    :param set_data: Dictionary containing set data
    :param request_url: URL of the current request
    :param tpl_utils: Utility object with helper methods, e.g., for Spotify URLs
    :return: JSON object
    """
    json_object = {
        "@context": "https://schema.org",
        "@type": "CreativeWork",
        "name": set_data["title"],
        "creator": {
            "@type": "Person",
            "name": set_data["channel"].author
        },
        "description": (
            f"A playlist created from '{set_data['title']}' by {set_data['channel'].author}. "
            "Discover songs and export tracks to Spotify or Apple Music."
        ),
        "url": request_url,
        "isBasedOn": {
            "@type": "VideoObject",
            "url": f"https://www.youtube.com/watch?v={set_data['video_id']}",
            "name": set_data["title"],
            "creator": {
                "@type": "Person",
                "name": set_data["channel"].author
            },
            "description": "The original mix from which this playlist was created.",
            "thumbnailUrl": set_data["thumbnail"]
        },
        "hasPart": []
    }

    for track in set_data["tracks"]:
        if track["id"] != 1:
            track_data = {
                "@type": "MusicRecording",
                "name": track["title"],
                "url": spotify_track_url(track),
                "inPlaylist": set_data["title"],
                "duration": f"PT{track['end_time'] - track['start_time']}S",
                "byArtist": {
                    "@type": "MusicGroup",
                    "name": track["artist_name"]
                }
            }

            if "cover_art" in track and track["cover_art"]:
                track_data["image"] = track["cover_art"]

            if "release_date" in track and track["release_date"]:
                track_data["datePublished"] = track["release_date"]

            if "genres" in track and track["genres"]:
                track_data["genre"] = [genre.name for genre in track["genres"]]

            json_object["hasPart"].append(track_data)

    return json.dumps(json_object, indent=4)
