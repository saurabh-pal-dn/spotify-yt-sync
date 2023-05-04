import requests
from typing import List
from classes.playlist import Playlist
from classes.track import Track
from youtube_client import YouTubeClient
import json
import sys
import logging


SPOTIFY_BASE_URL = 'https://api.spotify.com/v1/'

spotify_credentials = json.load(open('secrets/client_secret_spotify.json'))
youtube_client = YouTubeClient()
logging.basicConfig(level=logging.INFO)


def get_access_token():
    auth_response = requests.post(spotify_credentials["AUTH_URL"], {
        'grant_type': 'client_credentials',
        'client_id': spotify_credentials["CLIENT_ID"],
        'client_secret': spotify_credentials["CLIENT_SECRET"],
    })
    auth_response_data = auth_response.json()
    access_token = auth_response_data['access_token']
    return access_token


def get_header(access_token):
    headers = {
        'Authorization': 'Bearer {token}'.format(token=access_token)
    }
    return headers


def get_playlists_info(access_token):
    logging.info(f'Getting all spotify playlists of user')
    headers = get_header(access_token)
    r = requests.get(
        SPOTIFY_BASE_URL + f'users/{spotify_credentials["USER_ID"]}/playlists', headers=headers)
    return (r.json())


def get_playlist_info(access_token, playlist_id):
    logging.info(f'Getting playlist info for playlist id: {playlist_id}')
    headers = get_header(access_token)
    r = requests.get(
        SPOTIFY_BASE_URL + f'playlists/{playlist_id}', headers=headers)
    return (r.json())


def get_playlists(playlists_info) -> List[Playlist]:
    items = playlists_info["items"]
    playlists: List[Playlist] = list(map(lambda item: Playlist(
        item["id"], item["name"], item["tracks"]["total"]), items))
    return playlists


def get_all_artists(artists) -> List[str]:
    return list(map(lambda v: v["name"], artists))


def get_tracks(playlist_info) -> List[Track]:
    items = playlist_info["tracks"]["items"]
    all_tracks: List[Track] = []
    for item in items:
        track = item["track"]
        name = track["name"]
        id = track["id"]
        album_name = track["album"]["name"]
        artists = track["artists"]
        all_artists: List[str] = get_all_artists(artists)
        all_tracks.append(
            Track(name=name, id=id, album_name=album_name, artists=all_artists))
    return all_tracks


def check_or_make_playlist(playlist_name: str) -> None:
    if not youtube_client.is_playlist_in_youtube(playlist_name=playlist_name):
        youtube_client.create_new_playlist(playlist_name=playlist_name)


def handle_each_playlist(playlist_info, youtube_playlist: Playlist) -> None:
    tracks: List[Track] = get_tracks(playlist_info)
    all_video_ids_in_youtube_playlist: List[str] = youtube_client.get_all_video_ids_for_playlist(
        playlist_id=youtube_playlist.id)
    for track in tracks:
        query = f"{track.name}, {', '.join(track.artists)}"
        video_id_from_youtube_search: str = youtube_client.search_name_on_youtube_and_get_video_id(
            query=query)
        if video_id_from_youtube_search in all_video_ids_in_youtube_playlist:
            continue
        youtube_client.add_video_to_playlist(
            playlist_id=youtube_playlist.id, video_id=video_id_from_youtube_search)


def playlist_creation(consider_new_playlist: bool, playlists: List[Playlist]) -> None:
    logging.info('Creating playlists in youtube')
    if consider_new_playlist:
        for playlist in playlists:
            check_or_make_playlist(playlist_name=playlist.name)


if __name__ == "__main__":
    logging.info('Process started')
    consider_new_playlist: bool = sys.argv[1] == '-n' if len(
        sys.argv) > 1 else False
    access_token = get_access_token()
    playlists_info = get_playlists_info(access_token=access_token)
    playlists: List[Playlist] = get_playlists(playlists_info)
    playlist_creation(consider_new_playlist, playlists)
    all_youtube_playlists: List[Playlist] = youtube_client.get_all_playlists_of_user(
    )
    for playlist in playlists:
        youtube_playlists: List[Playlist] = [
            v for v in all_youtube_playlists if v.name == playlist.name]
        if len(youtube_playlists) != 1:
            logging.error(
                f'There must be exactly one playlist in youtube with name: {playlist.name}')
            exit(0)
        youtube_playlist = youtube_playlists.pop()
        playlist_info = get_playlist_info(
            access_token=access_token,
            playlist_id=playlist.id
        )
        handle_each_playlist(
            playlist_info=playlist_info, youtube_playlist=youtube_playlist)
