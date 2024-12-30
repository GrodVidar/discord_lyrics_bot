import discord
from discord.ext import commands
from sqlalchemy.orm import sessionmaker
from models import Base
from sqlalchemy import create_engine



class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        intents = discord.intents.default()
        intents.messages = True
        intents.message_content = True
        super().__init__(*args, **kwargs, intents=intents)

        engine = create_engine('sqlite:///lyrics.db')
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        self._session = Session()

    @property
    def session(self) -> Session:
        return self._session

    async def close(self):
        self._session.close()
        await super().close()
