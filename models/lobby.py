from peewee import *
from . import db
from .state import State


class Lobby(Model):
    channel_id = BigIntegerField(index=True)
    emoji = CharField(max_length=50)
    speed = IntegerField(null=True, default=None)
    size = IntegerField(null=True, default=None)
    game_id = IntegerField(null=True, default=None)
    state = ForeignKeyField(State, backref="lobbies")

    class Meta:
        database = db
        table_name = "lobbies"
