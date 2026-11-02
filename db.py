"""Accès PostgreSQL Neon pour RepairConnect (noms SQL conformes au MLD)."""
import psycopg
import streamlit as st
from psycopg.rows import dict_row


def connexion():
    # Un accès par opération : simple et robuste face à la mise en veille de Neon.
    return psycopg.connect(st.secrets["DATABASE_URL"], row_factory=dict_row, connect_timeout=10)


def lire(sql, params=()):
    with connexion() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()


def ecrire(sql, params):
    with connexion() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            n = cur.rowcount
        conn.commit()
        return n


def clients():
    return lire('SELECT "ID_CLIENT", "NOM", "PRENOM", "EMAIL", "TELEPHONE" FROM "CLIENT" ORDER BY "ID_CLIENT"')


def appareils():
    return lire('''SELECT a."ID_APPAREIL", a."CATEGORIE", a."MARQUE", a."MODELE", a."DATE_ACHAT",
                         a."ID_CLIENT", c."NOM", c."PRENOM"
                  FROM "APPAREIL" a JOIN "CLIENT" c ON a."ID_CLIENT" = c."ID_CLIENT"
                  ORDER BY a."ID_APPAREIL"''')


def demandes():
    return lire('''SELECT d."NUM_DEMANDE", d."DATE_DEPOT", d."DESC_PANNE", d."STATUT", d."COUT_ESTIME",
                         d."ID_APPAREIL", a."MARQUE", a."MODELE", c."NOM", c."PRENOM"
                  FROM "DEMANDE" d
                  JOIN "APPAREIL" a ON d."ID_APPAREIL" = a."ID_APPAREIL"
                  JOIN "CLIENT" c ON a."ID_CLIENT" = c."ID_CLIENT"
                  ORDER BY d."NUM_DEMANDE"''')


def interventions(num_demande):
    return lire('''SELECT i."ID_INTERVENTION", i."DATE_INTERVENTION", i."DESCRIPTION",
                         i."COUT_MAINDOEUVRE", t."NOM", t."PRENOM", t."SPECIALITE"
                  FROM "INTERVENTION" i
                  JOIN "TECHNICIEN" t ON i."ID_TECHNICIEN" = t."ID_TECHNICIEN"
                  WHERE i."NUM_DEMANDE" = %s
                  ORDER BY i."DATE_INTERVENTION", i."ID_INTERVENTION"''', (num_demande,))
