from logging import INFO

import discord
from discord import app_commands
from discord.ext import commands
from sqlalchemy.exc import NoResultFound
from sqlalchemy.inspection import _self_inspects
from thefuzz import process

from bot import Bot
from data_repository import DataRepository
from models import Artist, GameState, Song
from spotify_api import SpotifyAPI


class GuessLyrics(commands.Cog):
    FIRST_HINT = 5
    SECOND_HINT = 10

    def __init__(self, bot):
        self.bot = bot
        self.game_state = GameState(bot)
        self.repository = DataRepository(bot)

    @commands.Cog.listener()
    async def on_message(self, message):
        if (
            self.game_state.is_game_active
            and not message.author.bot
            and not message.content.startswith("!")
            and message.channel == self.game_state.thread
        ):
            if message.content == "give_up":
                await message.channel.send(
                    f"You guessed {self.game_state.attempts} times.\n"
                    f"The correct answer was: [{self.game_state.song.title}]({self.game_state.song.url})"
                )
                await self.game_state.stop_game()
                return
            if self.game_state.guess(message.content):
                await message.add_reaction("⭐")
                await message.channel.send(
                    f"{message.author.nick if message.author.nick else message.author.display_name} guessed correct!\n"
                    f"It took {self.game_state.attempts} attempts."
                    f"The correct answer was: [{self.game_state.song.title}]({self.game_state.song.url})"
                )
                await self.game_state.stop_game()
            else:
                await message.channel.send("Incorrect guess.")

    @app_commands.command(
        name="start", description="Start a game to guess the lyrics of a song."
    )
    async def start(self, interaction: discord.Interaction):
        if self.game_state.is_game_active:
            await interaction.response.send_message(
                "Game is already active.", ephemeral=True
            )
            return
        try:
            self.game_state.start_game(interaction.user.id)
        except NoResultFound:
            await interaction.response.send_message(
                "You need to add songs first.\nUse `/add_artist <url>` or `/add_album <url>`",
                ephemeral=True,
            )
            return
        thread = await interaction.channel.create_thread(
            name="Guess the lyrics!",
            auto_archive_duration=60,
            type=discord.ChannelType.public_thread,
        )
        self.game_state.thread = thread
        await thread.send(
            f"use `/hint` to get a hint(after {self.FIRST_HINT} and {self.SECOND_HINT} attempts).\n"
            "Type `give_up` to give up."
        )
        lyrics = "\n".join(
            list(
                map(
                    str.strip,
                    self.game_state.song.lyrics.replace("\r", "").split("\n")[:2],
                )
            )
        )
        await thread.send(f">>> {lyrics}")
        await interaction.response.send_message("Game started!", ephemeral=True)

    @app_commands.command(
        name="start_by_album_url",
        description="Start a game to guess the lyrics of a song from an album.",
    )
    async def start_by_album_url(self, interaction: discord.Interaction, url: str):
        if self.game_state.is_game_active:
            return await interaction.response.send_message(
                "Game is already active.", ephemeral=True
            )
        album_id = SpotifyAPI.extract_id_from_url(url)
        if not album_id:
            return await interaction.response.send_message(
                "Invalid album url.", ephemeral=True
            )
        await interaction.response.defer(ephemeral=True)
        try:
            self.repository.get_songs_from_album(album_id)
            self.game_state.start_game_from_album(album_id)
        except ValueError as e:
            return await interaction.followup.send(str(e), ephemeral=True)
        except NoResultFound as e:
            return await interaction.followup.send(str(e), ephemeral=True)
        thread = await interaction.channel.create_thread(
            name="Guess the lyrics!",
            auto_archive_duration=60,
            type=discord.ChannelType.public_thread,
        )
        self.game_state.thread = thread
        await thread.send(
            f"use `/hint` to get a hint(after {self.FIRST_HINT} and {self.SECOND_HINT} attempts).\n"
            "Type `give_up` to give up."
        )
        lyrics = "\n".join(
            self.game_state.song.lyrics.replace("\r", "").split("\n")[:2]
        ).strip()
        await thread.send(f">>> {lyrics}")
        await interaction.followup.send("Game started!", ephemeral=True)

    @app_commands.command(
        name="hint",
        description=f"Get a hint for the current game, hints are given after {FIRST_HINT} and {SECOND_HINT} guesses.",
    )
    async def hint(self, interaction: discord.Interaction):
        if not self.game_state.is_game_active:
            return await interaction.response.send_message(
                "No active game.", ephemeral=True
            )
        if interaction.channel != self.game_state.thread:
            return await interaction.response.send_message(
                "You can only get hints in the game thread.", ephemeral=True
            )
        if self.game_state.attempts < self.FIRST_HINT:
            return await interaction.response.send_message(
                f"You need to guess at least {self.FIRST_HINT} times to get a hint. {self.FIRST_HINT - self.game_state.attempts} guesses left.",
                ephemeral=True,
            )
        await interaction.response.defer()
        if (
            self.game_state.attempts >= self.FIRST_HINT
            and self.game_state.attempts < self.SECOND_HINT
        ):
            return await interaction.followup.send(
                f"Song is by artist: {self.game_state.song.artist.name}\n"
                f"next hint in {self.SECOND_HINT - self.game_state.attempts} guesses."
            )
        elif self.game_state.attempts == self.SECOND_HINT:
            return await interaction.followup.send(
                f"Song is by artist: {self.game_state.song.artist.name}\n"
                f"Song is on album: {self.game_state.song.album.name}"
            )


async def setup(bot):
    await bot.add_cog(GuessLyrics(bot))
