import json

def get_profile(discord_id):
    with open(f"profiles/{discord_id}_profile.json", "r") as file:
        profile = json.load(file)
    return profile