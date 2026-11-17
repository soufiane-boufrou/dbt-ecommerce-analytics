select
    {{ dbt_utils.generate_surrogate_key(['order_id', 'payment_seq']) }} as payment_id,
    order_id,
    payment_seq,
    lower(trim(payment_method))     as payment_method,
    amount_cents / 100.0            as amount
from {{ source('shop', 'payments') }}
