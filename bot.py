from typing import Optional

import discord
import requests
from discord.ext import commands
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Artist, Base, Song
from spotify_api import SpotifyAPI

EXTENSIONS = [
    "Functions.add_data",
    "Functions.guess_lyrics",
    "Functions.get_data",
    "Functions.delete_data",
]


class Bot(commands.Bot):

    def __init__(self, client_id, client_secret, *args, **kwargs):
        self.spotify = SpotifyAPI(client_id, client_secret)
        intents = discord.Intents.default()
        intents.messages = True
        intents.message_content = True

        engine = create_engine("sqlite:///lyrics.db")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        self._session = Session()
        super().__init__(*args, **kwargs, intents=intents, command_prefix="!")

    async def on_ready(self):
        await self.tree.sync()

    async def setup_hook(self) -> None:
        for ext in EXTENSIONS:
            await self.load_extension(ext)
            print("adding ext: ", ext)
        return await super().setup_hook()

    @property
    def session(self):
        return self._session

    async def close(self):
        self._session.close()
        await super().close()
