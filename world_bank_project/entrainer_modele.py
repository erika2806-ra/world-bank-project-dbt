import joblib

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
# 1. Charger le dataset ML depuis BigQuery
# --------------------------------------------------

df = creer_dataset_ml()


# --------------------------------------------------
# 2. Définir les features
# --------------------------------------------------

features = [
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


# ==================================================
# PARTIE 1 : ÉVALUATION DU MODÈLE
# ==================================================

# --------------------------------------------------
# 3. Séparation temporelle
#
# 2015 à 2021 = entraînement
# 2022 = test
# --------------------------------------------------

train_df = df[df["annee"] < 2022].copy()
test_df = df[df["annee"] == 2022].copy()

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
# 4. Pipeline d'évaluation
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
# 5. Entraînement sur 2015 à 2021
# --------------------------------------------------

print("\nEntraînement du modèle d'évaluation...")

pipeline_evaluation.fit(
    X_train,
    y_train
)

print("Entraînement terminé.")


# --------------------------------------------------
# 6. Prédictions sur 2022
# --------------------------------------------------

y_pred = pipeline_evaluation.predict(
    X_test
)


# --------------------------------------------------
# 7. Évaluation sur 2022
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
# 8. Sauvegarder le pipeline d'évaluation
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
# PARTIE 2 : MODÈLE FINAL DE PRODUCTION
# ==================================================

print("\n---------------------------------------")
print("ENTRAÎNEMENT DU MODÈLE FINAL")
print("---------------------------------------")


# --------------------------------------------------
# 9. Utiliser toutes les données connues
#    2015 à 2022
# --------------------------------------------------

X_final = df[features]
y_final = df["income_level"]

print(
    "\nPériode d'entraînement finale : "
    "2015 à 2022"
)

print(
    "Nombre total d'observations :",
    len(X_final)
)


# --------------------------------------------------
# 10. Créer un nouveau pipeline final
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
# 11. Entraîner sur 2015 à 2022
# --------------------------------------------------

print("\nEntraînement du modèle final...")

pipeline_final.fit(
    X_final,
    y_final
)

print("Entraînement final terminé.")


# --------------------------------------------------
# 12. Sauvegarder le modèle de production
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
    "pour predict.py."
)