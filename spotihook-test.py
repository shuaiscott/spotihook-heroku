from datetime import datetime
from dotenv import load_dotenv
import json
import os
import redisshelve
import redis
import requests
from string import Template
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import sys
import time

# VARIABLES
load_dotenv()

CLIENT_ID = os.environ.get('CLIENT_ID') or sys.exit("FAILURE: CLIENT_ID not specified")
CLIENT_SECRET = os.environ.get('CLIENT_SECRET') or sys.exit("FAILURE: CLIENT_SECRET not specified")
PLAYLIST_ID = os.environ.get('PLAYLIST_ID')  or sys.exit("FAILURE: PLAYLIST_ID not specified")
WEBHOOK_URL_TEMPLATE = os.environ.get('WEBHOOK_URL_TEMPLATE')  or sys.exit("FAILURE: WEBHOOK_URL_TEMPLATE not specified")
WEBHOOK_METHOD= os.environ.get('WEBHOOK_METHOD', 'POST')
WEBHOOK_CONTENT_TYPE = os.environ.get('WEBHOOK_CONTENT_TYPE', 'JSON')
WEBHOOK_BODY_TEMPLATE = os.environ.get('WEBHOOK_BODY_TEMPLATE')
DELAY_AMOUNT = int(os.environ.get('DELAY_AMOUNT', "5"))
DELAY_UNIT = os.environ.get('DELAY_UNIT', 'MINUTES')
DEBUG = os.environ.get('DEBUG', False)

def spotihook():
    sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET))

    snapshot_id = sp.playlist(PLAYLIST_ID)['snapshot_id']
    grab_time = datetime.utcnow()
    playlist = sp.playlist_items(PLAYLIST_ID, limit=100)
    total_items = playlist['total']

    items = playlist['items']
    
    offset = 100
    while offset < total_items:
        print(f"Offset:{offset}")
        playlist = sp.playlist_items(PLAYLIST_ID, offset=offset, limit=100)
        items.extend(playlist['items'])
        offset += 100

    for item in items:
        # Format: 2021-05-07T03:04:24Z
        print(f"{item['track']['name']} added at {item['added_at']}")
        print(f"Formatted time: {datetime.strptime(item['added_at'], '%Y-%m-%dT%H:%M:%SZ')}")
        print(f"New track found: {item['track']['artists'][0]['name']} - {item['track']['name']}")

        # Add Spotify data to data dict
        data = {}
        data['track_id'] = item['track']['id']
        data['track_name'] = item['track']['name']
        data['track_number'] = item['track']['track_number']
        data['track_duration'] = item['track']['duration_ms']
        data['artist_id'] = item['track']['artists'][0]['id']
        data['artist_name'] = item['track']['artists'][0]['name']
        data['album_id'] = item['track']['album']['id']
        data['album_name'] = item['track']['album']['name']
        data['album_type'] = item['track']['album']['album_type']
        if 'isrc' in item['track']['external_ids']: data['isrc'] = item['track']['external_ids']['isrc']

        # Submit Webhook Request
        url_template = Template(WEBHOOK_URL_TEMPLATE)
        url= url_template.safe_substitute(data)

        body = data
        if 'WEBHOOK_BODY_TEMPLATE' in globals() and WEBHOOK_BODY_TEMPLATE:
            body_template = Template(WEBHOOK_BODY_TEMPLATE)
            body = body_template.safe_substitute(data)
            if WEBHOOK_CONTENT_TYPE.upper() == 'JSON':
                body = json.loads(body)
            # else we don't know what it is, so just send it as form data

        print(f"Generated URL: {url}")
        print(f"Generated body: {body}")
    else:
        print(f"No changes detected @ {grab_time}")


# MAIN
r = redis.from_url(os.environ.get("REDIS_URL"))
dict = redisshelve.RedisShelf(redis=r)

# Run
spotihook()
