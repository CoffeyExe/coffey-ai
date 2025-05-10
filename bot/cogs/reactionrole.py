import discord
from discord.ext import commands
from discord import app_commands

class RoleSelect(discord.ui.Select):
    def __init__(self, roles):
        options = [discord.SelectOption(label=role.name, value=str(role.id)) for role in roles]
        super().__init__(placeholder="Choisissez un rôle...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        role_id = int(self.values[0])
        role = interaction.guild.get_role(role_id)
        if role:
            if role in interaction.user.roles:
                await interaction.user.remove_roles(role)
                await interaction.response.send_message(f"❌ Rôle {role.name} retiré.", ephemeral=True)
            else:
                await interaction.user.add_roles(role)
                await interaction.response.send_message(f"✅ Rôle {role.name} ajouté.", ephemeral=True)

class RoleView(discord.ui.View):
    def __init__(self, roles):
        super().__init__(timeout=None)
        self.add_item(RoleSelect(roles))

class ReactionRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="reactionrole", description="Créer un menu de rôles.")
    async def reactionrole(self, interaction: discord.Interaction):
        await interaction.response.send_message("Envoie le titre du menu dans le chat.")

        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel

        try:
            title_msg = await self.bot.wait_for("message", check=check, timeout=60)
            title = title_msg.content

            await interaction.followup.send("Envoie la description du menu.")
            desc_msg = await self.bot.wait_for("message", check=check, timeout=60)
            description = desc_msg.content

            await interaction.followup.send("Mentionne les rôles à inclure (séparés par un espace).")
            roles_msg = await self.bot.wait_for("message", check=check, timeout=60)
            role_mentions = roles_msg.role_mentions

            if not role_mentions:
                await interaction.followup.send("Aucun rôle mentionné. Commande annulée.")
                return

            embed = discord.Embed(title=title, description=description, color=discord.Color.blue())
            view = RoleView(role_mentions)

            await interaction.followup.send(embed=embed, view=view)

        except Exception as e:
            await interaction.followup.send(f"Erreur : {e}")

async def setup(bot):
    await bot.add_cog(ReactionRole(bot))
