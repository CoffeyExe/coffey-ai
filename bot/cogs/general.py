import discord
from discord.ext import commands

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("✅ Cog General chargée correctement.")

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        self.bot.tree.copy_global_to(guild=guild)
        await self.bot.tree.sync(guild=guild)

    @discord.app_commands.command(name="ping", description="Vérifie si le bot est en ligne.")
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.send_message("🏓 Pong en Slash Command !")

async def setup(bot):
    await bot.add_cog(General(bot))
