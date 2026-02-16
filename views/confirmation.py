import discord


class ConfirmationView(discord.ui.View):
    def __init__(self, timeout=30, label_confirm="Confirmer", label_cancel="Annuler"):
        super().__init__(timeout=timeout)
        self.value = None
        self.interaction_message = None
        self.callback_interaction = None
        self.message = None

        self.add_item(discord.ui.Button(label=label_confirm, style=discord.ButtonStyle.green, custom_id="confirm"))
        self.add_item(discord.ui.Button(label=label_cancel, style=discord.ButtonStyle.red, custom_id="cancel"))

    async def on_timeout(self):
        if self.interaction_message:
            try:
                await self.interaction_message.edit(view=None)
            except discord.NotFound:
                pass  # Le message a peut-être été supprimé

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Attraper les clics en fonction du custom_id
        if interaction.data["custom_id"] == "confirm":
            self.value = True
        elif interaction.data["custom_id"] == "cancel":
            self.value = False

        self.interaction_message = interaction.message
        self.callback_interaction = interaction

        # await interaction.response.edit_message(view=None)  # supprime les boutons
        self.stop()
        return True

    # @discord.ui.button(label=f"✅ Confirmer", style=discord.ButtonStyle.green)
    # async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
    #     self.value = True
    #     self.interaction_message = interaction.message
    #     self.callback_interaction = interaction
    #     self.stop()
    #
    # @discord.ui.button(label=f"❌ Annuler", style=discord.ButtonStyle.red)
    # async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
    #     self.value = False
    #     self.interaction_message = interaction.message
    #     self.callback_interaction = interaction
    #     self.stop()
