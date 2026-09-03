-- models/marts/fact_indicators.sql

with base as (

    select *
    from {{ ref('stg_world_bank') }}

    where type_entite = 'pays_ou_territoire'
      and countryiso3code is not null

),
neighbors as (

    select
        *,

        last_value(
            if(valeur is not null, valeur, null)
            ignore nulls
        ) over (
            partition by countryiso3code, indicator_code
            order by annee
            rows between unbounded preceding and 1 preceding
        ) as previous_value,

        last_value(
            if(valeur is not null, annee, null)
            ignore nulls
        ) over (
            partition by countryiso3code, indicator_code
            order by annee
            rows between unbounded preceding and 1 preceding
        ) as previous_year,

        first_value(
            if(valeur is not null, valeur, null)
            ignore nulls
        ) over (
            partition by countryiso3code, indicator_code
            order by annee
            rows between 1 following and unbounded following
        ) as next_value,

        first_value(
            if(valeur is not null, annee, null)
            ignore nulls
        ) over (
            partition by countryiso3code, indicator_code
            order by annee
            rows between 1 following and unbounded following
        ) as next_year,

        percentile_cont(valeur, 0.5) over (
            partition by countryiso3code, indicator_code
        ) as mediane_pays

    from base

),

treated as (

    select
        countryiso3code,
        annee,
        indicator_code,

        valeur as valeur_originale,

        case

            -- Niveau 1 : interpolation temporelle
            when valeur is null
                 and indicator_code in (
                     'SP.POP.TOTL',
                     'SP.DYN.LE00.IN',
                     'SP.DYN.CBRT.IN'
                 )
                 and previous_value is not null
                 and next_value is not null
                 and previous_year is not null
                 and next_year is not null
                 and next_year > previous_year
            then
                previous_value
                + (
                    (next_value - previous_value)
                    * safe_divide(
                        annee - previous_year,
                        next_year - previous_year
                    )
                )

            -- Niveau 2 : médiane du pays
            when valeur is null
                 and indicator_code in (
                     'NY.GDP.MKTP.CD',
                     'NY.GDP.PCAP.CD'
                 )
            then mediane_pays

            -- Niveau 3 : NULL conservé
            else valeur

        end as valeur,

        case

            when valeur is not null
            then 'originale'

            when indicator_code in (
                'SP.POP.TOTL',
                'SP.DYN.LE00.IN',
                'SP.DYN.CBRT.IN'
            )
            and previous_value is not null
            and next_value is not null
            then 'interpolation_temporelle'

            when indicator_code in (
                'NY.GDP.MKTP.CD',
                'NY.GDP.PCAP.CD'
            )
            and mediane_pays is not null
            then 'mediane_pays'

            else 'non_disponible'

        end as methode_traitement,

        obs_status,
        decimal_places,
        inserted_at

    from neighbors

)

select
    countryiso3code,
    annee,
    indicator_code,

    valeur_originale,

    case
        when indicator_code = 'SP.POP.TOTL'
             and methode_traitement = 'interpolation_temporelle'
        then round(valeur)

        else valeur
    end as valeur,

    methode_traitement,

    case
        when methode_traitement in (
            'interpolation_temporelle',
            'mediane_pays'
        )
        then true

        else false
    end as est_imputee,

    obs_status,
    decimal_places,
    inserted_at

from treated