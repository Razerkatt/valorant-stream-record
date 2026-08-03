import os
import json
import requests
from datetime import datetime, timezone

HENRIK_API_KEY = os.environ["HENRIK_API_KEY"]

TWITCH_CLIENT_ID = os.environ["TWITCH_CLIENT_ID"]
TWITCH_CLIENT_SECRET = os.environ["TWITCH_CLIENT_SECRET"]

PUUID = "223f6f3c-d8e6-53fc-9e02-394e87e51883"

TWITCH_USERNAME = "razerkatt"
REGION = "na"

DATA_FILE = "stream_data.json"
RECORD_FILE = "record.txt"


def load_data():
    with open(DATA_FILE, "r") as file:
        return json.load(file)


def save_data(data):
    with open(DATA_FILE, "w") as file:
        json.dump(data, file, indent=2)


def get_twitch_token():
    response = requests.post(
        "https://id.twitch.tv/oauth2/token",
        params={
            "client_id": TWITCH_CLIENT_ID,
            "client_secret": TWITCH_CLIENT_SECRET,
            "grant_type": "client_credentials"
        }
    )

    return response.json()["access_token"]


def get_stream():
    token = get_twitch_token()

    response = requests.get(
        f"https://api.twitch.tv/helix/streams?user_login={TWITCH_USERNAME}",
        headers={
            "Client-ID": TWITCH_CLIENT_ID,
            "Authorization": f"Bearer {token}"
        }
    )

    data = response.json()["data"]

    if len(data) == 0:
        return None

    return data[0]


def reset_stream(data, start_time):
    print("New stream detected. Resetting stream stats.")

    data["live"] = True
    data["stream_start_time"] = start_time
    data["wins"] = 0
    data["losses"] = 0
    data["draws"] = 0
    data["rr"] = 0
    data["current_streak"] = ""
    data["streak_count"] = 0
    data["matches"] = []


def get_matches():
    response = requests.get(
        f"https://api.henrikdev.xyz/valorant/v3/by-puuid/matches/{REGION}/{PUUID}",
        headers={
            "Authorization": HENRIK_API_KEY
        }
    )

    return response.json()["data"]


def get_rr_history():
    response = requests.get(
        f"https://api.henrikdev.xyz/valorant/v1/by-puuid/mmr-history/{REGION}/{PUUID}",
        headers={
            "Authorization": HENRIK_API_KEY
        }
    )

    return response.json()["data"]


def get_result(match):

    for player in match["players"]["all_players"]:
        if player["puuid"] == PUUID:
            team = player["team"]
            break
    else:
        print("Could not find player in match.")
        return None

    if match["teams"][team.lower()]["has_won"]:
        return "win"

    return "loss"


def update_streak(data, result):

    if data["current_streak"] == result:
        data["streak_count"] += 1
    else:
        data["current_streak"] = result
        data["streak_count"] = 1


def create_message(data):

    rr = data["rr"]

    if rr > 0:
        rr_text = f"is currently up {rr}RR"
    elif rr < 0:
        rr_text = f"is currently down {abs(rr)}RR"
    else:
        rr_text = "is currently even at 0RR"

    message = (
        f"Razerkatt has a record of "
        f"{data['wins']}W-{data['losses']}L-{data['draws']}D and "
        f"{rr_text}"
    )

    if data["streak_count"] >= 2:
        message += (
            f", on a {data['streak_count']} game "
            f"{data['current_streak']} streak this stream."
        )
    else:
        message += " this stream."

    return message


print("=" * 60)
print(f"Tracker started at {datetime.now(timezone.utc).isoformat()}")
print("=" * 60)


data = load_data()

stream = get_stream()

if stream is None:

    print("Stream is offline.")

    data["live"] = False
    save_data(data)

    with open(RECORD_FILE, "w") as file:
        file.write("@razerkatt's stream is currently offline.")

    exit()


stream_start = stream["started_at"]

start_time = int(
    datetime.fromisoformat(
        stream_start.replace("Z", "+00:00")
    ).timestamp()
)


if not data["live"] or data["stream_start_time"] != start_time:
    reset_stream(data, start_time)


print("Getting RR history...")

rr_history = get_rr_history()

rr_lookup = {}

for game in rr_history:
    rr_lookup[game["match_id"]] = game["mmr_change_to_last_game"]


print(f"RR history entries found: {len(rr_lookup)}")


print("Getting matches...")

matches = get_matches()

print(f"Henrik returned {len(matches)} matches.")


for match in matches:

    match_id = match["metadata"]["matchid"]

    print(f"Checking match {match_id}")

    if match_id in data["matches"]:
        print(f"Skipping {match_id}: already processed")
        continue

    if match["metadata"]["mode_id"] != "competitive":
        print(f"Skipping {match_id}: not competitive")
        continue

    if match["metadata"]["game_start"] < start_time:
        print(f"Skipping {match_id}: before stream started")
        continue

    print(f"Processing NEW match {match_id}")

    result = get_result(match)

    if result == "win":
        data["wins"] += 1
    else:
        data["losses"] += 1

    update_streak(data, result)

    if match_id in rr_lookup:
        print(f"RR change detected: {rr_lookup[match_id]}")
        data["rr"] += rr_lookup[match_id]
    else:
        print(f"No RR history found for {match_id}")

    data["matches"].append(match_id)


save_data(data)


message = create_message(data)

with open(RECORD_FILE, "w") as file:
    file.write(message)


print("------------------------------------")
print(message)
print("Tracker finished successfully.")
print("------------------------------------")
