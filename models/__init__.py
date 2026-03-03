from peewee import MySQLDatabase, IntegrityError

from config.loader import Config

config = Config()

# Initialisation de la DB (à configurer via variables d'environnement en prod)
db = MySQLDatabase(
    config.db_config["database"],
    user=config.db_config["user"],
    password=config.db_config["password"],
    host=config.db_config["host"],
    port=int(config.db_config["port"]),
    autoconnect=True,
    autorollback=True,
    stale_timeout=300,  # 5 minutes
)

# Import des modèles
from .state import State
from .lobby import Lobby
from .ghost import Ghost


def init_states():
    states = ["running", "won", "lost", "aborted"]
    for state_name in states:
        try:
            State.create(name=state_name)
        except IntegrityError:
            pass


# Création des tables
def init_db():
    db.connect()
    db.create_tables([State, Lobby, Ghost], safe=True)
    init_states()
