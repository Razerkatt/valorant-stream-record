import os
import json
import requests

API_KEY = os.environ["HENRIK_API_KEY"]

PUUID = "223f6f3c-d8e6-53fc-9e02-394e87e51883"

headers = {
    "Authorization": API_KEY
}

response = requests.get(
    f"https://api.henrikdev.xyz/valorant/v3/by-puuid/matches/na/{PUUID}",
    headers=headers
)

data = response.json()

print(json.dumps(data, indent=2))
