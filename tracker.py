import os
import json
import requests

API_KEY = os.environ["HENRIK_API_KEY"]

USERNAME = "Razerkatt"
TAG = "0101"
REGION = "na"

headers = {
    "Authorization": API_KEY
}

response = requests.get(
    f"https://api.henrikdev.xyz/valorant/v1/account/{USERNAME}/{TAG}",
    headers=headers
)

data = response.json()

print(json.dumps(data, indent=2))
