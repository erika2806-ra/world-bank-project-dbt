-- models/staging/stg_world_bank.sql

with source as (

    select
        indicator,
        country,
        countryiso3code,
        date,
        value,
        unit,
        obs_status,
        decimal,
        row_hash,
        inserted_at

    from {{ source('world_bank', 'raw_data') }}

),

country_metadata as (

    select
        countryiso3code,
        region,
        income_level,
        type_entite

    from {{ source('world_bank', 'country_metadata') }}

),

renamed as (

    select
        indicator.id as indicator_code,
        indicator.value as indicator_name,

        country.id as country_code,
        country.value as country_name,

        nullif(trim(countryiso3code), '') as countryiso3code,

        safe_cast(date as int64) as annee,
        safe_cast(value as float64) as valeur,

        nullif(trim(unit), '') as unit,
        nullif(trim(obs_status), '') as obs_status,
        safe_cast(decimal as int64) as decimal_places,

        row_hash,
        inserted_at

    from source

),


classified as (

    select
        r.*,

        m.region,
        m.income_level,

        case
            when m.type_entite is not null
                then m.type_entite
            when r.countryiso3code is null
                then 'agregat'
            else 'inconnu'
        end as type_entite

    from renamed as r

    left join country_metadata as m
        on r.countryiso3code = m.countryiso3code

),


ranked as (

    select
        *,

        row_number() over (
            partition by
                country_name,
                annee,
                indicator_code
            order by
                inserted_at desc,
                row_hash desc
        ) as version_rank

    from classified

    where annee is not null

)

select
    indicator_code,
    indicator_name,
    country_code,
    country_name,
    countryiso3code,
    region,
    income_level,
    type_entite,
    annee,
    valeur,
    unit,
    obs_status,
    decimal_places,
    row_hash,
    inserted_at

from ranked

where version_rank = 1