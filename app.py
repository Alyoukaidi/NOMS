import streamlit as st
import openai
from config import OPENAI_API_KEY  # Assurez-vous que la clé API est dans ce fichier

# Définir la clé API
openai.api_key = OPENAI_API_KEY

def extraire_noms(texte):
    """
    Remplacez cette fonction par l'appel à votre fonction d'extraction de noms
    """
    prompt = f"""
    Je te fournis un texte.
    Ta mission : Extraire tous les noms propres (personnes, lieux, organisations, etc.)
    sous forme d'une liste distincte, séparée par des virgules.

    Texte :
    {texte}
    """
    # Envoi de la requête à OpenAI
    try:
        response = openai.Completion.create(
            engine="text-davinci-003",  # Utilisez le modèle qui correspond à vos besoins
            prompt=prompt,
            max_tokens=1000,
            temperature=0.0
        )
        # Traitement de la réponse et extraction des noms
        noms_bruts = response.choices[0].text.strip()
        noms = noms_bruts.split(",")
        return noms
    except Exception as e:
        st.error(f"Une erreur s'est produite lors de l'appel à l'API OpenAI: {e}")
        return []

# Interface Streamlit
st.title("Extraction de Noms Propre")
texte = st.text_area("Entrez le texte ici")

if st.button("Extraire les Noms"):
    if texte:
        noms = extraire_noms(texte)
        st.write("Noms extraits:", noms)
    else:
        st.warning("Veuillez entrer un texte.")
