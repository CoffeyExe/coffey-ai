# -*- coding: utf-8 -*-
import os
import json
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Charger la config
def load_config():
    if os.path.exists("config.json"):
        with open("config.json", "r") as f:
            return json.load(f)
    return {}

# Fonction pour récupérer le préfixe dynamiquement
def get_prefix(bot, message):
    config = load_config()
    guild_id = str(message.guild.id) if message.guild else None
    if guild_id and guild_id in config and "prefix" in config[guild_id]:
        return config[guild_id]["prefix"]
    return "!"

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix=get_prefix, intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} est connecte et pret.')
    try:
        synced = await bot.tree.sync()
        print(f'✅ {len(synced)} slash commands synchronisees.')
    except Exception as e:
        print(f'Erreur lors de la synchronisation: {e}')

async def main():
    async with bot:
        await bot.load_extension('cogs.general')
        await bot.load_extension('cogs.config')
        await bot.load_extension('cogs.moderation')
        await bot.load_extension('cogs.reactionrole')
        await bot.load_extension('cogs.giveaways')
        await bot.start(TOKEN)

import asyncio
asyncio.run(main())
