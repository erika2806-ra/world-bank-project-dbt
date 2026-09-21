import os
from datetime import datetime, timezone
from pathlib import Path

import joblib
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

# Table de features propre créée par dbt
FEATURES_TABLE = (
    f"{PROJECT_ID}.marts.ml_country_features"
)

# Table qui recevra les prédictions
PREDICTIONS_TABLE = (
    f"{PROJECT_ID}.ml.predictions"
)

# Pipeline final entraîné
PIPELINE_PATH = Path(__file__).with_name(
    "pipeline.pkl"
)


# --------------------------------------------------
# 2. Features utilisées par le modèle
# --------------------------------------------------

FEATURES = [
    "Esperance_vie",
    "Chomage",
    "Depense_de_sante",
    "Achevement_primaire",
    "Scolarisation_secondaire",
    "Scolarisation_superieur",
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
    # 4. Lire la table de features propre
    # --------------------------------------------------

    query = f"""
        SELECT *
        FROM `{FEATURES_TABLE}`
        ORDER BY
            annee,
            countryiso3code
    """

    df = client.query(
        query
    ).to_dataframe()


    print(
        "Données chargées depuis BigQuery."
    )

    print(
        "Nombre de lignes à prédire :",
        len(df)
    )


    # --------------------------------------------------
    # 5. Charger le pipeline final
    # --------------------------------------------------

    pipeline = joblib.load(
        PIPELINE_PATH
    )

    print(
        "Pipeline final chargé."
    )


    # --------------------------------------------------
    # 6. Faire les prédictions
    # --------------------------------------------------

    df["income_level_predit"] = pipeline.predict(
        df[FEATURES]
    )

    df["date_prediction"] = datetime.now(
        timezone.utc
    )

    print(
        "Prédictions réalisées."
    )


    # --------------------------------------------------
    # 7. Préparer la table de sortie
    # --------------------------------------------------

    predictions = df[
        [
            "countryiso3code",
            "country_name",
            "region",
            "annee",
            "income_level",
            "income_level_predit",
            "date_prediction",
        ]
    ].copy()


    # --------------------------------------------------
    # 8. Remplacer la table ml.predictions
    #
    # WRITE_TRUNCATE :
    # les anciennes prédictions sont supprimées
    # et remplacées par les nouvelles.
    # --------------------------------------------------

    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE"
    )


    client.load_table_from_dataframe(
        predictions,
        PREDICTIONS_TABLE,
        job_config=job_config,
    ).result()


    print(
        f"{len(predictions)} prédictions enregistrées "
        f"dans {PREDICTIONS_TABLE}"
    )

    print(
        "Les anciennes prédictions ont été remplacées."
    )


# --------------------------------------------------
# 9. Lancer le script
# --------------------------------------------------

if __name__ == "__main__":
    predire()