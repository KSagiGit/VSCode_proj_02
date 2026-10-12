import math
import tkinter as tk
from tkinter import ttk

import numpy as np
import pandas as pd
import yfinance as yf


STOCKS = [
    {"symbol": "AAPL", "name": "Apple Inc.", "sector": "Technology", "price": 214.86, "change": 1.42},
    {"symbol": "MSFT", "name": "Microsoft Corp.", "sector": "Technology", "price": 432.18, "change": 0.87},
    {"symbol": "NVDA", "name": "NVIDIA Corp.", "sector": "Semiconductors", "price": 126.55, "change": 2.61},
    {"symbol": "AMZN", "name": "Amazon.com Inc.", "sector": "Consumer", "price": 189.33, "change": 1.08},
    {"symbol": "GOOGL", "name": "Alphabet Inc.", "sector": "Communication", "price": 174.42, "change": -0.44},
    {"symbol": "META", "name": "Meta Platforms Inc.", "sector": "Communication", "price": 512.91, "change": 2.14},
    {"symbol": "TSLA", "name": "Tesla Inc.", "sector": "Automotive", "price": 221.74, "change": -1.18},
    {"symbol": "NFLX", "name": "Netflix Inc.", "sector": "Communication", "price": 638.70, "change": 1.73},
    {"symbol": "AMD", "name": "Advanced Micro Devices", "sector": "Semiconductors", "price": 164.31, "change": 1.56},
    {"symbol": "INTC", "name": "Intel Corp.", "sector": "Semiconductors", "price": 51.74, "change": -0.32},
    {"symbol": "JPM", "name": "JPMorgan Chase & Co.", "sector": "Financials", "price": 201.05, "change": 0.79},
    {"symbol": "XOM", "name": "Exxon Mobil Corp.", "sector": "Energy", "price": 112.63, "change": 0.34},
    {"symbol": "V", "name": "Visa Inc.", "sector": "Financials", "price": 279.61, "change": 0.92},
    {"symbol": "WMT", "name": "Walmart Inc.", "sector": "Consumer", "price": 67.12, "change": -0.21},
    {"symbol": "PFE", "name": "Pfizer Inc.", "sector": "Healthcare", "price": 28.40, "change": -0.11},
    {"symbol": "NKE", "name": "Nike Inc.", "sector": "Consumer", "price": 96.58, "change": 0.66},
    {"symbol": "DIS", "name": "Walt Disney Co.", "sector": "Communication", "price": 94.20, "change": 0.48},
    {"symbol": "IBM", "name": "International Business Machines", "sector": "Technology", "price": 179.31, "change": 0.13},
    {"symbol": "SHOP", "name": "Shopify Inc.", "sector": "Technology", "price": 76.53, "change": 1.81},
    {"symbol": "CRWD", "name": "CrowdStrike Holdings", "sector": "Technology", "price": 287.44, "change": 2.09},
]


def normalize(text):
    return " ".join(str(text).lower().strip().split())


def stock_match_score(query, stock):
    q = normalize(query)
    if not q:
        return 0

    symbol = normalize(stock["symbol"])
    name = normalize(stock["name"])
    sector = normalize(stock["sector"])
    full = f"{symbol} {name} {sector}"

    score = 0

    if symbol.startswith(q):
        score += 50
    if q in symbol:
        score += 20

    if name.startswith(q):
        score += 40
    if q in name:
        score += 18

    if q in sector:
        score += 10

    if full.startswith(q):
        score += 15

    return score


def suggest_stocks(query, limit=8):
    q = normalize(query)
    if not q:
        return STOCKS[:limit]

    scored = []
    for stock in STOCKS:
        score = stock_match_score(q, stock)
        if score > 0:
            scored.append((stock, score))

    scored.sort(key=lambda item: (-item[1], item[0]["symbol"]))
    return [stock for stock, _ in scored[:limit]]


def fetch_stock_data(symbol):
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.fast_info or {}
        history = ticker.history(period="3mo", interval="1d", auto_adjust=True)
        if history.empty:
            return None

        close = history["Close"].dropna()
        if close.empty:
            return None

        price = float(close.iloc[-1])
        previous = float(close.iloc[-2]) if len(close) > 1 else price
        change_pct = ((price - previous) / previous) * 100 if previous else 0.0

        name = ticker.info.get("longName") or symbol
        sector = ticker.info.get("sector") or "Unknown"

        return {
            "symbol": symbol,
            "name": name,
            "sector": sector,
            "price": price,
            "change": change_pct,
            "history": history,
        }
    except Exception:
        return None


def compute_sma(series, window):
    if len(series) < window:
        return float("nan")
    return float(series.rolling(window=window).mean().iloc[-1])


def compute_rsi(series, window=14):
    if len(series) < window + 1:
        return 50.0

    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(window=window).mean().iloc[-1]
    avg_loss = loss.rolling(window=window).mean().iloc[-1]

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def compute_macd(series):
    if len(series) < 26:
        return 0.0

    ema12 = series.ewm(span=12, adjust=False).mean()
    ema26 = series.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    return float(macd.iloc[-1])


def get_signal_for_stock(stock, history):
    if history.empty:
        return "HOLD", "No data available"

    closes = history["Close"].dropna()
    if len(closes) < 10:
        return "HOLD", "Not enough data"

    sma5 = compute_sma(closes, 5)
    sma10 = compute_sma(closes, 10)
    rsi = compute_rsi(closes, 14)
    macd = compute_macd(closes)

    if math.isnan(sma5) or math.isnan(sma10):
        return "HOLD", "Trend not ready"

    if rsi < 35 and closes.iloc[-1] < sma10 and macd < 0:
        return "BUY", "Oversold + trend support"
    if rsi > 65 and closes.iloc[-1] > sma10 and macd > 0:
        return "SELL", "Overbought + momentum risk"
    return "HOLD", "Mixed trend"


class StockApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MarketPulse")
        self.geometry("1280x760")
        self.configure(bg="#0b1220")
        self.minsize(980, 620)

        self.style = ttk.Style(self)
        self.style.theme_use("clam")

        self.history_data = pd.DataFrame()
        self.configure_font()
        self.build_ui()
        self.selected_ticker = "AAPL"
        self.show_stock(STOCKS[0])

    def configure_font(self):
        self.option_add("*Font", "Arial 11")

    def build_ui(self):
        header = tk.Frame(self, bg="#101a2b", height=72)
        header.pack(fill="x", padx=0, pady=0)

        title = tk.Label(header, text="MarketPulse", fg="#dfe8ff", bg="#101a2b", font=("Arial", 20, "bold"))
        title.pack(side="left", padx=20, pady=18)

        search_frame = tk.Frame(header, bg="#192334", bd=0)
        search_frame.pack(side="left", fill="x", expand=True, padx=(40, 20), pady=14)

        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(
            search_frame,
            textvariable=self.search_var,
            bg="#1d2a3d",
            fg="#edf3ff",
            insertbackground="#ffffff",
            bd=0,
            relief="flat",
            width=50,
            font=("Arial", 13),
        )
        self.search_entry.pack(fill="x", pady=10, padx=12)
        self.search_entry.bind("<KeyRelease>", self.on_search)

        self.suggestion_box = tk.Listbox(
            self,
            bg="#111b2b",
            fg="#e3ebff",
            bd=0,
            highlightthickness=0,
            activestyle="none",
            width=55,
            height=9,
            font=("Arial", 11),
        )
        self.suggestion_box.pack(anchor="nw", padx=250, pady=(0, 10))
        self.suggestion_box.bind("<<ListboxSelect>>", self.on_select_suggestion)

        main = tk.Frame(self, bg="#0b1220")
        main.pack(fill="both", expand=True, padx=18, pady=(0, 18))

        left_panel = tk.Frame(main, bg="#0f1a2d", bd=1, relief="flat")
        left_panel.pack(side="left", fill="y", padx=(0, 18))
        left_panel.configure(width=360)

        self.symbol_label = tk.Label(left_panel, fg="#ffffff", bg="#0f1a2d", font=("Arial", 26, "bold"), anchor="w")
        self.symbol_label.pack(anchor="w", padx=20, pady=(20, 5))

        self.name_label = tk.Label(left_panel, fg="#9db6d9", bg="#0f1a2d", font=("Arial", 12), anchor="w")
        self.name_label.pack(anchor="w", padx=20, pady=(0, 12))

        price_row = tk.Frame(left_panel, bg="#0f1a2d")
        price_row.pack(fill="x", padx=20, pady=8)
        self.price_label = tk.Label(price_row, text="", fg="#edf3ff", bg="#0f1a2d", font=("Arial", 18, "bold"))
        self.price_label.pack(side="left")
        self.change_label = tk.Label(price_row, text="", fg="#7ef5a8", bg="#0f1a2d", font=("Arial", 12, "bold"))
        self.change_label.pack(side="left", padx=(12, 0))

        self.chart_canvas = tk.Canvas(left_panel, width=300, height=180, bg="#0f1a2d", highlightthickness=0)
        self.chart_canvas.pack(padx=20, pady=16)

        right_panel = tk.Frame(main, bg="#0b1220")
        right_panel.pack(side="left", fill="both", expand=True)

        overview = tk.Frame(right_panel, bg="#0f1a2d", bd=1, relief="flat")
        overview.pack(fill="both", expand=True)

        overview_title = tk.Label(overview, text="Market Overview", fg="#edf3ff", bg="#0f1a2d", font=("Arial", 16, "bold"), anchor="w")
        overview_title.pack(anchor="w", padx=18, pady=(18, 10))

        self.signal_label = tk.Label(overview, text="HOLD", fg="#f9d976", bg="#0f1a2d", font=("Arial", 18, "bold"), anchor="w")
        self.signal_label.pack(anchor="w", padx=18, pady=(0, 4))

        self.signal_note = tk.Label(overview, text="No signal", fg="#bfd2f3", bg="#0f1a2d", anchor="w")
        self.signal_note.pack(anchor="w", padx=18, pady=(0, 10))

        self.summary_text = tk.Text(overview, bg="#0f1a2d", fg="#dfeafc", height=14, wrap="word", bd=0, padx=18, pady=10)
        self.summary_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.summary_text.configure(state="disabled")

        watchlist = tk.Frame(right_panel, bg="#0f1a2d", bd=1, relief="flat")
        watchlist.pack(fill="x", pady=(18, 0))

        watch_title = tk.Label(watchlist, text="Watchlist", fg="#edf3ff", bg="#0f1a2d", font=("Arial", 16, "bold"), anchor="w")
        watch_title.pack(anchor="w", padx=18, pady=(16, 8))

        self.watchlist_box = tk.Listbox(
            watchlist,
            bg="#0f1a2d",
            fg="#edf3ff",
            bd=0,
            highlightthickness=0,
            activestyle="none",
            height=8,
            font=("Arial", 11),
        )
        self.watchlist_box.pack(fill="x", padx=12, pady=(0, 12))
        self.watchlist_box.bind("<<ListboxSelect>>", self.on_watchlist_select)

        self.default_suggestions()
        self.refresh_watchlist()

    def default_suggestions(self):
        self.search_var.set("")
        self.update_suggestions()

    def on_search(self, event=None):
        query = self.search_var.get()
        self.update_suggestions(query)

    def update_suggestions(self, query=""):
        suggestions = suggest_stocks(query, limit=8)
        self.suggestion_box.delete(0, tk.END)
        for stock in suggestions:
            self.suggestion_box.insert(tk.END, f"{stock['symbol']}  •  {stock['name']}")

    def on_select_suggestion(self, event=None):
        selection = self.suggestion_box.curselection()
        if not selection:
            return
        index = selection[0]
        value = self.suggestion_box.get(index)
        symbol = value.split("  •  ", 1)[0].strip()
        for stock in STOCKS:
            if stock["symbol"] == symbol:
                self.show_stock(stock)
                return

    def show_stock(self, stock):
        live = fetch_stock_data(stock["symbol"])
        if live:
            stock = {**stock, **live}
        self.history_data = live.get("history", pd.DataFrame()) if live else pd.DataFrame()

        self.selected_ticker = stock["symbol"]
        self.search_var.set(f"{stock['symbol']} {stock['name']}")
        self.symbol_label.config(text=stock["symbol"])
        self.name_label.config(text=stock["name"])
        self.price_label.config(text=f"${stock['price']:.2f}")
        color = "#7ef5a8" if stock["change"] >= 0 else "#ff6b6b"
        self.change_label.config(text=f"{stock['change']:+.2f}%", fg=color)
        self.draw_chart(stock)
        self.refresh_summary(stock)

    def on_watchlist_select(self, event=None):
        selection = self.watchlist_box.curselection()
        if not selection:
            return
        item = self.watchlist_box.get(selection[0])
        symbol = item.split(" ", 1)[0]
        for stock in STOCKS:
            if stock["symbol"] == symbol:
                self.show_stock(stock)
                return

    def refresh_watchlist(self):
        self.watchlist_box.delete(0, tk.END)
        for stock in STOCKS[:8]:
            live = fetch_stock_data(stock["symbol"])
            if live:
                price = live["price"]
                change = live["change"]
                color = "#7ef5a8" if change >= 0 else "#ff6b6b"
                self.watchlist_box.insert(tk.END, f"{stock['symbol']}  ${price:.2f}  {change:+.2f}%")
            else:
                self.watchlist_box.insert(tk.END, f"{stock['symbol']}  ${stock['price']:.2f}  {stock['change']:+.2f}%")

    def draw_chart(self, stock):
        self.chart_canvas.delete("all")
        width = 300
        height = 180
        center_y = height / 2

        self.chart_canvas.create_line(0, center_y, width, center_y, fill="#1f2d40", width=1)

        if not self.history_data.empty:
            candles = self.history_data.tail(20)
            if not candles.empty:
                closes = candles["Close"].dropna()
                highs = candles["High"].dropna()
                lows = candles["Low"].dropna()
                opens = candles["Open"].dropna()
                if len(closes) > 0:
                    min_v = float(min(lows.min(), closes.min()))
                    max_v = float(max(highs.max(), closes.max()))
                    span = max_v - min_v if max_v != min_v else 1.0
                    for i in range(len(candles)):
                        x = 15 + i * ((width - 30) / max(len(candles), 1))
                        open_val = float(opens.iloc[i])
                        close_val = float(closes.iloc[i])
                        high_val = float(highs.iloc[i])
                        low_val = float(lows.iloc[i])
                        body_top = height - 20 - ((max(open_val, close_val) - min_v) / span) * (height - 40)
                        body_bottom = height - 20 - ((min(open_val, close_val) - min_v) / span) * (height - 40)
                        wick_top = height - 20 - ((high_val - min_v) / span) * (height - 40)
                        wick_bottom = height - 20 - ((low_val - min_v) / span) * (height - 40)
                        self.chart_canvas.create_line(x, wick_top, x, wick_bottom, fill="#7dd3fc", width=1)
                        body_height = max(3, abs(body_bottom - body_top))
                        fill_color = "#2dd4bf" if close_val >= open_val else "#f87171"
                        self.chart_canvas.create_rectangle(x - 4, body_top, x + 4, body_bottom, fill=fill_color, outline=fill_color)
                    return

        points = []
        for i in range(0, 30):
            x = 10 + i * 9
            wave = math.sin(i / 3.0 + stock["price"] / 50.0) * 26
            y = center_y + wave + (stock["change"] * 8)
            points.append((x, y))

        if points:
            coords = []
            for x, y in points:
                coords.extend([x, y])
            self.chart_canvas.create_line(coords, fill="#2dd4bf", width=2)

    def refresh_summary(self, stock):
        signal, signal_note = get_signal_for_stock(stock, self.history_data)
        signal_color = "#7ef5a8" if signal == "BUY" else "#ff6b6b" if signal == "SELL" else "#f9d976"
        self.signal_label.config(text=signal, fg=signal_color)
        self.signal_note.config(text=signal_note)

        summary_lines = [
            f"{stock['symbol']} • {stock['name']}",
            f"Sector: {stock['sector']}",
            f"",
            f"Price: ${stock['price']:.2f}",
            f"Daily change: {stock['change']:+.2f}%",
            f"",
            f"Signal: {signal}",
        ]

        if not self.history_data.empty:
            closes = self.history_data["Close"].dropna()
            if len(closes) >= 10:
                sma5 = compute_sma(closes, 5)
                sma10 = compute_sma(closes, 10)
                rsi = compute_rsi(closes, 14)
                macd = compute_macd(closes)
                summary_lines.extend([
                    f"SMA(5): ${sma5:.2f}",
                    f"SMA(10): ${sma10:.2f}",
                    f"RSI(14): {rsi:.1f}",
                    f"MACD: {macd:.2f}",
                ])

        summary = "\n".join(summary_lines)
        self.summary_text.configure(state="normal")
        self.summary_text.delete("1.0", tk.END)
        self.summary_text.insert(tk.END, summary)
        self.summary_text.configure(state="disabled")


if __name__ == "__main__":
    app = StockApp()
    app.mainloop()
