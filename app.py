import streamlit as st
import NOMSPROCHES  # On importe les fonctions de NOMSPROCHES.py

def generer_fichier_txt(noms_proches, liste_finale):
    """
    Génère le contenu d'un fichier texte à partir des résultats.
    """
    contenu = "Noms proches à vérifier :\n"
    for nom1, nom2 in noms_proches:
        contenu += f"{nom1} - {nom2}\n"

    contenu += "\nListe de tous les noms trouvés :\n"
    for nom in liste_finale:
        contenu += f"{nom}\n"

    return contenu

def main():
    st.title("Extraction de Noms Propres")
    st.write("Saisissez ou collez du texte ci-dessous, puis cliquez sur 'Extraire'.")

    # Zone de texte pour le contenu
    texte_source = st.text_area("Texte à analyser", height=200)

    if st.button("Extraire"):
        if texte_source.strip():
            noms_proches, liste_finale = NOMSPROCHES.traiter_texte(texte_source)

            # Affichage des éventuels noms proches
            st.subheader("Noms proches à vérifier")
            if noms_proches:
                for (nom1, nom2) in noms_proches:
                    st.write(f"{nom1} - {nom2}")
            else:
                st.write("Aucun nom proche détecté.")

            # Affichage de la liste de noms
            st.subheader("Liste de tous les noms trouvés")
            if liste_finale:
                for nom in liste_finale:
                    st.write(nom)
            else:
                st.write("Aucun nom trouvé.")

            # Génération du fichier .txt
            contenu_fichier = generer_fichier_txt(noms_proches, liste_finale)

            # Bouton pour télécharger le fichier
            st.download_button(
                label="Télécharger les résultats",
                data=contenu_fichier,
                file_name="resultats_noms.txt",
                mime="text/plain"
            )
        else:
            st.warning("Veuillez saisir un texte avant de cliquer sur 'Extraire'.")

if __name__ == "__main__":
    main()
