import requests
from typing import List
from classes.playlist import Playlist
from classes.track import Track
from youtube_client import YouTubeClient
import json
import sys
import logging

logging.basicConfig(level=logging.INFO)
spotify_credentials = json.load(open('secrets/client_secret_spotify.json'))
youtube_client = YouTubeClient()
SPOTIFY_BASE_URL = 'https://api.spotify.com/v1/'


def __get_access_token():
    auth_response = requests.post(spotify_credentials["AUTH_URL"], {
        'grant_type': 'client_credentials',
        'client_id': spotify_credentials["CLIENT_ID"],
        'client_secret': spotify_credentials["CLIENT_SECRET"],
    }, timeout=30)
    auth_response_data = auth_response.json()
    return auth_response_data['access_token']


def __get_header(access_token):
    headers = {
        'Authorization': 'Bearer {token}'.format(token=access_token)
    }
    return headers


def __get_playlists_info(access_token):
    logging.info(f'Getting all spotify playlists of user')
    headers = __get_header(access_token)
    r = requests.get(
        SPOTIFY_BASE_URL + f'users/{spotify_credentials["USER_ID"]}/playlists', headers=headers, timeout=30)
    return (r.json())


def __get_playlist_info(access_token, playlist_id):
    logging.info(f'Getting playlist info for playlist id: {playlist_id}')
    headers = __get_header(access_token)
    r = requests.get(
        SPOTIFY_BASE_URL + f'playlists/{playlist_id}', headers=headers, timeout=30)
    return (r.json())


def __get_playlists(playlists_info) -> List[Playlist]:
    items = playlists_info["items"]
    return list(map(lambda item: Playlist(item["id"], item["name"], item["tracks"]["total"]), items))


def __get_all_artists(artists) -> List[str]:
    return list(map(lambda v: v["name"], artists))


def __get_tracks(playlist_info) -> List[Track]:
    items = playlist_info["tracks"]["items"]
    all_tracks: List[Track] = []
    for item in items:
        track = item["track"]
        name = track["name"]
        _id = track["id"]
        album_name = track["album"]["name"]
        artists = track["artists"]
        all_artists: List[str] = __get_all_artists(artists)
        all_tracks.append(
            Track(name=name, id=_id, album_name=album_name, artists=all_artists))
    return all_tracks


def __check_or_make_playlist(playlist_name: str) -> None:
    if not youtube_client.is_playlist_in_youtube(playlist_name=playlist_name):
        youtube_client.create_new_playlist(playlist_name=playlist_name)


def __handle_each_playlist(playlist_info, youtube_playlist: Playlist) -> None:
    tracks: List[Track] = __get_tracks(playlist_info)
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


def __playlist_creation(playlists: List[Playlist]) -> None:
    consider_new_playlist: bool = sys.argv[1] == '-n' if len(
        sys.argv) > 1 else False
    if not consider_new_playlist:
        return
    logging.info('Creating playlists in youtube')
    for playlist in playlists:
        __check_or_make_playlist(playlist_name=playlist.name)


def __sync_playlists(access_token) -> List[Playlist]:
    access_token = __get_access_token()
    playlists_info = __get_playlists_info(access_token=access_token)
    playlists: List[Playlist] = __get_playlists(playlists_info)
    __playlist_creation(playlists)
    return playlists


def __sync_tracks(access_token, playlists: List[Playlist]):
    all_youtube_playlists: List[Playlist] = youtube_client.get_all_playlists_of_user(
    )
    for playlist in playlists:
        youtube_playlists: List[Playlist] = [
            v for v in all_youtube_playlists if v.name == playlist.name]
        if len(youtube_playlists) != 1:
            logging.error(
                f'There must be exactly one playlist in youtube with name: {playlist.name}')
            sys.exit(0)
        youtube_playlist = youtube_playlists.pop()
        playlist_info = __get_playlist_info(
            access_token=access_token,
            playlist_id=playlist.id
        )
        __handle_each_playlist(
            playlist_info=playlist_info, youtube_playlist=youtube_playlist)


if __name__ == "__main__":
    logging.info('Process started')
    access_token = __get_access_token()
    playlists: List[Playlist] = __sync_playlists(access_token=access_token)
    __sync_tracks(access_token=access_token, playlists=playlists)
