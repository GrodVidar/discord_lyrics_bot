import os

from dotenv import load_dotenv
from bot import Bot


if __name__ == "__main__":
    load_dotenv()
    TOKEN = os.getenv("DISCORD_TOKEN")
    GAME = os.getenv("DISCORD_GAME")

    client = Bot(command_prefix="!", activity=discord.Game(name=GAME))

    cogs = ['Functions.guess_lyric']

    @client.event
    async def on_ready():
        print("Bot is ready.")
        for cog in cogs:
            client.load_extension(cog)

    client.run(TOKEN)
