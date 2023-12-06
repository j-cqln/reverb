"""
spotify.py

Module for handling Spotify API calls.
"""

import os
import base64
import json
import string
import random

from dotenv import load_dotenv
from requests import post, get

from utils.models import ContentItem

load_dotenv()

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")

SPOTIFY_ENDPOINT = "https://api.spotify.com/v1/"

def get_token():
    """Get token from Spotify API"""
    auth_string = client_id + ":" + client_secret
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")

    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": "Basic " + auth_base64,
        "Content-Type": "application/x-www-form-urlencoded"
    }

    data = {"grant_type": "client_credentials"}
    result = post(url, headers=headers, data=data)
    json_result = json.loads(result.content)
    token = json_result["access_token"]

    return token

def get_auth_header(token):
    """Get auth header"""
    return { "Authorization": "Bearer " + token}

# See https://developer.spotify.com/web-api/search-item/ for documentation
def spotify_search_item(name, content_type, token, number=10):
    """Queries spotify for content by type (track or album) in US market"""
    header = get_auth_header(token)

    query = f"?q={name}&type={content_type}&limit={number}&market=US"
    query_url = SPOTIFY_ENDPOINT + "search" + query

    response = get(query_url, headers=header)
    content_type_index = content_type + "s"
    items = json.loads(response.content)[content_type_index]["items"]

    content = []
    for item in items:
        content_id = item["id"]
        name = item["name"]

        # index correctly into json based for track or album response, then select first image url
        images_list = item["album"]["images"] if content_type == "track" else item["images"]
        image = images_list[0]["url"] if images_list else None

        artists = []
        for artist in item["artists"]:
            artists.append(artist["name"])

        # format into content display class
        content_item = ContentItem(content_id, content_type, name, image, artists)
        content.append(content_item)

    return content

def get_spotify_results(name, track, album):
    """Returns track and/or album results as requested."""
    token = get_token()

    results = []

    if track:
        tracks = spotify_search_item(name, "track", token)
        results += tracks

    if album:
        albums = spotify_search_item(name, "album", token)
        results += albums

    return results

def get_random_content(content_type, n, top=10):
    """Returns n random content items of the specified type."""
    token = get_token()

    results = []

    for _ in range(n):
        random_search = f"%25{random.choice(string.ascii_letters + string.digits)}%25"
        content = spotify_search_item(random_search, content_type, token, number=top)

        while True:
            result = random.sample(content, 1)

            if result not in results:
                results += random.sample(content, 1)
                break

    return results

def get_content_image(content_type, content_id):
    """Get content name, image, and artists if any from content id and type"""
    token = get_token()
    header = get_auth_header(token)

    content_type_plural = content_type + "s"
    query_url = SPOTIFY_ENDPOINT + f"{content_type_plural}/" + f"{content_id}"

    response = get(query_url, headers=header)
    item = json.loads(response.content)

    # index correctly into json based for track or album response, then select first image url
    images_list = item["album"]["images"] if content_type == "track" else item["images"]
    image = images_list[0]["url"] if images_list else None

    return image

def get_content_info(content_type, content_id):
    """Get content name, image, and artists if any from content id and type"""
    token = get_token()
    header = get_auth_header(token)

    content_type_plural = content_type + "s"
    query_url = SPOTIFY_ENDPOINT + f"{content_type_plural}/" + f"{content_id}"

    response = get(query_url, headers=header)
    item = json.loads(response.content)

    # To-do: error checking when id doesnt exist
    # if item["error"]:
    #     return None

    name = item["name"]

    # index correctly into json based for track or album response, then select first image url
    images_list = item["album"]["images"] if content_type == "track" else item["images"]
    image = images_list[0]["url"] if images_list else None

    artists = []
    for artist in item["artists"]:
        artists.append(artist["name"])

    content_item = ContentItem(content_id, content_type, name, image, artists)

    return content_item

def get_content_several_ids(content):
    """Get content name and image from id and type for several ids"""
    token = get_token()
    header = get_auth_header(token)

    track_ids = ",".join(content["tracks"])
    album_ids = ",".join(content["albums"])

    tracks_query = SPOTIFY_ENDPOINT + f"tracks?market=US&ids={track_ids}"
    albums_query =  SPOTIFY_ENDPOINT + f"albums?market=US&ids={album_ids}"

    content = []

    # To-do: make helper function for similar code
    if track_ids:
        response = get(tracks_query, headers=header)
        tracks = json.loads(response.content)["tracks"]

        for track in tracks:
            images_list = track["album"]["images"]
            image = images_list[0]["url"] if images_list else None

            artists = []
            for artist in track["artists"]:
                artists.append(artist["name"])

            content_item = ContentItem(track["id"], "track", track["name"], image, artists)
            content.append(content_item)

    if album_ids:
        response = get(albums_query, headers=header)
        albums = json.loads(response.content)["albums"]

        for album in albums:
            images_list = album["images"]
            image = images_list[0]["url"] if images_list else None

            artists = []
            for artist in album["artists"]:
                artists.append(artist["name"])

            content_item = ContentItem(album["id"], "album", album["name"], image, artists)
            content.append(content_item)

    return content
