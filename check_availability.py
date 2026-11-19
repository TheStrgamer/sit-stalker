import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

import config

STATE_FILE = Path(__file__).parent / "state.json"

GRAPHQL_URL = "https://as-portal-a-prod884f86a.azurewebsites.net/graphql"
HEADERS = {
    "content-type": "application/json",
    "accept": "*/*",
    "referer": "https://bolig.sit.no/",
    "origin": "https://bolig.sit.no",
}

# Room details (address, type, kitchen size, price...) live in SiT's CMS.
UNITS_QUERY = """query FindUnits($where: Sanity_EnhetFilter) {
  sanity_allEnhet(where: $where) {
    rentalObjectId
    isDeleted
    price
    area
    numberSharingKitchen
    category { housingType }
    building { address }
  }
}"""

# Availability comes from the housing search. Rooms that are not offered on the
# portal right now are simply left out of the response.
AVAILABILITY_QUERY = """query GetHousingIds($input: GetHousingsInput!) {
  housings(filter: $input) {
    housingRentalObjects {
      rentalObjectId
      isAvailable
      availableFrom
      availableTo
      hasActiveReservation
    }
  }
}"""

DISCORD_LIMIT = 2000


def graphql(query: str, variables: dict) -> dict:
    resp = requests.post(
        GRAPHQL_URL,
        json={"query": query, "variables": variables},
        headers=HEADERS,
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("errors"):
        raise RuntimeError(f"GraphQL error: {data['errors']}")
    return data["data"]


def address_matches(address: str | None) -> bool:
    wanted = config.BUILDING_ADDRESS
    if not wanted:
        return True
    if not address:
        return False
    address, wanted = address.lower(), wanted.lower()
    return address == wanted or address.startswith(wanted + " ")


def find_units() -> dict:
    """Returns {rentalObjectId: details} for every room matching the config."""
    where = {}
    if config.HOUSING_TYPE:
        where["category"] = {"housingType": {"eq": config.HOUSING_TYPE}}
    if config.SHARING_KITCHEN is not None:
        where["numberSharingKitchen"] = {"eq": config.SHARING_KITCHEN}
    if config.BUILDING_ADDRESS:
        where["building"] = {"address": {"matches": f"{config.BUILDING_ADDRESS}*"}}

    found = graphql(UNITS_QUERY, {"where": where})["sanity_allEnhet"]
    if config.EXTRA_UNIT_IDS:
        extra_where = {"rentalObjectId": {"in": config.EXTRA_UNIT_IDS}}
        extra = graphql(UNITS_QUERY, {"where": extra_where})["sanity_allEnhet"]
    else:
        extra = []

    units = {}
    for u in found:
        if not u["isDeleted"] and address_matches((u["building"] or {}).get("address")):
            units[u["rentalObjectId"]] = u
    for u in extra:
        units[u["rentalObjectId"]] = u
    for uid in config.EXTRA_UNIT_IDS:
        units.setdefault(uid, {"rentalObjectId": uid})
    return units


def fetch_availability(unit_ids: list[str]) -> dict:
    """Returns {rentalObjectId: {isAvailable, availableFrom, hasActiveReservation}}"""
    variables = {
        "input": {
            "rentalObjectIds": unit_ids,
            "showUnavailable": True,
            "reservationCode": "",
            "includeFilterCounts": False,
            "pageSize": len(unit_ids),
        }
    }
    objects = graphql(AVAILABILITY_QUERY, variables)["housings"]["housingRentalObjects"]
    return {
        o["rentalObjectId"]: {
            "isAvailable": o["isAvailable"],
            "availableFrom": o["availableFrom"],
            "availableTo": o["availableTo"],
            "hasActiveReservation": o["hasActiveReservation"],
        }
        for o in objects
    }


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}


def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")


def format_date(date_str: str | None) -> str:
    if not date_str:
        return "Unknown"
    return datetime.fromisoformat(date_str).strftime("%d.%m.%Y")


def floor_of(unit_id: str) -> int | None:
    # Room numbers look like MAL5-512: floor 5, room 12.
    number = unit_id.rsplit("-", 1)[-1]
    if number.isdigit() and len(number) >= 3:
        return int(number) // 100
    return None


def describe(uid: str, details: dict, info: dict) -> str:
    facts = []
    address = (details.get("building") or {}).get("address")
    if address:
        facts.append(address)
    floor = floor_of(uid)
    if floor is not None:
        facts.append(f"floor {floor}")
    if details.get("area"):
        facts.append(f"{details['area']:g} m²")
    if details.get("price"):
        facts.append(f"{details['price']:,.0f} kr/month".replace(",", " "))

    when = f"Available from {format_date(info['availableFrom'])}"
    if info.get("availableTo"):
        when += f" to {format_date(info['availableTo'])}"
    if info["hasActiveReservation"]:
        when += " (someone is reserving it right now)"

    return (
        f"• **{uid}** — {', '.join(facts)}\n"
        f"{when}\n"
        f"https://bolig.sit.no/en/unit/{uid.lower()}/"
    )


def notify_discord(lines: list[str]) -> None:
    webhook = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook:
        print("No Discord webhook configured")
        return

    # Discord rejects messages over 2000 characters, so split into several.
    messages, current = [], "**NYTT ROM LEDIG FOR FAEN!**\nRoom(s) just became available:"
    for line in lines:
        if len(current) + 1 + len(line) > DISCORD_LIMIT:
            messages.append(current)
            current = line
        else:
            current += "\n" + line
    messages.append(current)

    for content in messages:
        resp = requests.post(webhook, json={"content": content}, timeout=15)
        if resp.status_code == 429:  # rate limited: wait as told, then retry once
            time.sleep(float(resp.json().get("retry_after", 2)))
            resp = requests.post(webhook, json={"content": content}, timeout=15)
        if not resp.ok:
            print(f"Discord webhook failed: {resp.status_code} {resp.text}", file=sys.stderr)


def main():
    units = find_units()
    if not units:
        print("WARNING: no rooms match the config — check config.py.", file=sys.stderr)
        return

    availability = fetch_availability(sorted(units))
    print(f"Watching {len(units)} rooms, {len(availability)} currently listed on bolig.sit.no.")
    if not availability:
        print("WARNING: no rooms returned — API may have changed.", file=sys.stderr)
        return

    state = load_state()
    newly_available = []
    for uid, info in sorted(availability.items()):
        was_available = state.get(uid, {}).get("isAvailable", False)
        if info["isAvailable"]:
            print(f"Available: {uid} from {format_date(info['availableFrom'])}")
            if not was_available:
                newly_available.append(describe(uid, units.get(uid, {}), info))

    # Only keep rooms that are listed now, so a room that is taken and later
    # re-listed counts as new again.
    save_state(availability)

    if newly_available:
        notify_discord(newly_available)
    else:
        print("No newly available rooms.")


if __name__ == "__main__":
    main()
