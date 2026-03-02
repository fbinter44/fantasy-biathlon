import streamlit as st
import pandas as pd
import altair as alt
import datetime

from scorer.players_points import load_players_data, compute_all_players_points
from scorer.competitions_results import Season
from scorer.results_data import BiathlonTempStandings
from utils.ui import sidebar_menu, user_header
from utils.config import VENUES_NAMES


st.session_state["current_page"] = "3b_Evolution_Classement"

# ---------------------------------------------------------
# UI & sécurité utilisateur
# ---------------------------------------------------------
sidebar_menu()
user_header()

user = st.session_state.get("user")

if not user:
    st.error("Tu dois être connecté pour accéder à cette page.")
    st.stop()

# ---------------------------------------------------------
# Chargement des pronostics
# ---------------------------------------------------------
try:
    players_predictions = load_players_data()
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
# Chargement de la saison + timeline + index athlètes
# ---------------------------------------------------------
season = Season("2526")
season.load_venues()
season.load_all_results()
season.build_ibu_standings_after_each_venue()

# ---------------------------------------------------------
# Construction de la timeline des points fantasy
# ---------------------------------------------------------
timeline_rows = []

for v in range(1, season.nb_venues + 1):
    if datetime.datetime.now().date() <= season.venues[v-1].end_date:
        continue

    men_temp = BiathlonTempStandings(season, "Men", v)
    men_temp.load()

    women_temp = BiathlonTempStandings(season, "Women", v)
    women_temp.load()

    scoring = compute_all_players_points(players_predictions, men_temp, women_temp)

    v_name = VENUES_NAMES[season.venues[v-1].epreuves[0].location]

    for p in scoring.values():
        timeline_rows.append({
            "venue": v,
            "venue_name": v_name,
            "player": p.player,
            "points": p.total_points
        })

df_timeline = pd.DataFrame(timeline_rows)

df_timeline["venue_order"] = df_timeline["venue"]

# Définir l'ordre temporel
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
# Titre
# ---------------------------------------------------------
st.title("📉 Évolution du classement")

st.markdown(
    "Évolution des points fantasy **après chaque week-end**, "
    "calculée à partir des classements IBU reconstruits (général + globes)."
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
    alt.datum.player != user
).mark_line().encode(
    opacity=alt.condition(hover, alt.value(1), alt.value(0.3)),
    strokeWidth=alt.condition(hover, alt.value(3), alt.value(1.5))
)

# Ligne du joueur connecté
highlight = base.transform_filter(
    alt.datum.player == user
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