"""Render a 1600x1200 portfolio thumbnail (docs/thumbnail.png). Needs matplotlib: pip install matplotlib."""

import os

import duckdb
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

BG, CARD, INK, MUTED, ACCENT, GREEN = "#0f172a", "#1e293b", "#f8fafc", "#94a3b8", "#ff694a", "#22c55e"

con = duckdb.connect(os.environ.get("DUCKDB_PATH", "ecommerce.duckdb"), read_only=True)
ltv = con.sql("""
    select replace(acquisition_channel, '_', ' ') as channel, avg(lifetime_revenue) as ltv
    from core.dim_customers where valid_order_count > 0
    group by 1 order by ltv
""").fetchall()

fig = plt.figure(figsize=(16, 12), dpi=100, facecolor=BG)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 16)
ax.set_ylim(0, 12)
ax.axis("off")

ax.text(0.9, 10.9, "dbt analytics engineering", color=ACCENT, fontsize=26, weight="bold")
ax.text(0.9, 9.9, "E-commerce data, modelled, tested and CI-checked",
        color=INK, fontsize=33, weight="bold")

# Lineage: raw -> staging -> intermediate -> marts
layers = [("raw", "5 source\ntables"), ("staging", "5 views\nclean + typed"),
          ("intermediate", "orders\nenriched"), ("marts", "fct_orders\ndim_customers\nrevenue_monthly")]
x = 0.9
for i, (name, body) in enumerate(layers):
    ax.add_patch(FancyBboxPatch((x, 6.3), 3.0, 2.7, boxstyle="round,pad=0.02,rounding_size=0.25",
                                fc=CARD, ec=ACCENT if name == "marts" else "#334155", lw=3))
    ax.text(x + 1.5, 8.45, name, color=ACCENT if name == "marts" else MUTED,
            fontsize=22, weight="bold", ha="center")
    ax.text(x + 1.5, 7.35, body, color=INK, fontsize=19, ha="center", va="center", linespacing=1.4)
    if i < len(layers) - 1:
        ax.annotate("", xy=(x + 3.75, 7.65), xytext=(x + 3.1, 7.65),
                    arrowprops=dict(arrowstyle="-|>", color=MUTED, lw=3, mutation_scale=28))
    x += 3.75

# Stat tiles
stats = [("38", "data tests passing"), ("CI", "on every pull request"), ("€1.9M", "revenue reconciled")]
x = 0.9
for big, small in stats:
    ax.add_patch(FancyBboxPatch((x, 3.4), 3.0, 2.2, boxstyle="round,pad=0.02,rounding_size=0.25",
                                fc=CARD, ec="#334155", lw=2))
    ax.text(x + 0.35, 4.65, big, color=GREEN, fontsize=36, weight="bold")
    ax.text(x + 0.35, 3.85, small, color=MUTED, fontsize=17)
    x += 3.2

# LTV by channel mini-chart
cax = fig.add_axes([0.77, 0.29, 0.18, 0.19], facecolor=CARD)
names, vals = zip(*ltv)
cax.barh(names, vals, color=[ACCENT if v == max(vals) else "#475569" for v in vals], height=0.6)
for i, v in enumerate(vals):
    cax.text(v + 8, i, f"€{v:,.0f}", va="center", color=INK, fontsize=13)
cax.set_xlim(0, max(vals) * 1.35)
cax.tick_params(colors=MUTED, labelsize=14, length=0)
cax.set_xticks([])
for s in cax.spines.values():
    s.set_visible(False)
ax.text(10.95, 5.9, "Customer LTV by channel", color=INK, fontsize=18, weight="bold")

ax.text(0.9, 1.6, "dbt  ·  SQL  ·  DuckDB / Snowflake  ·  GitHub Actions", color=MUTED, fontsize=22)
ax.text(0.9, 0.85, "github.com/soufiane-boufrou/dbt-ecommerce-analytics", color=INK, fontsize=20)

os.makedirs("docs", exist_ok=True)
fig.savefig("docs/thumbnail.png", facecolor=BG)
print("wrote docs/thumbnail.png")
