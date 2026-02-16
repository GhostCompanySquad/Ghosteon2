import configparser
import mysql.connector


class Config:
    def __init__(self, ini_path: str = "config/settings.ini"):
        # Lecture du .ini
        self.parser = configparser.ConfigParser()
        self.parser.read(ini_path)

        # Section Discord
        self.token = self.parser["discord"]["token"]
        self.prefix = self.parser["discord"].get("command_prefix", "!")
        self.games_category_id = self.parser["discord"].get("games_category_id")
        self.archives_category_id = self.parser["discord"].get("archives_category_id")
        self.abyssal_category_id = self.parser["discord"].get("abyssal_category_id")
        self.ghost_role_ids = self.parser["discord"].get("ghost_role_ids").split(',')
        self.gold_control_channel_id = self.parser["discord"].get("gold_control_channel_id")
        self.control_delay = self.parser["discord"].get("control_delay")

        # Section MySQL
        self.db_config = {
            "host": self.parser["database"]["host"],
            "user": self.parser["database"]["user"],
            "password": self.parser["database"]["password"],
            "database": self.parser["database"]["database"],
            "port": self.parser["database"]["port"],
            "ssl_disabled": True  # ⬅️ clé magique
        }

        # Valeurs dynamiques (table config en DB)
        self.ensure_config_table()
        self.dynamic = self.load_dynamic_config()

    def ensure_config_table(self):
        # Créer la table config si elle n'existe pas
        conn = mysql.connector.connect(**self.db_config)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS config (
                id INT AUTO_INCREMENT PRIMARY KEY,
                `key` VARCHAR(100) NOT NULL UNIQUE,
                `value` VARCHAR(255) NOT NULL
            ) ENGINE=InnoDB;
        """)
        conn.commit()
        cursor.close()
        conn.close()

    def load_dynamic_config(self):
        conn = mysql.connector.connect(**self.db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT `key`, `value` FROM config")
        result = {row["key"]: row["value"] for row in cursor.fetchall()}
        cursor.close()
        conn.close()
        return result
