import streamlit as st
from utils.ui_components import sidebar_menu, user_header
from utils.auth import convert_id_to_name, convert_league_id_to_name

# ---------------------------------------------------------
# Identification de la page (permet de garder le menu
# "Pronostics" replié ou ouvert selon la navigation)
# ---------------------------------------------------------
st.session_state["current_page"] = "5_Reglement"
user_id = st.session_state.get("user")
username = convert_id_to_name(user_id)
club_id = st.session_state.get("current_league")
club_name = convert_league_id_to_name(club_id)

# ---------------------------------------------------------
# Configuration de la page (titre navigateur, largeur)
# ---------------------------------------------------------
st.set_page_config(page_title="Règlement", layout="wide")

# ---------------------------------------------------------
# Barre latérale + header utilisateur
# (affichés pour cohérence globale de l'application)
# ---------------------------------------------------------
sidebar_menu()
user_header(username, club_name)

# ---------------------------------------------------------
# Contenu principal : règlement du jeu
# ---------------------------------------------------------
st.title("📘 Règlement du jeu de pronostics")

st.markdown("""
## 🎯 Objectif du jeu
Le jeu consiste à prédire les performances des biathlètes sur l’ensemble de la saison.  
Chaque joueur doit sélectionner :
- un **Top 5 Hommes**,
- un **Top 5 Femmes**,
- les **vainqueurs des globes** (Sprint, Poursuite, Individuel, Mass Start).

L’objectif est d’obtenir le maximum de points en fonction des résultats réels de la saison.

---

## 🧭 Ce que chaque joueur doit faire
Chaque participant doit :
1. Choisir ses **5 biathlètes hommes** dans l’ordre.
2. Choisir ses **5 biathlètes femmes** dans l’ordre.
3. Sélectionner un **vainqueur pour chaque globe**.
4. Valider ses choix **avant le début de la saison**.

Une fois validés, les pronostics sont **définitifs**.

---

## ⏱️ Deadline et verrouillage
Les pronostics doivent être complétés **avant la première course de la saison**.  
Dès que la saison commence :
- les choix sont **verrouillés**,
- aucune modification n’est possible,
- les joueurs conservent leurs pronostics jusqu’à la fin de la saison.

---

## 🧮 Calcul des points

### Top 5
Des points sont attribués dès lors que le biathlète figure dans le top 10 du classement général. Les points correspondent au barème de l'IBU pour une course standard :
- **1er** → 90 points  
- **2ème** → 75 points  
- **3ème** → 65 points  
- **4ème** → 55 points  
- **5ème** → 50 points
- **6ème** → 45 points
- **7ème** → 41 points
- **8ème** → 37 points
- **9ème** → 34 points
- **10ème** → 31 points
            
Voir https://www.biathlonworld.com/fr/discover-biathlon/how-it-works/rankings-points pour plus d'informations.

De plus, un bonus de 50 points est attribué pour chaque biathlète bien placé.

### Globes
Pour chaque globe :
- **bon vainqueur** → 50 points  
- **mauvais vainqueur** → 0 point  

### Classement final
Le total des points Top 5 + Globes détermine le classement général des joueurs.

---

## 📌 Rappel important
Les pronostics sont **définitifs** dès le début de la saison.  
Aucune modification ne sera acceptée une fois la première course lancée.
""")
