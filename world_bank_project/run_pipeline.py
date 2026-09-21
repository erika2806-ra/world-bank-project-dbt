import logging
import subprocess
import time

from load_data import ingest_data
from predict import predire


# --------------------------------------------------
# 1. Configuration des logs
# --------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


# --------------------------------------------------
# 2. Fonction de retry
# --------------------------------------------------

def avec_retry(action, essais=3, delai=5):
    """Lance une action et réessaie en cas d'erreur."""

    for tentative in range(1, essais + 1):

        try:
            return action()

        except Exception as e:

            logger.error(
                f"Échec de l'action "
                f"(tentative {tentative}/{essais}) : {e}"
            )

            if tentative < essais:

                logger.warning(
                    f"Nouvel essai dans {delai} secondes."
                )

                time.sleep(delai)

    raise RuntimeError(
        f"Abandon après {essais} tentatives."
    )


# --------------------------------------------------
# 3. Étape 1 : ingestion World Bank → BigQuery
# --------------------------------------------------

logger.info(
    "Étape 1 : ingestion World Bank → BigQuery"
)

avec_retry(
    ingest_data,
    essais=3,
    delai=5,
)


# --------------------------------------------------
# 4. Étape 2 : transformations dbt
# --------------------------------------------------

logger.info(
    "Étape 2 : transformation dbt"
)

subprocess.run(
    ["dbt", "run"],
    check=True,
)


# --------------------------------------------------
# 5. Étape 3 : prédictions Machine Learning
# --------------------------------------------------

logger.info(
    "Étape 3 : prédictions Machine Learning"
)

avec_retry(
    predire,
    essais=3,
    delai=5,
)


# --------------------------------------------------
# 6. Fin du pipeline
# --------------------------------------------------

logger.info(
    "Pipeline terminé : "
    "données ingérées, transformées et prédictions réalisées."
)