Application Streamlit connectée à la base Neon PostgreSQL du projet BDD.

## Prérequis
- Exécuter le script de création et d'insertion des 7 tables sur NeonDB.
- Avoir Python 3.10+.

## Lancer en local
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```
Remplacer `DATABASE_URL` par l'URL de connexion donnée par Neon (SSL requis).
```bash
streamlit run app.py
```

## Mettre en ligne
1. Publier ce dossier sur GitHub, **sans** `.streamlit/secrets.toml`.
2. Dans Streamlit Community Cloud, sélectionner le dépôt et `app.py`.
3. Dans les secrets de l'application, ajouter :
   ```toml
   DATABASE_URL = "postgresql://..."
   ```
4. Déployer et tester les formulaires.

## Fonctionnalités
- Afficher et ajouter des clients (ID saisi manuellement).
- Afficher et ajouter des appareils à un client (ID saisi manuellement).
- Consulter et créer des demandes de réparation (numéro saisi manuellement).
- Modifier le statut d'une demande.
- Afficher les interventions associées à une demande.
- Exécuter des requêtes SQL de consultation

Note : application de démonstration sans authentification. Utiliser une base de test sans données personnelles réelles. Si déployée en public, toute personne ayant le lien peut modifier les données.
