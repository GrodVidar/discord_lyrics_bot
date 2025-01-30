import os

from dotenv import load_dotenv
from bot import Bot
import discord


if __name__ == "__main__":
    load_dotenv()
    TOKEN = os.getenv("DISCORD_TOKEN", '')
    GAME = os.getenv("DISCORD_GAME", "lyrics_guesser")
    CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
    CLIENT_SECRET = os.getenv("SPOTIFY_SECRET")

    bot = Bot(CLIENT_ID, CLIENT_SECRET, command_prefix="!", activity=discord.Game(name=GAME))

    cogs = ['Functions.add_data', 'Functions.guess_lyrics']

    @bot.event
    async def on_ready():
        print("Bot is ready.")
        for cog in cogs:
            await bot.load_extension(cog)
        try:
            synced = await bot.tree.sync()
            print(f"Synced {len(synced)} commands.")
        except Exception as e:
            print(e)

    bot.run(TOKEN)
