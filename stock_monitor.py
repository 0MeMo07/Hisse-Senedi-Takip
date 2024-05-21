import yfinance as yf
from plyer import notification
import time
from datetime import datetime

class StockMonitor:
    def __init__(self, stocks, price_threshold, WaitTime):
        self.stocks = stocks
        self.price_threshold = price_threshold
        self.WaitTime = WaitTime

    def check_stock_prices(self):
        for stock in self.stocks:
            try:
                data = yf.Ticker(stock)
                history = data.history(period="1d", interval="1m")
                if not history.empty:
                    last_close = history['Close'].iloc[-1]
                    previous_close = history['Close'].iloc[-2] if len(history) > 1 else last_close
                    price_change = last_close - previous_close
                    percentage_change = (price_change / previous_close) * 100
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    self.log_price_change(stock, last_close, previous_close, price_change, percentage_change, timestamp)
                    if abs(price_change) > self.price_threshold:
                        direction = "arttı" if price_change > 0 else "azaldı"
                        self.send_notification(stock, price_change, percentage_change, direction)
            except Exception as e:
                print(f"Veri çekme hatası: {e}")

    def send_notification(self, stock, price_change, percentage_change, direction):
        notification.notify(
            title=f"{stock} Hisse Senedi Bildirimi",
            message=f"{stock} hissesi {price_change:.2f} TL ({percentage_change:.2f}%) {direction}!",
            timeout=4
        )

    def log_price_change(self, stock, last_close, previous_close, price_change, percentage_change, timestamp):
        with open("price_changes.log", "a") as log_file:
            log_file.write(f"{timestamp} - {stock}: Onceki Kapanis: {previous_close:.2f} TL, "
                           f"Son Kapanis: {last_close:.2f} TL, Degisim: {price_change:.2f} TL, "
                           f"Yuzde Degisim: {percentage_change:.2f}%\n")

def monitor_stocks(stocks, price_threshold, WaitTime):
    monitor = StockMonitor(stocks, price_threshold, WaitTime)
    while True:
        monitor.check_stock_prices()
        time.sleep(WaitTime)
