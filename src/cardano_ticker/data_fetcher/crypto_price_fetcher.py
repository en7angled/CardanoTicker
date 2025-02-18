import logging
import time
from collections import defaultdict

import pandas as pd
import requests

logging.basicConfig(level=logging.INFO)


class CryptoPriceFetcher:
    def __init__(self, api_key):
        self.api_key = api_key
        self.max_cache_age = 60  # 1 minute
        self.current_prices_cache = defaultdict(dict)
        self.current_chart_cache = defaultdict(dict)

    def get_realtime(self, symbol, currency):
        fetched_time = time.time()

        # check if the price is in the cache
        if symbol in self.current_prices_cache and currency in self.current_prices_cache[symbol]:
            price, timestamp = self.current_prices_cache[symbol][currency]
            if fetched_time - timestamp < self.max_cache_age:
                return price

        # Final fallback to Binance
        price = self._get_from_binance(symbol, currency)
        if price:
            self.current_prices_cache[symbol][currency] = price, fetched_time
            return price

        # Try CoinGecko
        price = self._get_from_coingecko(symbol, currency)
        if price:
            self.current_prices_cache[symbol][currency] = price, fetched_time
            return price

        # Fall back to CryptoCompare
        price = self._get_from_cryptocompare(symbol, currency)
        if price:
            self.current_prices_cache[symbol][currency] = price, fetched_time
            return price

        # last resort is to try symbol with USD and currency with USD
        if currency != "USD":
            symbol_price = self.get_realtime(symbol, "USD")
            if symbol_price:
                currency_price = self.get_realtime(currency, "USD")
                if currency_price:
                    self.current_prices_cache[symbol][currency] = symbol_price / currency_price, fetched_time
                    return symbol_price / currency_price

        logging.error(f"Failed to fetch {symbol}/{currency} from all sources.")
        return 0

    def _get_from_cryptocompare(self, symbol, currency):
        """Fetch price from CryptoCompare"""
        api_url = f"https://min-api.cryptocompare.com/data/price?fsym={symbol}&tsyms={currency}&api_key={self.api_key}"
        try:
            raw = requests.get(api_url, timeout=5).json()
            if currency in raw:
                return raw[currency]
        except Exception as e:
            logging.error(f"CryptoCompare error: {e}")
        return None

    def _get_from_coingecko(self, symbol, currency):
        """Fetch price from CoinGecko"""
        api_url = f"https://api.coingecko.com/api/v3/simple/price?ids={symbol.lower()}&vs_currencies={currency.lower()}"
        try:
            raw = requests.get(api_url, timeout=5).json()
            if symbol.lower() in raw and currency.lower() in raw[symbol.lower()]:
                return raw[symbol.lower()][currency.lower()]
        except Exception as e:
            logging.error(f"CoinGecko error: {e}")
        return None

    def _get_from_binance(self, symbol, currency):
        """Fetch price from Binance"""
        currency = currency.upper()
        if currency == "USD":
            currency = "USDT"

        pair = f"{symbol}{currency}".upper()
        api_url = f"https://api.binance.com/api/v3/ticker/price?symbol={pair}"
        try:
            raw = requests.get(api_url, timeout=5).json()
            if "price" in raw:
                return float(raw["price"])
        except Exception as e:
            logging.error(f"Binance error: {e}")
        return None

    def get_chart_data(self, symbol, currency, days=7):

        fetch_time = time.time()
        # check if the chart data is in the cache
        if symbol in self.current_chart_cache and currency in self.current_chart_cache[symbol]:
            df, timestamp = self.current_chart_cache[symbol][currency]
            if fetch_time - timestamp < self.max_cache_age:
                return df

        # Try CoinGecko
        df = self._get_chart_from_coingecko(symbol, currency, days)
        if df is not None:
            self.current_chart_cache[symbol][currency] = (df, fetch_time)
            return df

        # Fall back to CryptoCompare
        df = self._get_chart_from_cryptocompare(symbol, currency, days)
        if df is not None:
            self.current_chart_cache[symbol][currency] = (df, fetch_time)
            return df

        # Final fallback to Binance
        df = self._get_chart_from_binance(symbol, currency, days)
        if df is not None:
            self.current_chart_cache[symbol][currency] = (df, fetch_time)
            return df

        # last resort is to try symbol with USD and currency with USD
        if currency != "USD":
            symbol_df = self.get_chart_data(symbol, "USD", days)
            if symbol_df is not None:
                currency_df = self.get_chart_data(currency, "USD", days)
                if currency_df is not None:
                    # Combine the two dataframes to get the final chart
                    new_df = symbol_df.join(currency_df, how="inner", lsuffix="_symbol", rsuffix="_currency")
                    new_df["close"] = new_df["close_symbol"] / new_df["close_currency"]
                    new_df['high'] = new_df['high_symbol'] / new_df['close_currency']
                    new_df['low'] = new_df['low_symbol'] / new_df['close_currency']
                    new_df['open'] = new_df['open_symbol'] / new_df['close_currency']
                    new_df['time'] = new_df['time_symbol']
                    combined_df = new_df[["time", "high", "low", "open", "close"]]
                    self.current_chart_cache[symbol][currency] = (combined_df, fetch_time)
                    return combined_df

        logging.error(f"Failed to fetch chart data for {symbol}/{currency} from all sources.")
        return None

    def _get_chart_from_cryptocompare(self, symbol, currency, days):
        """Fetch historical data from CryptoCompare"""
        api_url = f"https://min-api.cryptocompare.com/data/v2/histoday?fsym={symbol}&tsym={currency}&limit={days}&api_key={self.api_key}"
        try:
            raw = requests.get(api_url, timeout=5).json()
            if "Data" in raw and "Data" in raw["Data"]:
                df = pd.DataFrame(raw["Data"]["Data"])[["time", "high", "low", "open", "close"]].set_index("time")
                df.index = pd.to_datetime(df.index, unit="s")
                return df
        except Exception as e:
            logging.error(f"CryptoCompare error: {e}")
        return None

    def _get_chart_from_coingecko(self, symbol, currency, days):
        """Fetch historical data from CoinGecko"""
        api_url = f"https://api.coingecko.com/api/v3/coins/{symbol.lower()}/market_chart?vs_currency={currency.lower()}&days={days}&interval=daily"
        try:
            raw = requests.get(api_url, timeout=5).json()
            if "prices" in raw:
                df = pd.DataFrame(raw["prices"], columns=["time", "close"])
                df["time"] = pd.to_datetime(df["time"], unit="ms")
                return df.set_index("time")
        except Exception as e:
            logging.error(f"CoinGecko error: {e}")
        return None

    def _get_chart_from_binance(self, symbol, currency, days):
        """Fetch historical data from Binance"""
        currency = currency.upper()
        if currency == "USD":
            currency = "USDT"

        pair = f"{symbol}{currency}".upper()
        interval = "1d"  # Daily candles
        limit = days

        api_url = f"https://api.binance.com/api/v3/klines?symbol={pair}&interval={interval}&limit={limit}"
        try:
            raw = requests.get(api_url, timeout=5).json()
            if isinstance(raw, list):
                df = pd.DataFrame(
                    raw,
                    columns=[
                        "time",
                        "open",
                        "high",
                        "low",
                        "close",
                        "volume",
                        "close_time",
                        "quote_asset_volume",
                        "trades",
                        "taker_buy_base",
                        "taker_buy_quote",
                        "ignore",
                    ],
                )
                df = df[["time", "high", "low", "open", "close"]].set_index("time")
                # convert column to numeric
                df[['high', 'low', 'open', 'close']] = df[['high', 'low', 'open', 'close']].apply(pd.to_numeric)
                df.index = pd.to_datetime(df.index, unit="ms")
                return df
        except Exception as e:
            logging.error(f"Binance error: {e}")
        return None
