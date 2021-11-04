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

    playlist = sp.playlist(PLAYLIST_ID)
    snapshot_id = playlist['snapshot_id']
    grab_time = datetime.utcnow()

    if 'snapshot_id' not in dict:
        # Initializing, we need to ignore all songs up to this moment
        # Save the snapshot id and timestamp
        dict['snapshot_id'] = snapshot_id
        dict['snapshot_timestamp'] = grab_time

    if dict['snapshot_id'] != snapshot_id:
        # Playlist changed, we need to detect new songs
        print(f"New snapshot detected. Processing changes ({dict['snapshot_id']} => {snapshot_id})")
        last_sync = dict['snapshot_timestamp']
        print(f'Last snapshot timestamp: {last_sync}')
        if 'tracks' in playlist and 'items' in playlist['tracks']:
            for item in playlist['tracks']['items']:
                # Format: 2021-05-07T03:04:24Z
                print(f'{item['track']['name']} added at {item['added_at']}')
                if datetime.strptime(item['added_at'], '%Y-%m-%dT%H:%M:%SZ') > last_sync:
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

                    if DEBUG: print(f"Using URL: {url}")
                    if DEBUG: print(f"Using body: {body}")

                    resp = ''
                    if WEBHOOK_METHOD.upper() == 'GET':
                        resp = requests.get(url)
                    elif WEBHOOK_METHOD.upper() == 'POST' and WEBHOOK_CONTENT_TYPE.upper() == 'JSON':
                        resp = requests.post(url, json=body)
                    elif WEBHOOK_METHOD.upper() == 'POST' and WEBHOOK_CONTENT_TYPE.upper() == 'FORM':
                        resp = requests.post(url, data=body)
                    elif WEBHOOK_METHOD.upper() == 'PUT'  and WEBHOOK_CONTENT_TYPE.upper() == 'JSON':
                        resp = requests.put(url, json=body)
                    elif WEBHOOK_METHOD.upper() == 'PUT'  and WEBHOOK_CONTENT_TYPE.upper() == 'FORM':
                        resp = requests.put(url, data=body)
                    else:
                        print(f"ERROR: Invalid WEBHOOK_METHOD ({WEBHOOK_METHOD}) or WEBHOOK_CONTENT_TYPE ({WEBHOOK_CONTENT_TYPE})")
                        print(f"Not saving snapshot_id")
                        return

                    if DEBUG: print(f"Status code: {resp.status_code}")

                    if resp.status_code not in [200, 201, 204]:
                        print(f"Webhook call failed with status {resp.status_code} and response {resp.text}")
                        print(f"Not saving snapshot_id")
                        return
                    else:
                        print(f"Successfully submitted webhook for {item['track']['artists'][0]['name']} - {item['track']['name']}")

            # Save the snapshot id and timestamp
            dict['snapshot_id'] = snapshot_id
            dict['snapshot_timestamp'] = grab_time
    else:
        print(f"No changes detected @ {grab_time}")


# MAIN
r = redis.from_url(os.environ.get("REDIS_URL"))
dict = redisshelve.RedisShelf(redis=r)

# Run
spotihook()
