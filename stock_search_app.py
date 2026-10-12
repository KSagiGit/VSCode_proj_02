import math
import tkinter as tk
from tkinter import ttk


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


class StockApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MarketPulse")
        self.geometry("1280x760")
        self.configure(bg="#0b1220")
        self.minsize(980, 620)

        self.style = ttk.Style(self)
        self.style.theme_use("clam")

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

        self.summary_text = tk.Text(overview, bg="#0f1a2d", fg="#dfeafc", height=18, wrap="word", bd=0, padx=18, pady=10)
        self.summary_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.summary_text.configure(state="disabled")

        self.default_suggestions()

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
        self.selected_ticker = stock["symbol"]
        self.search_var.set(f"{stock['symbol']} {stock['name']}")
        self.symbol_label.config(text=stock["symbol"])
        self.name_label.config(text=stock["name"])
        self.price_label.config(text=f"${stock['price']:.2f}")
        color = "#7ef5a8" if stock["change"] >= 0 else "#ff6b6b"
        self.change_label.config(text=f"{stock['change']:+.2f}%", fg=color)
        self.draw_chart(stock)
        self.refresh_summary(stock)

    def draw_chart(self, stock):
        self.chart_canvas.delete("all")
        width = 300
        height = 180
        center_y = height / 2

        self.chart_canvas.create_line(0, center_y, width, center_y, fill="#1f2d40", width=1)

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
        summary = (
            f"{stock['symbol']} • {stock['name']}\n"
            f"Sector: {stock['sector']}\n\n"
            f"Price: ${stock['price']:.2f}\n"
            f"Daily change: {stock['change']:+.2f}%\n\n"
            f"Signal: Bullish continuation bias. Momentum remains constructive above short-term support.\n"
            f"Suggested view: trend + RSI confirmation + volume filter."
        )
        self.summary_text.configure(state="normal")
        self.summary_text.delete("1.0", tk.END)
        self.summary_text.insert(tk.END, summary)
        self.summary_text.configure(state="disabled")


if __name__ == "__main__":
    app = StockApp()
    app.mainloop()
