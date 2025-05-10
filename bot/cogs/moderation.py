import discord
from discord.ext import commands
from discord import app_commands
import json
import os

CONFIG_FILE = "config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send_log(self, guild, message):
        config = load_config()
        guild_id = str(guild.id)
        if guild_id in config and "log_channel" in config[guild_id]:
            channel_id = config[guild_id]["log_channel"]
            channel = guild.get_channel(channel_id)
            if channel:
                await channel.send(message)

    @commands.Cog.listener()
    async def on_ready(self):
        print("✅ Cog Moderation chargée avec Slash Commands.")

    @app_commands.command(name="mute", description="Mute un membre.")
    async def mute(self, interaction: discord.Interaction, member: discord.Member, reason: str = "Aucune raison fournie"):
        role = discord.utils.get(interaction.guild.roles, name="Muted")
        if not role:
            role = await interaction.guild.create_role(name="Muted", reason="Création du rôle Muted")
            for channel in interaction.guild.channels:
                await channel.set_permissions(role, send_messages=False, speak=False)
        await member.add_roles(role, reason=reason)
        await interaction.response.send_message(f"{member.mention} a été mute pour : {reason}")
        await self.send_log(interaction.guild, f"🔇 {member} a été mute pour : {reason}")

    @app_commands.command(name="kick", description="Kick un membre.")
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "Aucune raison fournie"):
        await member.kick(reason=reason)
        await interaction.response.send_message(f"{member.mention} a été kick pour : {reason}")
        await self.send_log(interaction.guild, f"🔨 {member} a été kick pour : {reason}")

    @app_commands.command(name="ban", description="Ban un membre.")
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "Aucune raison fournie"):
        await member.ban(reason=reason)
        await interaction.response.send_message(f"{member.mention} a été banni pour : {reason}")
        await self.send_log(interaction.guild, f"⛔ {member} a été banni pour : {reason}")

async def setup(bot):
    await bot.add_cog(Moderation(bot))
