import yaml
import logging

logger = logging.getLogger(__name__)


def load_config(config_path="config.yaml"):
    """Charge le fichier de configuration YAML."""
    logger.info(f"Chargement de la configuration depuis {config_path}")

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    logger.info(f"Configuration chargée : {list(config.keys())} sections trouvées")
    return config
