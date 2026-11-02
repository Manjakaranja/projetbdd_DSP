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


def message_erreur(exc):
    """Traduire les erreurs SQL courantes sans exposer les détails de connexion."""
    if isinstance(exc, psycopg.errors.UniqueViolation):
        nom = (exc.diag.constraint_name or "").lower()
        if "email" in nom:
            return "Cette adresse e-mail est déjà utilisée par un autre client."
        return "Cet identifiant existe déjà (clé primaire dupliquée). Choisis un autre identifiant."
    if isinstance(exc, psycopg.errors.ForeignKeyViolation):
        return "Référence invalide : le client, l'appareil, le technicien, la demande ou la pièce indiqué(e) n'existe pas, ou cette ligne est utilisée ailleurs."
    if isinstance(exc, psycopg.errors.CheckViolation):
        return "Valeur incohérente : vérifie le statut, les montants et les quantités autorisés."
    if isinstance(exc, psycopg.errors.NotNullViolation):
        return "Champ obligatoire manquant : renseigne toutes les informations requises."
    if isinstance(exc, psycopg.errors.SyntaxError):
        return "Erreur de syntaxe SQL : vérifie les mots-clés, virgules, guillemets et parenthèses."
    if isinstance(exc, psycopg.errors.UndefinedTable):
        return 'Table inconnue : vérifie son nom (ex. "CLIENT", avec les guillemets).'
    if isinstance(exc, psycopg.errors.UndefinedColumn):
        return 'Colonne inconnue : vérifie son nom exact et les guillemets doubles.'
    if isinstance(exc, psycopg.errors.InvalidTextRepresentation):
        return "Type de donnée incorrect : vérifie les nombres, dates et identifiants."
    if isinstance(exc, psycopg.errors.InsufficientPrivilege):
        return "Accès refusé : le compte PostgreSQL ne dispose pas des droits nécessaires."
    if isinstance(exc, psycopg.errors.QueryCanceled):
        return "La requête a dépassé le délai de 5 secondes. Simplifie-la."
    return "Requête refusée par PostgreSQL : vérifie les valeurs et les contraintes de la base."


def enregistrer(sql, valeurs, succes):
    try:
        db.ecrire(sql, valeurs)
    except (psycopg.Error, ValueError) as exc:
        detail = str(exc) if isinstance(exc, ValueError) else message_erreur(exc)
        st.error("Impossible d'enregistrer : " + detail, icon="⚠️")
    else:
        st.toast(succes + " Données enregistrées dans NeonDB.", icon="✅")
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

onglet_clients, onglet_appareils, onglet_demandes, onglet_interventions, onglet_sql = st.tabs(
    ["👤 Clients", "📱 Appareils", "📝 Demandes", "🛠️ Interventions", "🗃️ SQL Editor"]
)

with onglet_clients:
    st.subheader("Liste des clients")
    tableau(liste_clients)
    st.subheader("Ajouter un client")
    with st.form("ajout_client", clear_on_submit=True):
        id_client = st.number_input("ID_CLIENT (saisie manuelle)", min_value=1, step=1, value=max((c["ID_CLIENT"] for c in liste_clients), default=0) + 1)
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
            id_appareil = st.number_input("ID_APPAREIL (saisie manuelle)", min_value=1, step=1, value=max((a["ID_APPAREIL"] for a in liste_appareils), default=0) + 1)
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
            num_demande = st.number_input("NUM_DEMANDE (saisie manuelle)", min_value=1, step=1, value=max((d["NUM_DEMANDE"] for d in liste_demandes), default=0) + 1)
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


with onglet_sql:
    st.subheader("Schéma relationnel — RepairConnect")
    st.caption("PK soulignées dans le MLD du rapport ; ici, PK et FK sont indiquées par leur rôle. Les caractères # du MLD ne font pas partie du nom SQL.")
    mld = {
        "CLIENT": "ID_CLIENT (PK), NOM, PRENOM, EMAIL, TELEPHONE",
        "APPAREIL": "ID_APPAREIL (PK), CATEGORIE, MARQUE, MODELE, DATE_ACHAT, ID_CLIENT (FK)",
        "DEMANDE": "NUM_DEMANDE (PK), DATE_DEPOT, DESC_PANNE, STATUT, COUT_ESTIME, ID_APPAREIL (FK)",
        "TECHNICIEN": "ID_TECHNICIEN (PK), NOM, PRENOM, SPECIALITE",
        "INTERVENTION": "ID_INTERVENTION (PK), DATE_INTERVENTION, DESCRIPTION, COUT_MAINDOEUVRE, NUM_DEMANDE (FK), ID_TECHNICIEN (FK)",
        "PIECE": "REF_PIECE (PK), LIBELLE, PRIX_UNITAIRE, QUANTITE_DISPO",
        "UTILISER": "ID_INTERVENTION (PK, FK), REF_PIECE (PK, FK), QUANTITE_UTILISEE",
    }
    for nom, colonnes in mld.items():
        st.markdown(f"**{nom}** — {colonnes}")
    st.divider()
    st.subheader("Exécuter une requête PostgreSQL")
    st.info("Requêtes autorisées : SELECT, INSERT et UPDATE. DELETE, DROP, TRUNCATE et les changements de structure sont bloqués. Une seule instruction à la fois.")
    with st.form("sql_editor"):
        sql_utilisateur = st.text_area(
            "Requête SQL (respecte les majuscules et les guillemets doubles)",
            value='SELECT *\nFROM "CLIENT"\nORDER BY "ID_CLIENT" DESC;',
            height=170,
        )
        executer = st.form_submit_button("Exécuter la requête", type="primary")
    if executer:
        try:
            operation, resultat, nombre, tronque = db.executer_sql_editeur(sql_utilisateur)
            if operation == "SELECT":
                st.success("Consultation exécutée avec succès.", icon="✅")
                tableau(resultat)
                st.caption(f"{len(resultat)} ligne(s) affichée(s)" + (" (limite 500)" if tronque else ""))
            else:
                st.session_state["sql_message"] = f"{operation} exécuté : {nombre} ligne(s) concernée(s). Modifications enregistrées dans NeonDB."
                st.session_state["sql_resultat"] = resultat
                st.rerun()  # Recharge les listes et compteurs après la modification.
        except ValueError as exc:
            st.warning(str(exc), icon="⚠️")
        except psycopg.Error as exc:
            st.error(message_erreur(exc), icon="⚠️")
    if "sql_message" in st.session_state:
        st.success(st.session_state.pop("sql_message"), icon="✅")
        lignes = st.session_state.pop("sql_resultat", [])
        if lignes:
            tableau(lignes)
