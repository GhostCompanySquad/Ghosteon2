import discord
from discord import Interaction, TextStyle
import emoji

from models import Lobby


class NewGameModal(discord.ui.Modal):

    def __init__(self, edit=False, lobby: Lobby = None):
        super().__init__(title=f"{'Modification' if edit else 'Création'} d'un salon de partie")
        self.result = {}
        self.edit = edit

        self.emoji = discord.ui.TextInput(
            label="Émoji [ win + ; ]",
            placeholder="émoji",
            default=str(emoji.emojize(lobby.emoji)) if edit and lobby and lobby.emoji else None,
            required=False,  # toujours obligatoire
            style=TextStyle.short

        )
        self.add_item(self.emoji)

        self.speed = discord.ui.TextInput(
            label="Vitesse",
            placeholder="1, 2, 4, 6...",
            default=str(lobby.speed) if edit and lobby and lobby.speed else None,
            required=edit,  # obligatoire si edit=True
            style=TextStyle.short
        )
        self.add_item(self.speed)

        self.size = discord.ui.TextInput(
            label="Taille de la map",
            placeholder="2, 10, 31, 43, 100...",
            default=str(lobby.size) if edit and lobby and lobby.size else None,
            required=edit,
            style=TextStyle.short
        )
        self.add_item(self.size)

        self.game_id = discord.ui.TextInput(
            label="ID de la partie",
            placeholder="10512932",
            default=str(lobby.game_id) if edit and lobby and lobby.game_id else None,
            required=edit,
            style=TextStyle.short
        )
        self.add_item(self.game_id)

    async def on_submit(self, interaction: Interaction) -> None:
        self.result = {
            "emoji": self.emoji.value or None,
            "speed": self.speed.value or None,
            "size": self.size.value or None,
            "game_id": self.game_id.value or None
        }
        await interaction.response.defer()
        self.stop()
