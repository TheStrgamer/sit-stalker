import json
import sys
from pathlib import Path
from datetime import datetime
import requests
import os
import config

def format_date(date_str: str) -> str:
    if not date_str:
        return "Unknown"

    dt = datetime.fromisoformat(date_str)
    return dt.strftime("%d.%m.%Y")

STATE_FILE = Path(__file__).parent / "state.json"

GRAPHQL_URL = "https://as-portal-a-prod884f86a.azurewebsites.net/graphql"

QUERY = """query GetHousingIds($input: GetHousingsInput!) {
  housings(filter: $input) {
    housingRentalObjects {
      rentalObjectId
      isHighlighted
      isAvailable
      availableFrom
      availableTo
      hasActiveReservation
      __typename
    }
    filterCounts {
      locations { key value __typename }
      residenceCategories { key value __typename }
      categories { key value __typename }
      notAvailableCount
      __typename
    }
    totalCount
    __typename
  }
}"""


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}


def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2))


def fetch_units(unit_ids: list[str]) -> dict:
    """Returns {rentalObjectId: {isAvailable, availableFrom, hasActiveReservation}}"""
    payload = {
        "operationName": "GetHousingIds",
        "variables": {
            "input": {
                "rentalObjectIds": unit_ids,
                "showUnavailable": True,
                "reservationCode": "",
                "includeFilterCounts": False,
            }
        },
        "query": QUERY,
    }
    headers = {
        "content-type": "application/json",
        "accept": "*/*",
        "referer": "https://bolig.sit.no/",
        "origin": "https://bolig.sit.no",
    }
    resp = requests.post(GRAPHQL_URL, json=payload, headers=headers, timeout=20)
    resp.raise_for_status()
    data = resp.json()

    objects = data["data"]["housings"]["housingRentalObjects"]
    return {
        o["rentalObjectId"]: {
            "isAvailable": o["isAvailable"],
            "availableFrom": o["availableFrom"],
            "hasActiveReservation": o["hasActiveReservation"],
        }
        for o in objects
    }

def notify_discord(message: str) -> None:
    webhook = os.getenv("DISCORD_WEBHOOK_URL")

    if not webhook:
        print("No Discord webhook configured")
        return

    requests.post(
        webhook,
        json={"content": f"**NYTT ROM LEDIG FOR FAEN!**\n{message}"},
        timeout=15,
    )


def main():
    print(f"Checking {len(config.UNIT_IDS)} units...")
    units = fetch_units(config.UNIT_IDS)

    if not units:
        print("WARNING: no units returned — API may have changed.", file=sys.stderr)
        return

    state = load_state()
    newly_available = []

    for unit_id, info in units.items():
        was_available = state.get(unit_id, {}).get("isAvailable", False)
        if info != state.get(unit_id):
            state[unit_id] = info
        if info["isAvailable"] and not was_available:
            newly_available.append((unit_id, info))

    save_state(state)

    if newly_available:
        lines = [
            f"• **{uid}**\n"
            f"Available from: {format_date(info['availableFrom'])}\n"
            f"https://bolig.sit.no/en/unit/{uid.lower()}/"
            for uid, info in newly_available
        ]
        message = "Room(s) just became available:\n" + "\n".join(lines)
        notify_discord(message)
    else:
        print("No newly available rooms.")


if __name__ == "__main__":
    main()