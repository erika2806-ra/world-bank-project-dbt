-- models/marts/dim_date.sql

select distinct
    annee

from {{ ref('stg_world_bank') }}

where annee is not null