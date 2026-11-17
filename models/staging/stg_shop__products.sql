select
    product_id,
    lower(trim(product_category))   as product_category,
    list_price
from {{ source('shop', 'products') }}
