from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from typing import List
import os
import pickle
from util import get_random_time_interval_to_sleep
import time
from classes.playlist import Playlist
import logging


logging.basicConfig(level=logging.INFO)


class YouTubeClient:
    youtube = None
    SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]

    def __init__(self) -> None:
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
        api_service_name = "youtube"
        api_version = "v3"
        youtube_credentials = "secrets/client_secret_youtube.json"
        credentials = None
        if os.path.exists("token.pickle"):
            with open("token.pickle", "rb") as token:
                credentials = pickle.load(token)
        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    youtube_credentials, self.SCOPES)
                credentials = flow.run_local_server(port=0)
            with open("token.pickle", "wb") as token:
                pickle.dump(credentials, token)
        self.youtube = build(api_service_name, api_version,
                             credentials=credentials)

    def get_all_playlists_of_user(self) -> List[Playlist]:
        logging.info('Getting details of all the YT playlist for user')
        response = self.youtube.playlists().list(part="snippet,contentDetails",
                                                 maxResults=25,
                                                 mine=True).execute()
        results = response['items']
        return list(map(lambda v: Playlist(id=v["id"], name=v["snippet"]["title"], total_tracks=v["contentDetails"]["itemCount"]), results))

    def create_new_playlist(self, playlist_name: str):
        logging.info(f'Creating playlist: {playlist_name} in YT')
        return self.youtube.playlists().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": playlist_name,
                    "defaultLanguage": "en"
                },
                "status": {
                    "privacyStatus": "private"
                }
            }
        ).execute()

    def get_all_video_ids_for_playlist(self, playlist_id: str) -> List[str]:
        logging.info(
            f'Getting all videos in YT playlist with id: {playlist_id}')
        request = self.youtube.playlistItems().list(
            part="snippet,contentDetails",
            maxResults=100,
            playlistId=playlist_id
        )
        response = request.execute()
        videos = response["items"]
        return list(map(lambda v: v["contentDetails"]["videoId"], videos))

    # Operation not idempotent
    # Added a random timer to avoid spamming and 409s
    def add_video_to_playlist(self, playlist_id: str, video_id: str):
        time.sleep(get_random_time_interval_to_sleep())
        logging.info(
            f'Adding video id: {video_id} to YT playlist id: {playlist_id}')
        try:
            self.youtube.playlistItems().insert(
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": playlist_id,
                        "position": 0,
                        "resourceId": {
                            "kind": "youtube#video",
                            "videoId": video_id
                        }
                    }
                }
            ).execute()
            logging.info(
                f'Successfully added video id: {video_id} to YT playlist id: {playlist_id}')
        except Exception as e:
            logging.error(
                f'Failed to add video id: {video_id} to YT playlist id: {playlist_id}, due to {e}')

    def get_all_playlist_info(self, playlists: List[dict]) -> List[Playlist]:
        return list(map(lambda v: Playlist(id=v["id"], name=v["localized"]["title"], total_tracks=v["contentDetails"]["itemCount"]), playlists))

    def search_name_on_youtube_and_get_video_id(self, query: str) -> str:
        logging.info(f'Searching YT for query: {query}')
        request = self.youtube.search().list(
            part="snippet",
            maxResults=3,
            q=query
        )
        response = request.execute()
        results = response["items"]
        filtered_results = [v for v in results if v["id"]
                            ["kind"] == "youtube#video"]
        return filtered_results[0]["id"]["videoId"]

    def is_playlist_in_youtube(self, playlist_name: str) -> bool:
        all_playlists: List[Playlist] = self.get_all_playlists_of_user()
        for playlist in all_playlists:
            if playlist_name == playlist.name:
                return True
        return False
