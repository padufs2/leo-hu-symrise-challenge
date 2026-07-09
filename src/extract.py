import pandas as pd
import logging

logger = logging.getLogger(__name__)


def extract_all(config: dict):
    """Lit les 4 CSV définis dans la config et retourne un dictionnaire de DataFrames."""

    paths = config["data_paths"]
    raw = {}

    for name, path in paths.items():
        logger.info(f"Lecture de {name} depuis {path}")
        try:
            df = pd.read_csv(path)
            logger.info(f"{name}: {len(df)} lignes chargées avec succès")
            raw[name] = df
        except FileNotFoundError:
            logger.error(f"{name}: fichier introuvable à {path}")
            raise
        except Exception as e:
            logger.error(f"{name}: erreur lors de la lecture — {e}")
            raise

    logger.info(f"Extraction terminée : {len(raw)} tables chargées")
    return raw
