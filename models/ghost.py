from peewee import *
from . import db


class Ghost(Model):
    member_id = BigIntegerField(index=True)
    last_control = DateTimeField(null=True)
    active = BooleanField(default=True)
    gold_amount = BigIntegerField(null=True)
    calculated_gold_amount = BigIntegerField(null=True)

    class Meta:
        database = db
        table_name = "ghosts"
