# Symrise Data Engineering Challenge — Léo Hu

Solution au challenge de data engineering Symrise : pipeline ETL (Extract, Transform, Load) 
en Python + SQLite, avec réponses aux 5 questions business.

---

## Structure du projet
leo-hu-symrise-challenge/
├── README.md
├── requirements.txt
├── config.yaml
├── data/                       # CSV sources (non versionnés si volumineux)
├── src/
│   ├── config.py               # Chargement de config.yaml
│   ├── extract.py               # Lecture des 4 CSV
│   ├── transform.py             # Nettoyage et validation
│   ├── load.py                  # Création du schéma + insertion SQLite
│   └── main.py                  # Orchestration du pipeline complet
├── sql/
│   ├── schema.sql                # Définition des tables
│   └── queries.sql               # Les 5 requêtes business
└── output/
    ├── symrise.db                 # Base de données finale
    ├── pipeline.log                # Logs d'exécution
    ├── data_quality_report.md      # Problèmes détectés et corrigés
    └── business_answers.md         # Réponses aux 5 questions
---

## Setup

**Prérequis :** Python 3.12+

```bash
# Créer et activer l'environnement virtuel
python3 -m venv venv
source venv/bin/activate        # Windows : venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt
```

---

## Comment lancer le pipeline

```bash
mkdir -p output
uv run main.py
```

Le pipeline va, dans l'ordre :
1. Charger `config.yaml`
2. Lire les 4 CSV depuis `data/`
3. Nettoyer et valider les données (voir `output/data_quality_report.md`)
4. Créer le schéma SQLite (`sql/schema.sql`) et y insérer les données propres
5. Générer `output/symrise.db` et `output/pipeline.log`

## Comment exécuter les requêtes business

```bash
sqlite3 output/symrise.db
.read sql/queries.sql
```

Ou directement, pour une requête spécifique :
```bash
sqlite3 output/symrise.db < sql/queries.sql
```

Les résultats commentés sont disponibles dans `output/business_answers.md`.

---

## Design decisions & assumptions

### Architecture
- **Python + pandas** pour l'extraction et le nettoyage, **SQLite** pour le stockage et l'analyse. Choix dimensionné au volume réel des données (quelques dizaines à centaines de lignes par table) — un outil comme Databricks ou dbt serait surdimensionné ici, mais serait pertinent si le volume grandissait significativement (voir section "Pistes d'amélioration").
- **Schéma en étoile simplifié** : `products` et `ingredient_costs` comme tables dimension, `sales_transactions` et `customer_feedback` comme tables de faits.
- **Configuration centralisée** (`config.yaml`) : chemins de fichiers et seuils de validation ne sont jamais codés en dur dans le code Python.

### Principe de nettoyage général
Pour toute valeur invalide dont la vraie valeur ne peut pas être récupérée avec certitude, la donnée est mise à `NULL` plutôt que devinée ou fabriquée. Le détail complet des problèmes détectés et des décisions prises est dans `output/data_quality_report.md`.

Toutes les règles de nettoyage sont **génériques** (basées sur des conditions, pas sur des identifiants de lignes spécifiques) — elles s'appliqueraient automatiquement à tout nouveau jeu de données présentant les mêmes types de problèmes.

### Échelle de notation client (0-5)
Non documentée dans les fichiers sources. Déduite empiriquement du fait que `performance_rating` et `value_rating` plafonnent exactement à 5.0 sans jamais le dépasser. Appliquée de façon cohérente entre la validation Python (`transform.py`) et les contraintes `CHECK` du schéma SQL.

### Jointure textuelle products ↔ ingredient_costs
`products.primary_ingredient` (texte) est relié à `ingredient_costs.ingredient_name` (texte), faute d'identifiant commun dans les données sources. Vérifié comme fonctionnel sur ce jeu de données (aucune valeur orpheline), mais plus fragile qu'une vraie clé étrangère — sensible à la casse et aux fautes de frappe.

### Calcul de marge (Q5)
Basé uniquement sur l'ingrédient **principal** de chaque produit, faute de table de composition multi-ingrédients dans les données. C'est donc une approximation de marge, pas un coût de revient complet.

---

## Limites connues et hypothèses à vérifier

- **Q2 (satisfaction par région)** : `customer_feedback` n'a pas de colonne région ; elle est déduite via `(customer_id, product_id)` en supposant qu'un client achète toujours un produit donné depuis la même région — hypothèse vérifiée sur ce jeu de données mais non garantie en général.
- **Q3 (complexité vs satisfaction)** : la tranche 0-5 ingrédients ne contient qu'un seul produit, rendant sa moyenne peu représentative.
- **Q4 (déclin trimestriel)** : les données s'arrêtent le 20 août 2024, rendant Q3 incomplet. Seuls 8 produits sur 40 ont des données dans les deux trimestres comparés.

Le détail complet de chaque limite est documenté directement en commentaire dans `sql/queries.sql` et dans `output/business_answers.md`.

---

## Pistes d'amélioration (si le projet devait grandir)

- **Table de composition multi-ingrédients** par produit, pour un calcul de marge précis (au lieu de l'ingrédient principal seul).
- **ID d'ingrédient plutôt que nom** comme clé de jointure entre `products` et `ingredient_costs`, pour éliminer la fragilité textuelle.
- **Table `rejected_rows`** (déjà présente dans le schéma) : actuellement non utilisée par le pipeline (les rejets sont tracés via les logs), mais pourrait être peuplée pour une traçabilité interrogeable en SQL.
- À plus grande échelle (millions de lignes, sources multiples, temps réel), un stack type dbt + entrepôt cloud (Snowflake/BigQuery) apporterait la gestion de dépendances et les tests intégrés que ce pipeline Python + SQLite n'offre pas nativement.

---

## Auteur

Léo Hu