import pandas as pd
import logging

logger = logging.getLogger(__name__)


def extract_all(config: dict):
    """Reads the 4 CSVs defined in the config and returns a dictionary of DataFrames."""

    paths = config["data_paths"]
    raw = {}

    for name, path in paths.items():
        logger.info(f"Reading {name} from {path}")
        try:
            df = pd.read_csv(path)
            logger.info(f"{name}: {len(df)} rows loaded successfully")
            raw[name] = df
        except FileNotFoundError:
            logger.error(f"{name}: file not found at {path}")
            raise
        except Exception as e:
            logger.error(f"{name}: error while reading — {e}")
            raise

    logger.info(f"Extraction complete: {len(raw)} tables loaded")
    return raw
