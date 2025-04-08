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

def find_pumps(data, percent_threshold=20, volume_threshold=500_000):
    pumps = []

    for token in data:
        try:
            symbol = token["symbol"]
            price_change_percent = float(token["priceChangePercent"])
            quote_volume = float(token["quoteVolume"])

            # Только спотовые пары к USDT
            if symbol.endswith("USDT") and price_change_percent > percent_threshold and quote_volume > volume_threshold:
                pumps.append({
                    "symbol": symbol,
                    "priceChangePercent": price_change_percent,
                    "volume": quote_volume
                })
        except:
            continue

    return pumps

def save_pumps_to_json(data, filename="binance_pumps.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    print(f"✅ Сохранено {len(data)} памп-кандидатов в файл {filename}")

def update():
    all_data = fetch_binance_24h_data()
    pumps = find_pumps(all_data)
    save_pumps_to_json(pumps)

if __name__ == "__main__":
    all_data = fetch_binance_24h_data()
    pumps = find_pumps(all_data)
    save_pumps_to_json(pumps)


