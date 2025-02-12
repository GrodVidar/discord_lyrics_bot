import discord
from discord import app_commands
from discord.ext import commands

from bot import Bot
from models import Song, User


class DeleteData(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="delete_artist",
        description="Removes all songs from artist, related to user",
    )
    async def delete_artist(self, interaction: discord.Interaction, artist_id: int):
        await interaction.response.defer(ephemeral=True)
        user = (
            self.bot.session.query(User)
            .filter_by(discord_id=interaction.user.id)
            .first()
        )
        if user:
            songs = (
                self.bot.session.query(Song)
                .filter(Song.users.contains(user), Song.artist_id == artist_id)
                .all()
            )

            if not songs:
                return await interaction.followup.send(
                    f"No songs linked to artist_id({artist_id}) found for user",
                    ephemeral=True,
                )

            for song in songs:
                song.users.remove(user)

            self.bot.session.commit()
            await interaction.followup.send(
                f"Removed all songs related to artist({artist_id})", ephemeral=True
            )
        else:
            await interaction.followup.send("No user found.", ephemeral=True)

    @app_commands.command(
        name="delete_album", description="Removes all songs from album, related to user"
    )
    async def delete_album(self, interaction: discord.Interaction, album_id: int):
        await interaction.response.defer(ephemeral=True)
        user = (
            self.bot.session.query(User)
            .filter_by(discord_id=interaction.user.id)
            .first()
        )
        if user:

            songs = (
                self.bot.session.query(Song)
                .filter(Song.users.contains(user), Song.album_id == album_id)
                .all()
            )

            if not songs:
                return await interaction.followup.send(
                    f"No songs linked to album_id({album_id}) found for user",
                    ephemeral=True,
                )

            for song in songs:
                song.users.remove(user)

            self.bot.session.commit()
            await interaction.followup.send(
                f"Removed all songs related to album({album_id})", ephemeral=True
            )
        else:
            await interaction.followup.send("No user found.", ephemeral=True)

    @app_commands.command(
        name="delete_song", description="Removes song by id, related to user"
    )
    async def delete_song(self, interaction: discord.Interaction, song_id: int):
        await interaction.response.defer(ephemeral=True)
        user = (
            self.bot.session.query(User)
            .filter_by(discord_id=interaction.user.id)
            .first()
        )
        if user:
            song = (
                self.bot.session.query(Song)
                .filter(Song.users.contains(user), id == song_id)
                .first()
            )

            if not song:
                return await interaction.followup.send(
                    f"No songs linked to id({song_id}) found for user", ephemeral=True
                )

            song.users.remove(user)

            self.bot.session.commit()
            await interaction.followup.send(f"Removed song({song_id})", ephemeral=True)
        else:
            await interaction.followup.send("No user found.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(DeleteData(bot))
