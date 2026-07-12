# Business Questions — Answers

*Généré à partir de `sql/queries.sql`, exécuté sur `output/symrise.db`.*

---

## Q1 : Top 5 catégories de produits par revenu

**Au niveau `category`** (le plus haut niveau), il n'existe que 2 valeurs dans les données :

| Category | Total Revenue |
|---|---|
| Flavor | $298,425.00 |
| Fragrance | $191,096.00 |

Un "top 5" n'a pas de sens à ce niveau, puisqu'il n'existe que 2 catégories.

**Analyse complémentaire par `subcategory`** (13 valeurs uniques), plus pertinente pour un vrai top 5 actionnable :

| Subcategory | Total Revenue |
|---|---|
| *(à compléter avec le résultat de ta requête subcategory)* | |

---

## Q2 : Région avec la meilleure satisfaction client moyenne

| Region | Avg Satisfaction |
|---|---|
| North America | 4.6455 |
| EMEA | 4.4053 |
| LATAM | 4.1250 |
| APAC | 4.0714 |

**North America** a la meilleure satisfaction client moyenne (4.65/5).

**Assomption documentée :** `customer_feedback` ne contient pas de colonne `region`. Elle a été déduite en joignant sur `(customer_id, product_id)` à `sales_transactions`, en supposant qu'un client achète toujours un produit donné depuis la même région. Cette hypothèse a été vérifiée empiriquement : sur 89 paires (customer_id, product_id), aucune n'a de région différente selon la transaction. Une correction supplémentaire (`SELECT DISTINCT`) a été appliquée pour éviter qu'un même avis client soit compté en double lorsqu'un client a acheté le même produit plusieurs fois (cas de C011/P011).

---

## Q3 : Relation entre complexité du produit (nombre d'ingrédients) et satisfaction client

| Ingredient Range | Nb Products | Avg Satisfaction |
|---|---|---|
| 0-5 | 1 | 4.700 |
| 6-10 | 14 | 4.396 |
| 11-15 | 10 | 4.311 |
| 16-20 | 4 | 4.063 |

**Tendance observée :** la satisfaction moyenne diminue légèrement à mesure que le nombre d'ingrédients augmente (4.396 pour 6-10 ingrédients, contre 4.063 pour 16-20).

**Limite :** la tranche 0-5 ne contient qu'un seul produit — sa moyenne (4.7) n'est pas statistiquement représentative et ne doit pas être surinterprétée. Avec seulement 41 produits au total, cette tendance est indicative mais mériterait d'être confirmée sur un échantillon plus large avant toute conclusion business ferme.

---

## Q4 : Produits avec tendance de vente en déclin (comparaison des 2 derniers trimestres)

Les données couvrent le **5 janvier 2024 au 20 août 2024**. Les "2 derniers trimestres" disponibles sont donc **Q2 (avril-juin)** et **Q3 (juillet-août, incomplet — il manque septembre)**.

| Product ID | Q2 Revenue | Q3 Revenue | % Change |
|---|---|---|---|
| P012 | $5,637.50 | $5,535.00 | -1.8% |

**Constat :** sur 40 produits actifs, seuls **8** ont des transactions dans les deux trimestres à la fois (35 produits ont vendu en Q2, seulement 13 en Q3). Parmi ces 8 produits comparables, un seul montre un déclin : **P012**.

**Limite importante :** avec un échantillon aussi restreint (8 produits comparables) et un Q3 tronqué (pas de données de septembre), ce résultat n'est pas assez robuste pour identifier de vraies tendances de déclin. Une analyse plus fiable nécessiterait soit des trimestres complets, soit une comparaison sur les mêmes mois d'une année sur l'autre.

---

## Q5 : Marge par catégorie de produit (Revenue − Coûts ingrédients)

| Category | Total Revenue | Total Ingredient Cost | Estimated Margin |
|---|---|---|---|
| Flavor | $298,425.00 | $94,946.50 | **$203,478.50** |
| Fragrance | $191,096.00 | $95,842.88 | **$95,253.13** |

**Flavor** génère une marge estimée bien supérieure à **Fragrance**, malgré un revenu qui n'est pas proportionnellement aussi élevé — cela suggère que les ingrédients utilisés dans les produits Fragrance sont, en moyenne, plus coûteux au kg.

**Assomption et limite documentées :**
- Le coût est calculé uniquement à partir de l'ingrédient **principal** de chaque produit (`primary_ingredient`), pas de sa formulation complète. C'est donc une approximation, pas une marge réelle — un vrai calcul de coût de revient nécessiterait une table de composition multi-ingrédients par produit, absente de ces données.
- La jointure `products.primary_ingredient` ↔ `ingredient_costs.ingredient_name` se fait sur un texte, pas un ID — plus fragile qu'une vraie clé étrangère (vérifié : aucun ingrédient principal n'est resté sans correspondance dans ce jeu de données, mais ce point serait à surveiller avec de nouvelles données).