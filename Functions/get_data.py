import csv
import io

import discord
from discord import app_commands
from discord.ext import commands
from tabulate import tabulate

from bot import Bot
from models import Song, User


class GetData(commands.Cog):

    MAX_NAME_LENGTH = 17
    PREVIEW_ROWS = 20

    def __init__(self, bot):
        self.bot = bot

    def generate_file(self, data):
        table = tabulate(data, headers="keys", tablefmt="grid")
        file_output = io.StringIO()
        file_output.write(table)
        file_output.seek(0)
        text_file = io.BytesIO(file_output.getvalue().encode())

        return discord.File(fp=text_file, filename="data.txt")

    @app_commands.command(
        name="get_artists",
        description="Lists all artists added to the user and the `artist_id` to help with removing them from user",
    )
    async def get_artists(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user = (
            self.bot.session.query(User)
            .filter_by(discord_id=interaction.user.id)
            .first()
        )
        if user:
            artists = {s.artist for s in user.songs}
            objects = []
            for artist in artists:
                objects.append(
                    {
                        "Id": artist.id,
                        "Name": (
                            artist.name[: self.MAX_NAME_LENGTH] + "..."
                            if len(artist.name) > self.MAX_NAME_LENGTH + 3
                            else artist.name
                        ),
                    }
                )
            file = self.generate_file(objects)
            return await interaction.followup.send(file=file, ephemeral=True)
        else:
            return await interaction.followup.send("No user found.", ephemeral=True)

    @app_commands.command(
        name="get_albums",
        description="Lists all albums added to the user and the `album_id` to help with removing them from the user",
    )
    async def get_albums(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user = (
            self.bot.session.query(User)
            .filter_by(discord_id=interaction.user.id)
            .first()
        )
        if user:
            albums = {s.album for s in user.songs}
            objects = []
            for album in albums:
                objects.append(
                    {
                        "Id": album.id,
                        "Name": (
                            album.name[: self.MAX_NAME_LENGTH] + "..."
                            if len(album.name) > self.MAX_NAME_LENGTH + 3
                            else album.name
                        ),
                    }
                )
            file = self.generate_file(objects)
            return await interaction.followup.send(file=file, ephemeral=True)
        else:
            return await interaction.followup.send("No user found.", ephemeral=True)

    @app_commands.command(
        name="get_songs",
        description="Lists all songs added to the user and the `song_id` to help with removing them from the user",
    )
    async def get_songs(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user = (
            self.bot.session.query(User)
            .filter_by(discord_id=interaction.user.id)
            .first()
        )
        if user:
            objects = []
            for song in user.songs:
                objects.append(
                    {
                        "Id": song.id,
                        "Title": (
                            song.title[: self.MAX_NAME_LENGTH] + "..."
                            if len(song.title) > self.MAX_NAME_LENGTH + 3
                            else song.title
                        ),
                    }
                )
            table = tabulate(
                objects[: self.PREVIEW_ROWS], headers="keys", tablefmt="grid"
            )
            file = self.generate_file(objects)
            return await interaction.followup.send(file=file, ephemeral=True)
        else:
            return await interaction.followup.send("No user found.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(GetData(bot))
