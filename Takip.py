import yfinance as yf
from plyer import notification
import time
from datetime import datetime
import tkinter as tk
from tkinter import ttk, scrolledtext
import threading

def load_stocks():
    try:
        with open("stocks.txt", "r") as file:
            stocks = [line.strip() for line in file.readlines()]
    except FileNotFoundError:
        with open("stocks.txt", "w") as file:
            pass
        stocks = []
    return stocks

def save_stocks(stocks):
    with open("stocks.txt", "w") as file:
        for stock in stocks:
            file.write(stock + "\n")

stocks = load_stocks()
price_threshold = 1
WaitTime = 10

class StockMonitorApp:

    def __init__(self, root):
        self.root = root
        self.root.title("Hisse Senedi Takip Uygulaması")
        self.root.resizable(0, 0)
        self.stocks = stocks
        self.running = True
        self.reported_changes = self.load_reported_changes()
        self.price_threshold = price_threshold
        self.WaitTime = WaitTime
        self.create_widgets()
        self.check_prices_thread = threading.Thread(target=self.check_stock_prices)
        self.check_prices_thread.start()
        self.update_threshold()
    
    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.label = ttk.Label(main_frame, text="Takip Edilen Hisse Senetleri", font=("Arial", 14, "bold"), foreground="darkgreen")
        self.label.grid(row=0, column=0, columnspan=2, pady=10)

        self.stock_listbox = tk.Listbox(main_frame, height=6, width=25, selectmode=tk.SINGLE, font=("Arial", 12))
        self.stock_listbox.grid(row=1, column=0, columnspan=2, pady=5)
        for stock in self.stocks:
            self.stock_listbox.insert(tk.END, stock)

        self.add_remove_frame = ttk.Frame(main_frame)
        self.add_remove_frame.grid(row=2, column=0, columnspan=2, pady=5)

        self.entry_label = ttk.Label(self.add_remove_frame, text="Hisse Senedi Ekle/Çıkar:", font=("Arial", 12))
        self.entry_label.grid(row=0, column=0, padx=5)

        self.stock_entry = ttk.Entry(self.add_remove_frame, font=("Arial", 12))
        self.stock_entry.grid(row=0, column=1, padx=5)

        self.add_button = ttk.Button(self.add_remove_frame, text="Ekle", command=self.add_stock, style="Accent.TButton")
        self.add_button.grid(row=0, column=2, padx=5)

        self.remove_button = ttk.Button(self.add_remove_frame, text="Çıkar", command=self.remove_stock, style="Accent.TButton")
        self.remove_button.grid(row=0, column=3, padx=5)

        self.threshold_label = ttk.Label(main_frame, text="Fiyat Değişim Eşiği (TL):", font=("Arial", 12))
        self.threshold_label.grid(row=3, column=0, pady=5)

        self.threshold_entry = ttk.Entry(main_frame, font=("Arial", 12))
        self.threshold_entry.insert(0, str(self.price_threshold))
        self.threshold_entry.grid(row=3, column=1, pady=5)

        self.log_label = ttk.Label(main_frame, text="Fiyat Değişim Logları", font=("Arial", 14, "bold"), foreground="darkgreen")
        self.log_label.grid(row=4, column=0, columnspan=2, pady=10)

        self.log_text = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, width=50, height=10, font=("Arial", 12))
        self.log_text.grid(row=5, column=0, columnspan=2, pady=5)

        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("Accent.TButton", foreground="white", background="darkgreen")

        self.wait_label = ttk.Label(main_frame, text="Kontrol Aralığı (saniye):", font=("Arial", 12))
        self.wait_label.grid(row=6, column=0, pady=5)

        self.wait_entry = ttk.Entry(main_frame, font=("Arial", 12))
        self.wait_entry.insert(0, "10") 
        self.wait_entry.grid(row=6, column=1, pady=5)

        self.wait_entry.bind('<KeyRelease>', self.update_check_interval)

    def add_stock(self):
        new_stock = self.stock_entry.get().upper()
        if new_stock and new_stock not in self.stocks:
            self.stocks.append(new_stock)
            self.stock_listbox.insert(tk.END, new_stock)
            save_stocks(self.stocks)
            self.stock_entry.delete(0, tk.END)

    def remove_stock(self):
        selected_stock = self.stock_listbox.get(self.stock_listbox.curselection())
        if selected_stock in self.stocks:
            self.stocks.remove(selected_stock)
            self.stock_listbox.delete(self.stock_listbox.get(0, tk.END).index(selected_stock))
            save_stocks(self.stocks)

    def stop(self):
        self.running = False
        self.check_prices_thread.join()
        self.root.quit()

    def load_reported_changes(self):
        reported_changes = set()
        try:
            with open("price_changes.log", "r") as log_file:
                for line in log_file:
                    reported_changes.add(line.strip())
        except FileNotFoundError:
            with open("stocks.txt", "w") as log_file:
                for line in log_file:
                    reported_changes.add(line.strip())
        return reported_changes

    def update_threshold(self):
        try:
            global price_threshold
            self.price_threshold = float(self.threshold_entry.get())
            price_threshold = self.price_threshold
        except ValueError:
            pass
        self.root.after(1000, self.update_threshold) 

    def update_check_interval(self, event):
        try:
            global WaitTime
            self.WaitTime = int(self.wait_entry.get())
            WaitTime = self.WaitTime
        except ValueError:
            pass

    def check_stock_prices(self):
        while self.running:
            for stock in self.stocks:
                stock_code = stock + ".IS"  # VERI.IS şeklinde veriyi çekiyoruz
                try:
                    data = yf.Ticker(stock_code)
                    history = data.history(period="5d", interval="1m")
                    if not history.empty:
                        last_close = history['Close'].iloc[-1]
                        previous_close = history['Close'].iloc[-2] if len(history) > 1 else last_close
                        price_change = last_close - previous_close
                        percentage_change = (price_change / previous_close) * 100
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        log_entry = f"{timestamp} - {stock}: Onceki Kapanis: {previous_close:.2f} TL, Son Kapanis: {last_close:.2f} TL, Degisim: {price_change:.2f} TL, Yuzde Degisim: {percentage_change:.2f}%\n"
                        if log_entry not in self.reported_changes:
                            self.log_price_change(log_entry)
                            if abs(price_change) > self.price_threshold:
                                direction = "arttı" if price_change > 0 else "azaldı"
                                self.send_notification(stock, price_change, percentage_change, direction)
                            self.reported_changes.add(log_entry)
                except Exception as e:
                    pass
            time.sleep(WaitTime)

    def send_notification(self, stock, price_change, percentage_change, direction):
        notification.notify(
            title=f"{stock} Hisse Senedi Bildirimi",
            message=f"{stock} hissesi {price_change:.2f} TL ({percentage_change:.2f}%) {direction}!",
            timeout=4
        )

    def log_price_change(self, log_entry):
        with open("price_changes.log", "a") as log_file:
            log_file.write(log_entry)
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)

def main():
    root = tk.Tk()
    app = StockMonitorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
    from stock_monitor import monitor_stocks
    monitor_stocks(stocks, price_threshold, WaitTime)
