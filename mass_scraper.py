import requests

API_URL = "https://astranova-api.onrender.com"

# Your expanded fleet
ship_data = [
    {
        "ship": {"game_id": "077", "name": "Enterprise", "rarity": "Super Rare", "faction": "Eagle Union", "hull_type": "Aircraft Carrier"},
        "stats": {"health": 4200, "firepower": 0, "torpedo": 0, "aviation": 420, "anti_air": 280, "reload": 120, "evasion": 55, "armor_type": "Heavy", "speed": 33, "accuracy": 150, "luck": 95, "anti_sub": 0, "oil_cost": 13}
    },
    {
        "ship": {"game_id": "057", "name": "Belfast", "rarity": "Super Rare", "faction": "Royal Navy", "hull_type": "Light Cruiser"},
        "stats": {"health": 3600, "firepower": 165, "torpedo": 300, "aviation": 0, "anti_air": 320, "reload": 170, "evasion": 85, "armor_type": "Medium", "speed": 32, "accuracy": 145, "luck": 80, "anti_sub": 95, "oil_cost": 11}
    },
    {
        "ship": {"game_id": "495", "name": "New Jersey", "rarity": "Ultra Rare", "faction": "Eagle Union", "hull_type": "Battleship"},
        "stats": {"health": 8200, "firepower": 450, "torpedo": 0, "aviation": 0, "anti_air": 400, "reload": 140, "evasion": 40, "armor_type": "Heavy", "speed": 30, "accuracy": 160, "luck": 88, "anti_sub": 0, "oil_cost": 15}
    },
    {
        "ship": {"game_id": "001", "name": "Laffey", "rarity": "Elite", "faction": "Eagle Union", "hull_type": "Destroyer"},
        "stats": {"health": 1800, "firepower": 120, "torpedo": 250, "aviation": 0, "anti_air": 150, "reload": 180, "evasion": 160, "armor_type": "Light", "speed": 42, "accuracy": 180, "luck": 50, "anti_sub": 120, "oil_cost": 8}
    },
    {
        "ship": {"game_id": "316", "name": "Amagi", "rarity": "Super Rare", "faction": "Sakura Empire", "hull_type": "Battlecruiser"},
        "stats": {"health": 7500, "firepower": 410, "torpedo": 0, "aviation": 0, "anti_air": 310, "reload": 135, "evasion": 45, "armor_type": "Heavy", "speed": 28, "accuracy": 155, "luck": 40, "anti_sub": 0, "oil_cost": 14}
    }
]

print("🚀 Starting AstraNova Sync...")

# 1. Fetch existing ships so we don't cause duplicate errors
existing_ships_req = requests.get(f"{API_URL}/ships/")
existing_names = [s["name"] for s in existing_ships_req.json()] if existing_ships_req.status_code == 200 else []

for entry in ship_data:
    ship_name = entry["ship"]["name"]
    
    # Check if ship already exists
    if ship_name in existing_names:
        print(f"⏩ {ship_name} is already in the database. Skipping.")
        continue

    # --- THE IMAGE FIX ---
    # The Wiki requires underscores instead of spaces (e.g., "New_JerseyIcon.png")
    clean_name = ship_name.replace(" ", "_")
    entry["ship"]["icon_url"] = f"https://azurlane.koumakan.jp/wiki/Special:FilePath/{clean_name}Icon.png"
    
    # Insert Ship
    ship_resp = requests.post(f"{API_URL}/ships/", json=entry["ship"])
    if ship_resp.status_code == 200:
        ship_id = ship_resp.json()["id"]
        print(f"✅ Added {ship_name} (ID: {ship_id}) with official art!")
        
        # Insert Stats
        requests.post(f"{API_URL}/ships/{ship_id}/stats/", json=entry["stats"])
    else:
        print(f"❌ Failed to add {ship_name}: {ship_resp.text}")

print("🎉 Sync Complete!")