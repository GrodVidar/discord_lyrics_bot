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

    @property
    def session(self):
        return self._session

    async def close(self):
        self._session.close()
        await super().close()
