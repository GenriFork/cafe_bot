import requests
from bs4 import BeautifulSoup
import json

def fetch_binance_announcements(limit=10):
    url = "https://www.binance.com/en/support/announcement"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    links = soup.find_all("a", href=True)
    listings = []

    for link in links:
        title = link.text.strip()
        href = link["href"]
        if "will list" in title.lower():
            listings.append({
                "title": title,
                "url": "https://www.binance.com" + href
            })
        if len(listings) >= limit:
            break

    return listings

def update(filename="binance_announcements.json"):
    data = fetch_binance_announcements()
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"✅ Сохранено {len(data)} листингов в файл {filename}")
    return data

if __name__ == "__main__":
    save_announcements_to_json()
