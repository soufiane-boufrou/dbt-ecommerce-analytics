with order_stats as (
    select
        customer_id,
        min(ordered_at)             as first_order_at,
        max(ordered_at)             as last_order_at,
        count(*)                    as valid_order_count,
        sum(order_amount)           as lifetime_revenue
    from {{ ref('int_orders__enriched') }}
    where is_valid_order
    group by 1
)

select
    c.customer_id,
    c.customer_city,
    c.customer_region,
    c.acquisition_channel,
    c.created_at,
    s.first_order_at,
    s.last_order_at,
    date_trunc('month', s.first_order_at)           as cohort_month,
    coalesce(s.valid_order_count, 0)                as valid_order_count,
    coalesce(s.lifetime_revenue, 0)                 as lifetime_revenue,
    coalesce(s.valid_order_count, 0) > 1            as is_repeat_customer,
    case
        when s.customer_id is null then 'never_ordered'
        when coalesce(s.valid_order_count, 0) = 1 then 'one_time'
        else 'repeat'
    end                                             as customer_segment
from {{ ref('stg_shop__customers') }} as c
left join order_stats as s using (customer_id)
