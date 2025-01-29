from logging import INFO

import discord
from bot import Bot
from discord.ext import commands
from models import Artist, Song, GameState
from sqlalchemy.exc import NoResultFound
from thefuzz import process

class GuessLyric(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.game_state = GameState(bot)

    @commands.Cog.listener()
    async def on_message(self, message):
        if (
            self.game_state.is_game_active
            and not message.author.bot
            and not message.content.startswith('!')
            and message.channel == self.game_state.thread
        ):
            if message.content == 'give_up':
                await message.channel.send(
                    f"You guessed {self.game_state.attempts} times.\n"
                    f"The correct answer was: {self.game_state.song.title}"
                )
                await self.game_state.stop_game()
                return
            if self.game_state.guess(message.content):
                await message.channel.send(
                    f"{message.author.nick if message.author.nick else message.author.display_name} guessed correct!\n"
                    f"It took {self.game_state.attempts} attempts."
                    f"The correct answer was: {self.game_state.song.title}"
                )
                await self.game_state.stop_game()
            else:
                await message.channel.send("Incorrect guess.")

    @commands.command()
    async def guess_lyric(self, ctx, *, users=None):
        print(users)
        if self.game_state.is_game_active:
            await ctx.send("Game is already active.")
            return
        try:
            self.game_state.start_game(ctx.author.id)
        except NoResultFound:
            await ctx.send("You need to add songs first.\n"\
                "use `!add_artist <url>` or `!add_album <url>`")
            return
        thread = await ctx.channel.create_thread(
            name="Guess the lyric",
            auto_archive_duration=60,
            type=discord.ChannelType.public_thread
        )
        self.game_state.thread = thread
        await thread.send(
            "use `!hint` to get a hint(after 5 and 10 attempts).\n"
            "Type `give_up` to give up."
        )
        print(self.game_state.song.lyrics.split('\r\n')[:2])
        await thread.send('\n'.join(self.game_state.song.lyrics.split('\r\n')[:2]))

    @commands.command()
    async def hint(self, ctx):
        if not self.game_state.is_game_active:
            return await ctx.send("No active game.")
        if ctx.channel != self.game_state.thread:
            return
        if self.game_state.attempts < 5:
            return await ctx.channel.send(f"You need to guess at least 5 times to get a hint. {5 - self.game_state.attempts} guesses left.")
        if self.game_state.attempts == 5:
            return await ctx.channel.send(
                f"Song is by artist: {self.game_state.song.artist.name}"
                f"next hint in {10 - self.game_state.attempts} guesses."
            )
        elif self.game_state.attempts == 10:
            return await ctx.channel.send(
                f"Song is by artist: {self.game_state.song.artist.name}\n"
                f"Song is on album: {self.game_state.song.album}"
            )


async def setup(bot):
    await bot.add_cog(GuessLyric(bot))
