
import re

import psycopg
import sqlparse
import streamlit as st
from psycopg.rows import dict_row


def connexion():
    return psycopg.connect(
        st.secrets["DATABASE_URL"],
        row_factory=dict_row,
        connect_timeout=10
    )


def lire(sql, params=()):
    with connexion() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()


def ecrire(sql, params):
    with connexion() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            nombre = cur.rowcount
        conn.commit()
        return nombre


def clients():
    return lire("""
        SELECT "ID_CLIENT", "NOM", "PRENOM",
               "EMAIL", "TELEPHONE"
        FROM "CLIENT"
        ORDER BY "ID_CLIENT" DESC
    """)


def appareils():
    return lire("""
        SELECT a."ID_APPAREIL", a."CATEGORIE",
               a."MARQUE", a."MODELE", a."DATE_ACHAT",
               a."ID_CLIENT", c."NOM", c."PRENOM"
        FROM "APPAREIL" a
        JOIN "CLIENT" c
            ON a."ID_CLIENT" = c."ID_CLIENT"
        ORDER BY a."ID_APPAREIL"
    """)


def demandes():
    return lire("""
        SELECT d."NUM_DEMANDE", d."DATE_DEPOT",
               d."DESC_PANNE", d."STATUT",
               d."COUT_ESTIME", d."ID_APPAREIL",
               a."MARQUE", a."MODELE",
               c."NOM", c."PRENOM"
        FROM "DEMANDE" d
        JOIN "APPAREIL" a
            ON d."ID_APPAREIL" = a."ID_APPAREIL"
        JOIN "CLIENT" c
            ON a."ID_CLIENT" = c."ID_CLIENT"
        ORDER BY d."NUM_DEMANDE"
    """)


def interventions(num_demande):
    return lire("""
        SELECT i."ID_INTERVENTION",
               i."DATE_INTERVENTION",
               i."DESCRIPTION",
               i."COUT_MAINDOEUVRE",
               t."NOM", t."PRENOM",
               t."SPECIALITE"
        FROM "INTERVENTION" i
        JOIN "TECHNICIEN" t
            ON i."ID_TECHNICIEN" = t."ID_TECHNICIEN"
        WHERE i."NUM_DEMANDE" = %s
        ORDER BY i."DATE_INTERVENTION",
                 i."ID_INTERVENTION"
    """, (num_demande,))


def executer_sql_editeur(sql):
    # Une seule instruction par exécution
    instructions = [
        instruction
        for instruction in sqlparse.parse(sql)
        if str(instruction).strip().strip(";").strip()
    ]

    if len(instructions) != 1:
        raise ValueError(
            "Saisissez une seule requête SQL à la fois."
        )

    instruction = instructions[0]
    operation = instruction.get_type().upper()

    # Seules les trois opérations suivantes sont acceptées
    if operation not in ("SELECT", "INSERT", "UPDATE"):
        raise ValueError(
            "Commande non autorisée. "
            "Utilisez uniquement SELECT, INSERT ou UPDATE."
        )

    sql_nettoye = sqlparse.format(
        sql, strip_comments=True
    ).strip()

    if not re.match(
        r"^(SELECT|INSERT|UPDATE)\b",
        sql_nettoye,
        re.IGNORECASE
    ):
        raise ValueError(
            "Utilisez une requête SQL directe."
        )

    if operation == "SELECT":
        if re.search(r"\bINTO\b", sql_nettoye, re.I):
            raise ValueError(
                "SELECT INTO n'est pas autorisé."
            )

        if re.search(
            r"\bFOR\s+(UPDATE|SHARE)\b",
            sql_nettoye,
            re.I
        ):
            raise ValueError(
                "Les verrouillages ne sont pas autorisés."
            )

    with connexion() as conn:
        with conn.cursor() as cur:

            # Durée maximale de la requête
            cur.execute(
                "SET LOCAL statement_timeout = '5000ms'"
            )

            if operation == "SELECT":
                cur.execute(
                    "SET TRANSACTION READ ONLY"
                )

            # Une seule instruction côté PostgreSQL
            cur.execute(sql, prepare=True)

            if cur.description:
                lignes = cur.fetchmany(501)
                tronque = len(lignes) > 500
                lignes = lignes[:500]
            else:
                lignes = []
                tronque = False

            nombre = cur.rowcount

        # Enregistrement réel des INSERT / UPDATE
        conn.commit()

    return operation, lignes, nombre, tronque
