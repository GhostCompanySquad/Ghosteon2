import random


def generate_game_channel_name(username: str, params) -> str:
    emoji = params.get("emoji")
    speed = params.get("speed")
    size = params.get("size")
    game_id = params.get("game_id")

    temporary = False
    fragments = []
    if emoji is not None:
        fragments.append(emoji)
    if size is not None:
        fragments.append(size)
    else:
        temporary = True
    if speed is not None:
        fragments.append(f"x{speed}")
    else:
        temporary = True
    if game_id is not None:
        fragments.append(game_id)
    else:
        temporary = True

    if temporary:
        fragments.append(username.replace(" ", "-"))
        fragments.append(f"{random.randint(1000,9999)}")

    return "-".join(fragments)




