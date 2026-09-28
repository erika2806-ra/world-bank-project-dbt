import os
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd
from dotenv import load_dotenv
from google.cloud import bigquery


# --------------------------------------------------
# 1. Configuration
# --------------------------------------------------

load_dotenv()

credentials_path = os.getenv(
    "GOOGLE_APPLICATION_CREDENTIALS"
)

if credentials_path:
    os.environ[
        "GOOGLE_APPLICATION_CREDENTIALS"
    ] = credentials_path


PROJECT_ID = "data-quest-erika"

# Table propre créée par dbt
FEATURES_TABLE = (
    f"{PROJECT_ID}.marts.ml_country_features"
)

# Une seule table pour Power BI :
# test 2022 + prédictions de production 2023+
PREDICTIONS_TABLE = (
    f"{PROJECT_ID}.ml.predictions"
)

# Modèle final entraîné sur 2015-2022
PIPELINE_PATH = Path(__file__).with_name(
    "pipeline.pkl"
)


# --------------------------------------------------
# 2. Les 7 features utilisées par le modèle
# --------------------------------------------------

FEATURES = [
    "Esperance_vie",
    "Depense_de_sante",
    "Scolarisation_secondaire",
    "Depense_publique_education",
    "Taux_natalite",
    "CO2_par_habitant",
    "Acces_electricite",
]


# --------------------------------------------------
# 3. Fonction principale
# --------------------------------------------------

def predire():

    # Connexion à BigQuery
    client = bigquery.Client()


    # --------------------------------------------------
    # 4. Lire uniquement les années de production
    #
    # 2015-2021 = entraînement
    # 2022      = test
    # 2023+     = prédictions de production
    # --------------------------------------------------

    query = f"""
        SELECT *
        FROM `{FEATURES_TABLE}`
        WHERE annee >= 2023
        ORDER BY
            annee,
            countryiso3code
    """

    df = client.query(
        query
    ).to_dataframe()


    print(
        "Données de production chargées depuis BigQuery."
    )

    print(
        "Nombre de lignes à prédire :",
        len(df)
    )


    # --------------------------------------------------
    # 5. Vérifier s'il existe des données à prédire
    # --------------------------------------------------

    if df.empty:

        print(
            "Aucune donnée 2023 ou plus récente "
            "à prédire."
        )

        return


    # --------------------------------------------------
    # 6. Charger le pipeline final
    # --------------------------------------------------

    pipeline = joblib.load(
        PIPELINE_PATH
    )

    print(
        "Pipeline final chargé."
    )


    # --------------------------------------------------
    # 7. Faire les prédictions
    # --------------------------------------------------

    df["income_level_predit"] = pipeline.predict(
        df[FEATURES]
    )

    df["type_prediction"] = "Production"


    # --------------------------------------------------
    # 8. Comparer classe réelle et classe prédite
    #
    # Si income_level est NULL :
    # la vraie classe n'est pas encore disponible.
    # --------------------------------------------------

    

    def comparer_prediction(row):

        valeur_reelle = row["income_level"]

        # Valeur manquante : None, NaN ou <NA>
        if (
            valeur_reelle is None
            or valeur_reelle != valeur_reelle
            or str(valeur_reelle) == "<NA>"
        ):
            return "En attente"

        if row["income_level_predit"] == valeur_reelle:
            return "Juste"

        return "Faux"

    df["prediction_correcte"] = df.apply(
        comparer_prediction,
        axis=1
    )


    # --------------------------------------------------
    # 9. Date de la prédiction
    # --------------------------------------------------

    df["date_prediction"] = datetime.now(
        timezone.utc
    )


    # --------------------------------------------------
    # 10. Préparer les résultats
    # --------------------------------------------------

    predictions_production = df[
        [
            "countryiso3code",
            "country_name",
            "region",
            "annee",
            "income_level",
            "income_level_predit",
            "type_prediction",
            "prediction_correcte",
            "date_prediction",
        ]
    ].copy()


    # --------------------------------------------------
    # 11. Récupérer le test 2022 déjà présent
    #
    # Le test a été créé une seule fois par
    # entrainer_modele.py.
    # --------------------------------------------------

    query_test = f"""
        SELECT *
        FROM `{PREDICTIONS_TABLE}`
        WHERE type_prediction = 'Test'
    """

    predictions_test = client.query(
        query_test
    ).to_dataframe()


    print(
        "Nombre de prédictions de test 2022 conservées :",
        len(predictions_test)
    )


    # --------------------------------------------------
    # 12. Combiner :
    #
    # test 2022
    # +
    # production 2023+
    #
    # Cela évite de recalculer le test 2022.
    # --------------------------------------------------

    predictions_finales = predictions_test[
        [
            "countryiso3code",
            "country_name",
            "region",
            "annee",
            "income_level",
            "income_level_predit",
            "type_prediction",
            "prediction_correcte",
            "date_prediction",
        ]
    ].copy()

    
    predictions_finales = pd.concat(
        [
            predictions_finales,
            predictions_production
        ],
        ignore_index=True
    )

    # --------------------------------------------------
    # 13. Remplacer ml.predictions
    #
    # WRITE_TRUNCATE :
    # la table finale contient toujours :
    #
    # - le test 2022 conservé
    # - les dernières prédictions 2023+
    #
    # Pas de doublons entre les exécutions quotidiennes.
    # --------------------------------------------------

    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE"
    )


    client.load_table_from_dataframe(
        predictions_finales,
        PREDICTIONS_TABLE,
        job_config=job_config,
    ).result()


    print(
        f"{len(predictions_finales)} lignes enregistrées "
        f"dans {PREDICTIONS_TABLE}"
    )

    print(
        "Test 2022 conservé et prédictions "
        "2023+ actualisées."
    )


# --------------------------------------------------
# 14. Lancer le script
# --------------------------------------------------

if __name__ == "__main__":
    predire()