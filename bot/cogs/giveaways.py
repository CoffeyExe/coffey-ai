import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
import random

class GiveawayButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="🎉 Participer", style=discord.ButtonStyle.green)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user not in self.view.participants:
            self.view.participants.append(interaction.user)
            await interaction.response.send_message("Participation enregistrée ✅", ephemeral=True)
        else:
            await interaction.response.send_message("Tu es déjà inscrit 😎", ephemeral=True)

class GiveawayView(discord.ui.View):
    def __init__(self, timeout):
        super().__init__(timeout=timeout)
        self.participants = []
        self.add_item(GiveawayButton())

class Giveaways(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="giveaway", description="Lancer un giveaway.")
    @app_commands.describe(channel="Le salon où envoyer le giveaway", duration="Durée en minutes", winners="Nombre de gagnants", prize="Le prix à gagner")
    async def giveaway(self, interaction: discord.Interaction, channel: discord.TextChannel, duration: int, winners: int, prize: str):
        embed = discord.Embed(
            title="🎉 Giveaway 🎉",
            description=f"**Prix :** {prize}\n**Temps restant :** {duration} minutes\n**Clique sur 🎉 pour participer !**",
            color=discord.Color.gold()
        )
        view = GiveawayView(timeout=duration * 60)
        await channel.send(embed=embed, view=view)
        await interaction.response.send_message(f"Giveaway lancé dans {channel.mention} pour **{prize}**.")

        await asyncio.sleep(duration * 60)

        if not view.participants:
            await channel.send("🎉 Giveaway terminé. Aucun participant.")
        else:
            winners_list = random.sample(view.participants, min(winners, len(view.participants)))
            winners_mentions = ", ".join(winner.mention for winner in winners_list)
            await channel.send(f"🎉 Félicitations à {winners_mentions} pour avoir gagné **{prize}** !")

async def setup(bot):
    await bot.add_cog(Giveaways(bot))
