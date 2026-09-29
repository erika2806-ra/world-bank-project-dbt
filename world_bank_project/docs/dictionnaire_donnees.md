# Dictionnaire de données

Ce document décrit les principales tables utilisées dans le projet World Bank Project - Analyse du développement des pays

Les données proviennent de l'API de la Banque mondiale, sont stockées dans Google BigQuery et transformées avec dbt.

---

## Table `dim_pays`

Table de dimension contenant les informations permettant d'identifier et de caractériser les pays et territoires.

| Colonne | Type | Description | Exemple |
|---|---|---|---|
| `countryiso3code` | STRING | Code ISO à 3 caractères du pays ou territoire. Clé primaire utilisée pour relier la dimension à la table de faits. | `FRA` |
| `country_code` | STRING | Code pays à 2 caractères fourni par la Banque mondiale. | `FR` |
| `country_name` | STRING | Nom du pays ou territoire. | `France` |
| `region` | STRING | Région géographique à laquelle appartient le pays. | `Europe & Central Asia` |
| `income_level` | STRING | Catégorie de revenu associée au pays dans les données sources. | `High income` |

---

## Table `dim_date`

Table de dimension contenant les années disponibles dans les données.

| Colonne | Type | Description | Exemple |
|---|---|---|---|
| `annee` | INTEGER | Année de l'observation. Clé primaire utilisée pour relier la dimension à la table de faits. | `2023` |

---

## Table `dim_indicators`

Table de dimension contenant les informations descriptives des indicateurs de la Banque mondiale.

| Colonne | Type | Description | Exemple |
|---|---|---|---|
| `indicator_code` | STRING | Code unique de l'indicateur de la Banque mondiale. Clé primaire de la dimension. | `SP.POP.TOTL` |
| `indicator_name` | STRING | Nom original de l'indicateur fourni par la Banque mondiale. | `Population, total` |
| `indicator_label_fr` | STRING | Libellé simplifié en français utilisé pour l'analyse et la visualisation. | `Population` |
| `unit` | STRING | Unité associée à l'indicateur lorsqu'elle est disponible. | `null` |

### Principaux indicateurs

| Code | Libellé utilisé |
|---|---|
| `SE.ADT.LITR.ZS` | Alphabétisation adultes |
| `SL.UEM.TOTL.ZS` | Chômage |
| `NY.GDP.MKTP.KD.ZG` | Croissance PIB |
| `EG.ELC.ACCS.ZS` | Accès à l'électricité |
| `SP.DYN.LE00.IN` | Espérance de vie |
| `SH.XPD.CHEX.GD.ZS` | Dépenses de santé |
| `SP.DYN.CBRT.IN` | Taux de natalité |
| `FP.CPI.TOTL.ZG` | Inflation |
| `NY.GDP.PCAP.CD` | PIB par habitant |
| `SP.POP.TOTL` | Population |
| `SE.XPD.TOTL.GD.ZS` | Dépenses publiques d'éducation |
| `SE.PRM.CMPT.ZS` | Achèvement primaire |
| `SE.SEC.ENRR` | Scolarisation secondaire |
| `SE.TER.ENRR` | Scolarisation supérieure |
| `NY.GNP.PCAP.CD` | RNB par habitant - méthode Atlas |
| `NY.GDP.MKTP.CD` | PIB |
| `EN.GHG.CO2.PC.CE.AR5` | CO₂ par habitant |

---

## Table `fact_indicators`

Table de faits principale du modèle en étoile.

Une ligne représente une observation pour un pays, une année et un indicateur.

Granularité : 1 pays + 1 année + 1 indicateur.

| Colonne | Type | Description | Exemple |
|---|---|---|---|
| `countryiso3code` | STRING | Code ISO3 du pays. Clé étrangère vers `dim_pays`. | `FRA` |
| `annee` | INTEGER | Année de l'observation. Clé étrangère vers `dim_date`. | `2023` |
| `indicator_code` | STRING | Code de l'indicateur. Clé étrangère vers `dim_indicators`. | `SP.POP.TOTL` |
| `valeur_originale` | FLOAT | Valeur initiale de l'indicateur avant traitement. | `68170000` |
| `valeur` | FLOAT | Valeur de l'indicateur utilisée après les traitements de données. | `68170000` |
| `methode_traitement` | STRING | Méthode appliquée à la donnée lors de son traitement. | `non_disponible` |
| `est_imputee` | BOOLEAN | Indique si la valeur a été imputée lors du traitement des données. | `false` |
| `obs_status` | STRING | Statut de l'observation fourni par la source lorsqu'il est disponible. | `null` |
| `decimal_places` | INTEGER | Nombre de décimales associé à l'observation. | `1` |
| `inserted_at` | TIMESTAMP | Date et heure d'insertion de la donnée dans BigQuery. | `2026-09-03 14:55:29 UTC` |

---

## Table `predictions`

Table contenant les résultats du modèle de Machine Learning Random Forest.

Elle contient à la fois les résultats du test réalisé sur les données de 2022 et les prédictions de production réalisées à partir de 2023.

| Colonne | Type | Description | Exemple |
|---|---|---|---|
| `countryiso3code` | STRING | Code ISO3 du pays ou territoire concerné par la prédiction. | `FRA` |
| `country_name` | STRING | Nom du pays ou territoire. | `France` |
| `region` | STRING | Région géographique du pays. | `Europe & Central Asia` |
| `annee` | INTEGER | Année correspondant à la prédiction. | `2024` |
| `income_level` | STRING | Catégorie de revenu réelle lorsqu'elle est disponible. | `High income` |
| `income_level_predit` | STRING | Catégorie de revenu prédite par le modèle Random Forest. | `High income` |
| `type_prediction` | STRING | Indique s'il s'agit d'une prédiction issue du test ou de la production. | `Production` |
| `prediction_correcte` | STRING | Résultat de la comparaison entre la catégorie réelle et la catégorie prédite : `Juste`, `Faux` ou `En attente`. | `Juste` |
| `date_prediction` | TIMESTAMP | Date et heure auxquelles la prédiction a été calculée. | `2026-09-29 10:17:39 UTC` |

### Signification de `prediction_correcte`

- `Juste` : la catégorie prédite correspond à la catégorie réelle.
- `Faux` : la catégorie prédite est différente de la catégorie réelle.
- `En attente` : la prédiction a été réalisée mais la catégorie réelle n'est pas encore disponible, elle ne peut donc pas encore être évaluée.

---

## Relations entre les tables

Le modèle analytique principal est organisé selon un schéma en étoile :

- `dim_pays` → `fact_indicators` via `countryiso3code`
- `dim_date` → `fact_indicators` via `annee`
- `dim_indicators` → `fact_indicators` via `indicator_code`

Les relations entre les dimensions et la table de faits sont de type un-à-plusieurs (1:N).

La table `predictions` est utilisée séparément pour l'analyse des résultats du modèle de Machine Learning dans Power BI.