
from datetime import date

import pandas as pd
import psycopg
import streamlit as st

import db


st.set_page_config(
    page_title="RepairConnect",
    page_icon="🧑‍💻",
    layout="wide"
)

st.title("RepairConnect")
st.caption("Gestion des réparations électroniques — PostgreSQL / NeonDB")

STATUTS = ["en attente", "en cours", "terminée", "annulée"]
CATEGORIES = ["Smartphone", "Ordinateur portable", "Tablette"]


# --------------------------------------------------
# FONCTIONS UTILITAIRES
# --------------------------------------------------

def tableau(lignes):
    if lignes:
        st.dataframe(
            pd.DataFrame(lignes),
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("Aucune donnée à afficher.")


def enregistrer(sql, valeurs, succes):
    try:
        db.ecrire(sql, valeurs)

    except psycopg.errors.UniqueViolation:
        st.error("Identifiant ou email déjà utilisé.")

    except psycopg.errors.ForeignKeyViolation:
        st.error("La référence sélectionnée n'existe pas.")

    except psycopg.errors.CheckViolation:
        st.error("Une valeur ne respecte pas les contraintes.")

    except psycopg.Error:
        st.error("Erreur PostgreSQL. Vérifie les valeurs saisies.")

    else:
        st.success(succes)
        st.rerun()


# --------------------------------------------------
# CHARGEMENT DES DONNÉES
# --------------------------------------------------

try:
    liste_clients = db.clients()
    liste_appareils = db.appareils()
    liste_demandes = db.demandes()

except (psycopg.Error, KeyError, FileNotFoundError):
    st.error(
        "Connexion impossible. Vérifie DATABASE_URL "
        "et les tables NeonDB."
    )
    st.stop()


# --------------------------------------------------
# TABLEAU DE BORD
# --------------------------------------------------

col1, col2, col3 = st.columns(3)

col1.metric("Clients", len(liste_clients))
col2.metric("Demandes", len(liste_demandes))
col3.metric(
    "Demandes en cours",
    sum(d["STATUT"] == "en cours" for d in liste_demandes)
)


# --------------------------------------------------
# ONGLETS
# --------------------------------------------------

onglet_clients, onglet_appareils, onglet_demandes, \
onglet_interventions, onglet_sql = st.tabs([
    "👤 Clients",
    "📱 Appareils",
    "📝 Demandes",
    "🛠️ Interventions",
    "🗃️ SQL Editor"
])


# --------------------------------------------------
# CLIENTS
# --------------------------------------------------

with onglet_clients:

    st.subheader("Liste des clients")
    tableau(liste_clients)

    st.subheader("Ajouter un client")

    with st.form("ajout_client", clear_on_submit=True):

        id_client = st.number_input(
            "ID_CLIENT",
            min_value=1,
            step=1,
            value=11
        )

        nom = st.text_input("Nom")
        prenom = st.text_input("Prénom")
        email = st.text_input("Email")
        telephone = st.text_input("Téléphone")

        valide = st.form_submit_button("Ajouter le client")

        if valide:

            if not all(
                x.strip() for x in
                (nom, prenom, email, telephone)
            ):
                st.warning("Tous les champs sont obligatoires.")

            else:
                enregistrer(
                    """
                    INSERT INTO "CLIENT"
                    ("ID_CLIENT", "NOM", "PRENOM",
                     "EMAIL", "TELEPHONE")
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        int(id_client),
                        nom.strip(),
                        prenom.strip(),
                        email.strip(),
                        telephone.strip()
                    ),
                    "Client ajouté."
                )


# --------------------------------------------------
# APPAREILS
# --------------------------------------------------

with onglet_appareils:

    st.subheader("Appareils enregistrés")
    tableau(liste_appareils)

    st.subheader("Ajouter un appareil à un client")

    if not liste_clients:
        st.info("Ajoute d'abord un client.")

    else:
        choix_clients = {
            f'{c["ID_CLIENT"]} — {c["PRENOM"]} {c["NOM"]}':
                c["ID_CLIENT"]
            for c in liste_clients
        }

        with st.form("ajout_appareil", clear_on_submit=True):

            id_appareil = st.number_input(
                "ID_APPAREIL",
                min_value=1,
                step=1,
                value=16
            )

            categorie = st.selectbox(
                "Catégorie",
                CATEGORIES
            )

            marque = st.text_input("Marque")
            modele = st.text_input("Modèle")

            date_connue = st.checkbox("Date d'achat connue")

            date_achat = st.date_input(
                "Date d'achat",
                value=date(2024, 1, 1),
                disabled=not date_connue
            )

            proprietaire = st.selectbox(
                "Client propriétaire",
                list(choix_clients)
            )

            valide = st.form_submit_button(
                "Ajouter l'appareil"
            )

            if valide:

                if not marque.strip() or not modele.strip():
                    st.warning("Marque et modèle obligatoires.")

                else:
                    enregistrer(
                        """
                        INSERT INTO "APPAREIL"
                        ("ID_APPAREIL", "CATEGORIE",
                         "MARQUE", "MODELE",
                         "DATE_ACHAT", "ID_CLIENT")
                        VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                        (
                            int(id_appareil),
                            categorie,
                            marque.strip(),
                            modele.strip(),
                            date_achat if date_connue else None,
                            choix_clients[proprietaire]
                        ),
                        "Appareil ajouté."
                    )


# --------------------------------------------------
# DEMANDES
# --------------------------------------------------

with onglet_demandes:

    st.subheader("Demandes de réparation")
    tableau(liste_demandes)

    st.subheader("Créer une demande")

    if not liste_appareils:
        st.info("Ajoute d'abord un appareil.")

    else:
        choix_appareils = {
            f'{a["ID_APPAREIL"]} — '
            f'{a["MARQUE"]} {a["MODELE"]} '
            f'({a["PRENOM"]} {a["NOM"]})':
                a["ID_APPAREIL"]
            for a in liste_appareils
        }

        with st.form("ajout_demande", clear_on_submit=True):

            num_demande = st.number_input(
                "NUM_DEMANDE",
                min_value=1,
                step=1,
                value=16
            )

            date_depot = st.date_input(
                "Date de dépôt",
                value=date.today()
            )

            appareil = st.selectbox(
                "Appareil concerné",
                list(choix_appareils)
            )

            panne = st.text_area(
                "Description de la panne"
            )

            cout = st.number_input(
                "Coût estimé (€)",
                min_value=0.0,
                step=5.0,
                format="%.2f"
            )

            statut = st.selectbox("Statut", STATUTS)

            valide = st.form_submit_button(
                "Créer la demande"
            )

            if valide:

                if not panne.strip():
                    st.warning(
                        "La description de la panne est obligatoire."
                    )

                else:
                    enregistrer(
                        """
                        INSERT INTO "DEMANDE"
                        ("NUM_DEMANDE", "DATE_DEPOT",
                         "DESC_PANNE", "STATUT",
                         "COUT_ESTIME", "ID_APPAREIL")
                        VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                        (
                            int(num_demande),
                            date_depot,
                            panne.strip(),
                            statut,
                            cout,
                            choix_appareils[appareil]
                        ),
                        "Demande créée."
                    )

    st.divider()
    st.subheader("Modifier le statut d'une demande")

    if liste_demandes:

        choix_demandes = {
            f'{d["NUM_DEMANDE"]} — '
            f'{d["MARQUE"]} {d["MODELE"]} '
            f'({d["STATUT"]})':
                d["NUM_DEMANDE"]
            for d in liste_demandes
        }

        with st.form("statut_demande"):

            demande = st.selectbox(
                "Demande à modifier",
                list(choix_demandes)
            )

            nouveau_statut = st.selectbox(
                "Nouveau statut",
                STATUTS
            )

            valide = st.form_submit_button(
                "Enregistrer le statut"
            )

            if valide:
                enregistrer(
                    """
                    UPDATE "DEMANDE"
                    SET "STATUT" = %s
                    WHERE "NUM_DEMANDE" = %s
                    """,
                    (
                        nouveau_statut,
                        choix_demandes[demande]
                    ),
                    "Statut mis à jour."
                )


# --------------------------------------------------
# INTERVENTIONS
# --------------------------------------------------

with onglet_interventions:

    st.subheader("Interventions d'une demande")

    if liste_demandes:

        choix_interventions = {
            f'{d["NUM_DEMANDE"]} — '
            f'{d["MARQUE"]} {d["MODELE"]}':
                d["NUM_DEMANDE"]
            for d in liste_demandes
        }

        demande_choisie = st.selectbox(
            "Sélectionner une demande",
            list(choix_interventions)
        )

        try:
            tableau(
                db.interventions(
                    choix_interventions[demande_choisie]
                )
            )

        except psycopg.Error:
            st.error(
                "Impossible de charger les interventions."
            )

    else:
        st.info("Aucune demande disponible.")


# --------------------------------------------------
# SQL EDITOR
# --------------------------------------------------

with onglet_sql:

    st.subheader("Schéma relationnel — RepairConnect")

    st.caption(
        "PK = clé primaire | FK = clé étrangère. "
        "Le # du MLD n'appartient pas au nom SQL."
    )

    mld = {
        "CLIENT": (
            "ID_CLIENT (PK), NOM, PRENOM, EMAIL, TELEPHONE"
        ),
        "APPAREIL": (
            "ID_APPAREIL (PK), CATEGORIE, MARQUE, MODELE, "
            "DATE_ACHAT, ID_CLIENT (FK)"
        ),
        "DEMANDE": (
            "NUM_DEMANDE (PK), DATE_DEPOT, DESC_PANNE, "
            "STATUT, COUT_ESTIME, ID_APPAREIL (FK)"
        ),
        "TECHNICIEN": (
            "ID_TECHNICIEN (PK), NOM, PRENOM, SPECIALITE"
        ),
        "INTERVENTION": (
            "ID_INTERVENTION (PK), DATE_INTERVENTION, "
            "DESCRIPTION, COUT_MAINDOEUVRE, "
            "NUM_DEMANDE (FK), ID_TECHNICIEN (FK)"
        ),
        "PIECE": (
            "REF_PIECE (PK), LIBELLE, "
            "PRIX_UNITAIRE, QUANTITE_DISPO"
        ),
        "UTILISER": (
            "ID_INTERVENTION (PK, FK), "
            "REF_PIECE (PK, FK), QUANTITE_UTILISEE"
        )
    }

    for nom, colonnes in mld.items():
        st.markdown(f"**{nom}** — {colonnes}")

    st.divider()

    st.subheader("Exécuter une requête PostgreSQL")

    st.info(
        "Seules les requêtes SELECT sont autorisées. "
        "Maximum 500 lignes et 5 secondes d'exécution."
    )

    with st.form("sql_editor"):

        sql_utilisateur = st.text_area(
            "Requête SQL",
            value='SELECT * FROM "CLIENT" LIMIT 10;',
            height=150
        )

        executer = st.form_submit_button(
            "Exécuter la requête",
            type="primary"
        )

    if executer:

        try:
            resultat = db.requete_sql_lecture(
                sql_utilisateur
            )

            tableau(resultat)

            st.caption(
                f"{len(resultat)} ligne(s) affichée(s) "
                "— maximum 500."
            )

        except ValueError as exc:
            st.warning(str(exc))

        except psycopg.Error as exc:
            st.error(
                f"Erreur SQL : {str(exc).splitlines()[0]}"
            )
