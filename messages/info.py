import discord


def embedded_message(message: str, title: str | None, color: discord.Color) -> discord.Embed:
    embed = discord.Embed(
        title=title,
        description=message,
        color=color
    )

    return embed


def info(message: str, title: str | None = None):
    return embedded_message(message, title, discord.Color.blue())


def success(message: str, title: str | None = None):
    return embedded_message(message, title, discord.Color.green())


def error(message: str, title: str | None = None):
    return embedded_message(message, title, discord.Color.red())
