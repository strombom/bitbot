
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

    def get_minute_data(self, symbol, base_symbol, timestamp_start):
        binance_symbol = symbol + base_symbol
        timestamp_start = timestamp_start * 1000
        timestamp_end = timestamp_start + 1000 * 60 * 60 * 24 * 7
        klines = self.client.get_historical_klines(symbol = binance_symbol, 
                                                   interval = BinanceClient.KLINE_INTERVAL_1MINUTE, 
                                                   start_str = timestamp_start,
                                                   end_str = timestamp_end)
        minute_data = []
        for kline in klines:
            timestamp = int(kline[0] / 1000)
            price_high = kline[2]
            price_low = kline[3]
            volume = kline[5]
            minute_data.append({'timestamp': timestamp,
                                'price_high': price_high,
                                'price_low': price_low,
                                'volume': volume})
        return minute_data

binance = Binance()


class TokenDB:
    def __init__(self, filename):
        self.filename = filename
        conn = sqlite3.connect(self.filename)
        c = conn.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS tokens (trading_symbol text, base_symbol text, timestamp_first INTEGER, timestamp_last INTEGER)')
        c.execute('CREATE TABLE IF NOT EXISTS trade_data (trading_symbol text, base_symbol text, timestamp INTEGER, price_high REAL, price_low REAL, volume REAL)')
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

    def update_token(self, symbol, base_symbol, timestamp_start):
        conn = sqlite3.connect(self.filename)
        timestamp_last = None
        minute_data = binance.get_minute_data(symbol, base_symbol, timestamp_start)
        if len(minute_data) == 0:
            return
        print("Appending data (", symbol, base_symbol, ")", timestamp_start, len(minute_data))
        c = conn.cursor()
        for data in minute_data:
            timestamp_last = data['timestamp']
            c.execute("INSERT INTO trade_data VALUES (?,?,?,?,?,?)", (symbol, 
                                                                     base_symbol,
                                                                     data['timestamp'],
                                                                     data['price_high'],
                                                                     data['price_low'],
                                                                     data['volume']))
        c.execute('UPDATE tokens SET timestamp_last=? WHERE trading_symbol=? AND base_symbol=?', (timestamp_last, symbol, base_symbol))
        conn.commit()
        conn.close()

token_db = TokenDB('tokens.db')

while True:
    timeout = time.time() + 2

    symbols = token_db.get_symbols('USDT')
    print("---symbols---")
    for symbol in symbols:
        symbol = symbol[0]
        timestamp_first, timestamp_last = token_db.get_timestamps(symbol, 'USDT')

        print (timestamp_first, timestamp_last)

        if timestamp_first is None:
            token_db.init_token(symbol, 'USDT')
        else:
            timestamp_start = timestamp_last
            if timestamp_start != timestamp_first:
                timestamp_start += 60

            token_db.update_token(symbol, 'USDT', timestamp_start)

        #if timestamp_first

        #print(symbol, timestamp_first, timestamp_last)

    #quit()

    #timestamp_now = int((time.time()) // 60 * 60)

    #print(timestamp_now)
    #quit()

    while time.time() < timeout:
        time.sleep(1)

