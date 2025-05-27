import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import re
import time

# --- CONFIGURATION ---
FOLDER = Path(r"C:\Users\benva\OneDrive\Documents\Catullus\Catullus-poems\Data")
FOLDER.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}

# --- UTILITIES ---
def roman_to_int(roman):
    roman = roman.upper()
    values = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
    result, prev = 0, 0
    for char in reversed(roman):
        val = values.get(char, 0)
        result += -val if val < prev else val
        prev = val
    return result

def extract_id(title):
    match = re.match(r"([IVXLCDM]+)(b?)\.", title)
    if match:
        number = roman_to_int(match.group(1))
        return f"{number}b" if match.group(2) else str(number)
    return title

def index_by_id(poems):
    return {str(p['id']).lower(): p['text'] for p in poems}

def generate_poem_ids():
    ids = [str(i) for i in range(1, 117)]
    for b_id in ("2b", "14b", "58b", "68b", "78b"):
        index = ids.index(str(int(b_id[:-1]))) + 1
        ids.insert(index, b_id)
    return ids

# --- SCRAPERS ---
def scrape_latin_library():
    print("Scraping Latin Library...")
    url = "https://www.thelatinlibrary.com/catullus.shtml"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    paragraphs = soup.find_all("p")

    poems = []
    current_title, current_lines = None, []

    for p in paragraphs:
        b_tag = p.find("b")
        if b_tag:
            if current_title and current_lines:
                poems.append({"title": current_title, "text": "\n".join(current_lines)})
            current_title = b_tag.get_text(strip=True)
            current_lines = []
        else:
            lines = list(p.stripped_strings)
            if lines:
                current_lines.extend(lines)

    if current_title and current_lines:
        poems.append({"title": current_title, "text": "\n".join(current_lines)})

    path = FOLDER / "catullus_all_poems.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(poems, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(poems)} Latin poems to {path}\n")

def scrape_perseus(poem_ids):
    print("Scraping Perseus...")
    base_url = "https://www.perseus.tufts.edu/hopper/text?doc=Perseus:text:1999.02.0005:poem={}"
    poems = []
    for pid in poem_ids:
        print(f"Fetching poem {pid}...")
        url = base_url.format(pid)
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.content, "html.parser")
            text_div = soup.find("div", class_="text")
            if text_div:
                poems.append({"id": pid, "source": "Perseus", "url": url, "text": text_div.get_text("\n", strip=True)})
        except Exception as e:
            print(f"Error fetching poem {pid}: {e}")
        time.sleep(1)

    path = FOLDER / "translations/catullus_english_perseus.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(poems, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(poems)} poems to {path}\n")

def scrape_negenborn(poem_ids):
    print("Scraping Negenborn...")
    base_url = "http://rudy.negenborn.net/catullus/text2/e{}.htm"
    poems = []

    def fetch_negenborn_poem(poem_id):
        url = base_url.format(poem_id)
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.content, "html.parser")
            td_candidates = soup.find_all("td")
            poem_text = None
            for td in td_candidates:
                if td.find("catullus_translation"):
                    poem_text = td.find("catullus_translation").get_text(separator="\n", strip=True)
                    break
                elif "Mentula" in td.get_text() or "Lesbia" in td.get_text():
                    candidate_text = td.get_text(separator="\n", strip=True)
                    if len(candidate_text.split()) > 10:
                        poem_text = candidate_text
                        break
            if poem_text:
                return {"id": poem_id, "source": "Negenborn", "url": url, "text": poem_text}
            else:
                print(f"No text found for poem {poem_id}")
                return None
        except Exception as e:
            print(f"Error fetching poem {poem_id}: {e}")
            return None

    for pid in poem_ids:
        print(f"Fetching poem {pid}...")
        poem_data = fetch_negenborn_poem(pid)
        if poem_data:
            poems.append(poem_data)
        time.sleep(0.5)

    path = FOLDER / "translations/catullus_english_negenborn.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(poems, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(poems)} poems to {path}\n")



def scrape_poetryintranslation():
    url = "https://www.poetryintranslation.com/PITBR/Latin/Catullus.php"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    main_content = soup.find("div", class_="poem")
    poems, current_poem = [], None

    def is_caption(tag):
        text = tag.get_text(strip=True)
        return (not text or len(text.split()) <= 3 or
                text[0] in {"‘", "’", "“", "”", '"', "'"} or
                re.search(r"(museum|artist|anonymous|c\\. ?\\d{3,4})", text, re.IGNORECASE))

    for tag in main_content.find_all(["h2", "p"]):
        if tag.name == "h2" and tag.text.strip().split('.')[0].isdigit():
            if current_poem:
                current_poem["text"] = "\n".join(current_poem["text"])
                poems.append(current_poem)
            match = re.match(r"(\d+[a-z]?)\.", tag.text.strip().lower())
            poem_id = match.group(1) if match else str(len(poems) + 1)
            current_poem = {"id": poem_id, "source": "PoetryInTranslation", "url": url, "text": []}
        elif tag.name == "p" and current_poem:
            if not tag.find("img") and not is_caption(tag):
                text = tag.get_text(" ", strip=True)
                if text:
                    current_poem["text"].append(text)

    if current_poem:
        current_poem["text"] = "\n".join(current_poem["text"])
        poems.append(current_poem)

    with open(FOLDER / "translations/catullus_english_poetryintranslation.json", "w", encoding="utf-8") as f:
        json.dump(poems, f, ensure_ascii=False, indent=2)

def scrape_wikisource():
    print("Scraping Wikisource...")
    BASE_URL = "https://en.wikisource.org"
    INDEX_URL = f"{BASE_URL}/wiki/Translation:The_poems_of_Catullus"
    response = requests.get(INDEX_URL, headers=HEADERS)
    soup = BeautifulSoup(response.content, "html.parser")
    links = soup.select("div.mw-parser-output li a")
    poem_links = [(re.search(r"Catullus (\d+[a-z]?)", link.text).group(1), BASE_URL + link['href'])
                  for link in links if link['href'].startswith("/wiki/Translation:Catullus_") and "Catullus" in link.text]

    poems = []
    for pid, url in poem_links:
        print(f"Fetching poem {pid}...")
        try:
            res = requests.get(url, headers=HEADERS)
            page = BeautifulSoup(res.content, "html.parser")
            table = page.select_one("table")
            if not table:
                continue
            rows = table.find_all("tr")[1:]
            lines = [row.find_all("td")[0].get_text(" ", strip=True)
                     for row in rows if len(row.find_all("td")) >= 2]
            if lines:
                poems.append({"id": pid, "source": "Wikisource", "url": url, "text": "\n".join(lines)})
        except Exception as e:
            print(f"Error fetching Wikisource poem {pid}: {e}")

    path = FOLDER / "translations/catullus_wikisource_english_all.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(poems, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(poems)} poems to {path}\n")

def combine_all():
    print("Combining all sources into one JSON file...")

    # Load Latin poems from data/
    with open(FOLDER / "catullus_all_poems.json", encoding="utf-8") as f:
        latin_poems = json.load(f)

    # Translation files are inside data/translations/
    translation_folder = FOLDER / "translations"

    sources = {
        "Negenborn": "catullus_english_negenborn.json",
        "Perseus": "catullus_english_perseus.json",
        "Wikisource": "catullus_wikisource_english_all.json",
        "PoetryinTranslation": "catullus_english_poetryintranslation.json"
    }

    # Corrected: open translation files from data/translations/
    indexed_translations = {
        name: index_by_id(json.load(open(translation_folder / file, encoding="utf-8")))
        for name, file in sources.items()
    }

    combined_poems = []
    for poem in latin_poems:
        poem_id = extract_id(poem["title"])
        entry = {
            "id": poem_id,
            "latin_title": poem["title"],
            "latin_text": poem["text"],
            "translations": {
                name: translations[poem_id.lower()]
                for name, translations in indexed_translations.items()
                if poem_id.lower() in translations
            }
        }
        combined_poems.append(entry)

    # Save to data/
    path = FOLDER / "catullus_combined_translations.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(combined_poems, f, ensure_ascii=False, indent=2)

    print(f"Saved combined data with {len(combined_poems)} poems to {path}\n")

    print("Combining all sources into one JSON file...")
    with open(FOLDER / "catullus_all_poems.json", encoding="utf-8") as f:
        latin_poems = json.load(f)

    sources = {
        "Negenborn": "catullus_english_negenborn.json",
        "Perseus": "catullus_english_perseus.json",
        "Wikisource": "catullus_wikisource_english_all.json",
        "PoetryinTranslation": "catullus_english_poetryintranslation.json"
    }

    indexed_translations = {
        name: index_by_id(json.load(open(FOLDER / file, encoding="utf-8")))
        for name, file in sources.items()
    }

    combined_poems = []
    for poem in latin_poems:
        poem_id = extract_id(poem["title"])
        entry = {
            "id": poem_id,
            "latin_title": poem["title"],
            "latin_text": poem["text"],
            "translations": {
                name: translations[poem_id.lower()]
                for name, translations in indexed_translations.items()
                if poem_id.lower() in translations
            }
        }
        combined_poems.append(entry)

    path = FOLDER / "catullus_combined_translations.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(combined_poems, f, ensure_ascii=False, indent=2)
    print(f"Saved combined data with {len(combined_poems)} poems to {path}\n")

# --- MAIN ---
if __name__ == "__main__":
    poem_ids = generate_poem_ids()
    scrape_latin_library()
    scrape_perseus(poem_ids)
    scrape_negenborn(poem_ids)
    scrape_wikisource()
    scrape_poetryintranslation()
    combine_all()
