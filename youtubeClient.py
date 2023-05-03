from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from typing import List
import os
import pickle

from classes.playlist import Playlist


class YouTubeClient:
    youtube = None
    SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]

    def __init__(self) -> None:
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
        api_service_name = "youtube"
        api_version = "v3"
        client_secrets_file = "client_secret_youtube.json"
        credentials = None
        if os.path.exists("token.pickle"):
            with open("token.pickle", "rb") as token:
                credentials = pickle.load(token)
        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    client_secrets_file, self.SCOPES)
                credentials = flow.run_local_server(port=0)
            with open("token.pickle", "wb") as token:
                pickle.dump(credentials, token)
        self.youtube = build(api_service_name, api_version,
                             credentials=credentials)

    def get_video_details(self, **kwargs):
        return self.youtube.videos().list(
            part="snippet,contentDetails,statistics",
            **kwargs
        ).execute()

    def get_all_playlists_of_user(self) -> List[Playlist]:
        response = self.youtube.playlists().list(part="snippet,contentDetails",
                                                 maxResults=25,
                                                 mine=True).execute()
        results = response['items']
        return List(map(lambda v: Playlist(id=v["id"], name=v["localized"]["title"], total_tracks=v["contentDetails"]["itemCount"]), results))

    def create_new_playlist(self, playlist_name: str):
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
        request = self.youtube.playlistItems().list(
            part="snippet,contentDetails",
            maxResults=100,
            playlistId=playlist_id
        )
        response = request.execute()
        videos = response["items"]
        return List(map(lambda v: v["contentDetails"]["videoId"], videos))

    # this is not idempotent

    def add_video_to_playlist(self, playlist_id: str, video_id: str):
        return self.youtube.playlistItems().insert(
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

    def get_all_playlist_info(self, playlists: List[dict]) -> List[Playlist]:
        return List(map(lambda v: Playlist(id=v["id"], name=v["localized"]["title"], total_tracks=v["contentDetails"]["itemCount"]), playlists))

    def search_name_on_youtube_and_get_video_id(self, query: str):
        request = self.youtube.search().list(
            part="snippet",
            maxResults=3,
            q=query
        )
        response = request.execute()
        results = response["items"]
        filtered_results = filter(
            lambda v: v["id"]["kind"] == "youtube#video", results)
        return filtered_results[0]["id"]["videoId"]

    def is_playlist_in_youtube(self, playlist_name: str):
        all_playlists: List[Playlist] = self.get_all_playlists_of_user(
            youtube=self.youtube)
        for playlist in all_playlists:
            if playlist_name == playlist.name:
                return True
        return False
