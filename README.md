# E-commerce analytics with dbt

An analytics engineering project that turns raw e-commerce exports into tested, documented marts that answer questions like *how much revenue did we make last month?*, *which acquisition channel brings the most valuable customers?* and *how much of our revenue comes from repeat buyers?*

It runs locally on DuckDB in under a second. The SQL is portable to Snowflake, BigQuery or Databricks.

## Architecture

```
raw (source)            staging (views)            intermediate          marts (tables)
─────────────           ─────────────────          ──────────────        ──────────────────────────
customers     ──►  stg_shop__customers   ─────────────────────────►  core.dim_customers
products      ──►  stg_shop__products
orders        ──►  stg_shop__orders      ──┐
order_items   ──►  stg_shop__order_items ──┼──► int_orders__enriched ──►  core.fct_orders
payments      ──►  stg_shop__payments    ──┘                         └─►  finance.mart_revenue_monthly
```

| Layer | What it does |
|---|---|
| **staging** | One model per source table. Renames, casts text timestamps, converts cents to currency, normalises casing and whitespace. No joins. |
| **intermediate** | Aggregates items and payments to one row per order and numbers each customer's orders. Ephemeral, so it isn't exposed to BI users. |
| **marts** | `fct_orders` (one row per order), `dim_customers` (one row per customer, with cohort month and lifetime value), `mart_revenue_monthly` (monthly KPIs). |

## Data quality

38 data tests run on every build:

- **Keys:** `unique` + `not_null` on every primary key, including surrogate keys
- **Referential integrity:** `relationships` from orders → customers, items → products, payments → orders
- **Domains:** `accepted_values` on status, channel, region, category, payment method
- **Ranges:** no negative amounts or delivery times; `repeat_revenue_share` between 0 and 1
- **Conditional:** `delivered_at` must be set when `order_status = 'delivered'`
- **Business rules:** order amount matches the amount paid (warning); a singular test checks that monthly mart revenue reconciles with the orders fact to the cent

## Business definitions

| Metric | Definition |
|---|---|
| Valid order | Any order not canceled |
| Gross revenue | Items + freight on valid orders |
| Lifetime revenue | Sum of gross revenue across a customer's valid orders |
| Cohort month | Month of a customer's first valid order |
| Repeat revenue share | Revenue from orders that are not the customer's first, ÷ gross revenue |

## Run it

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export DBT_PROFILES_DIR=.

python scripts/load_raw_data.py      # generate and load raw data into DuckDB
dbt deps
dbt build                            # run all models and tests
dbt docs generate && dbt docs serve  # browse docs and the lineage graph
```

## The data

`scripts/load_raw_data.py` generates a reproducible synthetic dataset (5,000 customers, ~8,600 orders over 2024–2025) shaped like a real marketplace export, including the messy parts: inconsistent casing, padded strings, amounts in cents, timestamps stored as text, and orders split across payment methods. Retention differs by acquisition channel, so the marts produce realistic LTV patterns.

## CI

`.github/workflows/dbt_ci.yml` runs on every pull request: it installs dbt, loads data, and runs `dbt build --fail-fast`. A PR that breaks a model or a test can't be merged unnoticed.

## What I'd add next

- A semantic layer (MetricFlow) so revenue, AOV and retention are defined once for every tool
- Cohort retention and LTV marts with a BI dashboard on top
- Incremental models for orders once volumes grow
- Slim CI (`state:modified+`) with a production manifest
