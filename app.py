import streamlit as st
import NOMSPROCHES  # On importe le module NOMSPROCHES

def main():
    st.title("Extraction de Noms Propres")
    texte = st.text_area("Entrez le texte à analyser :")

    if st.button("Extraire"):
        if texte.strip():
            # Appel de la fonction traiter_texte (définie dans NOMSPROCHES.py)
            noms_proches, liste_finale = NOMSPROCHES.traiter_texte(texte)
            
            # Affichage des noms proches
            st.subheader("Noms proches à vérifier")
            if noms_proches:
                for (nom1, nom2) in noms_proches:
                    st.write(f"{nom1} - {nom2}")
            else:
                st.write("Aucun nom proche détecté.")
            
            # Affichage de la liste de tous les noms
            st.subheader("Liste de tous les noms trouvés")
            if liste_finale:
                for nom in liste_finale:
                    st.write(nom)
            else:
                st.write("Aucun nom trouvé.")
        else:
            st.warning("Veuillez saisir du texte avant de cliquer sur 'Extraire'.")

if __name__ == "__main__":
    main()