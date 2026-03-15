import streamlit as st
import altair as alt

from core.ibu.client import IBUClient
from core.scoring.scoring_service import load_players_data, get_user_predictions
from utils.ui_components import sidebar_menu, user_header, page_title_with_feedback
from utils.biathlon_data import DISCIPLINES_DISPLAY, DISCIPLINES_WINNERS, ids_to_names
from utils.visualisation_utils import make_highlighter
from utils.charts import make_points_chart
from utils.table_display import display_results_table, is_finalized


# ---------------------------------------------------------
# Configuration de la page
# ---------------------------------------------------------
st.set_page_config(layout="wide")

st.session_state["current_page"] = "4_Resultats_Officiels"

sidebar_menu()
user_header()

st.title("📊 Résultats Officiels")


# ---------------------------------------------------------
# Bandeau de navigation des disciplines
# ---------------------------------------------------------

options = {attr: display for attr, display in DISCIPLINES_DISPLAY}
keys = list(options.keys())

current = st.session_state.get("results_filter", "general")
index = keys.index(current)

selected = st.radio(
    "Choisis une discipline",
    keys,
    index=index,
    format_func=lambda x: options[x],
    horizontal=True,
    key="results_filter"
)

st.markdown("""
<style>
/* Cache le label */
div[data-testid="stRadio"] > label {
    display: none;
}

/* Conteneur horizontal */
div[data-testid="stRadio"] > div {
    flex-direction: row !important;
    gap: 10px;
}

/* Boutons pill */
div[data-testid="stRadio"] div[role="radiogroup"] > label {
    border-radius: 20px;
    padding: 6px 18px;
    border: 1px solid #1e88e5;
    background-color: #e8f4ff;
    color: #1e88e5;
    font-weight: 600;
    cursor: pointer;
    transition: 0.2s ease-in-out;
}

/* Bouton actif */
div[data-testid="stRadio"] div[role="radiogroup"] > label[data-checked="true"] {
    background-color: #1e88e5;
    color: white;
}

/* Hover */
div[data-testid="stRadio"] div[role="radiogroup"] > label:hover {
    background-color: #d0e6ff;
}
</style>
""", unsafe_allow_html=True)


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
# Récupérer l'état d'avancement de la saison
# ---------------------------------------------------------

ibu.get_season_progress()

# ---------------------------------------------------------
# Affichage discipline par discipline
# ---------------------------------------------------------

selected = st.session_state["results_filter"]

for attr, display_name in DISCIPLINES_DISPLAY:
    if attr != selected:
        continue  # on n'affiche que la discipline sélectionnée

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

    past_races_men = ibu.season_progress["Men"][attr]["finished_races"]
    past_races_women = ibu.season_progress["Women"][attr]["finished_races"]
    total_races_men = ibu.season_progress["Men"][attr]["total_races"]
    total_races_women = ibu.season_progress["Women"][attr]["total_races"]

    finalized_men, awarded_men = is_finalized(df_men, past_races_men, total_races_men)
    finalized_women, awarded_women = is_finalized(df_women, past_races_women, total_races_women)
    
    fav_men = ids_to_names(df_men, my_top_men)
    fav_women = ids_to_names(df_women, my_top_women)

    highlighter_men = make_highlighter(fav_men, highlight_leader=finalized_men or awarded_men)
    highlighter_women = make_highlighter(fav_women, highlight_leader=finalized_women or awarded_women)

    with col1:
        display_results_table(df_men, highlighter_men, "Hommes", past_races_men, total_races_men, attr)
        st.subheader("Écarts – Hommes")
        st.altair_chart(make_points_chart(df_men.head(10), "#1f77b4").properties(height=350), use_container_width=True)

    with col2:
        display_results_table(df_women, highlighter_women, "Femmes", past_races_women, total_races_women, attr)
        st.subheader("Écarts – Femmes")
        st.altair_chart(make_points_chart(df_women.head(10), "#e377c2").properties(height=350), use_container_width=True)

    st.markdown("---")
