import streamlit as st
import pandas as pd
import altair as alt
import datetime

from core.scoring.scoring_service import load_players_data, compute_all_players_points
from core.ibu.client import IBUClient
from utils.ui_components import sidebar_menu, user_header
from utils.biathlon_data import VENUES_NAMES
from utils.user_warnings import check_new_results, show_toast
from utils.auth import get_mapping_id_to_name, convert_league_id_to_name, get_league_members


# ---------------------------------------------------------
# Configuration de la page
# ---------------------------------------------------------

st.session_state["current_page"] = "3b_Evolution_Classement"

sidebar_menu()
user_id = st.session_state.get("user")
if user_id:
    id_to_name = get_mapping_id_to_name()
    username = id_to_name[user_id]
else:
    username = None
club_id = st.session_state.get("current_league")
club_name = convert_league_id_to_name(club_id)
user_header(username, club_name)

if not user_id:
    st.error("Tu dois être connecté pour accéder à cette page.")
    st.stop()


# ---------------------------------------------------------
# Chargement des données IBU via IBUClient
# ---------------------------------------------------------
# On utilise ici IBUClient pour :
#   - charger les venues
#   - charger les résultats course par course
#   - reconstruire les standings cumulés après chaque venue
#   - fournir les standings finaux (BiathlonStandings)
league_members = get_league_members(club_id)
try:
    players_predictions = load_players_data(league_members)
except KeyError as e:
    if str(e) == "'NO_PRONOS'":
        st.info(
            "Aucun joueur n’a encore rempli ses pronostics.\n\n"
            "👉 Commence par saisir les tiens dans la page **Saisie des pronostics**."
        )
        st.stop()
    else:
        raise


# ---------------------------------------------------------
# Chargement des données IBU via IBUClient
# ---------------------------------------------------------
# On utilise ici IBUClient pour :
#   - charger les venues
#   - charger les résultats course par course
#   - reconstruire les standings cumulés après chaque venue
#   - fournir les standings finaux (BiathlonStandings)

ibu = IBUClient("2526")
ibu.compute_evolutive_standings()
cumulated_standings = ibu.cumulated_standings


# ---------------------------------------------------------
# Pop-up si de nouveaux résultats sont disponibles
# ---------------------------------------------------------

if user_id and check_new_results(user_id):
    show_toast("🎉 Les résultats du dernier week-end sont disponibles !")


# ---------------------------------------------------------
# Construction de la timeline des points fantasy
# ---------------------------------------------------------
timeline_rows = []

for nb_venue in cumulated_standings:
    men_temp = cumulated_standings[nb_venue]["Men"]
    women_temp = cumulated_standings[nb_venue]["Women"]

    venue = ibu.competitions.venues[nb_venue - 1]

    if datetime.datetime.now().date() < venue.end_date:
        continue

    # Calcul des points fantasy
    scoring = compute_all_players_points(players_predictions, men_temp, women_temp)

    venue_name = VENUES_NAMES[ibu.competitions.venues[nb_venue - 1].epreuves[0].location]

    for p in scoring.values():
        timeline_rows.append({
            "venue": nb_venue,
            "venue_name": venue_name,
            "player": id_to_name [p.player],
            "points": p.total_points
        })

df_timeline = pd.DataFrame(timeline_rows)

df_timeline["venue_order"] = df_timeline["venue"]

ordered_names = (
    df_timeline.sort_values("venue_order")["venue_name"]
    .unique()
    .tolist()
)

df_timeline["venue_name"] = pd.Categorical(
    df_timeline["venue_name"],
    categories=ordered_names,
    ordered=True
)


# ---------------------------------------------------------
# Titre et message pour l'utilisateur
# ---------------------------------------------------------

st.title("📉 Évolution du classement")

st.markdown(
    "Évolution des points fantasy **après chaque week-end**, "
    "calculée à partir des classements IBU reconstruits (général + globes)."
)

st.markdown(
    """
    <div style="
        padding: 12px 16px;
        background-color: #fff4e5;
        border-left: 4px solid #ffa726;
        border-radius: 4px;
        margin-bottom: 20px;
        font-size: 15px;
    ">
        ⚠️ <strong>Attention :</strong> cette page n’est actualisée qu’à la fin de chaque week-end de compétitions.
        Les résultats intermédiaires ne sont pas pris en compte avant la fin du week-end.
    </div>
    """,
    unsafe_allow_html=True
)


# ---------------------------------------------------------
# Graphique d’évolution
# ---------------------------------------------------------

st.subheader("📈 Évolution des points fantasy")

y_min = df_timeline["points"].min()
y_max = df_timeline["points"].max()

base = alt.Chart(df_timeline).encode(
    x=alt.X(
        "venue_name:N",
        title="Week-end",
        sort=ordered_names   # 👈 impose l'ordre temporel
    ),
    y=alt.Y(
        "points:Q",
        title="Points fantasy",
        scale=alt.Scale(domain=[y_min - 50, y_max + 50])
    ),
    color=alt.Color("player:N", title="Joueur"),
    tooltip=[
        alt.Tooltip("player:N", title="Joueur"),
        alt.Tooltip("venue_name:N", title="Week-end"),
        alt.Tooltip("points:Q", title="Points")
    ]
)

hover = alt.selection_point(
    on="mouseover",
    fields=["player", "venue_name"],
    nearest=True,
    empty=False
)

# Lignes des autres joueurs
others = base.transform_filter(
    alt.datum.player != user_id
).mark_line().encode(
    opacity=alt.condition(hover, alt.value(1), alt.value(0.3)),
    strokeWidth=alt.condition(hover, alt.value(3), alt.value(1.5))
)

# Ligne du joueur connecté
highlight = base.transform_filter(
    alt.datum.player == user_id
).mark_line(color="red").encode(
    opacity=alt.condition(hover, alt.value(1), alt.value(0.6)),
    strokeWidth=alt.condition(hover, alt.value(5), alt.value(3))
)

# Points visibles uniquement au survol
points = base.mark_circle(size=80).encode(
    opacity=alt.condition(hover, alt.value(1), alt.value(0)),
    tooltip=[
        alt.Tooltip("player:N", title="Joueur"),
        alt.Tooltip("venue:O", title="Week-end"),
        alt.Tooltip("points:Q", title="Points")
    ]
).add_params(hover)

chart = (others + highlight + points).properties(height=450)

st.altair_chart(chart, use_container_width=True)


# ---------------------------------------------------------
# Tableau détaillé
# ---------------------------------------------------------

st.subheader("📋 Détail des points par week-end")

pivot = df_timeline.pivot(index="player", columns="venue_name", values="points").fillna(0)
pivot = pivot.loc[pivot.sum(axis=1).sort_values(ascending=False).index]
pivot.index.name = "Joueur"

st.dataframe(pivot, use_container_width=True)
