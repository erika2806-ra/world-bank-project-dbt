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


# Connexion à BigQuery
client = bigquery.Client()


# Créer le dataset BigQuery "ml"
dataset = bigquery.Dataset(f"{PROJECT_ID}.ml")

# Même localisation que le dataset marts
dataset.location = "US"

# Créer le dataset s'il n'existe pas déjà
client.create_dataset(dataset, exists_ok=True)

print("Dataset BigQuery 'ml' prêt.")