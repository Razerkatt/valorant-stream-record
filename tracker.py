import os
import json
import requests

API_KEY = os.environ["HENRIK_API_KEY"]

PUUID = "223f6f3c-d8e6-53fc-9e02-394e87e51883"
REGION = "na"

DATA_FILE = "stream_data.json"
RECORD_FILE = "record.txt"

headers = {
    "Authorization": API_KEY
}


def load_data():
    with open(DATA_FILE, "r") as file:
        return json.load(file)


def save_data(data):
    with open(DATA_FILE, "w") as file:
        json.dump(data, file, indent=2)


def get_matches():
    url = f"https://api.henrikdev.xyz/valorant/v3/by-puuid/matches/{REGION}/{PUUID}"
    response = requests.get(url, headers=headers)
    return response.json()["data"]


def get_rr_history():
    url = f"https://api.henrikdev.xyz/valorant/v1/by-puuid/mmr-history/{REGION}/{PUUID}"
    response = requests.get(url, headers=headers)
    return response.json()["data"]


def get_result(match):
    players = match["players"]["all_players"]

    me = None

    for player in players:
        if player["puuid"] == PUUID:
            me = player
            break

    if me is None:
        return None

    my_team = me["team"]

    teams = match["teams"]

    if teams[my_team.lower()]["has_won"]:
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


data = load_data()

matches = get_matches()
rr_history = get_rr_history()

rr_lookup = {}

for game in rr_history:
    rr_lookup[game["match_id"]] = game["mmr_change_to_last_game"]


for match in matches:

    match_id = match["metadata"]["matchid"]

    if match_id in data["matches"]:
        continue

    if match["metadata"]["mode_id"] != "competitive":
        continue

    result = get_result(match)

    if result is None:
        continue

    if result == "win":
        data["wins"] += 1
    else:
        data["losses"] += 1

    update_streak(data, result)

    if match_id in rr_lookup:
        data["rr"] += rr_lookup[match_id]

    data["matches"].append(match_id)


save_data(data)


with open(RECORD_FILE, "w") as file:
    file.write(create_message(data))


print(create_message(data))
