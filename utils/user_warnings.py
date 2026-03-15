import json
import streamlit as st
import os


def check_new_standings(user):
    
    state_file = "users_info/standings_state.json"
    os.makedirs("users_info", exist_ok=True)
    if not os.path.exists(state_file):
        with open(state_file, "w") as f:
            json.dump({"results_version": 1, "users_seen": {}}, f)  # fichier JSON vide

    state = json.load(open(state_file))

    global_version = state["results_version"]
    user_version = state["users_seen"].get(user, 0)

    if global_version > user_version:
        # L’utilisateur n’a pas encore vu les nouveaux résultats
        state["users_seen"][user] = global_version
        json.dump(state, open(state_file, "w"))
        return True

    return False


def check_new_results(user):
    state_file = "users_info/results_state.json"
    os.makedirs("users_info", exist_ok=True)
    if not os.path.exists(state_file):
        with open(state_file, "w") as f:
            json.dump({"results_version": 1, "users_seen": {}}, f)  # fichier JSON vide

    state = json.load(open(state_file))

    global_version = state["results_version"]
    user_version = state["users_seen"].get(user, 0)

    if global_version > user_version:
        # L’utilisateur n’a pas encore vu les nouveaux résultats
        state["users_seen"][user] = global_version
        json.dump(state, open(state_file, "w"))
        return True

    return False


def show_toast(message):
    st.markdown(f"""
    <style>
    @keyframes slidein {{
        from {{ bottom: -50px; opacity: 0; }}
        to {{ bottom: 30px; opacity: 1; }}
    }}
    .toast {{
        position: fixed;
        bottom: 30px;
        right: 30px;
        background-color: #1e88e5;
        color: white;
        padding: 16px 22px;
        border-radius: 10px;
        font-size: 17px;
        font-weight: 600;
        box-shadow: 0 4px 12px rgba(0,0,0,0.25);
        animation: slidein 0.4s ease-out;
        z-index: 9999;
    }}
    </style>

    <div class="toast">
        {message}
    </div>
    """, unsafe_allow_html=True)
