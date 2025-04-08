import requests
import json

def fetch_binance_24h_data():
    url = "https://api.binance.com/api/v3/ticker/24hr"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Ошибка запроса: {response.status_code}")
        return []

def find_dumps(data, drop_threshold=-15, volume_threshold=500_000):
    dumps = []

    for token in data:
        try:
            symbol = token["symbol"]
            price_change_percent = float(token["priceChangePercent"])
            quote_volume = float(token["quoteVolume"])

            if symbol.endswith("USDT") and price_change_percent < drop_threshold and quote_volume > volume_threshold:
                dumps.append({
                    "symbol": symbol,
                    "priceChangePercent": price_change_percent,
                    "volume": quote_volume
                })
        except:
            continue

    return dumps

def save_dumps_to_json(data, filename="binance_dumps.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    print(f"✅ Сохранено {len(data)} дамп-кандидатов в файл {filename}")

def update():
    all_data = fetch_binance_24h_data()
    dumps = find_dumps(all_data)
    save_dumps_to_json(dumps)

if __name__ == "__main__":
    all_data = fetch_binance_24h_data()
    dumps = find_dumps(all_data)
    save_dumps_to_json(dumps)


