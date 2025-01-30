from typing_extensions import CapsuleType
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import func
from sqlalchemy.exc import NoResultFound
from typing import Optional
from sqlalchemy import UniqueConstraint
from thefuzz import fuzz

Base = declarative_base()

class Artist(Base):
    __tablename__ = 'artists'

    id = Column(Integer, primary_key=True, index=True)
    spotify_id = Column(String, unique=True, index=True)
    name = Column(String, unique=True, index=True)

    albums = relationship('Album', back_populates='artist')
    songs = relationship('Song', back_populates='artist')

class Album(Base):
    __tablename__ = 'albums'

    id = Column(Integer, primary_key=True, index=True)
    spotify_id = Column(String, unique=True, index=True)
    name = Column(String, index=True)
    artist_id = Column(Integer, ForeignKey('artists.id'))

    artist = relationship('Artist', back_populates='albums')
    songs = relationship('Song', back_populates='album')

    @classmethod
    def get_random_song(cls, session, album_spotify_id):
        album = session.query(cls).filter_by(spotify_id=album_spotify_id).first()
        if album:
            return session.query(Song).filter_by(album_id=album.id).order_by(func.random()).first()
        raise NoResultFound("No songs/lyrics found for that album")

user_song = Table(
    'user_song',
    Base.metadata,
    Column('song_id', Integer, ForeignKey('songs.id')),
    Column('user_id', Integer, ForeignKey('users.id'))
)

class Song(Base):
    __tablename__ = 'songs'

    id = Column(Integer, primary_key=True, index=True)
    spotify_id = Column(String, unique=True, index=True)
    title = Column(String, index=True)
    lyrics = Column(String)
    album = Column(String)
    url = Column(String)
    album_id = Column(Integer, ForeignKey('albums.id'))
    artist_id = Column(Integer, ForeignKey('artists.id'))

    album = relationship('Album', back_populates='songs')
    artist = relationship('Artist', back_populates='songs')
    users = relationship('User', secondary=user_song, back_populates='songs')

    __table_args__ = (
        UniqueConstraint('title', 'artist_id', name='unique_song_title_artist'),
    )


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    discord_id = Column(Integer, unique=True, index=True)
    songs = relationship('Song', secondary=user_song, back_populates='users')

    @classmethod
    def get_random_song(cls, session, discord_id) -> Optional[Song]:
        user = session.query(cls)\
        .filter_by(discord_id=discord_id)\
        .first()
        if user and user.songs:
            return session.query(Song)\
            .filter(Song.users.contains(user))\
            .order_by(func.random())\
            .first()
        raise NoResultFound("No songs found for this user")

class GameState:
    threshold = 80
    def __init__(self, bot) -> None:
        self.bot = bot
        self.attempts = 0
        self.song = None
        self.thread = None
        self.is_game_active = False

    def start_game(self, user_id):
        self.attempts = 0
        self.song = User.get_random_song(self.bot.session, user_id)
        self.is_game_active = True

    def start_game_from_album(self, album_id):
        self.attempts = 0
        self.song = Album.get_random_song(self.bot.session, album_id)
        self.is_game_active = True

    async def stop_game(self):
        self.attempts = 0
        self.song = None
        await self.thread.edit(archived=True)
        self.thread = None
        self.is_game_active = False

    def guess(self, guess):
        self.attempts += 1
        ratio = fuzz.ratio(self.song.title.lower(), guess.lower())
        return ratio >= self.threshold
