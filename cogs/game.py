import logging
import emoji

import discord
from discord import app_commands
from discord.ext import commands
from peewee import IntegrityError, OperationalError, DataError

from config.loader import Config
from models import Lobby, State, db
from modals.game_modals import NewGameModal
from utils.game import generate_game_channel_name
from views.confirmation import ConfirmationView
from messages.info import error, info


class Game(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="ping", description="Commande de test")
    async def ping(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message("🏓 Pong !")

    @app_commands.command(name="lancer_partie", description="Crée un nouveau salon de partie.")
    @app_commands.describe(
        participants="Liste des joueurs"
    )
    async def lancer_partie(self, interaction: discord, participants: str = '') -> None:
        mentions = participants.split()
        config = Config()

        games_category_id = int(config.games_category_id)

        if not games_category_id:
            await interaction.response.send_message(
                embed=error("❌ La catégorie n'est pas configurée."),
                ephemeral=True
            )
            return

        games_category = discord.utils.get(interaction.guild.categories, id=games_category_id)

        if not games_category:
            await interaction.response.send_modal(
                embed=error("❌ La catégorie n'existe pas."),
                ephemeral=True
            )
            return

        new_game_modal = NewGameModal()
        await interaction.response.send_modal(new_game_modal)
        await new_game_modal.wait()

        username: str = interaction.user.display_name
        game_channel_name = generate_game_channel_name(username, new_game_modal.result)
        game_channel = await interaction.guild.create_text_channel(name=game_channel_name, category=games_category)

        try:
            game_id = int(new_game_modal.result.get("game_id"))
        except (TypeError, ValueError):
            game_id = None

        try:
            # Enregistrement du lobby en DB
            Lobby.create(
                channel_id=game_channel.id,
                emoji=emoji.demojize(new_game_modal.result.get("emoji")),
                speed=new_game_modal.result.get("speed"),
                size=new_game_modal.result.get("size"),
                game_id=game_id,
                state=State.get(State.name == "running")
            )
        except (IntegrityError, DataError, OperationalError) as e:
            embed = error(
                "Un problème est survenu.",
                "Erreur lors de la création du salon"
            )
            await game_channel.delete()
            logging.error(f"Erreur lors de l'enregistrement du lobby: {e}")
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        if interaction.user.mention not in mentions:
            mentions.append(interaction.user.mention)

        # Ping des joueurs
        await game_channel.send(
            embed=info(f"Participants : {' '.join(mentions)}.\nAmusez vous bien !", "🎮 Partie lancée !"),
            allowed_mentions=discord.AllowedMentions(
                users=True
            )
        )

        control_thread = await game_channel.create_thread(
            name="Cartes / Gold",
            type=discord.ChannelType.public_thread
        )
        await control_thread.send(
            "👮‍♂️ Merci d'envoyer ici un screen de votre inventaire de cartes "
            "et de votre solde de goldmarks."
        )

        await interaction.followup.send(f"✅ Salon créé pour {username} → {game_channel.mention}")

    @app_commands.command(name="terminer_partie", description="Ferme le salon de partie.")
    async def terminer_partie(self, interaction: discord.Interaction) -> None:
        config = Config()
        games_category_id = int(config.games_category_id)
        archives_category_id = int(config.archives_category_id)

        # Vérifier que la commande est lancée dans la bonne catégorie
        if interaction.channel.category_id != games_category_id:
            await interaction.response.send_message(
                embed=error("❌ Cette commande doit être utilisée dans un salon de partie."),
                ephemeral=True
            )
            return

        # Vérifier que la partie est terminée
        confirm_view = ConfirmationView()
        embed = discord.Embed(
            title="Confirmation ?",
            description="Confirmez vous que la partie est terminée ?"
        )
        await interaction.response.send_message(embed=embed, view=confirm_view, ephemeral=True)
        message = await interaction.original_response()
        confirm_view.message = message
        await confirm_view.wait()

        if confirm_view.value is None:
            await interaction.edit_original_response(
                embed=error("Action annulée.", "⏰ Temps écoulé"),
                view=None
            )
            return

        if confirm_view.value is False:
            await interaction.edit_original_response(
                embed=info("Action annulée.", "Vous avez annulé la demande"),
                view=None
            )
            await confirm_view.callback_interaction.response.defer()
            return

        await interaction.edit_original_response(view=None)
        await confirm_view.callback_interaction.response.defer()

        # Vérifier si c'est une victoire ou une défaite
        win_lose_view = ConfirmationView(label_confirm="Victoire", label_cancel="Défaite")
        embed = discord.Embed(
            title="Victoire ou défaites ?",
            description="Avez-vous gagné ou perdu la partie ?"
        )
        await interaction.edit_original_response(embed=embed, view=win_lose_view)
        win_lose_view.message = message
        await win_lose_view.wait()

        if confirm_view.value is None:
            await interaction.edit_original_response(
                embed=error("Action annulée.", "⏰ Temps écoulé"),
                view=None
            )
            return

        await win_lose_view.callback_interaction.response.defer()

        try:
            lobby = Lobby.get(Lobby.channel_id == interaction.channel.id)
        except Exception as e:
            lobby = None
            logging.error(f"Impossible de retrouver le lobby (channel_id = {interaction.channel.id}) : {e}")

        if win_lose_view.value:  # Victoire → Archivage du salon
            archive_category = discord.utils.get(interaction.guild.categories, id=archives_category_id)
            if archive_category:
                if lobby is not None:
                    lobby.state = State.get(State.name == "won")
                    lobby.save()

                await interaction.channel.edit(category=archive_category)
                await interaction.edit_original_response(
                    embed=info("📦 La partie est archivée."),
                    view=None
                )
            else:
                await interaction.edit_original_response(
                    embed=error("⚠️ Impossible de trouver la catégorie des archives."),
                    view=None
                )
        else:  # Défaite → Suppression du salon
            if lobby is not None:
                lobby.state = State.get(State.name == "lost")
                lobby.save()  # Sauvegarde en DB

            await interaction.channel.delete()

    @app_commands.command(name="renommer_partie", description="Renomme le salon de partie.")
    async def renommer_partie(self, interaction: discord.Interaction) -> None:
        config = Config()
        games_category_id = int(config.games_category_id)

        # Vérifier que la commande est lancée dans la bonne catégorie
        if interaction.channel.category_id != games_category_id:
            await interaction.response.send_message(
                embed=error("❌ Cette commande doit être utilisée dans un salon de partie."),
                ephemeral=True
            )
            return

        try:
            lobby = Lobby.get(Lobby.channel_id == interaction.channel.id)
        except Exception as e:
            lobby = None
            logging.error(f"Impossible de retrouver le lobby (channel_id = {interaction.channel.id}) : {e}")

        new_game_modal = NewGameModal(edit=True, lobby=lobby)
        await interaction.response.send_modal(new_game_modal)
        await new_game_modal.wait()

        game_channel_name = generate_game_channel_name("error", new_game_modal.result)
        await interaction.channel.edit(name=game_channel_name)

        if lobby is not None:
            with db.atomic():
                lobby.emoji = emoji.demojize(new_game_modal.result.get("emoji"))
                lobby.speed = new_game_modal.result.get("speed")
                lobby.size = new_game_modal.result.get("size")
                lobby.game_id = new_game_modal.result.get("game_id")
                lobby.save()
        else:
            Lobby.create(
                channel_id=interaction.channel.id,
                emoji=emoji.demojize(new_game_modal.result.get("emoji")),
                speed=new_game_modal.result.get("speed"),
                size=new_game_modal.result.get("size"),
                game_id=new_game_modal.result.get("game_id"),
                state=State.get(State.name == "running")
            )

        await interaction.followup.send(
            embed=info(f"✅ Le salon a été renommé → {game_channel_name}.")
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Game(bot))
