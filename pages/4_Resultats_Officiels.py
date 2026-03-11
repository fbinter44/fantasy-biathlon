import streamlit as st
import altair as alt

from core.ibu.client import IBUClient
from core.scoring.scoring_service import load_players_data, get_user_predictions
from utils.ui_components import sidebar_menu, user_header, page_title_with_feedback
from utils.biathlon_data import DISCIPLINES_DISPLAY, DISCIPLINES_WINNERS, ids_to_names
from utils.visualisation_utils import make_highlighter
from utils.charts import make_points_chart
from utils.table_display import display_results_table


# ---------------------------------------------------------
# Configuration de la page
# ---------------------------------------------------------

st.session_state["current_page"] = "4_Resultats_Officiels"

sidebar_menu()
user_header()

st.set_page_config(layout="wide")

st.title("📊 Résultats Officiels")
st.write("Classements officiels des différentes disciplines (Hommes & Femmes).")


# ---------------------------------------------------------
# Chargement des standings officiels via IBUClient
# ---------------------------------------------------------
# On utilise ici IBUClient (core/ibu/client.py), qui centralise
# tous les accès à l’API IBU. Cela permet :
#   - d’avoir un point d’entrée unique
#   - de garder une architecture propre et modulaire
#   - de remplacer facilement la source de données plus tard
#
# IBUClient.standings(gender) renvoie un objet BiathlonStandings,
# qui expose les DataFrames top 10 pour :
#   - general
#   - sprint
#   - pursuit
#   - individual
#   - mass_start
#
# Ces DataFrames sont ensuite affichés dans les tableaux et graphiques.

ibu = IBUClient("2526")
men_results, women_results = ibu.load_standings()

my_preds = get_user_predictions(st.session_state.get("user"))


# ---------------------------------------------------------
# Affichage discipline par discipline
# ---------------------------------------------------------

for attr, display_name in DISCIPLINES_DISPLAY:
    st.markdown(f"## 🏅 {display_name}")

    col1, col2 = st.columns(2)

    df_men = getattr(men_results, attr)
    df_women = getattr(women_results, attr)

    if attr == 'general':
        my_top_men = getattr(my_preds, f'{DISCIPLINES_WINNERS[attr]}_men').tolist()
        my_top_women = getattr(my_preds, f'{DISCIPLINES_WINNERS[attr]}_women').tolist()
    else:
        my_top_men = [getattr(my_preds, DISCIPLINES_WINNERS[attr]).winner_men]
        my_top_women = [getattr(my_preds, DISCIPLINES_WINNERS[attr]).winner_women]

    fav_men = ids_to_names(df_men, my_top_men)
    fav_women = ids_to_names(df_women, my_top_women)

    highlighter_men = make_highlighter(fav_men)
    highlighter_women = make_highlighter(fav_women)

    with col1:
        display_results_table(df_men, highlighter_men, "Hommes")
        st.subheader("Écarts – Hommes")
        st.altair_chart(make_points_chart(df_men.head(10), "#1f77b4").properties(height=350), use_container_width=True)

    with col2:
        display_results_table(df_women, highlighter_women, "Femmes")
        st.subheader("Écarts – Femmes")
        st.altair_chart(make_points_chart(df_women.head(10), "#e377c2").properties(height=350), use_container_width=True)

    st.markdown("---")
