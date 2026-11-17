select
    customer_id,
    upper(left(trim(customer_city), 1))
        || lower(substr(trim(customer_city), 2))  as customer_city,
    lower(trim(customer_region))        as customer_region,
    lower(trim(acquisition_channel))    as acquisition_channel,
    cast(created_at as timestamp)       as created_at
from {{ source('shop', 'customers') }}
