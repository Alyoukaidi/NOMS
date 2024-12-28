import streamlit as st
import openai
import re
import time
import logging
import sys
from difflib import SequenceMatcher

# 1) Import de la clé OpenAI
# Remplacez le chemin ci-dessous par le vôtre, ou mettez directement OPENAI_API_KEY = "votre_clé" dans ce script
sys.path.insert(0, r"C:\\Users\\wam\\Desktop\\programmes_chatgpt\\FINE_TUNING\\KEY")
from config import OPENAI_API_KEY
openai.api_key = OPENAI_API_KEY

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

# Configuration des logs (facultatif, utile surtout en local)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

#########################
# Fonctions utilitaires
#########################

def decouper_texte_en_blocs(texte, max_car=3000):
    """
    Découpe le texte en blocs cohérents, sans couper au milieu des phrases.
    """
    blocs = []
    bloc_courant = ""

    # Découpe par phrases terminées par ".", "!" ou "?"
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
    """
    Envoie le texte à GPT pour extraire les noms propres avec gestion des erreurs et retries.
    """
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
    """
    Retire un titre en début de chaîne, tout en conservant la casse du reste.
    """
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
    """
    Enlève la ponctuation de début/fin, retire les titres et découpe les noms multiples.
    """
    nettoye = nom_brut.strip(".,;!?\"'()[]{}:«»")
    parts = nettoye.split()

    resultat = []
    for p in parts:
        p_clean = retirer_titre_debut(p)
        if p_clean:
            resultat.append(p_clean)
    return resultat

def filtrer_noms(liste_brute):
    """
    Filtre les noms en excluant ceux qui commencent par une minuscule.
    """
    final_set = set()
    for elem in liste_brute:
        morceaux = decouper_et_nettoyer(elem)
        for m in morceaux:
            if m and m[0].isupper():  # Garde uniquement les mots commençant par une majuscule
                final_set.add(m)
    return sorted(final_set)

def detecter_noms_proches(liste_noms, seuil=SIMILARITY_THRESHOLD):
    """
    Détecte les noms propres très proches en utilisant la similarité de Levenshtein.
    """
    noms_proches = []
    for i, nom1 in enumerate(liste_noms):
        for nom2 in liste_noms[i + 1:]:
            similarity = SequenceMatcher(None, nom1, nom2).ratio()
            if similarity >= seuil:
                noms_proches.append((nom1, nom2))
    return noms_proches

#########################
# Fonction de traitement
#########################

def traiter_texte(texte_source):
    """
    Remplace la logique initiale qui lisait IN.txt,
    pour accepter un texte brut (saisi dans Streamlit).
    """
    # 1. Découpage en blocs
    blocs = decouper_texte_en_blocs(texte_source, max_car=MAX_CAR)

    # 2. Extraction par GPT
    tous_noms_bruts = set()
    for i, bloc in enumerate(blocs):
        logging.info(f"Traitement du bloc {i + 1}/{len(blocs)} (longueur {len(bloc)} caractères)...")
        noms_bloc = extraire_noms_propres_avec_gpt(bloc, model=OPENAI_MODEL)
        tous_noms_bruts.update(noms_bloc)

    # 3. Nettoyage final
    liste_finale = filtrer_noms(tous_noms_bruts)

    # 4. Détection des noms proches
    noms_proches = detecter_noms_proches(liste_finale)

    return noms_proches, liste_finale

#########################
# Interface Streamlit
#########################

def main():
    st.title("Extraction de Noms Propres")
    st.write("Saisissez ou collez du texte ci-dessous, puis cliquez sur 'Extraire'.")

    # Zone de texte pour le contenu
    texte_source = st.text_area("Texte à analyser", height=200)

    if st.button("Extraire"):
        if texte_source.strip():
            noms_proches, liste_finale = traiter_texte(texte_source)
            
            # Affichage des éventuels noms proches
            if noms_proches:
                st.subheader("Noms proches à vérifier")
                for (nom1, nom2) in noms_proches:
                    st.write(f"{nom1} - {nom2}")
            
            # Affichage de la liste de noms
            st.subheader("Liste de tous les noms trouvés")
            if liste_finale:
                for nom in liste_finale:
                    st.write(nom)
            else:
                st.write("Aucun nom n'a été trouvé.")
        else:
            st.warning("Veuillez saisir un texte avant de cliquer sur 'Extraire'.")

if __name__ == "__main__":
    main()
