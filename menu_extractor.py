import os
import re
from datetime import datetime
from bs4 import BeautifulSoup
import pandas as pd

def clean_text(text):
    if not text:
        return ''
    # Remove extra whitespace and normalize
    text = ' '.join(text.split())
    # Remove common price indicators
    text = re.sub(r'\s*\+\s*\d+\s*Ft\s*doboz', '', text)
    text = re.sub(r'\s*\(\s*\d+\s*Ft\s*\)', '', text)
    text = re.sub(r'\s*\d+\s*(?:Ft|ft)(?:\s*[,.].*)?$', '', text)
    # Remove phone numbers and delivery info
    text = re.sub(r'Tel(?:efon)?:?\s*(?:06|\+36)?[-\s]?\d[\d\s-]+', '', text)
    text = re.sub(r'Kiszállítás(?:\s+\w+)*', '', text)
    text = re.sub(r'Házhozszállítás(?:\s+\w+)*', '', text)
    text = re.sub(r'Menü(?:\s+\w+)*', '', text)
    text = re.sub(r'rendelés(?:\s+\w+)*', '', text)
    text = re.sub(r'\d{1,2}:\d{2}(?:-\d{1,2}:\d{2})?', '', text)
    # Remove extra punctuation and special characters
    text = re.sub(r'[,.!?]+$', '', text)
    text = re.sub(r'[\(\)]+', '', text)
    # Remove common phrases
    text = re.sub(r'(?i)(?:csak második|extra|előrendelés|kiszállítás|házhozszállítás|csomagolás|doboz|ingyenes|szép kártya|otp|bankkártya|készpénz|fizetés|nyitvatartás|zárva|nyitva|étlap|ajánlat|akció|kedvezmény).*$', '', text)
    # Clean up the result
    text = text.strip()
    return text if len(text) > 2 else ''

def extract_price(text):
    """Extract price from text."""
    if not text:
        return None
    price_match = re.search(r'(\d+)\s*(?:Ft|ft)', text)
    return int(price_match.group(1)) if price_match else None

def get_restaurant_name(img_src):
    """Get restaurant name from image source."""
    restaurant_map = {
        'desperado': 'Desperado',
        'sirius': 'Sirius Club',
        'rozsa': 'Rózsa Étterem',
        'family': 'Family Étterem',
        '2darvas': '2 Darvas',
        '2 serpenyo': '2 Serpenyő',
        'csklogo': 'CSK Burger',
        'gyros': 'Gyros Ház',
        'fornetti': 'Fornetti',
        'weber': 'Weber',
        'kulacs': 'Kulács Vendéglő',
        'otthon': 'Otthon Étterem'
    }
    
    if not img_src:
        return 'Unknown Restaurant'
    
    img_src = img_src.lower()
    for key, value in restaurant_map.items():
        if key in img_src:
            return value
    return 'Unknown Restaurant'

def extract_menu_items(soup, date):
    """Extract menu items from the HTML content."""
    menu_items = []
    
    # Find all restaurant sections (they start with an img tag followed by menu items)
    restaurant_sections = soup.find_all(['img', 'p'])
    
    current_restaurant = None
    menu_text = []
    
    for element in restaurant_sections:
        if element.name == 'img':
            # If we find a restaurant logo, process the previous restaurant's menu
            if current_restaurant and menu_text:
                menu_items.extend(process_restaurant_menu(current_restaurant, menu_text, date))
                menu_text = []
            
            # Get the new restaurant name
            src = element.get('src', '').lower()
            if any(name in src for name in ['desperado', 'sirius', 'rozsa', 'family', '2darvas', '2serpenyo', 'csklogo', 'gyros', 'fornetti', 'weber', 'kulacs', 'otthon']):
                current_restaurant = get_restaurant_name(src)
        
        elif current_restaurant and element.name == 'p':
            text = element.get_text().strip()
            if text and not any(skip in text.lower() for skip in ['étlap', 'ajánlat', 'nyitva', 'zárva', 'kártya', 'bankkártya', 'készpénz', 'tel:', 'rendelés', 'kiszállítás']):
                menu_text.append(text)
    
    # Process the last restaurant
    if current_restaurant and menu_text:
        menu_items.extend(process_restaurant_menu(current_restaurant, menu_text, date))
    
    return menu_items

def process_restaurant_menu(restaurant, menu_text, date):
    """Process a restaurant's menu text and extract dishes."""
    menu_items = []
    prices = {}
    
    # Extract prices first
    for text in menu_text:
        text_lower = text.lower()
        if 'menü' in text_lower and 'ft' in text_lower:
            price = extract_price(text)
            if price and (1500 <= price <= 3500):  # Reasonable price range for menus
                prices['regular'] = price
        elif 'extra' in text_lower and 'ft' in text_lower:
            price = extract_price(text)
            if price and (2000 <= price <= 4000):  # Reasonable price range for extra menus
                prices['extra'] = price
    
    # Process menu items - each text element should be processed separately
    for text in menu_text:
        # Skip price-only lines and very short texts
        if len(text) < 3 or re.match(r'^[\d\s]*(?:Ft|ft)[\s\W]*$', text):
            continue
        
        # Clean the text
        cleaned_text = clean_text(text)
        if not cleaned_text or len(cleaned_text) < 3:
            continue
        
        # Determine if this is a main dish or option based on content
        text_lower = cleaned_text.lower()
        
        # Check if it's an option (starts with A:, B:, C:, etc.)
        if re.match(r'^[A-Z]:', cleaned_text):
            # Extract the option letter and the dish name
            option_match = re.match(r'^([A-Z]):\s*(.+)', cleaned_text)
            if option_match:
                option_letter = option_match.group(1)
                dish_name = option_match.group(2).strip()
                if dish_name:
                    menu_items.append({
                        'restaurant': restaurant,
                        'dish_name': dish_name,
                        'item_number': 1,
                        'menu_type': f'option_{option_letter}',
                        'prices': prices,
                        'date': date
                    })
        # Check if text contains A: or B: separators and split them
        elif re.search(r'\s*[AB]:\s*', cleaned_text, re.IGNORECASE):
            # Split the text on separators
            split_parts = split_on_separators(cleaned_text)
            for i, part in enumerate(split_parts, 1):
                if part and len(part) > 2:
                    menu_items.append({
                        'restaurant': restaurant,
                        'dish_name': part,
                        'item_number': i,
                        'menu_type': 'main',
                        'prices': prices,
                        'date': date
                    })
        # Check if it's a main dish (contains soup-related words)
        elif any(soup_word in text_lower for soup_word in ['leves', 'gulyás', 'krémleves', 'gombócleves', 'csontleves', 'gyümölcsleves']):
            menu_items.append({
                'restaurant': restaurant,
                'dish_name': cleaned_text,
                'item_number': 1,
                'menu_type': 'main',
                'prices': prices,
                'date': date
            })
        # Otherwise, treat as a regular dish
        else:
            # Skip if it contains price information or other non-dish content
            if not any(skip in text_lower for skip in ['ft', 'tel:', 'rendelés', 'kiszállítás', 'nyitva', 'zárva']):
                menu_items.append({
                    'restaurant': restaurant,
                    'dish_name': cleaned_text,
                    'item_number': 1,
                    'menu_type': 'main',
                    'prices': prices,
                    'date': date
                })
    
    return menu_items

def process_html_file(file_path):
    """Process a single HTML file and extract menu items."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        try:
            # If UTF-8 fails, try with ISO-8859-2 (common for Hungarian text)
            with open(file_path, 'r', encoding='iso-8859-2') as f:
                content = f.read()
        except UnicodeDecodeError:
            # If ISO-8859-2 fails, try with windows-1250
            with open(file_path, 'r', encoding='windows-1250') as f:
                content = f.read()
    
    # Extract date from filename
    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', file_path)
    if not date_match:
        return []
    
    date = date_match.group(1)
    soup = BeautifulSoup(content, 'html.parser')
    return extract_menu_items(soup, date)

def split_on_separators(text):
    """Split text on A: and B: separators and return list of parts."""
    if not text:
        return []
    
    # Split on A: and B: (case insensitive)
    parts = re.split(r'\s*[AB]:\s*', text, flags=re.IGNORECASE)
    
    # Filter out empty parts and clean up
    cleaned_parts = []
    for part in parts:
        part = part.strip()
        if part and len(part) > 2:
            cleaned_parts.append(part)
    
    return cleaned_parts

def main():
    """Main function to process all HTML files."""
    html_dir = '1_html'
    all_menu_items = []
    processed_files = 0
    
    for filename in os.listdir(html_dir):
        if filename.endswith('.html'):
            file_path = os.path.join(html_dir, filename)
            menu_items = process_html_file(file_path)
            all_menu_items.extend(menu_items)
            processed_files += 1
    
    # Convert to DataFrame and save to CSV
    df = pd.DataFrame(all_menu_items)
    # Reorder columns to put date first
    df = df[['date', 'restaurant', 'dish_name', 'item_number', 'menu_type', 'prices']]
    df.to_csv('daily_menus.csv', index=False)
    print(f"Processed {len(all_menu_items)} menu items from {processed_files} files.")

if __name__ == '__main__':
    main() 