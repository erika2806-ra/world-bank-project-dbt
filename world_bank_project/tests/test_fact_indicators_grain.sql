-- Ce test doit retourner 0 ligne.

select
    countryiso3code,
    annee,
    indicator_code,
    count(*) as nombre_lignes

from {{ ref('fact_indicators') }}

group by
    countryiso3code,
    annee,
    indicator_code

having count(*) > 1