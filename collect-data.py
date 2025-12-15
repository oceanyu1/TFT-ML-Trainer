import pandas as pd
import requests, os, time
from dotenv import load_dotenv
import helpers # Your helper file with get_carry_unit

load_dotenv()
API_KEY = os.getenv("TFT_API_KEY")
headers = {"X-Riot-Token": API_KEY}

# CONFIGURATION
TARGET_MATCH_COUNT = 2000  # How many matches do you want total?
CSV_FILENAME = "tft_match_data.csv"
BATCH_SIZE = 50  # Save to CSV every 50 matches so you don't lose progress

# 1. SETUP: Check what we already have
existing_match_ids = set()
if os.path.exists(CSV_FILENAME):
    print(f"Found existing {CSV_FILENAME}. Loading IDs to avoid duplicates...")
    try:
        # Only read the match_id column to save memory
        existing_df = pd.read_csv(CSV_FILENAME, usecols=['match_id'])
        existing_match_ids = set(existing_df['match_id'].unique())
        print(f"Resuming! We already have {len(existing_match_ids)} unique matches.")
    except ValueError:
        print("CSV seems empty or corrupted. Starting fresh.")

# 2. GET PLAYER LIST (Challenger + Grandmaster to get enough matches)
# You might need more than just Challenger to get 2000 unique games quickly
queues = ["master"]
player_puuids = []

print("Fetching player lists...")
for tier in queues:
    url = f"https://na1.api.riotgames.com/tft/league/v1/{tier}?queue=RANKED_TFT"
    try:
        resp = requests.get(url, headers=headers).json()
        entries = resp.get('entries', [])
        print(f"Found {len(entries)} players in {tier}.")
        player_puuids.extend([e['puuid'] for e in entries])
    except:
        print(f"Could not fetch {tier}")

# 3. COLLECT MATCH IDs
print(f"Collecting Match IDs from {len(player_puuids)} players...")
match_ids_to_fetch = set()

for i, puuid in enumerate(player_puuids):
    # Stop if we have enough "planned" matches
    if len(match_ids_to_fetch) + len(existing_match_ids) >= TARGET_MATCH_COUNT:
        break
        
    url = f"https://americas.api.riotgames.com/tft/match/v1/matches/by-puuid/{puuid}/ids?start=0&count=20"
    try:
        new_ids = requests.get(url, headers=headers).json()
        
        # Only add IDs we haven't processed yet
        for mid in new_ids:
            if mid not in existing_match_ids:
                match_ids_to_fetch.add(mid)
                
        # Simple progress bar
        if i % 10 == 0:
            print(f"Scanned {i} players... Queue size: {len(match_ids_to_fetch)} new matches.")
            
        time.sleep(1.2) # Rate limit safety
    except Exception as e:
        print(f"Error fetching match list: {e}")

print(f"Ready to download {len(match_ids_to_fetch)} new matches!")

# 4. DOWNLOAD LOOP
new_rows = []
total_processed = 0

for match_id in list(match_ids_to_fetch):
    url = f"https://americas.api.riotgames.com/tft/match/v1/matches/{match_id}"
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 429:
            print("Rate limit hit! Sleeping 10s...")
            time.sleep(10)
            # Retry this match? Ideally yes, but skipping is easier for now
            continue
        
        game_json = response.json()
        participants = game_json.get('info', {}).get('participants', [])
        
        # --- YOUR PARSING LOGIC HERE ---
        for p in participants:
            # [PASTE YOUR EXACT PARSING LOGIC FROM THE PREVIOUS TURN HERE]
            # [Ensure you use app.get_carry_unit(p['units'])]
            
            # ... calculation logic ...
            # logic to calculate "Board Value" (Economy proxy)
            board_cost = 0
            three_star_count = 0

            current_carry = helpers.get_carry_unit(p['units'])
            temp_cost = current_carry.get('rarity', 10)
            carry_cost = 0 # cost of main carry (if it works)
            if temp_cost > 7:  # Filter out fake high costs
                carry_cost = -1
            elif temp_cost == 6:
                carry_cost = 5
            elif temp_cost in [0, 1, 2]:
                carry_cost = temp_cost + 1
            else:
                carry_cost = temp_cost
            
            for unit in p['units']:
                character_id = unit.get('character_id', '')
                
                # 1. SKIP Summons/Dummies
                # Standard Set 15 units look like "TFT15_Jinx", "TFT15_Sion"
                # Dummies/Summons usually look like "TFT_TargetDummy" or "TFT_VoidSpawn"
                if "TargetDummy" in character_id or "Minion" in character_id:
                    continue

                # 2. Get Rarity
                rarity = unit.get('rarity', 0)
                tier = unit.get('tier', 1)
                # 3. Cap the cost at 5 (Standard Legendary)
                # Even if it returns 9 (Dummy), we force it to 5 or skip it.
                
                # CHANGE THIS FOR SET 16 WHEN NEW UNITS ARE ADDED
                temp_cost = rarity
                real_cost = 0
                if temp_cost > 7:  # Filter out fake high costs
                    real_cost = 0
                elif temp_cost == 6:
                    real_cost = 5
                elif temp_cost in [0, 1, 2]:
                    real_cost = temp_cost + 1
                else:
                    real_cost = temp_cost

                # Now do your calculations
                board_cost += real_cost * (3**(tier-1))
                
                if tier == 3:
                    three_star_count += 1
            
            new_rows.append({
                "match_id": match_id,
                "puuid": p['puuid'],
                "placement": p['placement'],
                "level": p['level'],
                "gold_left": p['gold_left'],
                "last_round": p['last_round'],
                "time_eliminated": p['time_eliminated'],
                "total_damage": p['total_damage_to_players'],
                "board_value": board_cost,
                "three_star_count": three_star_count,
                "carry_unit_cost": carry_cost
            })
        # -------------------------------
        
        total_processed += 1
        print(f"[{total_processed}/{len(match_ids_to_fetch)}] Processed {match_id}")

        # BATCH SAVE
        if len(new_rows) >= BATCH_SIZE * 8: # (8 rows per match)
            df_batch = pd.DataFrame(new_rows)
            # If file doesn't exist, write header. If it does, append without header.
            header = not os.path.exists(CSV_FILENAME)
            df_batch.to_csv(CSV_FILENAME, mode='a', header=header, index=False)
            print(f"--- SAVED BATCH TO CSV ---")
            new_rows = [] # Clear memory

        time.sleep(1.2)

    except Exception as e:
        print(f"Failed {match_id}: {e}")

# Save any remaining rows
if new_rows:
    df_batch = pd.DataFrame(new_rows)
    header = not os.path.exists(CSV_FILENAME)
    df_batch.to_csv(CSV_FILENAME, mode='a', header=header, index=False)
    print("--- FINAL SAVE COMPLETE ---")

df = pd.read_csv("tft_match_data.csv")
print(f"Rows before cleaning: {len(df)}")

# 2. The 'Drop Duplicates' Nuke
# This keeps the first copy and deletes any others with the same match_id + puuid
df_clean = df.drop_duplicates(subset=['match_id', 'puuid'])

# 3. Save it back
df_clean.to_csv("tft_match_data_clean.csv", index=False)
print(f"Rows after cleaning: {len(df_clean)}")

print("Data collection done.")