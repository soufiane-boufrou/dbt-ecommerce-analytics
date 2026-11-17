select
    {{ dbt_utils.generate_surrogate_key(['order_id', 'order_item_seq']) }} as order_item_id,
    order_id,
    order_item_seq,
    product_id,
    quantity,
    price_cents / 100.0     as item_price,
    freight_cents / 100.0   as freight_value
from {{ source('shop', 'order_items') }}
