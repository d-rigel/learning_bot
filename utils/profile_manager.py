import json

def get_profile(discord_id):
    try:
        with open(f"profiles/{discord_id}_profile.json", "r") as file:
            profile = json.load(file)
    except FileNotFoundError:
        profile = None
    return profile

def save_profile(discord_id, profile):
    with open(f"profiles/{discord_id}_profile.json", "w") as file:
        json.dump(profile, file)