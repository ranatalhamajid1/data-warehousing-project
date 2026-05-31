"""
Enterprise Retail Analytics Engine
Part 1: Web Scraper — Competitor Price Extraction
Uses BeautifulSoup to parse competitor_products.html and export competitor_prices.csv
"""

import os
import csv
import re
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict
from bs4 import BeautifulSoup  # type: ignore

# ─── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# ─── Paths ────────────────────────────────────────────────────────────────────

SCRAPER_DIR  = Path(__file__).parent
PROJECT_ROOT = SCRAPER_DIR.parent
HTML_FILE    = SCRAPER_DIR / "competitor_products.html"
OUTPUT_CSV   = PROJECT_ROOT / "data" / "competitor_prices.csv"

OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

# ─── Field Definitions ────────────────────────────────────────────────────────

CSV_FIELDS = [
    "scraped_at",
    "category",
    "product_name",
    "competitor_name",
    "competitor_price_usd",
    "our_price_usd",
    "price_position",
    "last_updated",
    "price_delta_usd",
    "price_delta_pct",
]


# ─── Parser ───────────────────────────────────────────────────────────────────

def parse_price(text: str) -> float:
    """Extract numeric price from strings like '$749.99' or '749.99'."""
    cleaned = re.sub(r"[^\d.]", "", str(text))
    if cleaned:
        return round(float(cleaned), 2)
    return 0.0


def extract_price_position(badge_text: str) -> str:
    """Normalize the price position badge text."""
    text = badge_text.strip().lower()
    if "lower" in text:
        return "We're Lower"
    elif "higher" in text:
        return "We're Higher"
    elif "same" in text:
        return "Same"
    return badge_text.strip()


def scrape_competitor_prices(html_path: Path) -> List[Dict]:
    """
    Parse all product tables from the competitor HTML file.
    Returns a list of dicts, one per product row.
    """
    log.info(f"Reading HTML from: {html_path}")

    with open(html_path, encoding="utf-8") as fh:
        soup = BeautifulSoup(fh, "html.parser")

    scraped_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    results = []

    tables = soup.find_all("table", class_="product-table")
    log.info(f"Found {len(tables)} product category tables")

    for table in tables:
        # Category from data-category attribute or nearest h2
        category = table.get("data-category", "Unknown")

        rows = table.find("tbody").find_all("tr")
        log.info(f"  [{category}] — {len(rows)} rows")

        for row in rows:
            cells = row.find_all("td")
            if len(cells) < 6:
                log.warning(f"  Skipping malformed row: {row.get_text(strip=True)[:60]}")
                continue

            product_name     = cells[0].get_text(strip=True)
            competitor_name  = cells[1].get_text(strip=True)

            # Prefer data-price attribute for precision
            price_td = cells[2]
            if price_td.get("data-price"):
                competitor_price = float(price_td["data-price"])
            else:
                competitor_price = parse_price(price_td.get_text(strip=True))

            our_price        = parse_price(cells[3].get_text(strip=True))
            price_position   = extract_price_position(cells[4].get_text(strip=True))
            last_updated     = cells[5].get_text(strip=True)

            # Computed fields
            price_delta_usd = round(our_price - competitor_price, 2)
            price_delta_pct = (
                round((our_price - competitor_price) / competitor_price * 100, 2)
                if competitor_price > 0 else 0.0
            )

            results.append({
                "scraped_at":           scraped_at,
                "category":             category,
                "product_name":         product_name,
                "competitor_name":      competitor_name,
                "competitor_price_usd": competitor_price,
                "our_price_usd":        our_price,
                "price_position":       price_position,
                "last_updated":         last_updated,
                "price_delta_usd":      price_delta_usd,
                "price_delta_pct":      price_delta_pct,
            })

    return results


def export_csv(records: List[Dict], output_path: Path) -> None:
    """Write records to CSV file."""
    log.info(f"Writing {len(records)} records to {output_path}")
    with open(output_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(records)
    log.info(f"[OK] Exported: {output_path}")


def print_summary(records: List[Dict]) -> None:
    """Print a summary report to console."""
    if not records:
        log.warning("No records to summarize.")
        return

    categories = {}
    for r in records:
        cat = r["category"]
        categories.setdefault(cat, []).append(r)

    print("\n" + "=" * 65)
    print("  COMPETITOR PRICE SCRAPER - SUMMARY REPORT")
    print("=" * 65)
    print(f"  Total Products Scraped : {len(records)}")
    print(f"  Scraped At             : {records[0]['scraped_at']}")
    print()
    print(f"  {'Category':<20} {'Count':>5}  {'Avg Delta':>12}  {'Positions'}")
    print(f"  {'-'*20} {'-'*5}  {'-'*12}  {'-'*30}")

    for cat, recs in sorted(categories.items()):
        avg_delta = sum(r["price_delta_usd"] for r in recs) / len(recs)
        positions = {}
        for r in recs:
            positions[r["price_position"]] = positions.get(r["price_position"], 0) + 1
        pos_str = " | ".join(f"{k}: {v}" for k, v in sorted(positions.items()))
        print(f"  {cat:<20} {len(recs):>5}  ${avg_delta:>+10.2f}  {pos_str}")

    all_deltas = [r["price_delta_usd"] for r in records]
    overpriced  = [r for r in records if r["price_delta_usd"] > 0]
    underpriced = [r for r in records if r["price_delta_usd"] < 0]
    same_price  = [r for r in records if r["price_delta_usd"] == 0]

    print()
    print(f"  Overall Average Price Delta : ${sum(all_deltas)/len(all_deltas):>+.2f}")
    print(f"  Overpriced vs Competitors   : {len(overpriced)} products")
    print(f"  Underpriced vs Competitors  : {len(underpriced)} products")
    print(f"  Same Price                  : {len(same_price)} products")
    print()

    if overpriced:
        top_overpriced = sorted(overpriced, key=lambda r: r["price_delta_usd"], reverse=True)[:3]
        print("  Top 3 Most Overpriced:")
        for r in top_overpriced:
            print(f"    - {r['product_name'][:40]:<40} +${r['price_delta_usd']:>8.2f} ({r['price_delta_pct']:>+.1f}%)")

    print("=" * 65)


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    log.info("Starting competitor price scraper...")

    records = scrape_competitor_prices(HTML_FILE)

    if not records:
        log.error("No data extracted. Check HTML structure.")
        return

    export_csv(records, OUTPUT_CSV)
    print_summary(records)

    log.info("Scraping complete.")


if __name__ == "__main__":
    main()
