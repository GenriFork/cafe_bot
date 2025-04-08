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

def filter_pump_candidates(tokens, growth_threshold=10, volume_threshold=300_000):
    candidates = []
    for token in tokens:
        price_change = token.get("price_change_percentage_24h")
        volume = token.get("total_volume")

        if price_change is not None and price_change > growth_threshold and volume and volume > volume_threshold:
            exchanges = get_exchanges_for_token(token["id"])
            if not exchanges:
                continue  # ❌ Пропускаем токен без бирж

            candidates.append({
                "name": token["name"],
                "symbol": token["symbol"],
                "price": token["current_price"],
                "price_change_24h": price_change,
                "volume": volume,
                "market_cap": token.get("market_cap"),
                "exchanges": ", ".join(exchanges) if exchanges else "N/A"
            })

    return candidates
def get_recent_tokens_with_scores(days=7, max_tokens=200, min_score=4):
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

    def score_token(token):
        score = 0
        market = token.get("market_data", {})

        price_change = market.get("price_change_percentage_24h", 0)
        volume_change = market.get("total_volume", {}).get("usd", 0)
        market_cap = market.get("market_cap", {}).get("usd", 0)

        if price_change and price_change > 50:
            score += 2
        if volume_change and volume_change > 1_000_000:
            score += 2
        if market_cap and market_cap > 1_000_000:
            score += 1

        contracts = token.get("platforms", {})
        if "ethereum" in contracts or "binance-smart-chain" in contracts:
            score += 1

        try:
            token_date = datetime.strptime(token.get("genesis_date"), "%Y-%m-%d")
            if datetime.utcnow() - token_date < timedelta(days=3):
                score += 1
        except:
            pass

        if price_change and price_change < -30:
            score -= 1

        return score

    token_list = fetch_token_list()
    result = []

    for i, token in enumerate(token_list[:max_tokens]):
        details = fetch_token_details(token["id"])
        if details and is_recent_token(details, days):
            score = score_token(details)
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

    return result


def save_to_json(data, filename="pump_candidates_extended.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"\n✅ Сохранено {len(data)} памп-кандидатов в файл {filename}")

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

    print("\n📈 ТОКЕНЫ С ПОДОЗРЕНИЕМ НА ПАМП:")
    print(tabulate(table, headers=headers, tablefmt="fancy_grid"))

def debug_print_all_changes(tokens, count=40):
    print("\n📊 Ценовые изменения топ токенов по объёму:")
    for token in tokens[:count]:
        print(f"{token['name']} ({token['symbol']}): {token.get('price_change_percentage_24h')}%")

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
def update():
    tokens = get_recent_tokens_with_scores(days=7, max_tokens=200, min_score=4)
    save_to_json(tokens)

if __name__ == "__main__":
    tokens = fetch_tokens_from_pages(pages=2)
    debug_print_all_changes(tokens)
    pump_candidates = filter_pump_candidates(tokens)
    save_to_json(pump_candidates)
    print_table(pump_candidates)


