import json

def get_courses():
    return ["JavaScript", "Python"]

def create_profile(discord_id, chosen_course):
    profile = {
        "discord_id": discord_id,
        "chosen_course": chosen_course,
        "course_json_file": f"courses/{chosen_course.lower()}.json",
        "current_session_id": 0
    }
    with open(f"profiles/{discord_id}_profile.json", "w") as file:
        json.dump(profile, file)
    return profile

def next_session(profile):
    with open(profile["course_json_file"], "r") as course_file:
        course_data = json.load(course_file)
    session = course_data["sessions"][profile["current_session_id"]]
    profile["current_session_id"] += 1
    with open(f"profiles/{profile['discord_id']}_profile.json", "w") as file:
        json.dump(profile, file)
    return session



