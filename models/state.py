from peewee import *
from . import db


class State(Model):
    name = CharField(max_length=20, unique=True)

    class Meta:
        database = db
        table_name = "states"
