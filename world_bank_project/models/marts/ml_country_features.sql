-- models/marts/ml_country_features.sql
--
-- Dataset destiné au Machine Learning.
-- 1 ligne = 1 pays x 1 année.
-- Période étudiée : 2015 à 2022.
--
-- Les 10 features sont des indicateurs sociaux, éducatifs,
-- démographiques et environnementaux.
--
-- La cible income_level est reconstruite à partir du
-- RNB par habitant, méthode Atlas (NY.GNP.PCAP.CD),
-- avec les seuils historiques de la Banque mondiale.
--
-- Le RNB sert uniquement à construire la cible.
-- Il ne sera PAS utilisé comme feature du modèle ML.


with features_par_pays_annee as (

    select
        countryiso3code,
        annee,

        -- SOCIAL
        max(
            case
                when indicator_code = 'SP.DYN.LE00.IN'
                then valeur
            end
        ) as Esperance_vie,

        max(
            case
                when indicator_code = 'SL.UEM.TOTL.ZS'
                then valeur
            end
        ) as Chomage,

        max(
            case
                when indicator_code = 'SH.XPD.CHEX.GD.ZS'
                then valeur
            end
        ) as Depense_de_sante,


        -- EDUCATION
        max(
            case
                when indicator_code = 'SE.PRM.CMPT.ZS'
                then valeur
            end
        ) as Achevement_primaire,

        max(
            case
                when indicator_code = 'SE.SEC.ENRR'
                then valeur
            end
        ) as Scolarisation_secondaire,

        max(
            case
                when indicator_code = 'SE.TER.ENRR'
                then valeur
            end
        ) as Scolarisation_superieur,

        max(
            case
                when indicator_code = 'SE.XPD.TOTL.GD.ZS'
                then valeur
            end
        ) as Depense_publique_education,


        -- DEMOGRAPHIE
        max(
            case
                when indicator_code = 'SP.DYN.CBRT.IN'
                then valeur
            end
        ) as Taux_natalite,


        -- ENVIRONNEMENT / INFRASTRUCTURE
        max(
            case
                when indicator_code = 'EN.GHG.CO2.PC.CE.AR5'
                then valeur
            end
        ) as CO2_par_habitant,

        max(
            case
                when indicator_code = 'EG.ELC.ACCS.ZS'
                then valeur
            end
        ) as Acces_electricite,


        -- RNB Atlas :
        -- utilisé uniquement pour construire la cible
        max(
            case
                when indicator_code = 'NY.GNP.PCAP.CD'
                then valeur
            end
        ) as RNB_par_habitant_Atlas

    from {{ ref('fact_indicators') }}

    where annee between 2015 and 2022

    group by
        countryiso3code,
        annee

),


avec_informations_pays as (

    select
        f.*,
        p.country_name,
        p.region

    from features_par_pays_annee as f

    inner join {{ ref('dim_pays') }} as p
        on f.countryiso3code = p.countryiso3code

),


avec_income_level as (

    select
        *,

        case

            -- ==========================================
            -- RNB 2015 -> classification publiée en 2016
            -- ==========================================
            when annee = 2015 then
                case
                    when RNB_par_habitant_Atlas <= 1025
                        then 'Low income'
                    when RNB_par_habitant_Atlas <= 4035
                        then 'Lower middle income'
                    when RNB_par_habitant_Atlas <= 12475
                        then 'Upper middle income'
                    else 'High income'
                end


            -- ==========================================
            -- RNB 2016 -> classification publiée en 2017
            -- ==========================================
            when annee = 2016 then
                case
                    when RNB_par_habitant_Atlas <= 1005
                        then 'Low income'
                    when RNB_par_habitant_Atlas <= 3955
                        then 'Lower middle income'
                    when RNB_par_habitant_Atlas <= 12235
                        then 'Upper middle income'
                    else 'High income'
                end


            -- ==========================================
            -- RNB 2017 -> classification publiée en 2018
            -- ==========================================
            when annee = 2017 then
                case
                    when RNB_par_habitant_Atlas <= 995
                        then 'Low income'
                    when RNB_par_habitant_Atlas <= 3895
                        then 'Lower middle income'
                    when RNB_par_habitant_Atlas <= 12055
                        then 'Upper middle income'
                    else 'High income'
                end


            -- ==========================================
            -- RNB 2018 -> classification publiée en 2019
            -- ==========================================
            when annee = 2018 then
                case
                    when RNB_par_habitant_Atlas <= 1025
                        then 'Low income'
                    when RNB_par_habitant_Atlas <= 3995
                        then 'Lower middle income'
                    when RNB_par_habitant_Atlas <= 12375
                        then 'Upper middle income'
                    else 'High income'
                end


            -- ==========================================
            -- RNB 2019 -> classification publiée en 2020
            -- ==========================================
            when annee = 2019 then
                case
                    when RNB_par_habitant_Atlas <= 1035
                        then 'Low income'
                    when RNB_par_habitant_Atlas <= 4045
                        then 'Lower middle income'
                    when RNB_par_habitant_Atlas <= 12535
                        then 'Upper middle income'
                    else 'High income'
                end


            -- ==========================================
            -- RNB 2020 -> classification publiée en 2021
            -- ==========================================
            when annee = 2020 then
                case
                    when RNB_par_habitant_Atlas <= 1045
                        then 'Low income'
                    when RNB_par_habitant_Atlas <= 4095
                        then 'Lower middle income'
                    when RNB_par_habitant_Atlas <= 12695
                        then 'Upper middle income'
                    else 'High income'
                end


            -- ==========================================
            -- RNB 2021 -> classification publiée en 2022
            -- ==========================================
            when annee = 2021 then
                case
                    when RNB_par_habitant_Atlas <= 1085
                        then 'Low income'
                    when RNB_par_habitant_Atlas <= 4255
                        then 'Lower middle income'
                    when RNB_par_habitant_Atlas <= 13205
                        then 'Upper middle income'
                    else 'High income'
                end


            -- ==========================================
            -- RNB 2022 -> classification publiée en 2023
            -- ==========================================
            when annee = 2022 then
                case
                    when RNB_par_habitant_Atlas <= 1135
                        then 'Low income'
                    when RNB_par_habitant_Atlas <= 4465
                        then 'Lower middle income'
                    when RNB_par_habitant_Atlas <= 13845
                        then 'Upper middle income'
                    else 'High income'
                end

        end as income_level

    from avec_informations_pays

    -- Pas d'imputation de la cible :
    -- sans RNB Atlas, on ne peut pas déterminer income_level.
    where RNB_par_habitant_Atlas is not null

)


select

    countryiso3code,
    country_name,
    region,
    annee,

    Esperance_vie,
    Chomage,
    Depense_de_sante,

    Achevement_primaire,
    Scolarisation_secondaire,
    Scolarisation_superieur,
    Depense_publique_education,

    Taux_natalite,

    CO2_par_habitant,
    Acces_electricite,

    income_level

from avec_income_level