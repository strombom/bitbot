
import time
import sqlite3

from binance_keys import binance_keys
from binance.client import Client as BinanceClient


class Binance:
    def __init__(self):
        self.client = BinanceClient(binance_keys['api_key'], binance_keys['api_secret'])

    def get_first_timestamp(self, symbol, base_symbol):
        binance_symbol = symbol + base_symbol
        klines = self.client.get_klines(symbol = binance_symbol, 
                    interval = BinanceClient.KLINE_INTERVAL_1MINUTE, 
                    limit = 1,
                    startTime = 0)

        first_kline = klines[0]
        open_time = first_kline[0] // 1000
        return open_time

    def get_minute_data(self, symbol, base_symbol):
        binance_symbol = symbol + base_symbol
        klines = self.client.get_historical_klines(binance_symbol, BinanceClient.KLINE_INTERVAL_1MINUTE, start_str = 0)
        print(klines)
        quit()

binance = Binance()


class TokenDB:
    def __init__(self, filename):
        self.filename = filename
        conn = sqlite3.connect(self.filename)
        c = conn.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS tokens (trading_symbol text, base_symbol text, timestamp_first INTEGER, timestamp_last INTEGER)')
        conn.commit()
        conn.close()

    def get_symbols(self, base_symbol):
        conn = sqlite3.connect(self.filename)
        c = conn.cursor()
        c.execute('SELECT trading_symbol FROM tokens WHERE base_symbol=?', (base_symbol,))
        symbols = c.fetchall()
        conn.close()
        return symbols

    def get_timestamps(self, symbol, base_symbol):
        conn = sqlite3.connect(self.filename)
        c = conn.cursor()
        c.execute('SELECT timestamp_first, timestamp_last FROM tokens WHERE trading_symbol=? AND base_symbol=?', (symbol, base_symbol,))
        timestamp_first, timestamp_last = c.fetchall()[0]
        conn.close()
        return timestamp_first, timestamp_last

    def init_token(self, symbol, base_symbol):
        first_timestamp = binance.get_first_timestamp(symbol, base_symbol)
        conn = sqlite3.connect(self.filename)
        c = conn.cursor()
        c.execute('UPDATE tokens SET timestamp_first=?, timestamp_last=? WHERE trading_symbol=? AND base_symbol=?', (first_timestamp, first_timestamp, symbol, base_symbol,))
        conn.commit()
        conn.close()
        print("update_token", first_timestamp)
        print((first_timestamp, symbol, base_symbol,))

    def update_token(self, symbol, base_symbol):
        pass

token_db = TokenDB('tokens.db')

while True:
    timeout = time.time() + 5

    symbols = token_db.get_symbols('USDT')
    print("---symbols---")
    for symbol in symbols:
        symbol = symbol[0]
        timestamp_first, timestamp_last = token_db.get_timestamps(symbol, 'USDT')

        if timestamp_first is None:
            token_db.init_token(symbol, 'USDT')
        else:
            token_db.update_token(symbol, 'USDT')

        #if timestamp_first

        #print(symbol, timestamp_first, timestamp_last)

    #quit()

    #timestamp_now = int((time.time()) // 60 * 60)

    #print(timestamp_now)
    #quit()

    while time.time() < timeout:
        time.sleep(1)

