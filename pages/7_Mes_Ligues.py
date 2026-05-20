import streamlit as st
import pandas as pd
import uuid

from utils.ui_components import sidebar_menu, user_header
from utils.sheets import read_all, append_row, parse_members, update_cell
from utils.auth import get_mapping_id_to_name, generate_unique_invite_code


st.set_page_config(page_title="Mes Ligues", layout="wide")
st.session_state["current_page"] = "Mes_Ligues"

sidebar_menu()
user_id = st.session_state.get("user")
if user_id:
    id_to_name = get_mapping_id_to_name()
    username = id_to_name[user_id]
else:
    username = None
user_header(username)

if not user_id:
    st.error("Tu dois être connecté pour accéder à cette page.")
    st.stop()


st.title("🏆 Mes Ligues")

records = read_all("Leagues")

if records:
    df = pd.DataFrame(records)
else:
    df = pd.DataFrame(columns=["league_id", "league_name", "owner", "members", "invite_code"])


df["members_list"] = df["members"].apply(parse_members)

st.subheader("👥 Ligues dont je fais partie")

my_leagues = df[df["members_list"].apply(lambda lst: user_id in lst)]

if my_leagues.empty:
    st.info("Tu ne fais partie d’aucune ligue pour l’instant. Crées ta ligue ou rejoins-en une !")
else:
    for _, row in my_leagues.iterrows():
        member_names = [id_to_name.get(uid, "Unknown") for uid in row["members_list"]]
        is_owner = (row["owner"] == user_id)
        owner_badge = " 👑" if is_owner else ""
        invite_code = row.get("invite_code", None)

        with st.container(border=True):
            st.markdown(f"### {row['league_name']}{owner_badge}")
            st.markdown(f"**Membres :** {', '.join(member_names)}")

            # Si owner → afficher le code d’invitation
            if is_owner and invite_code:
                st.markdown(
                    f"""
                    <div style="
                        margin: 6px 0 12px 0;
                        padding: 8px 12px;
                        background: #f5f7ff;
                        border: 1px solid #d9dfff;
                        border-radius: 6px;
                        display: inline-block;
                    ">
                        <b>Code d’invitation :</b> <span style="font-size:16px;">{invite_code}</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            if st.button("➡️ Entrer dans cette ligue", key=f"enter_{row['league_id']}"):
                st.session_state["current_league"] = row["league_id"]
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
            invite_code = generate_unique_invite_code()
            new_row = [
                league_id,
                name.strip(),
                user_id,
                user_id,
                invite_code
            ]
            append_row("Leagues", new_row)
            st.success(f"Ligue **{name}** créée ! Code d’invitation : {invite_code}")
            st.rerun()


st.markdown("---")
st.subheader("🔑 Rejoindre une ligue")

with st.form("join_league"):
    code = st.text_input("Code de la ligue")
    submit_join = st.form_submit_button("Rejoindre")

    if submit_join:
        code = code.strip()
        match = df[df["invite_code"] == code]

        if match.empty:
            st.error("Aucune ligue trouvée.")
        else:
            row = match.iloc[0]
            idx = df.index[df["invite_code"] == code].tolist()[0]
            members = parse_members(row["members"])

            if user_id in members:
                st.info("Tu fais déjà partie de cette ligue.")
            else:
                members.append(user_id)
                new_members_str = ", ".join(members)

                # Mise à jour de la colonne "members"
                update_cell(
                    name="Leagues",
                    row=idx + 2,
                    col=4,
                    value=new_members_str
                )
                st.success(f"Tu as rejoint **{row['league_name']}** !")
                st.rerun()
