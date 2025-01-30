import requests
from models import Artist, Song, User, Album

class DataRepository:

    def __init__(self, bot):
        self.bot = bot

    def get_song_lyrics(self, artist_name, song_title):
        url = f"https://api.lyrics.ovh/v1/{artist_name}/"\
        f"{song_title.replace('/', '%2F').replace('.', '')}"
        try:
            return requests.get(url).json().get('lyrics')
        except Exception as e:
            print("Error occured with song: ", song_title)
            print(e)
            return None

    def add_song_from_data(self, data, album: Album):
        lyrics = self.get_song_lyrics(data['artists'][0]['name'], data['name'])
        if not lyrics:
            return
        artist = self.bot.session.query(Artist).filter_by(spotify_id=data['artists'][0]['id']).first()
        existing_album = self.bot.session.query(Album).filter_by(spotify_id=album.spotify_id).first()
        song = self.bot.session.query(Song).filter_by(spotify_id=data['id']).first()
        if not artist:
            artist = Artist(spotify_id=data['artists'][0]['id'], name=data['artists'][0]['name'])
            self.bot.session.add(artist)
        if not existing_album:
            self.bot.session.add(album)
        else:
            album = existing_album
        if not song:
            song = Song(spotify_id=data['id'], title=data['name'], url=data['external_urls'].get('spotify', ''), album=album, lyrics=lyrics, artist=artist)
            self.bot.session.add(song)
        return song

    def get_songs_from_album(self, album_id, user=None):
        album_data = self.bot.spotify.get_album_data(album_id)
        if album_data.get('error'):
            raise ValueError("No album found with that id")
        album = Album(spotify_id=album_data['id'], name=album_data['name'])
        for song in album_data.get('tracks', {}).get('items', []):
            db_song = self.add_song_from_data(song, album)
            if db_song and user and db_song not in user.songs:
                user.songs.append(db_song)
            try:
                self.bot.session.commit()
            except Exception as e:
                print(e)
                print("skipping duplicate: ", song['name'])
                continue

    def get_or_create_user(self, discord_id):
        user = self.bot.session.query(User).filter_by(discord_id=discord_id).first()
        if not user:
            user = User(discord_id=discord_id)
            self.bot.session.add(user)
        return user
