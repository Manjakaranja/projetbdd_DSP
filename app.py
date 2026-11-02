"""Application web RepairConnect — Partie C du projet BDD."""
from datetime import date

import pandas as pd
import psycopg
import streamlit as st

import db

st.set_page_config(page_title="RepairConnect", page_icon="🔧", layout="wide")
st.title("🔧 RepairConnect")
st.caption("Gestion des réparations électroniques — PostgreSQL / NeonDB")

STATUTS = ["en attente", "en cours", "terminée", "annulée"]
CATEGORIES = ["Smartphone", "Ordinateur portable", "Tablette"]


def tableau(lignes):
    if lignes:
        st.dataframe(pd.DataFrame(lignes), hide_index=True, use_container_width=True)
    else:
        st.info("Aucune donnée à afficher.")


def enregistrer(sql, valeurs, succes):
    try:
        db.ecrire(sql, valeurs)
    except psycopg.errors.UniqueViolation:
        st.error("Identifiant ou adresse email déjà utilisé(e).")
    except psycopg.errors.ForeignKeyViolation:
        st.error("La référence sélectionnée n'existe pas dans la base.")
    except psycopg.errors.CheckViolation:
        st.error("Une valeur ne respecte pas les contraintes de la base.")
    except psycopg.Error:
        st.error("Erreur PostgreSQL. Vérifie la connexion et les valeurs saisies.")
    else:
        st.success(succes)
        st.rerun()


try:
    liste_clients = db.clients()
    liste_appareils = db.appareils()
    liste_demandes = db.demandes()
except (psycopg.Error, KeyError, FileNotFoundError):
    st.error("Connexion impossible. Vérifie DATABASE_URL dans les secrets Streamlit et les tables NeonDB.")
    st.stop()

col1, col2, col3 = st.columns(3)
col1.metric("Clients", len(liste_clients))
col2.metric("Demandes", len(liste_demandes))
col3.metric("Demandes en cours", sum(d["STATUT"] == "en cours" for d in liste_demandes))

onglet_clients, onglet_appareils, onglet_demandes, onglet_interventions = st.tabs(
    ["👤 Clients", "📱 Appareils", "📝 Demandes", "🛠️ Interventions"]
)

with onglet_clients:
    st.subheader("Liste des clients")
    tableau(liste_clients)
    st.subheader("Ajouter un client")
    with st.form("ajout_client", clear_on_submit=True):
        id_client = st.number_input("ID_CLIENT (saisie manuelle)", min_value=1, step=1, value=11)
        nom = st.text_input("Nom")
        prenom = st.text_input("Prénom")
        email = st.text_input("Email")
        telephone = st.text_input("Téléphone")
        valide = st.form_submit_button("Ajouter le client")
        if valide:
            if not all(x.strip() for x in (nom, prenom, email, telephone)):
                st.warning("Tous les champs sont obligatoires.")
            else:
                enregistrer('''INSERT INTO "CLIENT" ("ID_CLIENT", "NOM", "PRENOM", "EMAIL", "TELEPHONE")
                               VALUES (%s, %s, %s, %s, %s)''',
                            (int(id_client), nom.strip(), prenom.strip(), email.strip(), telephone.strip()),
                            "Client ajouté.")

with onglet_appareils:
    st.subheader("Appareils enregistrés")
    tableau(liste_appareils)
    st.subheader("Ajouter un appareil à un client")
    if not liste_clients:
        st.info("Ajoute d'abord un client.")
    else:
        choix_clients = {f'{c["ID_CLIENT"]} — {c["PRENOM"]} {c["NOM"]}': c["ID_CLIENT"] for c in liste_clients}
        with st.form("ajout_appareil", clear_on_submit=True):
            id_appareil = st.number_input("ID_APPAREIL (saisie manuelle)", min_value=1, step=1, value=16)
            categorie = st.selectbox("Catégorie", CATEGORIES)
            marque = st.text_input("Marque")
            modele = st.text_input("Modèle")
            date_connue = st.checkbox("Date d'achat connue")
            date_achat = st.date_input("Date d'achat", value=date(2024, 1, 1), disabled=not date_connue)
            proprietaire = st.selectbox("Client propriétaire", list(choix_clients))
            valide = st.form_submit_button("Ajouter l'appareil")
            if valide:
                if not marque.strip() or not modele.strip():
                    st.warning("La marque et le modèle sont obligatoires.")
                else:
                    enregistrer('''INSERT INTO "APPAREIL"
                                   ("ID_APPAREIL", "CATEGORIE", "MARQUE", "MODELE", "DATE_ACHAT", "ID_CLIENT")
                                   VALUES (%s, %s, %s, %s, %s, %s)''',
                                (int(id_appareil), categorie, marque.strip(), modele.strip(),
                                 date_achat if date_connue else None, choix_clients[proprietaire]),
                                "Appareil ajouté.")

with onglet_demandes:
    st.subheader("Demandes de réparation")
    tableau(liste_demandes)
    st.subheader("Créer une demande")
    if not liste_appareils:
        st.info("Ajoute d'abord un appareil.")
    else:
        choix_appareils = {f'{a["ID_APPAREIL"]} — {a["MARQUE"]} {a["MODELE"]} ({a["PRENOM"]} {a["NOM"]})': a["ID_APPAREIL"] for a in liste_appareils}
        with st.form("ajout_demande", clear_on_submit=True):
            num_demande = st.number_input("NUM_DEMANDE (saisie manuelle)", min_value=1, step=1, value=16)
            date_depot = st.date_input("Date de dépôt", value=date.today())
            appareil = st.selectbox("Appareil concerné", list(choix_appareils))
            panne = st.text_area("Description de la panne")
            cout = st.number_input("Coût estimé (€)", min_value=0.0, step=5.0, format="%.2f")
            statut = st.selectbox("Statut", STATUTS)
            valide = st.form_submit_button("Créer la demande")
            if valide:
                if not panne.strip():
                    st.warning("La description de la panne est obligatoire.")
                else:
                    enregistrer('''INSERT INTO "DEMANDE"
                                   ("NUM_DEMANDE", "DATE_DEPOT", "DESC_PANNE", "STATUT", "COUT_ESTIME", "ID_APPAREIL")
                                   VALUES (%s, %s, %s, %s, %s, %s)''',
                                (int(num_demande), date_depot, panne.strip(), statut, cout, choix_appareils[appareil]),
                                "Demande créée.")

    st.subheader("Modifier le statut d'une demande")
    if liste_demandes:
        choix_demandes = {f'{d["NUM_DEMANDE"]} — {d["MARQUE"]} {d["MODELE"]} ({d["STATUT"]})': d["NUM_DEMANDE"] for d in liste_demandes}
        with st.form("statut_demande"):
            demande = st.selectbox("Demande à modifier", list(choix_demandes))
            nouveau_statut = st.selectbox("Nouveau statut", STATUTS)
            valide = st.form_submit_button("Enregistrer le statut")
            if valide:
                enregistrer('UPDATE "DEMANDE" SET "STATUT" = %s WHERE "NUM_DEMANDE" = %s',
                            (nouveau_statut, choix_demandes[demande]), "Statut mis à jour.")

with onglet_interventions:
    st.subheader("Interventions d'une demande")
    if liste_demandes:
        choix_interventions = {f'{d["NUM_DEMANDE"]} — {d["MARQUE"]} {d["MODELE"]}': d["NUM_DEMANDE"] for d in liste_demandes}
        demande_choisie = st.selectbox("Sélectionner une demande", list(choix_interventions))
        try:
            tableau(db.interventions(choix_interventions[demande_choisie]))
        except psycopg.Error:
            st.error("Impossible de charger les interventions.")
    else:
        st.info("Aucune demande disponible.")
