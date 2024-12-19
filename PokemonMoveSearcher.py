import requests
from bs4 import BeautifulSoup
import csv
import re

def title_case_move(move_name):
    """Helper function to properly capitalize move names"""
    lowercase_words = {'of', 'the', 'in', 'at', 'to', 'for', 'with', 'on', 'by'}
    words = move_name.split()
    result = []
    
    for i, word in enumerate(words):
        if i == 0 or word.lower() not in lowercase_words:
            result.append(word.title())
        else:
            result.append(word.lower())
    
    return '_'.join(result)

def get_pokemon_with_move(move_name):
    """
    Scrapes Bulbapedia to find all Pokémon that can learn a specific move from the Learnset section.
    
    Args:
        move_name (str): Name of the move (e.g., "Tackle", "Thunderbolt")
        
    Returns:
        list: List of Pokémon names that can learn the move
    """
    move_url = title_case_move(move_name)
    url = f"https://bulbapedia.bulbagarden.net/wiki/{move_url}_(move)"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        pokemon_set = set()

        # Find the Learnset section
        learnset_heading = soup.find(lambda tag: tag.name in ['h2', 'h3', 'h4'] and 
                                   tag.get_text(strip=True).lower().startswith('learnset'))
        
        if learnset_heading:
            # Start from the learnset heading and process until the next major section
            current = learnset_heading
            while current and not (current.name == 'h2' and current != learnset_heading):
                if current.name == 'table':
                    # Look for Pokémon links in the table
                    pokemon_links = current.find_all('a', title=re.compile(r'.+?\s\(Pokémon\)'))
                    for link in pokemon_links:
                        title = link['title']
                        if '(Pokémon)' in title:
                            base_name = title.replace(' (Pokémon)', '').strip()
                            # Add base form
                            pokemon_set.add(base_name)
                            
                            # Check for form text after the link
                            next_element = link.find_next()
                            while next_element and not next_element.name == 'a':
                                text = next_element.get_text().strip()
                                form_match = re.search(r'(Alolan|Galarian|Hisuian|Paldean)\s*Form', text)
                                if form_match:
                                    form = form_match.group(1)
                                    pokemon_set.add(f"{form} {base_name}")
                                next_element = next_element.next_sibling
                current = current.find_next()

        # Convert set to sorted list
        pokemon_list = sorted(list(pokemon_set))
        
        # Debug information
        print(f"Found {len(pokemon_list)} Pokémon that can learn {move_name}")
        
        # Save to CSV
        filename = f"{move_name.lower().replace(' ', '_')}_learners.csv"
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            formatted_pokemon_list = []
            for pokemon in pokemon_list:
                if pokemon == "Nidoran♂":
                    formatted_pokemon_list.append("NIDORANmA")
                elif pokemon == "Nidoran♀":
                    formatted_pokemon_list.append("NIDORANfE")
                else:
                    formatted_pokemon_list.append(pokemon.upper())
            writer.writerow(formatted_pokemon_list)
        
        return pokemon_list
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data. Does the following URL exist?: {e}")
        return []
    except Exception as e:
        print(f"Error processing data: {e}")
        print(f"URL attempted: {url}")
        return []

if __name__ == "__main__":
    move_name = input("Enter the move name: ")  # Allow user input
    pokemon_list = get_pokemon_with_move(move_name)
    if pokemon_list:
        print(f"\nPokémon that can learn {move_name}:")
        print(", ".join(pokemon_list))
    else:
        print(f"\nNo Pokémon found that can learn {move_name}")
        
    print(f"\nURL checked: https://bulbapedia.bulbagarden.net/wiki/{move_name.replace(' ', '_').title()}_(move)")