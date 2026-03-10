import streamlit as st
import altair as alt

from core.ibu.client import IBUClient
from utils.ui_components import sidebar_menu, user_header
from utils.biathlon_data import DISCIPLINES_DISPLAY


# ---------------------------------------------------------
# Configuration de la page
# ---------------------------------------------------------

st.session_state["current_page"] = "4_Resultats_Officiels"

sidebar_menu()
user_header()

st.set_page_config(layout="wide")

st.title("📊 Résultats Officiels – Top 10")
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
men_results = ibu.current_men_standings
men_results.load_all()

women_results = ibu.current_women_standings
women_results.load_all()


# ---------------------------------------------------------
# Affichage discipline par discipline
# ---------------------------------------------------------

for attr, display_name in DISCIPLINES_DISPLAY:
    st.markdown(f"## 🏅 {display_name}")

    col1, col2 = st.columns(2)

    # Récupération dynamique des DataFrames
    df_men = getattr(men_results, attr)
    df_women = getattr(women_results, attr)

    df_men.drop("id", axis=1, inplace=True)
    df_women.drop("id", axis=1, inplace=True)

    with col1:
        st.subheader("Hommes")
        st.dataframe(
            df_men.reset_index(drop=True),
            use_container_width=True,
            hide_index=True
        )

    with col2:
        st.subheader("Femmes")
        st.dataframe(
            df_women.reset_index(drop=True),
            use_container_width=True,
            hide_index=True
        )

    # Préparation des données Hommes
    df_m = df_men.copy()
    df_m["rank"] = df_m["rank"].astype(int)
    rank_order_m = df_m["rank"].sort_values().unique().tolist()

    bars_m = alt.Chart(df_m).mark_bar(size=20).encode(
        y=alt.Y(
            "rank:N",
            sort=rank_order_m,
            axis=alt.Axis(title="Rang", labelAngle=0)
        ),
        x=alt.X("points:Q", title="Points"),
        color=alt.value("#1f77b4")  # bleu discret
    )

    labels_m = alt.Chart(df_m).mark_text(
        align="left",
        baseline="middle",
        dx=5,
        color="black",
        fontSize=11
    ).encode(
        y=alt.Y("rank:N", sort=rank_order_m),
        x="points:Q",
        text="name:N"
    )

    st.subheader("Écarts – Hommes")
    st.altair_chart((bars_m + labels_m).properties(height=350), use_container_width=True)

    # Préparation des données Femmes
    df_w = df_women.copy()
    df_w["rank"] = df_w["rank"].astype(int)
    rank_order_w = df_w["rank"].sort_values().unique().tolist()

    bars_w = alt.Chart(df_w).mark_bar(size=20).encode(
        y=alt.Y(
            "rank:N",
            sort=rank_order_w,
            axis=alt.Axis(title="Rang", labelAngle=0)
        ),
        x=alt.X("points:Q", title="Points"),
        color=alt.value("#e377c2")  # rose discret
    )

    labels_w = alt.Chart(df_w).mark_text(
        align="left",
        baseline="middle",
        dx=5,
        color="black",
        fontSize=11
    ).encode(
        y=alt.Y("rank:N", sort=rank_order_w),
        x="points:Q",
        text="name:N"
    )

    st.subheader("Écarts – Femmes")
    st.altair_chart((bars_w + labels_w).properties(height=350), use_container_width=True)

    st.markdown("---")
