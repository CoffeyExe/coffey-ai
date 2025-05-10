import discord
import json
import os
from discord.ext import commands

CONFIG_FILE = "config.json"

# Charger la configuration depuis le fichier JSON
def load_config():
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w") as f:
            json.dump({}, f)
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

# Sauvegarder la configuration dans le fichier JSON
def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

class Config(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = load_config()

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setprefix(self, ctx, prefix: str):
        guild_id = str(ctx.guild.id)
        self.config[guild_id] = self.config.get(guild_id, {})
        self.config[guild_id]["prefix"] = prefix
        save_config(self.config)
        await ctx.send(f"Nouveau prefix defini: `{prefix}`")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setlog(self, ctx, channel: discord.TextChannel):
        guild_id = str(ctx.guild.id)
        self.config[guild_id] = self.config.get(guild_id, {})
        self.config[guild_id]["log_channel"] = channel.id
        save_config(self.config)
        await ctx.send(f"Salon de log defini: {channel.mention}")

async def setup(bot):
    await bot.add_cog(Config(bot))
