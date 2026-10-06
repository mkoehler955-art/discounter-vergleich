
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests, re, sqlite3, hashlib
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from typing import Optional

DB = "offers.db"
HEADERS = {"User-Agent": "Mozilla/5.0 (Android 14; Mobile) AppleWebKit/537.36 Chrome/140 Safari/537.36"}

SOURCES = {
    "ALDI Nord": "https://www.aldi-nord.de/prospekte/aldi-aktuell.html",
    "Lidl": "https://www.lidl.de/c/online-prospekte/s10005610",
    "PENNY": "https://www.penny.de/angebote",
    "Netto": "https://netto.de/angebote/",
    "NORMA": "https://www.norma-online.de/de/angebote/",
}

PRICE_RE = re.compile(r'(?<!\d)(\d{1,3}[,.]\d{2})\s*€')
UNIT_RE = re.compile(r'(\d+(?:[,.]\d+)?)\s*(kg|g|l|ml|stück|stk\.|packung|dose|becher|flasche)', re.I)

app = FastAPI(title="Discounter-Vergleich API", version="1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

def init_db():
    c = sqlite3.connect(DB)
    c.execute("""CREATE TABLE IF NOT EXISTS offers(
        id INTEGER PRIMARY KEY,
        store TEXT, product TEXT, price REAL, pack TEXT, unit_price REAL,
        valid_from TEXT, valid_to TEXT, source TEXT, fetched_at TEXT, fingerprint TEXT UNIQUE
    )""")
    c.commit(); c.close()

init_db()

def money(x):
    try: return float(x.replace(".", "").replace(",", "."))
    except: return None

def scrape_page(store, url):
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    for x in soup(["script","style","noscript","svg"]): x.decompose()
    blocks = soup.select("article, li, [class*='product'], [class*='offer'], [class*='Product'], [class*='Offer']")
    if not blocks: blocks = soup.find_all(["div","section"])
    rows = []
    seen = set()
    for b in blocks:
        txt = re.sub(r"\s+", " ", b.get_text(" ", strip=True))
        if not (10 <= len(txt) <= 1200): continue
        prices = PRICE_RE.findall(txt)
        if not prices: continue
        price = money(prices[0])
        if not price or price <= 0 or price > 1000: continue
        name = ""
        for tag in b.find_all(["h1","h2","h3","h4","h5","strong","b"]):
            t = re.sub(r"\s+", " ", tag.get_text(" ", strip=True)).strip()
            if 2 <= len(t) <= 180 and not PRICE_RE.search(t):
                name = t; break
        if not name:
            name = PRICE_RE.sub("", txt)[:180].strip()
        if len(name) < 2: continue
        um = UNIT_RE.search(txt)
        pack = um.group(0) if um else ""
        up = None
        gm = re.search(r'(\d+[,.]\d{2})\s*€?\s*/\s*(kg|l|stück)', txt, re.I)
        if gm: up = money(gm.group(1))
        key = (store, name.lower(), price, pack)
        if key in seen: continue
        seen.add(key)
        fp = hashlib.sha256("|".join(map(str,key)).encode()).hexdigest()
        rows.append(dict(store=store, product=name, price=price, pack=pack,
                         unit_price=up, source=url, fingerprint=fp))
    return rows

def save(rows):
    c = sqlite3.connect(DB)
    now = datetime.now(timezone.utc).isoformat()
    for x in rows:
        c.execute("""INSERT OR IGNORE INTO offers
        (store,product,price,pack,unit_price,source, fetched_at,fingerprint)
        VALUES (?,?,?,?,?,?,?,?)""",
        (x["store"],x["product"],x["price"],x["pack"],x["unit_price"],x["source"],now,x["fingerprint"]))
    c.commit(); c.close()

@app.get("/health")
def health(): return {"ok": True, "time": datetime.now(timezone.utc).isoformat()}

@app.post("/refresh")
def refresh():
    result, errors = {}, {}
    for store, url in SOURCES.items():
        try:
            rows = scrape_page(store, url); save(rows); result[store] = len(rows)
        except Exception as e:
            errors[store] = str(e)
    return {"loaded": result, "errors": errors}

@app.get("/offers")
def offers(q: str = Query("", description="Produkt-Suchbegriff"),
           limit: int = 200):
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row
    if q:
        rows = c.execute("""SELECT * FROM offers WHERE product LIKE ?
                            ORDER BY price ASC LIMIT ?""", (f"%{q}%", limit)).fetchall()
    else:
        rows = c.execute("SELECT * FROM offers ORDER BY price ASC LIMIT ?", (limit,)).fetchall()
    c.close()
    return [dict(x) for x in rows]

@app.get("/best")
def best(q: str):
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row
    rows = c.execute("""SELECT * FROM offers WHERE product LIKE ?
                        ORDER BY price ASC""", (f"%{q}%",)).fetchall()
    c.close()
    return [dict(x) for x in rows]

@app.get("/stores")
def stores():
    return [{"name": k, "source": v} for k,v in SOURCES.items()]
