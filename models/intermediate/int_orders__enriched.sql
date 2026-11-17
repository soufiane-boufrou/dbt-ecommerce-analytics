-- Order-level totals: items and payments aggregated to one row per order,
-- plus the customer's order sequence (1 = first order).

with items as (
    select
        order_id,
        count(*)                as item_count,
        sum(quantity)           as unit_count,
        sum(item_price)         as items_amount,
        sum(freight_value)      as freight_amount
    from {{ ref('stg_shop__order_items') }}
    group by 1
),

payments as (
    select
        order_id,
        sum(amount)                                 as paid_amount,
        count(*)                                    as payment_count,
        bool_or(payment_method = 'gift_card')       as used_gift_card
    from {{ ref('stg_shop__payments') }}
    group by 1
)

select
    o.order_id,
    o.customer_id,
    o.order_status,
    o.ordered_at,
    o.delivered_at,
    o.order_status != 'canceled'                            as is_valid_order,
    coalesce(i.item_count, 0)                               as item_count,
    coalesce(i.unit_count, 0)                               as unit_count,
    coalesce(i.items_amount, 0)                             as items_amount,
    coalesce(i.freight_amount, 0)                           as freight_amount,
    coalesce(i.items_amount, 0) + coalesce(i.freight_amount, 0) as order_amount,
    coalesce(p.paid_amount, 0)                              as paid_amount,
    coalesce(p.payment_count, 0)                            as payment_count,
    coalesce(p.used_gift_card, false)                       as used_gift_card,
    row_number() over (
        partition by o.customer_id order by o.ordered_at, o.order_id
    )                                                       as customer_order_seq
from {{ ref('stg_shop__orders') }} as o
left join items as i using (order_id)
left join payments as p using (order_id)
