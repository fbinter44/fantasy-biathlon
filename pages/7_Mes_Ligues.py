import streamlit as st
import pandas as pd
import uuid

from utils.ui_components import sidebar_menu, user_header
from utils.sheets import read_all, append_row, parse_members, update_cell, get_sheet
from utils.auth import get_mapping_id_to_name, generate_unique_invite_code, convert_league_id_to_name


st.set_page_config(page_title="Mes Ligues", layout="wide")
st.session_state["current_page"] = "Mes_Ligues"

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


st.title("🏔️ Mes Ski Clubs")

records = read_all("Leagues")

if records:
    df = pd.DataFrame(records)
else:
    df = pd.DataFrame(columns=["league_id", "league_name", "owner", "members", "invite_code"])

if not st.session_state.get("current_league"):
    st.markdown(
        """
        <div style="
            background: #eef6ff;
            border-left: 6px solid #4a90e2;
            padding: 12px 16px;
            border-radius: 6px;
            margin-bottom: 20px;
            font-size: 16px;
        ">
            <b>ℹ️ Sélectionne un ski club pour accéder aux pronos, résultats et classements !</b>
        </div>
        """,
        unsafe_allow_html=True
    )

df["members_list"] = df["members"].apply(parse_members)

st.subheader("🛠️ Gérer mes ski clubs")

my_leagues = df[df["members_list"].apply(lambda lst: user_id in lst)]

if my_leagues.empty:
    st.info("Tu ne fais partie d’aucun ski club pour l’instant. Crées ton ski club ou rejoins-en un !")
else:
    for _, row in my_leagues.iterrows():
        member_names = [id_to_name.get(uid, "Unknown") for uid in row["members_list"]]
        is_owner = (row["owner"] == user_id)
        owner_badge = " 👑" if is_owner else ""
        invite_code = row.get("invite_code", None)
        league_id = row["league_id"]
        league_name = row["league_name"]
        members = parse_members(row["members"])

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

            col1, col2 = st.columns([1, 1])

            with col1:
                selected_id = st.session_state.get("current_league")
                if st.button(
                    "➡️ Sélectionner ce ski club", 
                    key=f"enter_{row['league_id']}",
                    disabled=(selected_id==league_id)
                ):
                    st.session_state["current_league"] = row["league_id"]
                    st.success(f"Ligue sélectionnée : {row['league_name']}")
                    st.rerun()

            # --- ACTIONS DE GESTION ---
            with col2:
                # Si owner → supprimer la ligue
                if is_owner:
                    if st.button("🗑️ Supprimer ce ski club", key=f"delete_{league_id}"):
                        sheet = get_sheet("Leagues")
                        idx = df.index[df["league_id"] == league_id].tolist()[0]
                        sheet.delete_rows(idx + 2)  # +2 = header + index 0-based
                        st.success(f"La ligue **{league_name}** a été supprimée.")
                        st.rerun()

                # Si membre mais pas owner -> quitter la ligue
                else:
                    if st.button("🚪 Quitter ce ski club", key=f"leave_{league_id}"):
                        if user_id in members:
                            members.remove(user_id)
                            new_members_str = ", ".join(members)
                            
                            # Mise à jour de la colonne "members"
                            idx = df.index[df["league_id"] == league_id].tolist()[0]
                            update_cell(
                                name="Leagues",
                                row=idx + 2,
                                col=4,
                                value=new_members_str
                            )

                            st.success(f"Tu as quitté le ski club **{league_name}**.")
                            st.rerun()
                        else:
                            st.error("Erreur : tu n'es pas membre de ce ski club.")


st.markdown("---")
st.subheader("➕ Créer un Ski Club")

with st.form("create_league"):
    name = st.text_input("Nom du ski club")
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
            st.success(f"Ski Club **{name}** créée ! Code d’invitation : {invite_code}")
            st.rerun()


st.markdown("---")
st.subheader("🔑 Rejoindre un Ski Club")

with st.form("join_league"):
    code = st.text_input("Code du ski club")
    submit_join = st.form_submit_button("Rejoindre")

    if submit_join:
        code = code.strip()
        match = df[df["invite_code"] == code]

        if match.empty:
            st.error("Aucun ski club trouvée.")
        else:
            row = match.iloc[0]
            idx = df.index[df["invite_code"] == code].tolist()[0]
            members = parse_members(row["members"])

            if user_id in members:
                st.info("Tu fais déjà partie de ce ski club.")
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
