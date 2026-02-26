import streamlit as st

def sidebar_menu():
    st.sidebar.title("Navigation")

    user = st.session_state.get("user")

    st.sidebar.page_link("pages/5_Reglement.py", label="📘 Règlement")
    if user:
        with st.sidebar.expander("📌 Pronostics", expanded=False):
            st.page_link("pages/1_Pronostics_Modifier.py", label="Voir/Modifier mes pronos")
            st.page_link("pages/2_Pronostics_Tous.py", label="Tous les pronos")

        st.sidebar.page_link("pages/3_Classement.py", label="📈 Classement")
        st.sidebar.page_link("pages/4_Resultats_Officiels.py", label="📜 Résultats officiels")
        # st.sidebar.page_link("pages/4_Mon_Compte.py", label="Mon compte")

        # Déconnexion
        if st.sidebar.button("Se déconnecter"):
            st.session_state.clear()
            st.rerun()

    else:
        # Pages visibles uniquement si déconnecté
        st.sidebar.page_link("pages/0_Login.py", label="🔐 Connexion / Inscription")


def user_header():
    st.markdown(
        """
        <style>
        .user-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 0;
        }
        .user-circle {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            background-color: #4A90E2;
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            margin-left: 10px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    user = st.session_state.get("user")

    col1, col2 = st.columns([0.8, 0.2])

    with col1:
        if user:
            initial = user[0].upper()
            st.markdown(
                f"""
                <div class="user-bar">
                    <div>Connecté en tant que <strong>{user}</strong></div>
                    <div class="user-circle">{initial}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.markdown("<em>Non connecté</em>", unsafe_allow_html=True)

    with col2:
        if user:
            if st.button("Déconnexion"):
                st.session_state.clear()
                st.rerun()