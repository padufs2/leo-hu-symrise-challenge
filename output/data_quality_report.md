# Data Quality Report

*Généré à partir de l'exécution du pipeline ETL (`main.py`) sur les 4 fichiers sources.
Détails complets et horodatés disponibles dans `output/pipeline.log`.*

---

## Résumé

| Table | Lignes en entrée | Lignes en sortie | Lignes supprimées |
|---|---|---|---|
| products | 41 | 40 | 1 |
| sales_transactions | 90 | 89 | 1 |
| customer_feedback | 55 | 54 | 1 |
| ingredient_costs | 42 | 41 | 1 |

---

## products.csv

| Problème détecté | Règle appliquée | Décision |
|---|---|---|
| 1 doublon complet sur `product_id` | Détection de tout `product_id` apparaissant plusieurs fois | Suppression du doublon (garde la 1ère occurrence) |
| `num_ingredients = -5` (P033) | Toute valeur négative est invalide | Mise à `NULL` plutôt que deviner la vraie valeur (ex: `abs(-5)`) — aucune preuve de la valeur correcte n'existe |
| `num_ingredients = "NULL"` (texte littéral, P024) | Conversion en vrai `NaN` avant tout calcul numérique | Converti en `NULL` propre |
| `product_name` manquant (P029) | Valeur manquante conservée, pas de suppression de ligne | Ligne conservée, loguée pour traçabilité |
| `launch_date` — format mixte (P040 : `15-12-2023` au lieu de `YYYY-MM-DD`) | Parsing avec `format="mixed"` pour ne pas perdre de dates valides à cause d'un format différent | Date correctement récupérée (`2023-12-15`) au lieu d'être perdue |
| `launch_date` réellement manquant (P019) | Valeur manquante d'origine, distincte du cas de format ci-dessus | Ligne conservée, loguée |
| `status` : casse incohérente (`active`, `Active`, `ACTIVE`) | Standardisation via `.str.strip().str.title()` | Uniformisé à `Active` / `Discontinued` |

---

## sales_transactions.csv

| Problème détecté | Règle appliquée | Décision |
|---|---|---|
| `transaction_id` "T011" dupliqué (2 vraies transactions distinctes, dates et quantités différentes) | Ce n'est pas un doublon à supprimer — 2 transactions réelles avec le même ID par erreur | Renommage automatique de la 2e occurrence (`T011` → `T011_2`) pour rendre les IDs uniques, sans perdre de données |
| `total_amount_usd` manquant (T024) | Recalcul via `quantity_kg × unit_price_usd` | Valeur recalculée (7700.0) plutôt que la ligne supprimée |
| `customer_id` manquant (1 ligne) | Valeur manquante conservée | Ligne conservée, loguée |
| Référence orpheline : `product_id = P999` (T059) n'existe dans aucune ligne de `products` | Toute ligne référençant un produit inexistant est supprimée (nécessaire pour respecter la contrainte `FOREIGN KEY` du schéma) | Ligne supprimée |

**Assomption documentée :** `total_amount_usd = quantity_kg × unit_price_usd`, sans taxes ni remises. Utilisée uniquement pour recalculer les valeurs manquantes, jamais pour écraser des valeurs déjà présentes (au cas où une remise commerciale légitime existerait).

---

## customer_feedback.csv

| Problème détecté | Règle appliquée | Décision |
|---|---|---|
| `quality_rating = 6.0` (F052), hors de l'échelle attendue [0, 5] | Validation appliquée uniformément aux 4 colonnes de notes (`quality_rating`, `performance_rating`, `value_rating`, `overall_satisfaction`), pas seulement à la colonne où le problème a été repéré manuellement | Mise à `NULL` |
| `overall_satisfaction = 5.2` (F052) | Cette colonne est dérivée (≈ moyenne des 3 autres notes) — sa valeur invalide est la conséquence directe du `quality_rating = 6.0` de la même ligne, pas une erreur indépendante | Mise à `NULL` (plutôt que recalculée, pour ne pas fabriquer une valeur à partir d'une donnée déjà invalide) |
| `quality_rating` manquant (F024, et F052 après nettoyage) | Valeur manquante conservée | Ligne conservée, loguée |
| `customer_id` manquant (F053) | Valeur manquante conservée | Ligne conservée, loguée |
| `would_reorder` : casse incohérente (`yes`, `Yes`, `YES`) | Standardisation via `.str.strip().str.title()` | Uniformisé à `Yes` / `No` / `Maybe` |
| Référence orpheline : `product_id = P999` (F034) | Même règle que pour `sales_transactions` | Ligne supprimée |

**Échelle de notation (0-5) :** non documentée dans les fichiers sources. Déduite empiriquement : `performance_rating` et `value_rating` plafonnent exactement à 5.0 sans jamais le dépasser, et 0-5 est l'échelle standard de satisfaction client. Cette hypothèse est appliquée de façon cohérente entre le code Python (validation) et le schéma SQL (contrainte `CHECK`).

---

## ingredient_costs.csv

| Problème détecté | Règle appliquée | Décision |
|---|---|---|
| Doublon `Lemon Oil` (I001 / I018), identique sur nom, coût et fournisseur, seul l'ID diffère | Deux lignes avec le même `ingredient_name`, `cost_per_kg_usd` et `supplier` sont considérées comme un vrai doublon | Suppression du doublon (garde `I001`) |

---

## Notes méthodologiques générales

- **Principe général appliqué partout :** privilégier une valeur `NULL` honnête plutôt qu'une valeur devinée/fabriquée, quand la vraie valeur ne peut pas être récupérée avec certitude.
- **Toutes les règles de nettoyage sont génériques**, pas des corrections ciblées sur des lignes spécifiques : elles détecteraient et corrigeraient automatiquement le même type de problème sur n'importe quel futur jeu de données avec les mêmes caractéristiques.
- **Jointure textuelle fragile :** la relation entre `products.primary_ingredient` et `ingredient_costs.ingredient_name` se fait sur un texte, pas un identifiant — vérifiée comme fonctionnelle sur ce jeu de données (aucune valeur orpheline), mais plus sensible aux fautes de frappe/casse que ne le serait une vraie clé étrangère.