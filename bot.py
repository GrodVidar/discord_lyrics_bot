import discord
from discord.ext import commands
from sqlalchemy.orm import sessionmaker
from models import Base, Artist, Song
from sqlalchemy import create_engine
from spotify_api import SpotifyAPI
import requests
from typing import Optional


class Bot(commands.Bot):
    def __init__(self, client_id, client_secret, *args, **kwargs):
        self.spotify = SpotifyAPI(client_id, client_secret)
        intents = discord.Intents.default()
        intents.messages = True
        intents.message_content = True
        super().__init__(*args, **kwargs, intents=intents)

        engine = create_engine('sqlite:///lyrics.db')
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        self._session = Session()

    def get_song_lyrics(self, artist_name, song_title) -> Optional[str]:
        url = f"https://api.lyrics.ovh/v1/{artist_name}/{song_title}"
        try:
            return requests.get(url).json().get('lyrics')
        except Exception as e:
            print(e)
            return None

    def add_song_from_data(self, data):
        lyrics = self.get_song_lyrics(data['artists'][0]['name'], data['name'])
        if lyrics is None:
            return
        artist = self._session.query(Artist).filter_by(spotify_id=data['artists'][0]['id']).first()
        song = self._session.query(Song).filter_by(spotify_id=data['id']).first()
        if not artist:
            artist = Artist(spotify_id=data['artists'][0]['id'], name=data['artists'][0]['name'])
            self._session.add(artist)
        if not song:
            song = Song(spotify_id=data['id'], title=data['name'], lyrics=lyrics, artist=artist)
            self._session.add(song)

    def get_songs_from_album(self, album_id):
        songs_data = self.spotify.get_album_songs(album_id)
        for song in songs_data.get('items', []):
            self.add_song_from_data(song)


    @property
    def session(self):
        return self._session

    async def close(self):
        self._session.close()
        await super().close()
