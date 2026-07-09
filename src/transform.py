import pandas as pd
import logging

logger = logging.getLogger(__name__)


def transform_products(df: pd.DataFrame) -> pd.DataFrame:
    # On travaille sur une copie pour ne jamais modifier le DataFrame original
    df = df.copy()
    before = len(df)

    # RÈGLE : un product_id ne doit jamais apparaître plus d'une fois.
    # keep="first" garde la première occurrence trouvée, supprime les autres.
    df = df.drop_duplicates(subset="product_id", keep="first")
    dropped = before - len(df)
    if dropped:
        logger.info(f"products: {dropped} doublon(s) supprimé(s) sur product_id")

    # STANDARDISATION : uniformise la casse et enlève les espaces parasites
    # (ex: "active ", "ACTIVE" -> "Active") pour que les mêmes statuts
    # soient bien reconnus comme identiques.
    df["status"] = df["status"].str.strip().str.title()

    # NETTOYAGE num_ingredients (en 3 temps) :
    # 1) "NULL" est une chaîne de texte littérale dans le CSV, pas un vrai NaN
    #    -> on la convertit en vraie valeur manquante pandas
    df["num_ingredients"] = df["num_ingredients"].replace("NULL", pd.NA)

    # 2) Une fois "NULL" retiré, on force la conversion numérique.
    #    errors="coerce" transforme en NaN tout ce qui n'est pas un nombre valide,
    #    au lieu de faire planter le programme.
    df["num_ingredients"] = pd.to_numeric(df["num_ingredients"], errors="coerce")

    # 3) RÈGLE : un nombre d'ingrédients ne peut jamais être négatif.
    # DÉCISION : on met à null plutôt que de deviner la vraie valeur
    # (ex: abs(-5) -> 5 serait une supposition non vérifiable).
    masque = df["num_ingredients"] < 0
    nb_negatifs = masque.sum()
    if nb_negatifs:
        logger.warning(
            f"products: {nb_negatifs} valeur(s) négative(s) dans num_ingredients, mise(s) à null"
        )
        df.loc[masque, "num_ingredients"] = pd.NA

    logger.info(f"products: {before} lignes avant, {len(df)} lignes après")

    # DÉCISION : product_name manquant -> on garde la ligne (le produit existe
    # quand même) mais on logue quels product_id sont concernés pour traçabilité.
    missing_name = df["product_name"].isna()
    if missing_name.any():
        ids = df.loc[missing_name, "product_id"].tolist()
        logger.warning(f"products: product_name manquant pour {ids}")

    # PARSING DE DATE : format="mixed" gère le cas où certaines lignes ont un
    # format différent du reste (ex: P040 était en "15-12-2023" au lieu de
    # "2023-12-15"). Sans ça, ces dates valides seraient perdues (-> NaT)
    # alors qu'elles sont récupérables.
    df["launch_date"] = pd.to_datetime(
        df["launch_date"], format="mixed", dayfirst=False, errors="coerce"
    )

    # Les launch_date encore NaT après ce parsing intelligent sont de VRAIES
    # valeurs manquantes d'origine (ex: P019), pas des erreurs de format.
    missing_date = df["launch_date"].isna()
    if missing_date.any():
        ids = df.loc[missing_date, "product_id"].tolist()
        logger.warning(f"products: launch_date manquant ou invalide pour {ids}")

    return df
