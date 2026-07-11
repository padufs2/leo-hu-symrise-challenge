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


def transform_sales(df: pd.DataFrame, valid_product_ids: set) -> pd.DataFrame:
    df = df.copy()
    before = len(df)

    # PARSING DE DATE : comme pour products, on gère les formats mixtes
    # pour ne pas perdre de dates valides écrites différemment.
    df["transaction_date"] = pd.to_datetime(
        df["transaction_date"], format="mixed", errors="coerce"
    )

    missing_dates = df["transaction_date"].isna()
    if missing_dates.any():
        ids = df.loc[missing_dates, "transaction_id"].tolist()
        logger.warning(f"sales_transactions: transaction_date invalide pour {ids}")

    # RÈGLE : un transaction_id doit être unique. Si on en trouve un dupliqué,
    # ce sont probablement 2 vraies transactions différentes qui ont eu le
    # même ID par erreur (pas un doublon à supprimer) — on les rend uniques
    # plutôt que de perdre l'une des deux.
    dup_mask = df.duplicated(subset="transaction_id", keep=False)

    if dup_mask.any():
        dup_ids = df.loc[dup_mask, "transaction_id"].unique().tolist()
        logger.warning(
            f"sales_transactions: transaction_id dupliqué(s) détecté(s) : {dup_ids}"
        )

        # On compte combien de fois on a déjà vu chaque ID, pour ajouter
        # un suffixe uniquement à partir de la 2e occurrence.
        counters = {}
        new_ids = []
        for tid in df["transaction_id"]:
            counters[tid] = counters.get(tid, 0) + 1
            if counters[tid] == 1:
                new_ids.append(tid)  # première occurrence : on ne touche pas
            else:
                new_ids.append(f"{tid}_{counters[tid]}")  # 2e, 3e... : suffixe

        df["transaction_id"] = new_ids
        # ASSOMPTION : total_amount_usd = quantity_kg * unit_price_usd, sans
        # taxes ni remises. On utilise cette formule uniquement pour recalculer
        # les valeurs manquantes, pas pour écraser des valeurs déjà présentes
        # (au cas où il y aurait une raison légitime à une différence, comme
        # une remise commerciale qu'on ne veut pas supprimer silencieusement).
        missing_total = df["total_amount_usd"].isna()

        if missing_total.any():
            ids = df.loc[missing_total, "transaction_id"].tolist()
            logger.warning(
                f"sales_transactions: total_amount_usd manquant pour {ids}, recalculé"
            )

            df.loc[missing_total, "total_amount_usd"] = (
                df.loc[missing_total, "quantity_kg"]
                * df.loc[missing_total, "unit_price_usd"]
            )

        # RÈGLE : toute transaction dont le product_id n'existe pas dans la table
        # products (nettoyée) est une référence orpheline — on ne peut pas la
        # garder car elle violerait la contrainte FOREIGN KEY lors du chargement.
        orphan_mask = ~df["product_id"].isin(valid_product_ids)

        if orphan_mask.any():
            orphan_rows = df.loc[orphan_mask, ["transaction_id", "product_id"]]
            logger.warning(
                f"sales_transactions: suppression de {orphan_mask.sum()} ligne(s) "
                f"avec product_id invalide :\n{orphan_rows.to_string(index=False)}"
            )
            df = df[~orphan_mask]
    return df


def transform_feedback(df: pd.DataFrame, valid_product_ids: set) -> pd.DataFrame:
    df = df.copy()
    before = len(df)

    # STANDARDISATION : uniformise la casse et enlève les espaces parasites
    # (ex: "Yes ", "yes" -> "Yes") pour que les mêmes statuts
    # soient bien reconnus comme identiques.
    df["would_reorder"] = df["would_reorder"].str.strip().str.title()

    # RÈGLE : toute note en dehors de [0, 5] est invalide -> mise à null.
    # Appliqué aux 4 colonnes de notes de la même façon, plutôt que de ne
    # traiter que la colonne où on a repéré le problème manuellement —
    # ça attrape aussi d'éventuelles valeurs hors échelle non détectées.
    RATING_MIN, RATING_MAX = 0, 5
    RATING_COLUMNS = [
        "quality_rating",
        "performance_rating",
        "value_rating",
        "overall_satisfaction",
    ]

    for col in RATING_COLUMNS:
        out_of_range = (df[col] < RATING_MIN) | (df[col] > RATING_MAX)
        if out_of_range.any():
            ids = df.loc[out_of_range, "feedback_id"].tolist()
            logger.warning(
                f"customer_feedback: {col} hors de [{RATING_MIN}, {RATING_MAX}] pour {ids}"
            )
            df.loc[out_of_range, col] = pd.NA

    # DÉCISION : quality_rating manquant -> on garde la ligne, on logue.
    missing_quality = df["quality_rating"].isna()
    if missing_quality.any():
        ids = df.loc[missing_quality, "feedback_id"].tolist()
        logger.warning(f"customer_feedback: quality_rating manquant pour {ids}")

    # DÉCISION : customer_id manquant -> on garde la ligne, on logue.
    missing_cust = df["customer_id"].isna() | (
        df["customer_id"].astype(str).str.strip() == ""
    )
    if missing_cust.any():
        ids = df.loc[missing_cust, "feedback_id"].tolist()
        logger.warning(f"customer_feedback: customer_id manquant pour {ids}")

    # PARSING DE DATE : comme pour products, on gère les formats mixtes
    # pour ne pas perdre de dates valides écrites différemment.
    df["feedback_date"] = pd.to_datetime(
        df["feedback_date"], format="mixed", errors="coerce"
    )

    # RÈGLE : tout feedback dont le product_id n'existe pas dans la table
    # products (nettoyée) est une référence orpheline — on ne peut pas la
    # garder car elle violerait la contrainte FOREIGN KEY lors du chargement.
    orphan_mask = ~df["product_id"].isin(valid_product_ids)
    if orphan_mask.any():
        orphan_rows = df.loc[orphan_mask, ["feedback_id", "product_id"]]
        logger.warning(
            f"customer_feedback: suppression de {orphan_mask.sum()} ligne(s) "
            f"avec product_id invalide :\n{orphan_rows.to_string(index=False)}"
        )
        df = df[~orphan_mask]

    logger.info(f"customer_feedback: {before} lignes avant, {len(df)} lignes après")
    return df


def transform_ingredient_costs(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    before = len(df)
    df = df.drop_duplicates(
        subset=["ingredient_name", "cost_per_kg_usd", "supplier"], keep="first"
    )

    # PARSING DE DATE : comme pour products, on gère les formats mixtes
    # pour ne pas perdre de dates valides écrites différemment.
    df["last_updated"] = pd.to_datetime(
        df["last_updated"], format="mixed", errors="coerce"
    )
    logger.info(f"ingredient_costs: {before} lignes avant, {len(df)} lignes après")

    return df


def transform_all(raw: dict) -> dict:
    """Run all transforms in dependency order (products first, since
    sales and feedback need its product_id list for orphan checks)."""
    products = transform_products(raw["products"])
    valid_product_ids = set(products["product_id"])

    sales = transform_sales(raw["sales_transactions"], valid_product_ids)
    feedback = transform_feedback(raw["customer_feedback"], valid_product_ids)
    costs = transform_ingredient_costs(raw["ingredient_costs"])

    return {
        "products": products,
        "sales_transactions": sales,
        "customer_feedback": feedback,
        "ingredient_costs": costs,
    }
