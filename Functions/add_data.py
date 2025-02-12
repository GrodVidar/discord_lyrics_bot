import discord
import requests
from discord import app_commands
from discord.ext import commands
from sqlalchemy.exc import IntegrityError

from bot import Bot
from data_repository import DataRepository
from models import Artist, Song, User
from spotify_api import SpotifyAPI


class AddData(commands.Cog):

    def __init__(self, bot: Bot):
        self.bot = bot
        self.repository = DataRepository(bot)

    @app_commands.command(
        name="add_artist", description="Add an artist to the database."
    )
    async def add_artist(self, interaction: discord.Interaction, url: str):
        await interaction.response.defer(ephemeral=True)
        artist_id = SpotifyAPI.extract_id_from_url(url)
        if artist_id is None:
            return await interaction.followup.send("Invalid URL.", ephemeral=True)
        user = self.repository.get_or_create_user(interaction.user.id)
        albums_data = self.bot.spotify.get_artist_albums(artist_id)
        if albums_data.get("error"):
            return await interaction.followup.send(
                "No artist found with that id.", ephemeral=True
            )
        progress_message = await interaction.followup.send(
            "Processing albums...", ephemeral=True
        )
        songs_added = 0
        albums_added = 0
        for i, item in enumerate(albums_data.get("items", [])):
            albums_added += 1
            await progress_message.edit(
                content=f"Processing album {albums_added + 1}: {item['name']}"
            )
            songs_added += self.repository.get_songs_from_album(item["id"], user)
        return await progress_message.edit(
            content=f"Artist added with {songs_added} songs."
        )

    @app_commands.command(name="add_album", description="Add an album to the database.")
    async def add_album(self, interaction: discord.Interaction, url: str):
        await interaction.response.defer(ephemeral=True)
        album_id = SpotifyAPI.extract_id_from_url(url)
        if not album_id:
            return await interaction.followup.send("Invalid URL.", ephemeral=True)
        user = self.repository.get_or_create_user(interaction.user.id)
        songs_added = 0
        try:
            songs_added = self.repository.get_songs_from_album(album_id, user)
        except ValueError:
            return await interaction.followup.send(
                "No album found with that id", ephemeral=True
            )
        return await interaction.followup.send(
            f"Album added with {songs_added} songs", ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(AddData(bot))
