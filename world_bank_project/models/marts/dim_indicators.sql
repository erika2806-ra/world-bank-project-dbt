-- models/marts/dim_indicators.sql

select
    indicator_code,

    any_value(indicator_name) as indicator_name,

    case indicator_code
        when 'NY.GDP.MKTP.CD' then 'PIB'
        when 'NY.GDP.PCAP.CD' then 'PIB_par_habitant'
        when 'NY.GNP.PCAP.CD' then 'RNB_par_habitant_Atlas'
        when 'NY.GDP.MKTP.KD.ZG' then 'Croissance_PIB'
        when 'SP.POP.TOTL' then 'Population'
        when 'SP.DYN.LE00.IN' then 'Esperance_vie'
        when 'SL.UEM.TOTL.ZS' then 'Chomage'
        when 'FP.CPI.TOTL.ZG' then 'Inflation'
        when 'EG.ELC.ACCS.ZS' then 'Acces_electricite'
        when 'EN.GHG.CO2.PC.CE.AR5' then 'CO2_par_habitant'
        when 'SP.DYN.CBRT.IN' then 'Taux_natalite'
        when 'SE.SEC.ENRR' then 'Scolarisation_secondaire'
        when 'SE.TER.ENRR' then 'Scolarisation_superieur'
        when 'SE.PRM.CMPT.ZS' then 'Achevement_primaire'
        when 'SH.XPD.CHEX.GD.ZS' then 'Depense_de_sante'
        when 'SE.XPD.TOTL.GD.ZS' then 'Depense_publique_education'
        when 'SE.ADT.LITR.ZS' then 'Alphabetisation_adultes'
        else any_value(indicator_name)
    end as indicator_label_fr,

    any_value(unit) as unit

from {{ ref('stg_world_bank') }}

where indicator_code is not null

group by indicator_code