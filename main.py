import discord
from discord.ext import commands
from config.loader import Config
from models import init_db

config = Config()

intents = discord.Intents.default()
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix=config.prefix, intents=intents)

# Charger les cogs
initial_cogs = ["cogs.game", "cogs.control", "cogs.admin"]

init_db()

@bot.event
async def on_ready():
    print(f"✅ Connecté en tant que {bot.user}")
    # Synchronisation globale
    await bot.tree.sync()
    print("✅ Slash commands synchronisées.")


async def setup_hook():
    # Chargement asynchrone des cogs au démarrage
    for cog in initial_cogs:
        await bot.load_extension(cog)


bot.setup_hook = setup_hook

bot.run(config.token)
