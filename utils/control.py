import math
import random
from datetime import datetime, timedelta
from typing import List

import discord

from models import Ghost


def generate_abyssal_channel_name(members: list[discord.Member]) -> str:
    usernames = []
    for member in members:
        username = member.display_name
        # Nettoyage: remplace les espaces/caractères spéciaux par "-"
        clean_username = "".join(
            c if c.isalnum() else "-" for c in username.lower()
        ).strip("-")
        usernames.append(clean_username or "user")

    # 3. Construction du nom final
    if not usernames:
        return "conseil-vide"

    # Tronquer à 100 caractères (limite Discord)
    base_name = "conseil-" + "-".join(usernames)
    return base_name[:100]


def select_members_to_control(
        guild: discord.Guild,
        member_ids: List[int],
        control_delay_days: int,
        max_selected: int = 10,
        never_controlled_weight: float = 10.0,
) -> list[discord.Member]:
    eligible_members = []
    now = datetime.now()

    for member_id in member_ids:
        try:
            # Récupérer l'historique de contrôle depuis la DB
            member_record = Ghost.get(member_id=member_id)
            last_control = member_record.last_control

            # Exclure si contrôlé récemment
            if last_control and (now - last_control) < timedelta(days=control_delay_days):
                continue

            # Calculer le poids
            if last_control is None:
                weight = never_controlled_weight
            else:
                days_since_control = (now - last_control).days
                weight = 1.0 + math.log1p(days_since_control)  # log(1 + x) pour éviter log(0)

            eligible_members.append((member_id, weight))

        except Ghost.DoesNotExist:
            # Membre non enregistré = jamais contrôlé
            eligible_members.append((member_id, never_controlled_weight))

        # --- Sélection pondérée ---
    if not eligible_members:
        return []

    member_ids, weights = zip(*eligible_members)
    total_weight = sum(weights)
    probabilities = [w / total_weight for w in weights]

    # Sélection sans remplacement (évite les doublons)
    selected_ids = set()
    max_attempts = min(100, len(eligible_members) * 2)  # Évite une boucle infinie

    while len(selected_ids) < min(max_selected, len(eligible_members)) and max_attempts > 0:
        chosen_id = random.choices(member_ids, weights=probabilities, k=1)[0]
        selected_ids.add(chosen_id)
        max_attempts -= 1

    # --- Récupérer les objets discord.Member ---
    selected_members = []
    for mid in selected_ids:
        member = guild.get_member(mid)
        if member:  # Ignore si le membre a quitté le serveur
            selected_members.append(member)

    return selected_members
