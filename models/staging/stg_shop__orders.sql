select
    order_id,
    customer_id,
    lower(trim(order_status))           as order_status,
    cast(ordered_at as timestamp)       as ordered_at,
    cast(delivered_at as timestamp)     as delivered_at,
    cast(_loaded_at as timestamp)       as loaded_at
from {{ source('shop', 'orders') }}
