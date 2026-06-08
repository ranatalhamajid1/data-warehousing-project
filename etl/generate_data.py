"""
Enterprise Retail Analytics Engine
Part 1: Synthetic Data Generation
Generates Customers, Products, Orders, Order Items datasets
Uses Faker, Pandas, NumPy with reproducible seed and proper FK relationships
"""

import os
import random
from typing import List, Optional
import numpy as np
import pandas as pd
from faker import Faker
from datetime import datetime, timedelta

# ─── Configuration ──────────────────────────────────────────────────────────

SEED = 42
random.seed(SEED)
np.random.seed(SEED)
fake = Faker()
Faker.seed(SEED)

NUM_CUSTOMERS    = 10_000
NUM_PRODUCTS     = 500
NUM_ORDERS       = 50_000
NUM_ORDER_ITEMS  = 150_000

START_DATE = datetime(2024, 1, 1)
END_DATE   = datetime(2024, 12, 31)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ─── Category / Product Definitions ─────────────────────────────────────────

CATEGORIES = {
    "Electronics":    {"weight": 0.18, "price_range": (50, 1500),  "margin_range": (0.12, 0.30)},
    "Clothing":       {"weight": 0.20, "price_range": (15, 250),   "margin_range": (0.35, 0.60)},
    "Home & Garden":  {"weight": 0.15, "price_range": (10, 600),   "margin_range": (0.25, 0.50)},
    "Sports":         {"weight": 0.12, "price_range": (20, 800),   "margin_range": (0.20, 0.45)},
    "Books":          {"weight": 0.10, "price_range": (5, 80),     "margin_range": (0.30, 0.55)},
    "Toys":           {"weight": 0.08, "price_range": (10, 200),   "margin_range": (0.30, 0.55)},
    "Beauty":         {"weight": 0.07, "price_range": (8, 300),    "margin_range": (0.40, 0.65)},
    "Food":           {"weight": 0.05, "price_range": (2, 150),    "margin_range": (0.20, 0.40)},
    "Automotive":     {"weight": 0.03, "price_range": (15, 2000),  "margin_range": (0.15, 0.35)},
    "Office":         {"weight": 0.02, "price_range": (5, 500),    "margin_range": (0.25, 0.50)},
}

PRODUCT_NAMES = {
    "Electronics":   ["Smart TV", "Laptop", "Smartphone", "Tablet", "Headphones", "Smartwatch",
                      "Camera", "Bluetooth Speaker", "Gaming Console", "Monitor", "Keyboard",
                      "Mouse", "USB Hub", "External SSD", "Webcam", "Drone", "VR Headset"],
    "Clothing":      ["Running Shoes", "Denim Jacket", "Yoga Pants", "Polo Shirt", "Summer Dress",
                      "Winter Coat", "Baseball Cap", "Sports Bra", "Cargo Shorts", "Hoodie",
                      "Leather Belt", "Swim Trunks", "Sneakers", "Blazer", "Skirt"],
    "Home & Garden": ["Coffee Maker", "Air Fryer", "Vacuum Cleaner", "Bed Sheets", "Throw Pillow",
                      "Wall Clock", "Scented Candle", "Plant Pot", "Tool Set", "Curtains",
                      "Lamp", "Storage Box", "Bath Towel", "Doormat", "Kitchen Scale"],
    "Sports":        ["Yoga Mat", "Dumbbells", "Resistance Bands", "Cycling Helmet", "Tennis Racket",
                      "Basketball", "Football", "Jump Rope", "Fitness Tracker", "Water Bottle",
                      "Foam Roller", "Pull-Up Bar", "Kettlebell", "Treadmill Belt"],
    "Books":         ["Business Strategy Guide", "Python Programming", "Data Science Handbook",
                      "Self Help Journal", "History of Finance", "Marketing Masterclass",
                      "Novel Collection", "Cookbook", "Leadership Book", "Cloud Computing Guide"],
    "Toys":          ["LEGO Set", "Board Game", "Action Figure", "Puzzle", "Remote Control Car",
                      "Doll", "Science Kit", "Art Supply Set", "Stuffed Animal", "Card Game"],
    "Beauty":        ["Face Moisturizer", "Lip Gloss", "Mascara", "Foundation", "Perfume",
                      "Hair Mask", "Nail Polish", "Serum", "Eye Shadow Palette", "Sunscreen"],
    "Food":          ["Protein Powder", "Organic Honey", "Coffee Beans", "Green Tea",
                      "Nut Butter", "Dried Fruit Mix", "Dark Chocolate", "Olive Oil"],
    "Automotive":    ["Car Phone Mount", "Dash Cam", "Car Vacuum", "Seat Cover",
                      "Jump Starter", "Tire Inflator"],
    "Office":        ["Ergonomic Chair", "Standing Desk", "Desk Organizer", "Notebook",
                      "Pen Set", "Whiteboard"],
}

COUNTRIES_CITIES = {
    "United States": ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia",
                      "San Antonio", "San Diego", "Dallas", "San Jose", "Austin", "Jacksonville"],
    "United Kingdom": ["London", "Manchester", "Birmingham", "Glasgow", "Leeds", "Liverpool"],
    "Canada":         ["Toronto", "Vancouver", "Montreal", "Calgary", "Ottawa", "Edmonton"],
    "Australia":      ["Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide", "Canberra"],
    "Germany":        ["Berlin", "Hamburg", "Munich", "Cologne", "Frankfurt", "Stuttgart"],
    "France":         ["Paris", "Lyon", "Marseille", "Toulouse", "Nice", "Nantes"],
    "India":          ["Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai", "Kolkata"],
    "Brazil":         ["São Paulo", "Rio de Janeiro", "Brasília", "Salvador", "Fortaleza"],
}

COUNTRY_WEIGHTS = [0.35, 0.15, 0.10, 0.08, 0.10, 0.07, 0.10, 0.05]


# ─── Helpers ─────────────────────────────────────────────────────────────────

def random_date(start: datetime, end: datetime) -> datetime:
    delta = end - start
    random_days = random.randint(0, delta.days)
    return start + timedelta(days=random_days)


def random_date_array(start: datetime, end: datetime, n: int) -> list:
    delta = (end - start).days
    offsets = np.random.randint(0, delta + 1, size=n)
    return [start + timedelta(days=int(d)) for d in offsets]


# ─── 1. Customers ─────────────────────────────────────────────────────────────

def generate_customers(n: int = NUM_CUSTOMERS) -> pd.DataFrame:
    print(f"[1/4] Generating {n:,} customers...")
    countries = list(COUNTRIES_CITIES.keys())
    country_choices = np.random.choice(countries, size=n, p=COUNTRY_WEIGHTS)

    rows = []
    for i in range(n):
        country = country_choices[i]
        city = random.choice(COUNTRIES_CITIES[country])
        gender = random.choice(["Male", "Female", "Non-Binary"])
        if gender == "Male":
            first_name = fake.first_name_male()
        elif gender == "Female":
            first_name = fake.first_name_female()
        else:
            first_name = fake.first_name()
        last_name = fake.last_name()
        email_domain = random.choice(["gmail.com", "yahoo.com", "outlook.com", "hotmail.com",
                                       "icloud.com", "protonmail.com"])
        email = f"{first_name.lower()}.{last_name.lower()}{random.randint(1,999)}@{email_domain}"
        reg_date = random_date(datetime(2018, 1, 1), END_DATE)
        rows.append({
            "customer_id":       f"CUST-{i+1:06d}",
            "first_name":        first_name,
            "last_name":         last_name,
            "gender":            gender,
            "email":             email,
            "city":              city,
            "country":           country,
            "registration_date": reg_date.strftime("%Y-%m-%d"),
        })

    df = pd.DataFrame(rows)
    print(f"   [OK] {len(df):,} customers generated")
    return df


# ─── 2. Products ─────────────────────────────────────────────────────────────

def generate_products(n: int = NUM_PRODUCTS) -> pd.DataFrame:
    print(f"[2/4] Generating {n:,} products...")
    categories = list(CATEGORIES.keys())
    cat_weights = [CATEGORIES[c]["weight"] for c in categories]

    # Load competitor products from HTML to inject
    import re
    from bs4 import BeautifulSoup
    comp_prods = []
    html_path = os.path.join(os.path.dirname(__file__), "..", "scraper", "competitor_products.html")
    if os.path.exists(html_path):
        try:
            with open(html_path, encoding="utf-8") as fh:
                soup = BeautifulSoup(fh, "html.parser")
            tables = soup.find_all("table", class_="product-table")
            seen_names = set()
            for table in tables:
                category = table.get("data-category", "Unknown")
                # Normalize category name just in case
                if category == "Home &amp; Garden" or "Home" in category:
                    category = "Home & Garden"
                rows = table.find("tbody").find_all("tr")
                for row in rows:
                    cells = row.find_all("td")
                    if len(cells) < 6:
                        continue
                    name = cells[0].get_text(strip=True)
                    if name in seen_names:
                        continue
                    seen_names.add(name)
                    
                    our_price_str = cells[3].get_text(strip=True)
                    our_price = float(re.sub(r"[^\d.]", "", our_price_str))
                    
                    comp_prods.append({
                        "product_name": name,
                        "category": category,
                        "retail_price": our_price
                    })
            print(f"   [OK] Loaded {len(comp_prods)} competitor products to inject")
        except Exception as e:
            print(f"   [WARNING] Failed to load competitor products for injection: {e}")
            comp_prods = []

    rows = []
    product_counter = 1

    # Inject competitor products
    for cp in comp_prods:
        cat = cp["category"]
        cfg = CATEGORIES.get(cat, {"margin_range": (0.25, 0.50)})
        retail_price = cp["retail_price"]
        margin_rate = random.uniform(*cfg["margin_range"])
        base_cost = round(retail_price * (1 - margin_rate), 2)
        
        rows.append({
            "product_id":    f"PROD-{product_counter:04d}",
            "product_name":  cp["product_name"],
            "category":      cat,
            "retail_price":  retail_price,
            "base_cost":     base_cost,
        })
        product_counter += 1

    # Generate remaining products to reach N
    remaining_count = max(0, n - len(rows))
    for _ in range(remaining_count):
        cat = np.random.choice(categories, p=cat_weights)
        cfg = CATEGORIES[cat]
        base_names = PRODUCT_NAMES[cat]

        # Generate unique product name
        suffix = random.choice(["Pro", "Plus", "Elite", "Max", "Mini", "Lite", "Ultra", "Basic", "Premium", ""])
        base = random.choice(base_names)
        brand = fake.company().split()[0]
        product_name = f"{brand} {base} {suffix}".strip()

        retail_price = round(random.uniform(*cfg["price_range"]), 2)
        margin_rate  = random.uniform(*cfg["margin_range"])
        base_cost    = round(retail_price * (1 - margin_rate), 2)

        rows.append({
            "product_id":    f"PROD-{product_counter:04d}",
            "product_name":  product_name,
            "category":      cat,
            "retail_price":  retail_price,
            "base_cost":     base_cost,
        })
        product_counter += 1

    df = pd.DataFrame(rows)
    print(f"   [OK] {len(df):,} products generated ({len(comp_prods)} injected)")
    return df


# ─── 3. Orders ───────────────────────────────────────────────────────────────

def generate_orders(n: int = NUM_ORDERS, customer_ids: Optional[List[str]] = None) -> pd.DataFrame:
    print(f"[3/4] Generating {n:,} orders...")

    # Seasonal & weekly weights — retail peaks in Nov/Dec
    month_weights = np.array([0.06, 0.055, 0.07, 0.075, 0.08, 0.08,
                               0.085, 0.085, 0.08, 0.09, 0.11, 0.13])
    month_weights /= month_weights.sum()

    order_dates = random_date_array(START_DATE, END_DATE, n)

    # Repeat buyers: some customers order many times, most once or twice
    customer_probs = np.random.zipf(1.5, size=len(customer_ids))
    customer_probs = customer_probs / customer_probs.sum()
    chosen_customers = np.random.choice(customer_ids, size=n, p=customer_probs)

    rows = []
    for i in range(n):
        rows.append({
            "order_id":    f"ORD-{i+1:07d}",
            "customer_id": chosen_customers[i],
            "order_date":  order_dates[i].strftime("%Y-%m-%d"),
        })

    df = pd.DataFrame(rows)
    print(f"   [OK] {len(df):,} orders generated")
    return df


# ─── 4. Order Items ──────────────────────────────────────────────────────────

def generate_order_items(
    n: int = NUM_ORDER_ITEMS,
    order_ids: Optional[List[str]] = None,
    product_ids: Optional[List[str]] = None,
    products_df: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    print(f"[4/4] Generating {n:,} order items...")

    product_price_map = dict(zip(products_df["product_id"], products_df["retail_price"]))

    # Orders get 1–6 items; oversample order_ids based on typical multi-item patterns
    items_per_order = np.random.choice([1, 2, 3, 4, 5, 6], size=len(order_ids),
                                        p=[0.35, 0.30, 0.18, 0.10, 0.05, 0.02])
    order_id_expanded = np.repeat(order_ids, items_per_order)

    # Trim or pad to exactly n
    if len(order_id_expanded) > n:
        order_id_expanded = order_id_expanded[:n]
    elif len(order_id_expanded) < n:
        extra = np.random.choice(order_ids, size=n - len(order_id_expanded))
        order_id_expanded = np.concatenate([order_id_expanded, extra])

    np.random.shuffle(order_id_expanded)

    # Product selection weighted by category popularity
    product_weights = np.random.pareto(1.5, size=len(product_ids)) + 1
    product_weights /= product_weights.sum()
    chosen_products = np.random.choice(product_ids, size=n, p=product_weights)

    quantities = np.random.choice([1, 2, 3, 4, 5], size=n, p=[0.55, 0.25, 0.12, 0.05, 0.03])

    # Unit price = retail price ± small discount (0–15%)
    rows = []
    for i in range(n):
        pid = chosen_products[i]
        base_price = product_price_map[pid]
        discount = random.uniform(0, 0.15)
        unit_price = round(base_price * (1 - discount), 2)
        rows.append({
            "order_item_id": f"ITEM-{i+1:08d}",
            "order_id":      order_id_expanded[i],
            "product_id":    pid,
            "quantity":      int(quantities[i]),
            "unit_price":    unit_price,
        })

    df = pd.DataFrame(rows)
    print(f"   [OK] {len(df):,} order items generated")
    return df


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  Enterprise Retail Analytics Engine — Data Generator")
    print("=" * 60)

    customers_df = generate_customers()
    products_df  = generate_products()
    orders_df    = generate_orders(customer_ids=customers_df["customer_id"].tolist())
    order_items_df = generate_order_items(
        order_ids=orders_df["order_id"].tolist(),
        product_ids=products_df["product_id"].tolist(),
        products_df=products_df,
    )

    # ── Export ─────────────────────────────────────────────────────
    print("\nExporting CSV files...")
    customers_df.to_csv(os.path.join(OUTPUT_DIR, "customers.csv"), index=False)
    products_df.to_csv(os.path.join(OUTPUT_DIR, "products.csv"), index=False)
    orders_df.to_csv(os.path.join(OUTPUT_DIR, "orders.csv"), index=False)
    order_items_df.to_csv(os.path.join(OUTPUT_DIR, "order_items.csv"), index=False)

    # ── Validation ─────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  VALIDATION REPORT")
    print("=" * 60)
    print(f"  customers.csv    : {len(customers_df):>8,} rows")
    print(f"  products.csv     : {len(products_df):>8,} rows")
    print(f"  orders.csv       : {len(orders_df):>8,} rows")
    print(f"  order_items.csv  : {len(order_items_df):>8,} rows")

    # FK integrity checks
    invalid_orders = orders_df[~orders_df["customer_id"].isin(customers_df["customer_id"])]
    invalid_items_order = order_items_df[~order_items_df["order_id"].isin(orders_df["order_id"])]
    invalid_items_prod  = order_items_df[~order_items_df["product_id"].isin(products_df["product_id"])]

    print(f"\n  FK Violations:")
    print(f"    orders -> customers   : {len(invalid_orders):,} invalid")
    print(f"    items  -> orders      : {len(invalid_items_order):,} invalid")
    print(f"    items  -> products    : {len(invalid_items_prod):,} invalid")

    # Business stats
    total_revenue = (order_items_df["quantity"] * order_items_df["unit_price"]).sum()
    print(f"\n  Business Metrics:")
    print(f"    Total Revenue       : ${total_revenue:>14,.2f}")
    print(f"    Avg Order Value     : ${total_revenue / len(orders_df):>14,.2f}")
    print(f"    Date Range          : {orders_df['order_date'].min()} -> {orders_df['order_date'].max()}")
    print(f"    Unique Customers    : {orders_df['customer_id'].nunique():>8,}")
    print(f"    Unique Products     : {order_items_df['product_id'].nunique():>8,}")

    print("\n  [SUCCESS] All files exported to ./data/")
    print("=" * 60)


if __name__ == "__main__":
    main()
