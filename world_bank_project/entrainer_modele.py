import os
from datetime import datetime, timezone

import joblib
import pandas as pd
from dotenv import load_dotenv
from google.cloud import bigquery

from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)

from creer_dataset_ml import creer_dataset_ml


# --------------------------------------------------
# 1. Configuration BigQuery
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

PREDICTIONS_TABLE = (
    f"{PROJECT_ID}.ml.predictions"
)


# --------------------------------------------------
# 2. Charger le dataset ML depuis BigQuery
# --------------------------------------------------

df = creer_dataset_ml()


# --------------------------------------------------
# 3. Définir les 7 features
# --------------------------------------------------

features = [
    "Esperance_vie",
    "Depense_de_sante",
    "Scolarisation_secondaire",
    "Depense_publique_education",
    "Taux_natalite",
    "CO2_par_habitant",
    "Acces_electricite",
]


# ==================================================
# PARTIE 1 : ÉVALUATION DU MODÈLE
# ==================================================

# --------------------------------------------------
# 4. Séparation temporelle
#
# 2015 à 2021 = entraînement
# 2022 = test
#
# On retire uniquement les lignes sans cible réelle.
# Les NaN présents dans les FEATURES sont conservés :
# SimpleImputer les traitera.
# --------------------------------------------------

train_df = df[
    (df["annee"].between(2015, 2021))
    & (df["income_level"].notna())
].copy()

test_df = df[
    (df["annee"] == 2022)
    & (df["income_level"].notna())
].copy()


X_train = train_df[features]
y_train = train_df["income_level"]

X_test = test_df[features]
y_test = test_df["income_level"]


print("\n---------------------------------------")
print("ÉVALUATION DU MODÈLE")
print("---------------------------------------")

print("\nPériode d'entraînement : 2015 à 2021")
print("Année de test : 2022")

print(
    "Nombre d'observations d'entraînement :",
    len(X_train)
)

print(
    "Nombre d'observations de test :",
    len(X_test)
)


# --------------------------------------------------
# 5. Pipeline d'évaluation
# --------------------------------------------------

pipeline_evaluation = Pipeline(
    steps=[
        (
            "imputer",
            SimpleImputer(
                strategy="median"
            ),
        ),
        (
            "model",
            RandomForestClassifier(
                n_estimators=200,
                random_state=42,
                class_weight="balanced",
            ),
        ),
    ]
)


# --------------------------------------------------
# 6. Entraîner sur 2015 à 2021
# --------------------------------------------------

print("\nEntraînement du modèle d'évaluation...")

pipeline_evaluation.fit(
    X_train,
    y_train
)

print("Entraînement terminé.")


# --------------------------------------------------
# 7. Prédire 2022
# --------------------------------------------------

y_pred = pipeline_evaluation.predict(
    X_test
)


# --------------------------------------------------
# 8. Évaluer le modèle sur 2022
# --------------------------------------------------

accuracy = accuracy_score(
    y_test,
    y_pred
)

print(
    "\nAccuracy sur l'année 2022 :",
    round(accuracy, 3)
)

print("\nRapport de classification :")

print(
    classification_report(
        y_test,
        y_pred
    )
)

print("\nMatrice de confusion :")

print(
    confusion_matrix(
        y_test,
        y_pred
    )
)


# --------------------------------------------------
# 9. Sauvegarder le pipeline d'évaluation
# --------------------------------------------------

joblib.dump(
    pipeline_evaluation,
    "pipeline_evaluation.pkl"
)

print(
    "\nPipeline d'évaluation sauvegardé "
    "dans pipeline_evaluation.pkl"
)


# ==================================================
# PARTIE 2 : ENREGISTRER LE TEST 2022
#             DANS ml.predictions
# ==================================================

# --------------------------------------------------
# 10. Préparer les résultats du test 2022
# --------------------------------------------------

predictions_test = test_df[
    [
        "countryiso3code",
        "country_name",
        "region",
        "annee",
        "income_level",
    ]
].copy()

predictions_test["income_level_predit"] = y_pred

predictions_test["type_prediction"] = "Test"

predictions_test["prediction_correcte"] = (
    predictions_test["income_level"]
    == predictions_test["income_level_predit"]
).map(
    {
        True: "Juste",
        False: "Faux",
    }
)

predictions_test["date_prediction"] = datetime.now(
    timezone.utc
)


# --------------------------------------------------
# 11. Enregistrer le test 2022 dans BigQuery
#
# WRITE_TRUNCATE est volontaire ici :
# on initialise ml.predictions avec le test 2022.
#
# Les prédictions 2023+ seront ajoutées ensuite
# par predict.py.
# --------------------------------------------------

client = bigquery.Client()

job_config = bigquery.LoadJobConfig(
    write_disposition="WRITE_TRUNCATE"
)

client.load_table_from_dataframe(
    predictions_test,
    PREDICTIONS_TABLE,
    job_config=job_config,
).result()


print(
    f"\n{len(predictions_test)} prédictions de test "
    f"2022 enregistrées dans {PREDICTIONS_TABLE}"
)


# ==================================================
# PARTIE 3 : MODÈLE FINAL DE PRODUCTION
# ==================================================

print("\n---------------------------------------")
print("ENTRAÎNEMENT DU MODÈLE FINAL")
print("---------------------------------------")


# --------------------------------------------------
# 12. IMPORTANT :
#     entraînement final limité à 2015-2022
#
# 2023, 2024, 2025... sont EXCLUS.
# --------------------------------------------------

final_df = df[
    (df["annee"].between(2015, 2022))
    & (df["income_level"].notna())
].copy()


X_final = final_df[features]
y_final = final_df["income_level"]


print(
    "\nPériode d'entraînement finale : "
    "2015 à 2022"
)

print(
    "Nombre total d'observations :",
    len(X_final)
)


# --------------------------------------------------
# 13. Créer le pipeline final
# --------------------------------------------------

pipeline_final = Pipeline(
    steps=[
        (
            "imputer",
            SimpleImputer(
                strategy="median"
            ),
        ),
        (
            "model",
            RandomForestClassifier(
                n_estimators=200,
                random_state=42,
                class_weight="balanced",
            ),
        ),
    ]
)


# --------------------------------------------------
# 14. Entraîner le modèle final
# --------------------------------------------------

print("\nEntraînement du modèle final...")

pipeline_final.fit(
    X_final,
    y_final
)

print("Entraînement final terminé.")


# --------------------------------------------------
# 15. Sauvegarder le modèle de production
# --------------------------------------------------

joblib.dump(
    pipeline_final,
    "pipeline.pkl"
)

print(
    "\nModèle final sauvegardé dans pipeline.pkl"
)

print(
    "Ce pipeline est maintenant prêt "
    "pour prédire les années 2023 et suivantes."
)