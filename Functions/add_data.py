from discord.ext import commands
from spotify_api import SpotifyAPI
from bot import Bot
import requests
from models import Artist, Song, User
from sqlalchemy.exc import IntegrityError

class AddData(commands.Cog):

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command()
    async def add_artist(self, ctx, url: str):
        artist_id = SpotifyAPI.extract_id_from_url(url)
        if artist_id is None:
            return await ctx.send("Invalid URL.")
        user = self._get_or_create_user(ctx.author.id)
        albums_data = self.bot.spotify.get_artist_albums(artist_id)
        for item in albums_data.get('items', []):
            self._get_songs_from_album(item['id'], user)
        return await ctx.send("Artist added.")

    @commands.command()
    async def add_album(self, ctx, url: str):
        album_id =  SpotifyAPI.extract_id_from_url(url)
        if album_id is None:
            return await ctx.send("Invalid URL.")
        user = self._get_or_create_user(ctx.author.id)
        self._get_songs_from_album(album_id, user)
        return await ctx.send("Album added.")

    def _get_song_lyrics(self, artist_name, song_title):
        url = f"https://api.lyrics.ovh/v1/{artist_name}/"\
        f"{song_title.replace('/', '%2F').replace('.', '')}"
        try:
            return requests.get(url).json().get('lyrics')
        except Exception as e:
            print("Error occured with song: ", song_title)
            print(e)
            return None

    def _add_song_from_data(self, data , user, album_name):
        lyrics = self._get_song_lyrics(data['artists'][0]['name'], data['name'])
        if lyrics is None:
            return
        artist = self.bot.session.query(Artist).filter_by(spotify_id=data['artists'][0]['id']).first()
        song = self.bot.session.query(Song).filter_by(spotify_id=data['id']).first()
        if not artist:
            artist = Artist(spotify_id=data['artists'][0]['id'], name=data['artists'][0]['name'])
            self.bot.session.add(artist)
        if not song:
            song = Song(spotify_id=data['id'], title=data['name'], url=data['external_urls'].get('spotify', ''), album=album_name, lyrics=lyrics, artist=artist)
            self.bot.session.add(song)
        if song not in user.songs:
            user.songs.append(song)
        try:
            self.bot.session.commit()
        except Exception as e:
            print(e)
            print("skipping duplicate: ", data['name'])
            return

    def _get_songs_from_album(self, album_id, user):
        album_data = self.bot.spotify.get_album_data(album_id)
        album_name = album_data.get('name')
        for song in album_data.get('tracks', {}).get('items', []):
            self._add_song_from_data(song, user, album_name)

    def _get_or_create_user(self, discord_id):
        user = self.bot.session.query(User).filter_by(discord_id=discord_id).first()
        if not user:
            user = User(discord_id=discord_id)
            self.bot.session.add(user)
        return user

async def setup(bot):
    await bot.add_cog(AddData(bot))
