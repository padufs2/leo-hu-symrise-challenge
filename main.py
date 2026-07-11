import logging
from src.config import load_config
from src.extract import extract_all
from src.transform import transform_all
from src.load import load_all

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.FileHandler("output/pipeline.log"), logging.StreamHandler()],
)


def main():
    config = load_config()
    raw = extract_all(config)
    clean = transform_all(raw)
    load_all(clean, config)


if __name__ == "__main__":
    main()
