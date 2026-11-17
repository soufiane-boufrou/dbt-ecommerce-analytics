-- Monthly revenue KPIs on valid (non-canceled) orders.

select
    date_trunc('month', o.ordered_at)                       as order_month,
    count(*)                                                as order_count,
    count(distinct o.customer_id)                           as active_customers,
    count(distinct case when o.is_first_order then o.customer_id end) as new_customers,
    sum(o.order_amount)                                     as gross_revenue,
    sum(o.items_amount)                                     as items_revenue,
    sum(o.freight_amount)                                   as freight_revenue,
    sum(o.order_amount) / count(*)                          as average_order_value,
    sum(case when not o.is_first_order then o.order_amount else 0 end)
        / nullif(sum(o.order_amount), 0)                    as repeat_revenue_share
from {{ ref('fct_orders') }} as o
where o.is_valid_order
group by 1
