-- Monthly mart revenue must equal the sum of valid orders in fct_orders.
-- Returns rows (= failure) if the two disagree by more than a cent.

with mart as (
    select sum(gross_revenue) as revenue from {{ ref('mart_revenue_monthly') }}
),
orders as (
    select sum(order_amount) as revenue from {{ ref('fct_orders') }} where is_valid_order
)
select mart.revenue as mart_revenue, orders.revenue as orders_revenue
from mart cross join orders
where abs(mart.revenue - orders.revenue) > 0.01
