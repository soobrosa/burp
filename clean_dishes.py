import pandas as pd
import re
from collections import defaultdict

def is_noise_line(dish_name):
    """Identify lines that are clearly noise (not actual dish names)"""
    dish_lower = dish_name.lower()
    
    # URLs and contact info
    if any(pattern in dish_lower for pattern in ['http', 'www.', '@', 'tel:', 'telefon', '+36', '06-']):
        return True
    
    # Addresses and location info
    if any(pattern in dish_lower for pattern in ['utca', 'könyök', 'kiskunfélegyháza']):
        return True
    
    # Website/business text
    if any(pattern in dish_lower for pattern in ['weboldal', 'logo', 'facebook', 'honlap', 'kattintson']):
        return True
    
    # Marketing text and business phrases
    if any(pattern in dish_lower for pattern in ['korrekt árak', 'kedves kiszolgálás', 'hétköznapi árak', 
                                                'változatos ételek', 'paypass', 'bankkártya', 'svédasztal',
                                                'korlátlan ételfogyasztás', 'hétfőtől-péntekig']):
        return True
    
    # Menu structure text and pricing
    if any(pattern in dish_lower for pattern in ['állandó kínálat', 'húsos második helyett', 'választható:',
                                                'kínálatunk itt', 'előfizetve', 'mai menü ár', 'menü ár',
                                                'menekülő menü:', 'napi menünk:', 'mai menü:',
                                                'a mai menekülő menü:', 'menekülő menük:']):
        return True

    # Greetings, opening announcements, season's greetings, menu chrome
    if any(pattern in dish_lower for pattern in ['kínálatunk', 'itt találja', 'köszönjük', 'megértés',
                                                'kedves vendég', 'vendégeink', 'várjuk', 'viszontlát',
                                                'jó étvágy', 'nyitás', 'nyitva', 'zárva', 'áraink',
                                                'kellemes', 'boldog új', 'ünnepeket', 'rendelhető',
                                                'ételeink', 'első:', 'második:', 'harmadik:',
                                                'levesek:', 'főételek:', 'köretek:', 'desszertek:']):
        return True

    # Price tokens (e.g. "2300ft", "990 ft") — menu pricing, not a dish
    if re.search(r'\d+\s*ft\b', dish_lower):
        return True

    # Section headers / labels ending in a colon (e.g. "Levesek:", "Mai menü :")
    if dish_name.strip().endswith(':'):
        return True
    
    # Time indicators and administrative text
    if re.match(r'^[\d:\s-]+$', dish_name) or dish_name in ['felnőtt:', 'leves nélkül']:
        return True
    
    # Price patterns (standalone prices or price lists)
    if re.match(r'^\d+ft$', dish_lower) or re.match(r'^\d+$', dish_name):
        return True
    if 'tartárral 2.' in dish_lower and 'rántott szelet' in dish_lower:  # Price list patterns
        return True
    
    # Generic administrative text
    if dish_name.strip() in ['BUÉK', 'Mai menü', 'Mai menü:', '']:
        return True
    
    # Complex menu descriptions (these are menu formats, not actual dishes)
    if any(pattern in dish_lower for pattern in ['menekülő menü:', 'csülkös babgulyás a. vagy b.',
                                                'crispy chicken nuggets 7db', 'cryspy chicken wings',
                                                'weber, crispy vagy grillezett']):
        return True
    
    # Long administrative descriptions
    if len(dish_name) > 100 and any(word in dish_lower for word in ['vagy', 'menü', 'választható']):
        return True
    
    return False

# Proper noun stems in Hungarian cuisine (geographic, personal, foreign terms)
# These should stay capitalized after case normalization.
# We match by prefix so that suffixed forms (e.g. "debrecenivel") also match.
PROPER_NOUN_STEMS = [
    # Geographic style names
    'bakonyi', 'bolognai', 'brassói', 'csongrádi', 'debreceni', 'frankfurti',
    'hortobágyi', 'jókai', 'kolozsvári', 'milánói', 'müncheni', 'párizsi',
    'pozsonyi', 'szegedi', 'újházy',
    # Personal/style names
    'cordon', 'bleu', 'holstein', 'orly', 'stefánia', 'pékné',
    'stroganoff', 'wellington',
    # Foreign terms that are conventionally capitalized
    'bbq', 'gyros',
]

def _is_proper(word):
    """Check if a word (lowercase, punctuation-stripped) matches a proper noun stem."""
    for stem in PROPER_NOUN_STEMS:
        if word == stem or word.startswith(stem):
            return True
    return False

def normalize_case(dish_name):
    """Normalize capitalization: sentence case, preserving proper nouns."""
    if not dish_name:
        return dish_name

    words = dish_name.lower().split()
    result = []
    for i, word in enumerate(words):
        # Strip punctuation for lookup, but keep original punctuation
        stripped = word.strip(',:;.!?+()-"\'')
        if i == 0:
            # Always capitalize first word
            result.append(word[0].upper() + word[1:] if word else word)
        elif _is_proper(stripped):
            # Capitalize proper nouns
            idx = word.index(stripped[0]) if stripped else 0
            result.append(word[:idx] + word[idx].upper() + word[idx+1:] if word else word)
        else:
            result.append(word)

    return ' '.join(result)

def clean_dish_name(dish_name):
    """Clean and standardize dish names"""
    # Remove quotes
    dish_name = dish_name.strip('"\'')

    # Remove leading dashes and bullets
    dish_name = re.sub(r'^[-•\s]+', '', dish_name)

    # Remove trailing price information (like "2.370,-")
    dish_name = re.sub(r'\s+\d+[\.,]\d+[\.,]?-?\s*$', '', dish_name)

    # Remove portion weights (like "30dkg", "40dkg")
    dish_name = re.sub(r'\b\d+dkg\b', '', dish_name)

    # Remove allergen codes (numbers in parentheses or standalone)
    dish_name = re.sub(r'\s*\(\s*\d+[\s,\d]*\)\s*', ' ', dish_name)
    dish_name = re.sub(r'\s+\d+[\s,\d]*$', '', dish_name)

    # Remove dessert additions
    dish_name = re.sub(r'\s*Desszert:.*$', '', dish_name, flags=re.IGNORECASE)
    dish_name = re.sub(r'\s*\+\s*sütemény.*$', '', dish_name, flags=re.IGNORECASE)
    dish_name = re.sub(r'\s*\+\s*meglepetés.*$', '', dish_name, flags=re.IGNORECASE)

    # Remove option letters (A:, B:, C:) at the beginning
    dish_name = re.sub(r'^[A-Z]:\s*', '', dish_name)

    # Remove trailing punctuation like " -"
    dish_name = re.sub(r'\s*-\s*$', '', dish_name)

    # Clean up multiple spaces
    dish_name = re.sub(r'\s+', ' ', dish_name).strip()

    # Normalize capitalization
    dish_name = normalize_case(dish_name)

    return dish_name

def is_actual_dish(dish_name):
    """Additional filter to identify actual dishes vs menu descriptions"""
    dish_lower = dish_name.lower()
    
    # Skip very short names
    if len(dish_name) < 4:
        return False
    
    # Skip if it contains multiple dish options (menu descriptions)
    if dish_lower.count(' vagy ') > 1:  # "vagy" means "or" in Hungarian
        return False
    
    # Skip if it's clearly a menu structure description
    if any(pattern in dish_lower for pattern in ['rántott /sajt vagy', 'állandó levesek:', 
                                                'minden nap', ': - ig']):
        return False
    
    # Look for actual food indicators (Hungarian food terms)
    food_indicators = ['leves', 'gulyás', 'pörkölt', 'rántott', 'sült', 'főzelék', 'húsleves', 
                      'schnitzel', 'spagetti', 'tészta', 'rizs', 'burgonya', 'saláta',
                      'csirke', 'sertés', 'marha', 'hal', 'sajt', 'tokány', 'paprikás']
    
    if any(indicator in dish_lower for indicator in food_indicators):
        return True
    
    # If it doesn't contain food indicators, it might still be food if it's simple
    if len(dish_name.split()) <= 3 and not any(char in dish_name for char in [':', '/', 'vagy']):
        return True
    
    return False

def normalize_similar_dishes(dishes):
    """Group similar dishes together (typos, variations)"""
    normalized = {}
    dish_groups = defaultdict(list)
    
    for dish, count in dishes.items():
        if len(dish) < 4:  # Skip very short names
            continue
            
        # Create a normalized key for grouping similar dishes
        key = dish.lower()
        
        # Normalize Hungarian characters
        key = re.sub(r'[áà]', 'a', key)
        key = re.sub(r'[éè]', 'e', key)
        key = re.sub(r'[íì]', 'i', key)
        key = re.sub(r'[óò]', 'o', key)
        key = re.sub(r'[úù]', 'u', key)
        key = re.sub(r'[űü]', 'u', key)
        key = re.sub(r'[őö]', 'o', key)
        
        # Remove punctuation and normalize spaces
        key = re.sub(r'[^\w\s]', ' ', key)
        key = re.sub(r'\s+', ' ', key).strip()
        
        dish_groups[key].append((dish, count))
    
    # For each group, pick the most frequent version as canonical
    for key, group in dish_groups.items():
        if len(group) == 1:
            dish, count = group[0]
            normalized[dish] = count
        else:
            # Pick the version with highest count, or longest name if tied
            group.sort(key=lambda x: (-x[1], -len(x[0])))
            canonical_dish = group[0][0]
            total_count = sum(count for _, count in group)
            normalized[canonical_dish] = total_count
    
    return normalized

def main():
    # Read the CSV file
    df = pd.read_csv('dish_count.csv')
    
    print(f"Original entries: {len(df)}")
    
    # Filter out noise lines
    clean_df = df[~df['dish_name'].apply(is_noise_line)].copy()
    print(f"After removing noise: {len(clean_df)}")
    
    # Clean dish names
    clean_df['cleaned_dish'] = clean_df['dish_name'].apply(clean_dish_name)
    
    # Remove empty names after cleaning
    clean_df = clean_df[clean_df['cleaned_dish'].str.len() > 3]
    print(f"After cleaning names: {len(clean_df)}")
    
    # Filter for actual dishes
    clean_df = clean_df[clean_df['cleaned_dish'].apply(is_actual_dish)]
    print(f"After filtering for actual dishes: {len(clean_df)}")
    
    # Create a dictionary of dish counts
    dish_counts = {}
    for _, row in clean_df.iterrows():
        dish = row['cleaned_dish']
        count = row['count']
        if dish in dish_counts:
            dish_counts[dish] += count
        else:
            dish_counts[dish] = count
    
    # Normalize similar dishes
    normalized_dishes = normalize_similar_dishes(dish_counts)
    
    print(f"After normalizing similar dishes: {len(normalized_dishes)}")
    
    # Convert back to DataFrame and sort by count
    result_df = pd.DataFrame([
        {'dish_name': dish, 'count': count}
        for dish, count in normalized_dishes.items()
    ]).sort_values('count', ascending=False)
    
    # Save cleaned results
    result_df.to_csv('cleaned_dishes.csv', index=False)
    
    print("\nTop 30 cleaned dishes:")
    print(result_df.head(30).to_string(index=False))
    
    print(f"\nSaved {len(result_df)} cleaned dishes to 'cleaned_dishes.csv'")

if __name__ == '__main__':
    main() 