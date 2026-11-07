# -*- coding: utf-8 -*-
#
## ╭────────────────────────────────────────────────────────────────────────────────────────────╮
## │  Library         : doydl's Finance API Client — quantsumore                                 │
## │                                                                                             │
## │                                                                                             │
## │  Description     : `quantsumore` is a comprehensive Python library designed to streamline   │
## │                    the process of accessing and analyzing real-time financial data across   │
## │                    various markets. It provides specialized API clients to fetch data       │
## │                    from multiple financial instruments, including:                          │
## │                      - Cryptocurrencies                                                     │
## │                      - Equities and Stock Markets                                           │
## │                      - Foreign Exchange (Forex)                                             │
## │                      - Treasury Instruments                                                 │
## │                      - Consumer Price Index (CPI) Metrics                                   │
## │                                                                                             │
## │                    The library offers a unified interface for retrieving diverse financial  │
## │                    data, enabling users to perform in-depth financial and technical         │
## │                    analysis. Whether you're developing trading algorithms, conducting       │
## │                    market research, or building financial dashboards, `quantsumore` serves  │
## │                    as a reliable and efficient tool in your data pipeline.                  │
## │                                                                                             │
## │                                                                                             │
## │  Key Features    : - Real-time data retrieval from multiple financial markets               │
## │                    - Support for various financial instruments and metrics                  │
## │                    - Simplified API clients for ease of integration                         │
## │                    - Designed for both personal and non-commercial use                      │
## │                                                                                             │
## │                                                                                             │
## │  Legal Disclaimer: `quantsumore` is an independent Python library and is not affiliated     │
## │                    with any financial institutions or data providers. Likewise, doydl       │
## │                    technologies is not affiliated with, endorsed by, or sponsored by any    │
## │                    government, corporate, or financial institutions. Users should verify    │
## │                    the accuracy of the data obtained and consult professional advice        │
## │                    before making investment decisions.                                      │
## │                                                                                             │
## │                                                                                             │
## │  Copyright       : © 2023–2025 by doydl technologies. All rights reserved.                  │
## │                                                                                             │
## │                                                                                             │
## │  License         : Licensed under the Apache License, Version 2.0 (the "License");          │
## │                    you may not use this file except in compliance with the License.         │
## │                    You may obtain a copy of the License at:                                 │
## │                                                                                             │
## │                        http://www.apache.org/licenses/LICENSE-2.0                           │
## │                                                                                             │
## │                    Unless required by applicable law or agreed to in writing, software      │
## │                    distributed under the License is distributed on an "AS IS" BASIS,        │
## │                    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or          │
## │                    implied. See the License for the specific language governing             │
## │                    permissions and limitations under the License.                           │
## ╰────────────────────────────────────────────────────────────────────────────────────────────╯
#



import os
import json
import requests
import base64
import random

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

exchanges_url = base64.b64decode('aHR0cHM6Ly9zMy5jb2lubWFya2V0Y2FwLmNvbS9nZW5lcmF0ZWQvY29yZS9leGNoYW5nZS9leGNoYW5nZXMuanNvbg==').decode('utf-8')
cryptos_url = base64.b64decode('aHR0cHM6Ly9zMy5jb2lubWFya2V0Y2FwLmNvbS9nZW5lcmF0ZWQvY29yZS9jcnlwdG8vY3J5cHRvcy5qc29u').decode('utf-8')



headers = {
    'User-Agent': 'Mozilla/5.0 (compatible; GitHubActionBot/1.0)',
    'Accept': 'application/json'
}

def fetch_data(url):
    try:
        print(f"Fetching data from: {url}")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        print("Data fetched successfully.")
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from {url}: {e}")
        return None
    except json.JSONDecodeError:
        print(f"Failed to parse JSON response from {url}")
        return None

def process_exchanges(url):
    data = fetch_data(url)
    if not data or "values" not in data:
        print("Invalid data format for exchanges.")
        return
    crypto_exchanges = {}
    for value in data["values"]:
        if len(value) < 3:
            print("Unexpected data format in exchange values.")
            continue
        exchange_id = str(value[0])
        crypto_exchanges[exchange_id] = {
            "exchangeId": exchange_id,
            "exchangeName": value[1],
            "exchangeSlug": value[2]
        }
    output = {"crypto_exchanges": crypto_exchanges}
    file_path = os.path.join(ROOT_DIR, "files", "crypto", "exchanges.json")
    save_to_file(output, file_path)
    print(f"Exchange data saved to {file_path}")

def process_cryptos(url):
    data = fetch_data(url)
    if not data or "values" not in data:
        print("Invalid data format for cryptos.")
        return
    cryptos = {}
    for value in data["values"]:
        if len(value) < 7:
            print("Unexpected data format in crypto values.")
            continue
        crypto_id = str(value[0])
        cryptos[crypto_id] = {
            "id": value[0],
            "name": value[1],
            "symbol": value[2],
            "slug": value[3],
            "is_active": value[4],
            "status": value[5],
            "rank": value[6]
        }
    output = {"cryptos": cryptos}
    file_path = os.path.join(ROOT_DIR, "files", "crypto", "cryptocurrency.json")
    save_to_file(output, file_path)
    print(f"Crypto data saved to {file_path}")

def save_to_file(data, file_path):
    try:
        with open(file_path, 'w') as file:
            json.dump(data, file, indent=4)
        print(f"Data successfully saved to {file_path}")
    except IOError as e:
        print(f"Error saving file {file_path}: {e}")

if __name__ == "__main__":
    process_exchanges(exchanges_url)
    process_cryptos(cryptos_url)

    try:
        with open(os.path.join(ROOT_DIR, "files", "crypto", "cryptocurrency.json"), 'r') as file:
            cryptos = json.load(file)
        with open(os.path.join(ROOT_DIR, "files", "crypto", "exchanges.json"), 'r') as file:
            exchanges = json.load(file)
        with open(os.path.join(ROOT_DIR, "files", "crypto", "pairs.json"), 'r') as file:
            pairs = json.load(file)

        combined_data = {**cryptos, **exchanges, **pairs}
        save_to_file(combined_data, os.path.join(ROOT_DIR, "files", "crypto", "all_data.json"))
    except Exception as e:
        print(f"Error combining or saving crypto data: {e}")







    
