import discord
from discord import app_commands
from discord.ext import commands
import random
from datetime import datetime, timedelta

from config.loader import Config
from messages.info import error, info
from models import Ghost
from utils.control import generate_abyssal_channel_name, select_members_to_control


class Control(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="conseil", description="Traine les joueurs dans les abysses.")
    @app_commands.describe(
        joueurs="Liste des joueurs"
    )
    async def conseil(self, interaction: discord.Interaction, joueurs: str) -> None:
        mentions = joueurs.split()
        config = Config()

        members = []
        for mention in mentions:
            if mention.startswith("<@") and mention.endswith(">"):
                user_id = int(mention[2:-1].lstrip("!"))
                member = interaction.guild.get_member(user_id)
                if member:
                    members.append(member)

        abyssal_category_id = int(config.abyssal_category_id)

        if not abyssal_category_id:
            await interaction.response.send_message(
                embed=error("❌ La catégorie n'est pas configurée."),
                ephemeral=True
            )
            return

        abyssal_category = discord.utils.get(interaction.guild.categories, id=abyssal_category_id)

        if not abyssal_category:
            await interaction.response.send_modal(
                embed=error("❌ La catégorie n'existe pas."),
                ephemeral=True
            )
            return

        abyssal_channel_name = generate_abyssal_channel_name(members)
        abyssal_channel = await interaction.guild.create_text_channel(name=abyssal_channel_name,
                                                                      category=abyssal_category)

        perms = {
            "read_messages": True,
            "send_messages": True,
            "read_message_history": True,
            "attach_files": True,  # Images/fichiers
            "embed_links": True,  # Liens enrichis
            "add_reactions": True,  # Réactions
            "use_external_emojis": True  # Emojis personnalisés
        }

        for member in members:
            await abyssal_channel.set_permissions(member, **perms)

        embed = info(
            f"{interaction.user.mention} a ouvert ce salon pour un **conseil disciplinaire**.\n"
            f"Salon : {abyssal_channel.mention}\n\n"
            "🔹 **Participants autorisés** :\n"
            f"- {', '.join([m.mention for m in members])}\n"
            "- Le staff\n\n"
            "📢 *Ce salon sera archivé après résolution du problème.*",
            "👮‍♂️ **Conseil disciplinaire**"
        )

        await abyssal_channel.send(
            embed=embed
        )

        await interaction.response.send_message(
            f"✅ Salon créé : {abyssal_channel.mention}",
            ephemeral=True
        )

    @app_commands.command(name="controle_aleatoire", description="Lance une session de contrôle aléatoire des golds.")
    @app_commands.describe(
        joueurs="Liste des joueurs forcée"
    )
    async def controle_aleatoire(self, interaction: discord.Interaction, joueurs: str | None = None) -> None:
        await interaction.response.defer(ephemeral=True)

        mentions = joueurs.split() if joueurs else []
        config = Config()

        ghost_members = set()

        await interaction.guild.chunk()

        for role_id in config.ghost_role_ids:
            role = interaction.guild.get_role(int(role_id))
            if role:
                ghost_members.update(role.members)

        for member in ghost_members:
            try:
                Ghost.get(member_id=member.id)
            except Ghost.DoesNotExist:
                Ghost.create(member_id=member.id, last_control=None)

        active_members = Ghost.select().where(Ghost.active == True)
        member_ids = [m.member_id for m in active_members]

        forced_ids = []
        if joueurs:
            forced_ids = [int(j.strip()) for j in joueurs.split(",") if j.strip().isdigit()]
            valid_forced_ids = [jid for jid in forced_ids if interaction.guild.get_member(jid)]
            member_ids = list(set(member_ids + valid_forced_ids))

        selected_members = select_members_to_control(
            guild=interaction.guild,
            member_ids=member_ids,
            control_delay_days=int(config.control_delay)
        )

        if len(selected_members) < 3:
            await interaction.followup.send(
                f"❌ Il n'y a pas assez de membres éligibles : {len(selected_members)}", ephemeral=True)
            return

        control_channel = interaction.guild.get_channel(int(config.gold_control_channel_id))
        if not control_channel:
            await interaction.followup.send(
                "❌ Salon de contrôle introuvable. Vérifiez `config.gold_control_channel_id`.", ephemeral=True)
            return

        embed = info(
            "Les membres suivants doivent **envoyer un screenshot de leur solde actuel de golds** "
            f"dans ce salon **sous 24h** :\n\n"
            + "\n".join(f"- {member.mention} ({member.display_name})" for member in selected_members) + "\n\n"
            "**⚠️ Sanction** : Tout membre ne répondant pas sera sanctionné (voir règlement).",
            "**🔍 CONTRÔLE ALÉATOIRE DES GOLDMARKS 🔍**"
        )

        await control_channel.send(embed=embed)
        await interaction.followup.send(
            f"✅ Contrôle lancé : {len(selected_members)} membres sélectionnés.",
            ephemeral=True
        )

        for member in selected_members:
            Ghost.update(last_control=datetime.now()).where(Ghost.member_id == member.id).execute()




async def setup(bot: commands.Bot):
    await bot.add_cog(Control(bot))
