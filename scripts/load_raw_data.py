"""Generate a synthetic e-commerce dataset and load it into DuckDB's `raw` schema.

The shape mirrors a typical marketplace export (customers, products, orders,
order items, payments), with a few realistic quirks the staging layer has to
clean up: inconsistent casing, padded strings, amounts in cents, timestamps
stored as text.

Usage:
    python scripts/load_raw_data.py [--customers 5000] [--db ecommerce.duckdb]
"""

import argparse
import os
import random
from datetime import datetime, timedelta

import duckdb

CHANNELS = [("organic_search", 0.35), ("paid_search", 0.25), ("social", 0.18),
            ("referral", 0.12), ("email", 0.10)]
# Average orders per customer differs by channel, so LTV by channel is interesting.
CHANNEL_REPEAT_RATE = {"organic_search": 0.55, "paid_search": 0.40, "social": 0.35,
                       "referral": 0.62, "email": 0.58}
REGIONS = {"north": ["Lille", "Rouen", "Amiens"], "south": ["Marseille", "Nice", "Toulouse"],
           "east": ["Lyon", "Strasbourg", "Grenoble"], "west": ["Nantes", "Bordeaux", "Rennes"],
           "paris": ["Paris"]}
CATEGORIES = {"home": (15, 120), "electronics": (40, 600), "fashion": (10, 150),
              "beauty": (5, 60), "sports": (20, 250), "books": (5, 40)}
PAYMENT_METHODS = [("credit_card", 0.70), ("paypal", 0.18), ("gift_card", 0.07), ("bank_transfer", 0.05)]

START = datetime(2024, 1, 1)
END = datetime(2025, 12, 31)


def weighted(choices):
    values, weights = zip(*choices)
    return random.choices(values, weights=weights)[0]


def messy(s):
    """Randomly upper-case or pad a string, like a real source system would."""
    r = random.random()
    if r < 0.10:
        return s.upper()
    if r < 0.15:
        return f" {s} "
    return s


def ts(d):
    return d.strftime("%Y-%m-%d %H:%M:%S")


def generate(n_customers):
    customers, products, orders, items, payments = [], [], [], [], []

    for i in range(1, 301):
        cat = random.choice(list(CATEGORIES))
        lo, hi = CATEGORIES[cat]
        products.append((f"P{i:04d}", messy(cat), round(random.uniform(lo, hi), 2)))

    order_n = 0
    span_days = (END - START).days
    for c in range(1, n_customers + 1):
        cid = f"C{c:06d}"
        channel = weighted(CHANNELS)
        region = random.choice(list(REGIONS))
        signup = START + timedelta(days=random.randint(0, span_days - 30),
                                   seconds=random.randint(0, 86399))
        customers.append((cid, messy(random.choice(REGIONS[region])), region, channel, ts(signup)))

        # First order shortly after signup, then repeat purchases with decaying probability.
        order_date = signup + timedelta(hours=random.randint(1, 72))
        repeat_p = CHANNEL_REPEAT_RATE[channel]
        while order_date <= END:
            order_n += 1
            oid = f"O{order_n:07d}"
            status = weighted([("delivered", 0.90), ("canceled", 0.04),
                               ("shipped", 0.04), ("processing", 0.02)])
            delivered = ts(order_date + timedelta(days=random.randint(2, 9))) if status == "delivered" else None
            orders.append((oid, cid, messy(status), ts(order_date), delivered,
                           ts(order_date + timedelta(minutes=5))))

            total_cents = 0
            for seq in range(1, random.choices([1, 2, 3, 4], weights=[60, 25, 10, 5])[0] + 1):
                pid, _, price = random.choice(products)
                qty = random.choices([1, 2, 3], weights=[80, 15, 5])[0]
                price_cents = int(price * 100) * qty
                freight_cents = random.randint(0, 1500)
                items.append((oid, seq, pid, qty, price_cents, freight_cents))
                total_cents += price_cents + freight_cents

            # Most orders are paid in one go; some split across two methods.
            if random.random() < 0.08:
                first = int(total_cents * random.uniform(0.2, 0.8))
                payments.append((oid, 1, "gift_card", first))
                payments.append((oid, 2, weighted(PAYMENT_METHODS), total_cents - first))
            else:
                payments.append((oid, 1, weighted(PAYMENT_METHODS), total_cents))

            if random.random() > repeat_p:
                break
            repeat_p *= 0.85
            order_date += timedelta(days=int(random.expovariate(1 / 60)) + 7,
                                    seconds=random.randint(0, 86399))

    return customers, products, orders, items, payments


def load(db_path, customers, products, orders, items, payments):
    con = duckdb.connect(db_path)
    con.execute("create schema if not exists raw")
    ddl = {
        "customers": "customer_id varchar, customer_city varchar, customer_region varchar, "
                     "acquisition_channel varchar, created_at varchar",
        "products": "product_id varchar, product_category varchar, list_price double",
        "orders": "order_id varchar, customer_id varchar, order_status varchar, ordered_at varchar, "
                  "delivered_at varchar, _loaded_at varchar",
        "order_items": "order_id varchar, order_item_seq integer, product_id varchar, quantity integer, "
                       "price_cents bigint, freight_cents bigint",
        "payments": "order_id varchar, payment_seq integer, payment_method varchar, amount_cents bigint",
    }
    data = {"customers": customers, "products": products, "orders": orders,
            "order_items": items, "payments": payments}
    for table, cols in ddl.items():
        con.execute(f"create or replace table raw.{table} ({cols})")
        placeholders = ", ".join("?" * len(data[table][0]))
        con.executemany(f"insert into raw.{table} values ({placeholders})", data[table])
        print(f"raw.{table:<12} {len(data[table]):>8,} rows")
    con.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--customers", type=int, default=5000)
    parser.add_argument("--db", default=os.environ.get("DUCKDB_PATH", "ecommerce.duckdb"))
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    random.seed(args.seed)
    load(args.db, *generate(args.customers))


if __name__ == "__main__":
    main()
