import streamlit as st
import pandas as pd
import uuid

from utils.ui_components import sidebar_menu, user_header
from utils.sheets import read_all, append_row, parse_members

st.set_page_config(page_title="Mes Ligues", layout="wide")
st.session_state["current_page"] = "Mes_Ligues"

sidebar_menu()
user_header()

user = st.session_state.get("user")
if not user:
    st.error("Tu dois être connecté pour accéder à cette page.")
    st.stop()


st.title("🏆 Mes Ligues")

records = read_all("Leagues")

if records:
    df = pd.DataFrame(records)
else:
    df = pd.DataFrame(columns=["league_id", "league_name", "owner", "members"])


df["members_list"] = df["members"].apply(parse_members)

st.subheader("👥 Ligues dont je fais partie")

my_leagues = df[df["members_list"].apply(lambda lst: user in lst)]

if my_leagues.empty:
    st.info("Tu ne fais partie d’aucune ligue pour l’instant. Crées ta ligue ou rejoins-en une !")
else:
    for _, row in my_leagues.iterrows():
        is_owner = (row["owner"] == user)
        owner_badge = " 👑" if is_owner else ""

        with st.container(border=True):
            st.markdown(f"### {row['league_name']}{owner_badge}")
            st.markdown(f"**Membres :** {', '.join(row['members_list'])}")

            if st.button("➡️ Entrer dans cette ligue", key=f"enter_{row['league_id']}"):
                st.session_state["current_league"] = row["league_id"]
                st.session_state["current_league_name"] = row["league_name"]
                st.success(f"Ligue sélectionnée : {row['league_name']}")


st.markdown("---")
st.subheader("➕ Créer une nouvelle ligue")

with st.form("create_league"):
    name = st.text_input("Nom de la ligue")
    submit = st.form_submit_button("Créer")

    if submit:
        if not name.strip():
            st.warning("Merci de saisir un nom.")
        else:
            league_id = str(uuid.uuid4())[:8]
            new_row = [
                league_id,
                name.strip(),
                user,
                user,
            ]
            append_row("Leagues", new_row)
            st.success(f"Ligue **{name}** créée !")
            st.rerun()


# st.markdown("---")
# st.subheader("🔑 Rejoindre une ligue")

# with st.form("join_league"):
#     code = st.text_input("Code de la ligue")
#     submit_join = st.form_submit_button("Rejoindre")

#     if submit_join:
#         code = code.strip()
#         match = df[df["league_id"] == code]

#         if match.empty:
#             st.error("Aucune ligue trouvée.")
#         else:
#             row = match.iloc[0]
#             members = row["members_list"]

#             if user in members:
#                 st.info("Tu fais déjà partie de cette ligue.")
#             else:
#                 members.append(user)
#                 update_cell(
#                     sheet_name="Leagues",
#                     key_column="league_id",
#                     key_value=code,
#                     updated_values={"members": ", ".join(members)}
#                 )
#                 st.success(f"Tu as rejoint **{row['name']}** !")
#                 st.experimental_rerun()



# import pdb
# pdb.set_trace()
