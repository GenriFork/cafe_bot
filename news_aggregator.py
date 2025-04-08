import requests
from bs4 import BeautifulSoup

def get_cointelegraph_news(token: str, limit: int = 5):
    import requests
    from bs4 import BeautifulSoup

    url = f"https://cointelegraph.com/tags/{token.lower()}"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/119.0.0.0 Safari/537.36"
        )
    }

    session = requests.Session()
    response = session.get(url, headers=headers)

    if response.status_code != 200:
        print(f"⚠️ CoinTelegraph: {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    articles = soup.select("a[href^='/news/']")  # более универсальный способ
    seen = set()
    news = []

    for a in articles:
        link = a.get("href")
        title = a.get_text(strip=True)
        full_url = "https://cointelegraph.com" + link

        # уникальность по ссылке
        if full_url not in seen and title and "/news/" in link:
            seen.add(full_url)
            news.append({"title": title, "url": full_url, "source": "CoinTelegraph"})

        if len(news) >= limit:
            break

    return news



def get_coindesk_news(token: str, limit: int = 5):
    import requests
    from bs4 import BeautifulSoup

    url = f"https://www.coindesk.com/tag/{token.lower()}"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/119.0.0.0 Safari/537.36"
        )
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"⚠️ CoinDesk: {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    articles = soup.select("a[href^='/tech/'], a[href^='/policy/'], a[href^='/business/'], a[href^='/markets/']")

    news = []
    seen = set()
    for a in articles:
        link = a.get("href")
        title = a.get_text(strip=True)
        full_url = "https://www.coindesk.com" + link
        if full_url not in seen and title:
            seen.add(full_url)
            news.append({"title": title, "url": full_url, "source": "CoinDesk"})
        if len(news) >= limit:
            break

    return news



def get_cryptoslate_news(token: str, limit: int = 5):
    import requests
    from bs4 import BeautifulSoup

    url = f"https://cryptoslate.com/?s={token.lower()}"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"⚠️ CryptoSlate: {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    articles = soup.select("a.entry-title-link")

    news = []
    seen = set()
    for a in articles:
        title = a.get_text(strip=True)
        link = a.get("href")
        if not link.startswith("http"):
            link = "https://cryptoslate.com" + link
        if link not in seen and title:
            seen.add(link)
            news.append({"title": title, "url": link, "source": "CryptoSlate"})
        if len(news) >= limit:
            break

    return news



def get_utoday_news(token: str, limit: int = 5):
    import requests
    from bs4 import BeautifulSoup

    url = f"https://u.today/tags/{token.lower()}"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"⚠️ U.Today: {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    articles = soup.select("a.news-feed__item-title")

    news = []
    seen = set()
    for a in articles:
        title = a.get_text(strip=True)
        link = "https://u.today" + a.get("href")
        if link not in seen and title:
            seen.add(link)
            news.append({"title": title, "url": link, "source": "U.Today"})
        if len(news) >= limit:
            break

    return news



def get_all_news(token: str, limit_per_site: int = 3):
    all_news = []

    try:
        all_news += get_cointelegraph_news(token, limit_per_site)
    except Exception as e:
        print(f"[CoinTelegraph ❌] {e}")

    try:
        all_news += get_coindesk_news(token, limit_per_site)
    except Exception as e:
        print(f"[CoinDesk ❌] {e}")

    return all_news



# Пример использования
if __name__ == "__main__":
    token = input("🔍 Введите токен для проверки новостей: ")
    print("\n🔎 Проверяем источники...\n")

    print("📡 CoinTelegraph:")
    try:
        ct_news = get_cointelegraph_news(token)
        for item in ct_news:
            print(f"  🔸 {item['title']} — {item['url']}")
        if not ct_news:
            print("  ❌ Нет новостей.")
    except Exception as e:
        print(f"  ❗ Ошибка: {e}")

    print("\n📡 CoinDesk:")
    try:
        cd_news = get_coindesk_news(token)
        for item in cd_news:
            print(f"  🔸 {item['title']} — {item['url']}")
        if not cd_news:
            print("  ❌ Нет новостей.")
    except Exception as e:
        print(f"  ❗ Ошибка: {e}")

    print("\n📡 CryptoSlate:")
    try:
        cs_news = get_cryptoslate_news(token)
        for item in cs_news:
            print(f"  🔸 {item['title']} — {item['url']}")
        if not cs_news:
            print("  ❌ Нет новостей.")
    except Exception as e:
        print(f"  ❗ Ошибка: {e}")

    print("\n📡 U.Today:")
    try:
        ut_news = get_utoday_news(token)
        for item in ut_news:
            print(f"  🔸 {item['title']} — {item['url']}")
        if not ut_news:
            print("  ❌ Нет новостей.")
    except Exception as e:
        print(f"  ❗ Ошибка: {e}")



