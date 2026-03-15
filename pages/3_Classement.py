import streamlit as st
import pandas as pd
import altair as alt

from core.scoring.scoring_service import load_players_data, compute_all_players_points
from core.ibu.client import IBUClient
from utils.ui_components import sidebar_menu, user_header
from utils.visualisation_utils import player_podium_card
from utils.user_warnings import check_new_standings, show_toast


# ---------------------------------------------------------
# Configuration de la page
# ---------------------------------------------------------

st.session_state["current_page"] = "3_Classement"

sidebar_menu()
user_header()

user = st.session_state.get("user")

if not user:
    st.error("Tu dois être connecté pour accéder à cette page.")
    st.stop()


# ---------------------------------------------------------
# Chargement des pronostics joueurs
# ---------------------------------------------------------

try:
    players_predictions = load_players_data()
except KeyError as e:
    if str(e) == "'NO_PRONOS'":
        st.info(
            "Aucun joueur n’a encore rempli ses pronostics.\n\n"
            "👉 Commence par saisir les tiens dans la page **Voir/Modifier mes pronos**."
        )
        st.stop()
    else:
        raise


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

ibu = IBUClient("2526")

men_results = ibu.current_men_standings
men_results.load_all()

women_results = ibu.current_women_standings
women_results.load_all()


# ---------------------------------------------------------
# Pop-up si de nouveaux résultats sont disponibles
# ---------------------------------------------------------

if user and check_new_standings(user):
    show_toast("🎉 De nouveaux résultats sont sortis ! Va voir si ça t’arrange 😉")


# ---------------------------------------------------------
# Calcul du scoring
# ---------------------------------------------------------

scoring_summary = compute_all_players_points(players_predictions, men_results, women_results)

st.set_page_config(layout="wide")

st.title("🏆 Classement général")


# ---------------------------------------------------------
# Construction du DataFrame
# ---------------------------------------------------------

ranking = sorted(
    scoring_summary.values(),
    key=lambda p: p.total_points,
    reverse=True
)

df = pd.DataFrame([
    {
        "Joueur": p.player,
        "Total": p.total_points,
        "Hommes": p.total_men_points,
        "Femmes": p.total_women_points,
        "Bonus place": p.bonus_right_place,
        "Bonus globes": p.bonus_globes,
    }
    for p in ranking
])


# ---------------------------------------------------------
# Mise en avant du Top 3
# ---------------------------------------------------------

st.subheader("🥇 Top 3")

col1, col2, col3 = st.columns([1, 1, 1])

top3 = df.head(3)

with col1:
    player_podium_card(
        rank=1,
        player=top3.iloc[0]["Joueur"],
        total_points=top3.iloc[0]["Total"],
        bonus_points=top3.iloc[0]["Bonus place"] + top3.iloc[0]["Bonus globes"]
    )

with col2:
    if len(top3) > 1:
        player_podium_card(
            rank=2,
            player=top3.iloc[1]["Joueur"],
            total_points=top3.iloc[1]["Total"],
            bonus_points=top3.iloc[1]["Bonus place"] + top3.iloc[1]["Bonus globes"]
        )

with col3:
    if len(top3) > 2:
        player_podium_card(
            rank=3,
            player=top3.iloc[2]["Joueur"],
            total_points=top3.iloc[2]["Total"],
            bonus_points=top3.iloc[2]["Bonus place"] + top3.iloc[2]["Bonus globes"]
        )

st.markdown("---")


# ---------------------------------------------------------
# Tableau complet
# ---------------------------------------------------------

st.subheader("📋 Tableau complet")

st.dataframe(df, use_container_width=True, hide_index=True)

st.markdown("---")


# ---------------------------------------------------------
# Graphique comparatif
# ---------------------------------------------------------

st.subheader("📊 Répartition des points")

chart = alt.Chart(df).mark_bar(size=25).encode(
    x=alt.X(
        "Joueur:N",
        sort=df["Joueur"].tolist(),                 # ordre imposé
        axis=alt.Axis(title=None, labelAngle=0)
    ),
    y=alt.Y("Total:Q", title="Points"),
    color=alt.Color("Joueur:N", legend=None)
)

labels = alt.Chart(df).mark_text(
    align="center",
    baseline="bottom",
    dy=-5,
    color="black",
    fontSize=12
).encode(
    x=alt.X("Joueur:N", sort=df["Joueur"].tolist()),
    y="Total:Q",
    text="Total:Q"
)

st.altair_chart((chart + labels).properties(height=400), use_container_width=True)


# ---------------------------------------------------------
# Graphique Hommes vs Femmes
# ---------------------------------------------------------

st.subheader("👥 Points Hommes vs Femmes")

df_long = df.melt(id_vars="Joueur", value_vars=["Hommes", "Femmes"])

bars = alt.Chart(df_long).mark_bar(size=25).encode(
    x=alt.X(
        "Joueur:N",
        sort=df["Joueur"].tolist(),                 # ordre imposé
        axis=alt.Axis(title=None, labelAngle=0)
    ),
    y=alt.Y("value:Q", title="Points"),
    color=alt.Color("variable:N", title="Catégorie"),
    xOffset="variable:N"
)

labels = alt.Chart(df_long).mark_text(
    align="center",
    baseline="bottom",
    dy=-5,
    color="black",
    fontSize=11
).encode(
    x=alt.X("Joueur:N", sort=df["Joueur"].tolist()),
    y="value:Q",
    text="value:Q",
    xOffset="variable:N"
)

st.altair_chart((bars + labels).properties(height=400), use_container_width=True)


# -----------------------------
# BONUS GOURMAND
# -----------------------------

st.subheader("🍫 Bonus Gourmand")

# On passe en format long
df_bonus = df.melt(
    id_vars="Joueur",
    value_vars=["Bonus place", "Bonus globes"],
    var_name="Type",
    value_name="Points"
)

# Barres empilées
bars_bonus = alt.Chart(df_bonus).mark_bar(size=25).encode(
    x=alt.X(
        "Joueur:N",
        sort=df["Joueur"].tolist(),                 # ordre du classement
        axis=alt.Axis(title=None, labelAngle=0)
    ),
    y=alt.Y("Points:Q", title="Points bonus"),
    color=alt.Color("Type:N", title="Type de bonus")
)

# Labels au-dessus de la barre totale
# On calcule la somme des bonus par joueur
df_bonus_total = df_bonus.groupby("Joueur")["Points"].sum().reset_index()

labels_bonus = alt.Chart(df_bonus_total).mark_text(
    align="center",
    baseline="bottom",
    dy=-5,
    color="black",
    fontSize=12
).encode(
    x=alt.X("Joueur:N", sort=df["Joueur"].tolist()),
    y="Points:Q",
    text="Points:Q"
)

st.altair_chart((bars_bonus + labels_bonus).properties(height=400), use_container_width=True)
