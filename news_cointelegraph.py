import requests
from bs4 import BeautifulSoup

def get_cointelegraph_news(token: str, limit: int = 5):
    url = f"https://cointelegraph.com/tags/{token.lower()}"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/119.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    }

    session = requests.Session()
    response = session.get(url, headers=headers)

    if response.status_code != 200:
        print(f"⚠️ Не удалось загрузить страницу: {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    articles = soup.find_all("a", class_="post-card-inline__title-link", limit=limit)

    news = []
    for a in articles:
        title = a.text.strip()
        link = "https://cointelegraph.com" + a.get("href")
        news.append({"title": title, "url": link})

    return news

# Пример запуска
if __name__ == "__main__":
    token = "pepe"  # подставь любой
    results = get_cointelegraph_news(token)
    for item in results:
        print(f"🔸 {item['title']}\n{item['url']}\n")
