import asyncio
import os
import sys
import traceback

import discord
from discord.ext import commands
from discord_slash import SlashCommand

import hypixelaPY
import ksoftapi
from config import Config
from core.hypixel import Hypixel_
from core.lastfm import LastFM_
from core.static import Static
from data.data import Data

config = Config()
data = Data()
os.environ["JISHAKU_NO_UNDERSCORE"] = "True"


async def get_prefix(bot, message):
    if isinstance(message.channel, discord.DMChannel) or not message.guild:
        return commands.when_mentioned_or(config.default_prefix, "myaer ", "Myaer ")(bot, message)
    prefix = data.guilds.get_silent(message.guild.id).prefix or config.default_prefix
    return commands.when_mentioned_or(prefix, "myaer ", "Myaer ")(bot, message)


bot = commands.Bot(
    command_prefix=get_prefix,
    owner_id=config.owner,
    allowed_mentions=discord.AllowedMentions(everyone=False, replied_user=False),
    intents=discord.Intents.all()
)
slash = SlashCommand(bot, override_type=True, auto_register=True, auto_delete=True)
bot.static = Static(bot)
bot.config = config
bot.data = data
bot.mojang = hypixelaPY.Mojang()
bot.ksoft = ksoftapi.Client(config.keys.ksoft)

extensions = [os.path.join(dp, f) for dp, dn, fn in os.walk("cogs") for f in fn] + \
             [os.path.join(dp, f) for dp, dn, fn in os.walk("commands") for f in fn] + \
             [os.path.join(dp, f) for dp, dn, fn in os.walk("modules") for f in fn] + \
             [os.path.join(dp, f) for dp, dn, fn in os.walk("events") for f in fn] + \
             ["jishaku", "initialize"]
for file in extensions[:]:
    if not file.endswith(".py") and file not in ["jishaku", "initialize"]:  # jishaku cog is a special case
        extensions.remove(file)
bot.static.failed_extensions = []

for extension in extensions:
    try:
        bot.load_extension(((extension.replace("/", "."))[:-3]) if extension.endswith(".py") else extension)
        # i. don't. want. to. talk. about. it.
    except Exception as e:
        exception = '{}: {}'.format(type(e).__name__, e)
        print("Failed to load extension {}\n{}".format(extension, exception))
        error_traceback = "".join(traceback.format_exception(type(e), e, e.__traceback__))
        bot.static.failed_extensions.append((extension, error_traceback))


@bot.event
async def on_error(event, *args, **kwargs):
    error = sys.exc_info()
    error_traceback = "".join(traceback.format_exception(error[0], error[1], error[2]))
    print(error_traceback)
    await bot.config.channels.events.send(embed=discord.Embed(
        title="Exception",
        description=f"```{error_traceback}```",
        timestamp=bot.static.time()
    ))


async def start():
    try:
        bot.hypixel = await Hypixel_(bot, config.keys.hypixel)
        bot.lastfm = await LastFM_(bot, config.keys.lastfm)
        await bot.start(config.token)
    except KeyboardInterrupt:
        await bot.logout()


async def stop():
    await bot.logout()


if __name__ == "__main__":
    try:
        asyncio.get_event_loop().run_until_complete(start())
    except KeyboardInterrupt:
        asyncio.get_event_loop().run_until_complete(stop())
