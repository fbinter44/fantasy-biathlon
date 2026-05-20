import streamlit as st
from streamlit_autorefresh import st_autorefresh

from utils.ui_components import sidebar_menu, user_header, render_deadline_banner
from utils.sheets import get_sheet, get_player_row
from utils.auth import convert_id_to_name
from utils.biathlon_data import athlete_label, get_index, DISPLAY_H, DISPLAY_F, DISPLAY_TO_IBUID


# ---------------------------------------------------------
# 1) Configuration de la page
# ---------------------------------------------------------

st.session_state["current_page"] = "1_Pronostics_Modifier"
sidebar_menu()
user_id = st.session_state.get("user")
username = convert_id_to_name(user_id)
user_header(username)

if not user_id:
    st.error("Tu dois être connecté pour accéder à cette page.")
    st.stop()


# ---------------------------------------------------------
# 2) TIMER DYNAMIQUE (isolé dans un placeholder)
# ---------------------------------------------------------

deadline_passed = render_deadline_banner()


# ---------------------------------------------------------
# 3) Lecture des pronostics existants
# ---------------------------------------------------------

sheet = get_sheet("Pronostics")
row_index, row_values = get_player_row(sheet, user_id)

if row_values:
    existing_top5_h = row_values[1].split(",")
    existing_top5_f = row_values[2].split(",")
    existing_globes = row_values[3:11]
else:
    existing_top5_h = [""] * 5
    existing_top5_f = [""] * 5
    existing_globes = [""] * 8


# ---------------------------------------------------------
# 4) Formulaire
# ---------------------------------------------------------

st.title("📝 Voir/Modifier mes pronostics")

col_h, col_f = st.columns(2)

# --- HOMMES ---
with col_h:
    st.subheader("🧔 Hommes — Top 5 général")

    top5_h = []
    used_h = set()
    for i in range(1, 6):
        existing_display = athlete_label(existing_top5_h[i-1])
        available = [d for d in DISPLAY_H if d not in used_h or d == existing_display]

        selected_display = st.selectbox(
            f"Place {i}",
            available,
            index=get_index(available, existing_display),
            key=f"top5_h_{i}",
            disabled=deadline_passed
        )

        top5_h.append(DISPLAY_TO_IBUID[selected_display])
        used_h.add(selected_display)

    st.subheader("Globes Hommes")

    globe_sprint_h = DISPLAY_TO_IBUID[st.selectbox(
        "Globe Sprint",
        DISPLAY_H,
        index=get_index(DISPLAY_H, athlete_label(existing_globes[0])),
        key="globe_sprint_h",
        disabled=deadline_passed
    )]

    globe_pursuit_h = DISPLAY_TO_IBUID[st.selectbox(
        "Globe Poursuite",
        DISPLAY_H,
        index=get_index(DISPLAY_H, athlete_label(existing_globes[2])),
        key="globe_pursuit_h",
        disabled=deadline_passed
    )]

    globe_individual_h = DISPLAY_TO_IBUID[st.selectbox(
        "Globe Individuel",
        DISPLAY_H,
        index=get_index(DISPLAY_H, athlete_label(existing_globes[4])),
        key="globe_individual_h",
        disabled=deadline_passed
    )]

    globe_mass_h = DISPLAY_TO_IBUID[st.selectbox(
        "Globe Mass Start",
        DISPLAY_H,
        index=get_index(DISPLAY_H, athlete_label(existing_globes[6])),
        key="globe_mass_h",
        disabled=deadline_passed
    )]

# --- FEMMES ---
with col_f:
    st.subheader("👩 Femmes — Top 5 général")

    top5_f = []
    used_f = set()
    for i in range(1, 6):
        existing_display = athlete_label(existing_top5_f[i-1])
        available = [d for d in DISPLAY_F if d not in used_f or d == existing_display]

        selected_display = st.selectbox(
            f"Place {i}",
            available,
            index=get_index(available, existing_display),
            key=f"top5_f_{i}",
            disabled=deadline_passed
        )

        top5_f.append(DISPLAY_TO_IBUID[selected_display])
        used_f.add(selected_display)


    st.subheader("Globes Femmes")

    globe_sprint_f = DISPLAY_TO_IBUID[st.selectbox(
        "Globe Sprint",
        DISPLAY_F,
        index=get_index(DISPLAY_F, athlete_label(existing_globes[1])),
        key="globe_sprint_f",
        disabled=deadline_passed
    )]

    globe_pursuit_f = DISPLAY_TO_IBUID[st.selectbox(
        "Globe Poursuite",
        DISPLAY_F,
        index=get_index(DISPLAY_F, athlete_label(existing_globes[3])),
        key="globe_pursuit_f",
        disabled=deadline_passed
    )]

    globe_individual_f = DISPLAY_TO_IBUID[st.selectbox(
        "Globe Individuel",
        DISPLAY_F,
        index=get_index(DISPLAY_F, athlete_label(existing_globes[5])),
        key="globe_individual_f",
        disabled=deadline_passed
    )]

    globe_mass_f = DISPLAY_TO_IBUID[st.selectbox(
        "Globe Mass Start",
        DISPLAY_F,
        index=get_index(DISPLAY_F, athlete_label(existing_globes[7])),
        key="globe_mass_f",
        disabled=deadline_passed
    )]


# ---------------------------------------------------------
# 5) Validation
# ---------------------------------------------------------

all_filled = all([
    *top5_h, *top5_f,
    globe_sprint_h, globe_sprint_f,
    globe_pursuit_h, globe_pursuit_f,
    globe_individual_h, globe_individual_f,
    globe_mass_h, globe_mass_f
])

if not all_filled:
    st.warning("Merci de remplir **tous** les pronostics avant de sauvegarder.")

# Vérification des doublons dans les TOP 5
duplicates_h = len(top5_h) != len(set(top5_h))
duplicates_f = len(top5_f) != len(set(top5_f))

if duplicates_h:
    st.error("Tu as sélectionné deux fois le même biathlète dans le TOP 5 Hommes.")
if duplicates_f:
    st.error("Tu as sélectionné deux fois le même biathlète dans le TOP 5 Femmes.")


# ---------------------------------------------------------
# 6) Sauvegarde
# ---------------------------------------------------------

can_save = all_filled and not deadline_passed and not duplicates_h and not duplicates_f
if st.button("💾 Enregistrer mes pronostics", disabled=not can_save):

    row_values = [
        user_id,
        ",".join(top5_h),
        ",".join(top5_f),
        globe_sprint_h, globe_sprint_f,
        globe_pursuit_h, globe_pursuit_f,
        globe_individual_h, globe_individual_f,
        globe_mass_h, globe_mass_f
    ]

    players_column = sheet.col_values(1)

    if user_id in players_column:
        row_index = players_column.index(user_id) + 1
        sheet.update(f"A{row_index}:K{row_index}", [row_values])
        st.success("Tes pronostics ont été mis à jour ✅")
    else:
        sheet.append_row(row_values)
        st.success("Tes pronostics ont été enregistrés ✅")

    
# ---------------------------------------------------------
# 7) Rafraîchissement automatique (TOUJOURS TOUT EN BAS)
# ---------------------------------------------------------

st_autorefresh(interval=1000*60, key="timer_only")
