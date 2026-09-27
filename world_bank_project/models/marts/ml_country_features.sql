-- models/marts/ml_country_features.sql
--
-- Dataset propre destiné au Machine Learning.
-- 1 ligne = 1 pays x 1 année.
--
-- Les 7 features utilisées par le modèle sont des indicateurs
-- sociaux, éducatifs, démographiques et environnementaux.
--
-- La cible income_level est reconstruite à partir du
-- RNB par habitant, méthode Atlas (NY.GNP.PCAP.CD),
-- avec les seuils historiques de la Banque mondiale.
--
-- IMPORTANT :
-- Le RNB sert uniquement à construire la classe réelle.
-- Il n'est PAS utilisé comme feature du modèle ML.
--
-- 2015-2021 : entraînement du modèle d'évaluation
-- 2022      : test
-- 2023+     : nouvelles données destinées aux prédictions


with features_par_pays_annee as (

    select
        countryiso3code,
        annee,

        -- ==========================================
        -- SOCIAL / SANTE
        -- ==========================================

        max(
            case
                when indicator_code = 'SP.DYN.LE00.IN'
                then valeur
            end
        ) as Esperance_vie,

        max(
            case
                when indicator_code = 'SH.XPD.CHEX.GD.ZS'
                then valeur
            end
        ) as Depense_de_sante,


        -- ==========================================
        -- EDUCATION
        -- ==========================================

        max(
            case
                when indicator_code = 'SE.SEC.ENRR'
                then valeur
            end
        ) as Scolarisation_secondaire,

        max(
            case
                when indicator_code = 'SE.XPD.TOTL.GD.ZS'
                then valeur
            end
        ) as Depense_publique_education,


        -- ==========================================
        -- DEMOGRAPHIE
        -- ==========================================

        max(
            case
                when indicator_code = 'SP.DYN.CBRT.IN'
                then valeur
            end
        ) as Taux_natalite,


        -- ==========================================
        -- ENVIRONNEMENT / INFRASTRUCTURE
        -- ==========================================

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


        -- ==========================================
        -- RNB PAR HABITANT - METHODE ATLAS
        --
        -- Sert UNIQUEMENT à construire la vraie classe.
        -- Il ne sera jamais transmis au modèle comme feature.
        -- ==========================================

        max(
            case
                when indicator_code = 'NY.GNP.PCAP.CD'
                then valeur
            end
        ) as RNB_par_habitant_Atlas

    from {{ ref('fact_indicators') }}

    -- On ne bloque plus à 2022.
    -- Les nouvelles années pourront donc apparaître
    -- automatiquement après l'actualisation des données.
    where annee >= 2015

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
            -- RNB 2015
            -- ==========================================

            when annee = 2015
                 and RNB_par_habitant_Atlas is not null then
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
            -- RNB 2016
            -- ==========================================

            when annee = 2016
                 and RNB_par_habitant_Atlas is not null then
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
            -- RNB 2017
            -- ==========================================

            when annee = 2017
                 and RNB_par_habitant_Atlas is not null then
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
            -- RNB 2018
            -- ==========================================

            when annee = 2018
                 and RNB_par_habitant_Atlas is not null then
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
            -- RNB 2019
            -- ==========================================

            when annee = 2019
                 and RNB_par_habitant_Atlas is not null then
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
            -- RNB 2020
            -- ==========================================

            when annee = 2020
                 and RNB_par_habitant_Atlas is not null then
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
            -- RNB 2021
            -- ==========================================

            when annee = 2021
                 and RNB_par_habitant_Atlas is not null then
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
            -- RNB 2022
            -- ==========================================

            when annee = 2022
                 and RNB_par_habitant_Atlas is not null then
                case
                    when RNB_par_habitant_Atlas <= 1135
                        then 'Low income'
                    when RNB_par_habitant_Atlas <= 4465
                        then 'Lower middle income'
                    when RNB_par_habitant_Atlas <= 13845
                        then 'Upper middle income'
                    else 'High income'
                end


            -- ==========================================
            -- RNB 2023
            -- ==========================================

            when annee = 2023
                 and RNB_par_habitant_Atlas is not null then
                case
                    when RNB_par_habitant_Atlas <= 1145
                        then 'Low income'
                    when RNB_par_habitant_Atlas <= 4515
                        then 'Lower middle income'
                    when RNB_par_habitant_Atlas <= 14005
                        then 'Upper middle income'
                    else 'High income'
                end


            -- ==========================================
            -- RNB 2024
            -- Classification FY2026
            -- ==========================================

            when annee = 2024
                 and RNB_par_habitant_Atlas is not null then
                case
                    when RNB_par_habitant_Atlas <= 1135
                        then 'Low income'
                    when RNB_par_habitant_Atlas <= 4495
                        then 'Lower middle income'
                    when RNB_par_habitant_Atlas <= 13935
                        then 'Upper middle income'
                    else 'High income'
                end


            -- ==========================================
            -- RNB 2025
            -- Classification FY2027
            -- ==========================================

            when annee = 2025
                 and RNB_par_habitant_Atlas is not null then
                case
                    when RNB_par_habitant_Atlas <= 1175
                        then 'Low income'
                    when RNB_par_habitant_Atlas <= 4635
                        then 'Lower middle income'
                    when RNB_par_habitant_Atlas <= 14375
                        then 'Upper middle income'
                    else 'High income'
                end


            -- ==========================================
            -- 2026 ET ANNEES SUIVANTES
            --
            -- La ligne reste disponible pour la prédiction,
            -- mais la vraie classe reste NULL tant que les
            -- seuils officiels correspondant à cette année
            -- ne sont pas disponibles dans ce modèle dbt.
            -- ==========================================

            else null

        end as income_level

    from avec_informations_pays

)


select

    countryiso3code,
    country_name,
    region,
    annee,

    -- 7 FEATURES DU MODELE

    Esperance_vie,
    Depense_de_sante,

    Scolarisation_secondaire,
    Depense_publique_education,

    Taux_natalite,

    CO2_par_habitant,
    Acces_electricite,

    -- Classe réelle.
    -- Peut être NULL pour les nouvelles années.
    income_level

from avec_income_level