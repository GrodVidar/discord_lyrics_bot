from datetime import datetime

import requests

MARKET = "SE"
LIMIT = 50


class SpotifyAPI:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.expires_at = None

    @classmethod
    def extract_id_from_url(cls, url):
        return url.split("/")[-1].split("?")[0]

    def _renew_access_token(self, client_id, client_secret):
        url = "https://accounts.spotify.com/api/token"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        }
        try:
            resp = requests.post(url, headers=headers, data=data).json()
            self.access_token = resp["access_token"]
            self.expires_in = datetime.now().timestamp() + resp["expires_in"]
        except requests.exceptions.RequestException as e:
            print(e)

    def _get_valid_token(self):
        if self.access_token is None or datetime.now().timestamp() > self.expires_in:
            self._renew_access_token(self.client_id, self.client_secret)
        return self.access_token

    def get_album_data(self, album_id) -> dict:
        url = f"https://api.spotify.com/v1/albums/{album_id}"
        token = self._get_valid_token()
        headers = {"Authorization": f"Bearer {token}"}
        params = {"market": MARKET}
        try:
            return requests.get(url, headers=headers, params=params).json()
        except requests.exceptions.RequestException as e:
            print(e)
            return {}

    def get_album_songs(self, album_id) -> dict:
        url = f"https://api.spotify.com/v1/albums/{album_id}/tracks"
        token = self._get_valid_token()
        headers = {"Authorization": f"Bearer {token}"}
        params = {
            "market": MARKET,
            "limit": LIMIT,
        }
        try:
            return requests.get(url, headers=headers, params=params).json()
        except requests.exceptions.RequestException as e:
            print(e)
            return {}

    def get_artist_albums(self, artist_id) -> dict:
        url = f"https://api.spotify.com/v1/artists/{artist_id}/albums"
        token = self._get_valid_token()
        headers = {"Authorization": f"Bearer {token}"}
        params = {
            "market": MARKET,
            "include_groups": "single,album",
            "limit": LIMIT,
        }
        try:
            return requests.get(url, headers=headers, params=params).json()
        except requests.exceptions.RequestException as e:
            print(e)
            return {}
