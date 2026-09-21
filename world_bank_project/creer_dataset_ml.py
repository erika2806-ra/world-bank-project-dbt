
import os
from dotenv import load_dotenv
from google.cloud import bigquery

# Charger les variables du fichier .env
load_dotenv()

# Utiliser la même clé BigQuery que le reste du projet
credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

if credentials_path:
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path

# Projet Google Cloud
PROJECT_ID = "data-quest-erika"

# Table créée avec dbt
TABLE_ID = f"{PROJECT_ID}.marts.ml_country_features"


def creer_dataset_ml():
    """Charge le dataset destiné au Machine Learning depuis BigQuery."""

    # Connexion à BigQuery
    client = bigquery.Client()

    # Requête SQL
    query = f"""
        SELECT *
        FROM `{TABLE_ID}`
        ORDER BY countryiso3code, annee
    """

    # Chargement dans un DataFrame pandas
    df = client.query(query).to_dataframe()

    # Vérifications
    print("Dataset ML chargé depuis BigQuery.")
    print("Nombre de lignes :", len(df))
    print("Nombre de colonnes :", len(df.columns))

    print("\nColonnes :")
    print(df.columns.tolist())

    print("\nRépartition de income_level :")
    print(df["income_level"].value_counts())

    print("\nValeurs manquantes :")
    print(df.isna().sum())

    return df


if __name__ == "__main__":
    df = creer_dataset_ml()