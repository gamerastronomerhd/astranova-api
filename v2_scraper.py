import requests

# Point this to your live Render API
API_URL = "https://astranova-api.onrender.com"

print("📡 Connecting to Global Azur Lane Database...")
response = requests.get("https://raw.githubusercontent.com/AzurAPI/azurapi-js-setup/master/ships.json")
ships_data = response.json()

# Handle both Dictionary and List formats
ship_list = ships_data.values() if isinstance(ships_data, dict) else ships_data

print(f"📦 Found {len(ship_list)} ships! Beginning high-speed uplink to AstraNova Cloud...\n")

success_count = 0

for ship in ship_list:
    try:
        # Map the community data to your database schema
        payload = {
            "name": ship['names']['en'],
            "rarity": ship.get('rarity', 'Unknown'),
            "faction": ship.get('nationality', 'Unknown'),
            "hull_type": ship.get('hullType', 'Unknown'),
            "icon_url": ship.get('thumbnail', 'null'), # The unblocked image URL!
            "health": int(ship['stats']['level120'].get('health', 0)),
            "firepower": int(ship['stats']['level120'].get('firepower', 0)),
            "anti_air": int(ship['stats']['level120'].get('antiair', 0)),
            "armor_type": ship.get('armor', 'Light')
        }

        # Fire it into your Render database
        res = requests.post(f"{API_URL}/ships/", json=payload)
        
        if res.status_code == 200:
            success_count += 1
            print(f"[{success_count}] Uplinked: {payload['name']}")
            
    except Exception as e:
        # Skip any ships with missing data fields
        continue

print(f"\n✅ Uplink Complete! {success_count} ships and official images added to the global library.")