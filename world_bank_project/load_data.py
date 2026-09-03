# load_data.py

import hashlib
import json
import time
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv
from google.api_core.exceptions import NotFound
from google.cloud import bigquery


# Charge GOOGLE_APPLICATION_CREDENTIALS depuis .env
load_dotenv()


# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------

INDICATORS = {
    "NY.GDP.MKTP.CD": "PIB",
    "NY.GDP.PCAP.CD": "PIB_par_habitant",
    "NY.GDP.MKTP.KD.ZG": "Croissance_PIB",
    "SP.POP.TOTL": "Population",
    "SP.DYN.LE00.IN": "Esperance_vie",
    "SL.UEM.TOTL.ZS": "Chomage",
    "FP.CPI.TOTL.ZG": "Inflation",
    "EG.ELC.ACCS.ZS": "Acces_electricite",
    "EN.GHG.CO2.PC.CE.AR5": "CO2_par_habitant",
    "SP.DYN.CBRT.IN": "Taux_natalite",
    "SE.SEC.ENRR": "Scolarisation_secondaire",
    "SE.TER.ENRR": "Scolarisation_superieur",
    "SE.PRM.CMPT.ZS": "Achevement_primaire",
    "SH.XPD.CHEX.GD.ZS": "Depense_de_sante",
    "SE.XPD.TOTL.GD.ZS": "Depense_publique_education",
    "SE.ADT.LITR.ZS": "Alphabetisation_adultes",
}

PROJECT_ID = "data-quest-erika"
DATASET_ID = "world_bank_raw"
TABLE_ID = "raw_data"

FULL_TABLE_ID = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"

# Nombre maximum de hash récents récupérés depuis BigQuery.
# À ajuster si le volume du projet devient beaucoup plus important.
HASH_LOOKBACK_LIMIT = 500000


# ---------------------------------------------------------
# SCHÉMA DE LA TABLE RAW
# ---------------------------------------------------------

RAW_SCHEMA = [
    bigquery.SchemaField(
        "indicator",
        "RECORD",
        fields=[
            bigquery.SchemaField("id", "STRING"),
            bigquery.SchemaField("value", "STRING"),
        ],
    ),
    bigquery.SchemaField(
        "country",
        "RECORD",
        fields=[
            bigquery.SchemaField("id", "STRING"),
            bigquery.SchemaField("value", "STRING"),
        ],
    ),
    bigquery.SchemaField("countryiso3code", "STRING"),
    bigquery.SchemaField("date", "STRING"),
    bigquery.SchemaField("value", "FLOAT64"),
    bigquery.SchemaField("unit", "STRING"),
    bigquery.SchemaField("obs_status", "STRING"),
    bigquery.SchemaField("decimal", "INTEGER"),
    bigquery.SchemaField("row_hash", "STRING"),
    bigquery.SchemaField("inserted_at", "TIMESTAMP"),
]


# ---------------------------------------------------------
# HASH
# ---------------------------------------------------------

def calculer_hash(row):
    """
    Calcule un hash SHA-256 à partir de la ligne brute
    telle qu'elle est renvoyée par l'API.

    inserted_at n'est pas inclus dans le hash.
    """

    contenu = json.dumps(
        row,
        sort_keys=True,
        default=str,
        ensure_ascii=False,
    )

    return hashlib.sha256(
        contenu.encode("utf-8")
    ).hexdigest()


# ---------------------------------------------------------
# APPEL D'UNE PAGE DE L'API
# ---------------------------------------------------------

def recuperer_page(code, page):
    """
    Récupère une page de données pour un indicateur World Bank.
    """

    url = (
        "https://api.worldbank.org/v2/"
        f"country/all/indicator/{code}"
    )

    params = {
        "format": "json",
        "per_page": 20000,
        "page": page,
    }

    response = requests.get(
        url,
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    try:
        data = response.json()
    except requests.exceptions.JSONDecodeError as e:
        raise ValueError(
            f"Réponse non JSON pour l'indicateur {code}"
        ) from e

    if (
        not isinstance(data, list)
        or len(data) < 2
        or not isinstance(data[0], dict)
        or data[1] is None
    ):
        raise ValueError(
            f"Structure de réponse inattendue pour {code}"
        )

    return data[0], data[1]


# ---------------------------------------------------------
# RÉCUPÉRATION DES DONNÉES WORLD BANK
# ---------------------------------------------------------

def recuperer_donnees_world_bank():
    """
    Récupère les données World Bank dans leur format long.

    Une ligne correspond à :
    pays + année + indicateur.
    """

    lignes = []

    for code, nom in INDICATORS.items():

        print(
            f"\n🔎 Récupération : {nom} ({code})"
        )

        try:
            metadata, premiere_page = recuperer_page(
                code,
                page=1,
            )

        except requests.RequestException as e:
            print(
                f"❌ Erreur HTTP pour {code} : {e}"
            )
            continue

        except ValueError as e:
            print(f"❌ {e}")
            continue

        total = int(
            metadata.get("total", len(premiere_page))
        )

        pages = int(
            metadata.get("pages", 1)
        )

        print(
            f"✅ {total} lignes disponibles "
            f"sur {pages} page(s)"
        )

        lignes_indicateur = list(premiere_page)

        # Pagination si nécessaire
        for page in range(2, pages + 1):

            try:
                _, donnees_page = recuperer_page(
                    code,
                    page,
                )

                lignes_indicateur.extend(
                    donnees_page
                )

            except (
                requests.RequestException,
                ValueError,
            ) as e:

                raise RuntimeError(
                    f"Échec lors de la récupération "
                    f"de la page {page}/{pages} "
                    f"pour {code}"
                ) from e

        print(
            f"📥 {len(lignes_indicateur)} "
            f"lignes réellement récupérées"
        )

        if len(lignes_indicateur) != total:
            print(
                "⚠️ Attention : le nombre de lignes "
                "récupérées diffère du total annoncé "
                "par l'API."
            )

        lignes.extend(lignes_indicateur)

        # Petite pause entre deux indicateurs
        time.sleep(0.5)

    if not lignes:
        raise ValueError(
            "Aucune donnée n'a été récupérée "
            "depuis l'API World Bank."
        )

    print(
        f"\n📊 Nombre total de lignes RAW : "
        f"{len(lignes)}"
    )

    return lignes


# ---------------------------------------------------------
# RÉCUPÉRATION DES HASH DÉJÀ PRÉSENTS
# ---------------------------------------------------------

def recuperer_hash_existants(client):
    """
    Récupère les hash les plus récents déjà présents
    dans BigQuery.
    """

    try:
        client.get_table(FULL_TABLE_ID)

        print(
            f"✅ Table trouvée : {FULL_TABLE_ID}"
        )

    except NotFound:

        print(
            "ℹ️ La table n'existe pas encore. "
            "Elle sera créée."
        )

        return set()

    query = f"""
        SELECT row_hash
        FROM `{FULL_TABLE_ID}`
        WHERE row_hash IS NOT NULL
        ORDER BY inserted_at DESC
        LIMIT {HASH_LOOKBACK_LIMIT}
    """

    resultats = client.query(query).result()

    hashes = {
        row.row_hash
        for row in resultats
    }

    print(
        f"🔎 Hash récents vérifiés : "
        f"{len(hashes)}"
    )

    return hashes


# ---------------------------------------------------------
# INGESTION BIGQUERY
# ---------------------------------------------------------

def ingest_data():
    """
    Récupère les données World Bank et charge
    uniquement les nouvelles lignes dans BigQuery.
    """

    print(
        "\n=== INGESTION WORLD BANK → BIGQUERY ==="
    )

    # 1. Récupération API
    lignes_api = recuperer_donnees_world_bank()

    # Pas de project=PROJECT_ID :
    # le projet est déjà connu grâce aux credentials.
    client = bigquery.Client()

    # 2. Récupération des hash déjà présents
    existing_hashes = recuperer_hash_existants(
        client
    )

    # 3. Timestamp commun au chargement
    inserted_at = datetime.now(
        timezone.utc
    ).isoformat()

    nouvelles_lignes = []

    # 4. Calcul du hash ligne par ligne
    for ligne in lignes_api:

        # Copie de la réponse brute
        ligne_raw = dict(ligne)

        row_hash = calculer_hash(
            ligne_raw
        )

        # Ligne déjà présente : on ne la recharge pas
        if row_hash in existing_hashes:
            continue

        ligne_raw["row_hash"] = row_hash
        ligne_raw["inserted_at"] = inserted_at

        nouvelles_lignes.append(
            ligne_raw
        )

    print(
        f"🆕 Nouvelles lignes : "
        f"{len(nouvelles_lignes)}"
    )

    if not nouvelles_lignes:

        print(
            "✅ Aucune nouvelle donnée "
            "à insérer."
        )

        return

    # 5. Configuration du chargement
    job_config = bigquery.LoadJobConfig(
        schema=RAW_SCHEMA,
        write_disposition=(
            bigquery.WriteDisposition.WRITE_APPEND
        ),
    )

    # 6. Chargement direct JSON → BigQuery
    load_job = client.load_table_from_json(
        nouvelles_lignes,
        FULL_TABLE_ID,
        job_config=job_config,
    )

    load_job.result()

    print(
        f"✅ {len(nouvelles_lignes)} "
        f"nouvelles lignes insérées "
        f"dans {FULL_TABLE_ID}"
    )


# ---------------------------------------------------------
# EXÉCUTION DIRECTE
# ---------------------------------------------------------

if __name__ == "__main__":
    ingest_data()