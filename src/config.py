import yaml
import logging

logger = logging.getLogger(__name__)


def load_config(config_path="config.yaml"):
    """Loads the YAML configuration file."""
    logger.info(f"Loading configuration from {config_path}")

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    logger.info(f"Configuration loaded: {list(config.keys())} sections found")
    return config
