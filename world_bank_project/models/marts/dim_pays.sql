-- models/marts/dim_pays.sql

select distinct
    countryiso3code,
    country_code,
    country_name

from {{ ref('stg_world_bank') }}

where type_entite = 'pays_ou_territoire'
  and countryiso3code is not null
  and country_name is not null