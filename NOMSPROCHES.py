import streamlit as st
import openai
import re
import time
import logging
from difflib import SequenceMatcher
import os  # Pour récupérer la clé API depuis les secrets Streamlit

# Définir la clé API OpenAI depuis les secrets Streamlit
openai.api_key = os.getenv("OPENAI_API_KEY")

#########################
# Configuration globale
#########################

# Taille max d'un bloc
MAX_CAR = 3000
# Modèle utilisé
OPENAI_MODEL = "gpt-4o-mini"

# Titres à enlever quand ils apparaissent en début de chaîne
TITRES_A_ENLEVER = [
    "agent", "commandant", "inspecteur", "sergent",
    "m.", "mme", "madame", "monsieur",
    "l'agent", "l'inspecteur", "le sergent", "la sergente"
]

# Seuil de similarité pour détecter des noms proches
SIMILARITY_THRESHOLD = 0.7

# Configuration des logs
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

#########################
# Fonctions utilitaires
#########################

def decouper_texte_en_blocs(texte, max_car=3000):
    blocs = []
    bloc_courant = ""
    phrases = re.split(r"(?<=[\.\!\?])\s+", texte)

    for phrase in phrases:
        if len(bloc_courant) + len(phrase) > max_car:
            if bloc_courant:
                blocs.append(bloc_courant.strip())
            bloc_courant = phrase
        else:
            bloc_courant += " " + phrase

    if bloc_courant.strip():
        blocs.append(bloc_courant.strip())
    return blocs

def extraire_noms_propres_avec_gpt(texte, model="gpt-4o-mini", max_retries=5):
    prompt = f"""
Je te fournis un texte.
Ta mission : Extraire tous les noms propres (personnes, lieux, organisations, etc.)
sous forme d'une liste distincte, séparée par des virgules.

- Ne liste pas simplement tous les mots en majuscule ou en début de phrase.
- Ne corrige pas l'orthographe.
- Donne-moi seulement une liste brute (séparée par des virgules).

Texte :
{texte}
"""
    for attempt in range(max_retries):
        try:
            completion = openai.ChatCompletion.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
            )
            reponse = completion.choices[0].message["content"].strip()
            noms_bruts = [x.strip() for x in reponse.split(",") if x.strip()]
            return set(noms_bruts)
        except openai.error.RateLimitError:
            logging.warning(f"Rate limit atteint. Tentative {attempt + 1}/{max_retries}. Attente 5s...")
            time.sleep(5)
        except Exception as e:
            logging.error(f"Erreur d'appel GPT : {e}")
            return set()

    logging.error("Impossible d'extraire les noms après plusieurs tentatives.")
    return set()

def retirer_titre_debut(token):
    token_lower = token.lower()
    for t in TITRES_A_ENLEVER:
        prefix_regex = r"^" + re.escape(t) + r"([\s\.\,\!]|$)"
        match = re.match(prefix_regex, token_lower)
        if match:
            debut = match.end()
            token = token[debut:].lstrip(" .,\t!?")
            break
    return token

def decouper_et_nettoyer(nom_brut):
    nettoye = nom_brut.strip(".,;!?\"'()[]{}:«»")
    parts = nettoye.split()

    resultat = []
    for p in parts:
        p_clean = retirer_titre_debut(p)
        if p_clean:
            resultat.append(p_clean)
    return resultat

def filtrer_noms(liste_brute):
    final_set = set()
    for elem in liste_brute:
        morceaux = decouper_et_nettoyer(elem)
        for m in morceaux:
            if m and m[0].isupper():
                final_set.add(m)
    return sorted(final_set)

def detecter_noms_proches(liste_noms, seuil=SIMILARITY_THRESHOLD):
    noms_proches = []
    for i, nom1 in enumerate(liste_noms):
        for nom2 in liste_noms[i + 1:]:
            similarity = SequenceMatcher(None, nom1, nom2).ratio()
            if similarity >= seuil:
                noms_proches.append((nom1, nom2))
    return noms_proches

#########################
# Fonction principale
#########################

def traiter_texte(texte_source):
    blocs = decouper_texte_en_blocs(texte_source, max_car=MAX_CAR)
    tous_noms_bruts = set()
    for i, bloc in enumerate(blocs):
        logging.info(f"Traitement du bloc {i + 1}/{len(blocs)} (longueur {len(bloc)} caractères)...")
        noms_bloc = extraire_noms_propres_avec_gpt(bloc, model=OPENAI_MODEL)
        tous_noms_bruts.update(noms_bloc)
    liste_finale = filtrer_noms(tous_noms_bruts)
    noms_proches = detecter_noms_proches(liste_finale)
    return noms_proches, liste_finale
