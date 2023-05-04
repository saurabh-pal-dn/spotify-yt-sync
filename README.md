# Music Syncer

## Setup

Get your Google credentials, follow the tutorial from [here](https://www.thepythoncode.com/article/using-youtube-api-in-python). Save them in `secrets\client_secret_youtube.json`

Get your Spotify credentials, follow the instruction [here](https://developer.spotify.com/documentation/web-api/tutorials/getting-started).
Save them in `secrets\client_secret_spotify.json`

## Steps to run

If you are sure that your playlists are already created in YT and you just need to add music to them.

```bash
$ python3 main.py
```

If you don't know whether all your playlists are created in YT or not.

```bash
$ python3 main.py -n
```

## Motivation

Spotify provides a great place to listen & explore music but I don't pay for it. I use a cracked version of YT to listen to songs while working. The need to sync music from Spotify to YT arises; this script does that work for me.
