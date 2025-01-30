import discord
from discord.ext import commands
from discord import app_commands
from spotify_api import SpotifyAPI
from bot import Bot
import requests
from models import Artist, Song, User
from sqlalchemy.exc import IntegrityError
from data_repository import DataRepository

class AddData(commands.Cog):

    def __init__(self, bot: Bot):
        self.bot = bot
        self.repository = DataRepository(bot)

    @app_commands.command(name="add_artist", description="Add an artist to the database.")
    async def add_artist(self, interaction: discord.Interaction, url: str):
        await interaction.response.defer()
        artist_id = SpotifyAPI.extract_id_from_url(url)
        if artist_id is None:
            return await interaction.followup.send("Invalid URL.", ephemeral=True)
        user = self.repository.get_or_create_user(interaction.user.id)
        albums_data = self.bot.spotify.get_artist_albums(artist_id)
        if albums_data.get('error'):
            return await interaction.followup.send("No artist found with that id.", ephemeral=True)
        for item in albums_data.get('items', []):
            self.repository.get_songs_from_album(item['id'], user)
        return await interaction.followup.send("Artist added.", ephemeral=True)

    @app_commands.command(name="add_album", description="Add an album to the database.")
    async def add_album(self, interaction: discord.Interaction, url: str):
        await interaction.response.defer()
        album_id =  SpotifyAPI.extract_id_from_url(url)
        if not album_id:
            return await interaction.followup.send("Invalid URL.", ephemeral=True)
        user = self.repository.get_or_create_user(interaction.user.id)
        try:
            self.repository.get_songs_from_album(album_id, user)
        except ValueError:
            return await interaction.followup.send("No album found with that id", ephemeral=True)
        return await interaction.followup.send("Album added.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(AddData(bot))
