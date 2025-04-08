import requests
import json
from tabulate import tabulate

def fetch_tokens_from_pages(pages=2, per_page=250):
    all_tokens = []
    for page in range(1, pages + 1):
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            "vs_currency": "usd",
            "order": "volume_desc",
            "per_page": per_page,
            "page": page,
            "sparkline": False
        }

        response = requests.get(url, params=params)
        if response.status_code == 200:
            all_tokens.extend(response.json())
        else:
            print(f"Ошибка на странице {page}: {response.status_code}")
    return all_tokens

def get_exchanges_for_token(token_id, max_exchanges=3):
    url = f"https://api.coingecko.com/api/v3/coins/{token_id}/tickers"
    response = requests.get(url)
    exchanges = []
    if response.status_code == 200:
        data = response.json()
        tickers = data.get("tickers", [])
        for ticker in tickers:
            exchange = ticker.get("market", {}).get("name")
            if exchange and exchange not in exchanges:
                exchanges.append(exchange)
            if len(exchanges) >= max_exchanges:
                break
    return exchanges

def filter_dump_candidates(tokens, drop_threshold=-10, volume_threshold=300_000):
    candidates = []
    for token in tokens:
        price_change = token.get("price_change_percentage_24h")
        volume = token.get("total_volume")

        if price_change is not None and price_change < drop_threshold and volume and volume > volume_threshold:
            exchanges = get_exchanges_for_token(token["id"])
            if not exchanges:
                continue  # Пропускаем токены без бирж

            candidates.append({
                "name": token["name"],
                "symbol": token["symbol"],
                "price": token["current_price"],
                "price_change_24h": price_change,
                "volume": volume,
                "market_cap": token.get("market_cap"),
                "exchanges": ", ".join(exchanges)
            })

    return candidates

def get_tokens_with_dump_risk(days=7, max_tokens=200, min_score=3):
    from datetime import datetime, timedelta
    import time

    def fetch_token_list():
        url = "https://api.coingecko.com/api/v3/coins/list"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        return []

    def fetch_token_details(token_id):
        url = f"https://api.coingecko.com/api/v3/coins/{token_id}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        return None

    def is_recent_token(token_info, days=7):
        genesis_date = token_info.get("genesis_date")
        if genesis_date:
            try:
                token_date = datetime.strptime(genesis_date, "%Y-%m-%d")
                return datetime.utcnow() - token_date <= timedelta(days=days)
            except:
                return False
        return False

    def score_for_dump(token):
        score = 0
        market = token.get("market_data", {})

        price_change = market.get("price_change_percentage_24h", 0)
        volume = market.get("total_volume", {}).get("usd", 0)
        market_cap = market.get("market_cap", {}).get("usd", 0)

        if price_change and price_change < -30:
            score += 2
        elif price_change and price_change < -15:
            score += 1

        if volume and volume > 500_000:
            score += 1

        if market_cap and market_cap < 2_000_000:
            score += 1

        try:
            token_date = datetime.strptime(token.get("genesis_date"), "%Y-%m-%d")
            if datetime.utcnow() - token_date <= timedelta(days=7):
                score += 1
        except:
            pass

        return score

    token_list = fetch_token_list()
    result = []

    for i, token in enumerate(token_list[:max_tokens]):
        details = fetch_token_details(token["id"])
        if details and is_recent_token(details, days):
            score = score_for_dump(details)
            if score >= min_score:
                result.append({
                    "name": details.get("name"),
                    "symbol": details.get("symbol"),
                    "score": score,
                    "price": details.get("market_data", {}).get("current_price", {}).get("usd", 0),
                    "price_change_24h": details.get("market_data", {}).get("price_change_percentage_24h"),
                    "volume_24h": details.get("market_data", {}).get("total_volume", {}).get("usd", 0),
                    "market_cap": details.get("market_data", {}).get("market_cap", {}).get("usd", 0),
                    "genesis_date": details.get("genesis_date"),
                    "contract_address": details.get("platforms", {})
                })
        print(f"[{i+1}/{max_tokens}] Обработано: {token['name']}")
        time.sleep(1.5)

    return result  # ← вот он должен быть внутри функции, как здесь


def save_to_json(data, filename="dump_candidates_final.json"):
    if not data:
        print("⚠️ Нечего сохранять — список пуст.")
        return
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"\n✅ Сохранено {len(data)} дамп-кандидатов в файл {filename}")


def print_table(data):
    headers = ["Name", "Symbol", "Price ($)", "Change 24h (%)", "Volume ($)", "Market Cap ($)", "Exchanges"]
    table = []
    for token in data:
        table.append([
            token["name"],
            token["symbol"],
            round(token["price"], 6) if token["price"] else "-",
            round(token["price_change_24h"], 2),
            round(token["volume"], 2),
            round(token["market_cap"], 2) if token["market_cap"] else "-",
            token["exchanges"]
        ])
    print("\n📉 ТОКЕНЫ С ПОДОЗРЕНИЕМ НА ДАМП:")
    print(tabulate(table, headers=headers, tablefmt="fancy_grid"))

def update():
    tokens = get_tokens_with_dump_risk(days=7, max_tokens=200, min_score=3)
    if tokens:
        save_to_json(tokens)
    else:
        print("⚠️ Нет данных для дамп-кандидатов.")



if __name__ == "__main__":
    tokens = fetch_tokens_from_pages(pages=2)
    dump_candidates = filter_dump_candidates(tokens)
    save_to_json(dump_candidates)
    print_table(dump_candidates)

