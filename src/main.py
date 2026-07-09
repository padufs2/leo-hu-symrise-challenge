import logging
from config import load_config
from extract import extract_all

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.FileHandler("output/pipeline.log"), logging.StreamHandler()],
)


def main():
    config = load_config()
    raw = extract_all(config)

    # Juste pour vérifier visuellement que ça marche
    for name, df in raw.items():
        print(f"\n--- {name} ---")
        print(df.head())


if __name__ == "__main__":
    main()
