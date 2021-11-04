[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?env[CLIENT_ID]=CLIENT_ID&env[CLIENT_SECRET]=CLIENT_SECRET)

# Environment Variables
|Variable|Description|Example|
|--|--|--|
|CLIENT_ID|Spotify Dev App Client ID [Link](https://developer.spotify.com/dashboard/applications)|1234567890|
|CLIENT_SECRET|Spotify Dev App Client Secret [Link](https://developer.spotify.com/dashboard/applications)|1234567890|
|PLAYLIST_ID|Spotify Playlist ID to Monitor|1234567890|
|WEBHOOK_URL_TEMPLATE|URL Template|https://api.com?artist=$artist_name&album=$album_name&title=$track_name&artwork-url=$album_artwork_url|
|WEBHOOK_METHOD|Web Hook HTTP Method|GET|
|WEBHOOK_CONTENT_TYPE|Web Hook HTTP Content Type|JSON|
|WEBHOOK_BODY_TEMPLATE|Body Template||
|DEBUG|Show Debug logs|True|