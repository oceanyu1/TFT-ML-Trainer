def get_carry_unit(player_units):
    # A quick "Ban List" of words that usually indicate a Tank item
    # If an item name contains these, we don't count it towards "Carry Score"
    TANK_KEYWORDS = [
        "Warmog", "Bramble", "Vest", "Negatron", "Dragon", "Claw", 
        "Gargoyle", "Stoneplate", "Sunfire", "Redemption", "Vow", 
        "Steadfast", "Crownguard", "Protector", "Thief" 
        # "Thief" is Thief's Gloves (usually on a secondary tank/carry, unreliable)
    ]

    best_carry = None
    max_score = -1

    for unit in player_units:
        # 1. Get their items (API usually returns 'itemNames' list)
        items = unit.get('itemNames', [])
        
        # 2. Calculate "Offensive Item Count"
        offensive_item_count = 0
        for item in items:
            # If the item is NOT a tank item, we assume it's offensive/utility
            is_tank = any(keyword in item for keyword in TANK_KEYWORDS)
            if not is_tank:
                offensive_item_count += 1
        
        # 3. Calculate Carry Score
        # Formula: (Offensive Items * 10) + (Unit Cost) + (Star Level * 0.5)
        # This prioritizes Items heavily, then Cost.
        
        # Safe get for rarity (cost)
        cost = unit.get('rarity', 10)
        # Filter out "fake" high costs (Target Dummies are rarity 9/10)
        if cost > 7: 
            continue
        
        star_level = unit.get('tier', 10)
        if star_level > 3:
            continue
        
        score = (offensive_item_count * 10) + cost + (star_level * 0.5)

        # 4. Compare
        if score > max_score:
            max_score = score
            best_carry = unit

    return best_carry